import os
import lxml.etree
import lxml.objectify
import re
import sys
import numpy as np
from wav_handler import write_wav_file, load_wav_data

def get_value(name, val_str, as_type):
  try:
    val = as_type(val_str)
    return val
  except ValueError:
    print "ERROR: file {} has invalid {} '{}'".format(
      filename, name, val_str)
    sys.exit(1)

def get_attribute_value(xml, name, default, as_type):
  """ Extract a value from the dictionary and check convert it to the
      requested type """
  val_str = xml.get(name, default)
  return get_value(name, val_str, as_type)

class Base(object):

  def __init__(self, args, xml):
    self.children = []
    for child in xml:
      self.children.append(eval(child.tag)(args, child))

    self.seconds = get_attribute_value(xml, 'seconds', '0', float)
    self.num_samples = get_attribute_value(xml, 'samples', '0', int)
    self.repeat = get_attribute_value(xml, 'repeat', '1', int)
    self.extend = get_attribute_value(xml, 'extend', '0', int)

    if self.seconds != 0 and self.num_samples != 0:
      print "ERROR: Silence specifies both seconds {} and samples {}".format(
        self.seconds, self.num_samples)

  def get_sample_rates(self, sample_rates):
    for child in self.children:
      child.get_sample_rates(sample_rates)

  def apply_repeat(self, samples):
    if self.repeat == 0:
      samples = np.array([])
    elif self.repeat > 1:
      samples = np.resize(samples, (len(samples) * self.repeat))
    return samples

  def apply_length(self, samples, sample_rate):
    # Resize an array to the length defind by either 'seconds' or 'samples' attribute
    if self.num_samples:
      samples = np.array(samples, copy=True)
      samples.resize((self.num_samples), refcheck=False)
    elif self.seconds:
      num_samples = int(sample_rate * self.seconds)
      samples = np.array(samples, copy=True)
      samples.resize((num_samples), refcheck=False)
    return samples


class Channel(Base):
  def __init__(self, args, xml):
    if len(xml) != 1:
      print "ERROR: 'Channel' should have a single sub-node"
      sys.exit(1)

    super(Channel, self).__init__(args, xml)

  def get_samples(self, sample_rate):
    return self.children[0].get_samples(sample_rate).copy()


class Seq(Base):
  """ Concatenate tracks
  """
  def __init__(self, args, xml):
    super(Seq, self).__init__(args, xml)
    self.repeat = get_attribute_value(xml, 'repeat', '1', int)

  def get_samples(self, sample_rate):
    samples = np.array([])
    for child in self.children:
      samples = np.hstack((samples, child.get_samples(sample_rate)))

    samples = self.apply_repeat(samples)
    samples = self.apply_length(samples, sample_rate)
    return samples


class Mix(Base):
  """ Mix multiple tracks together
  """
  def __init__(self, args, xml):
    super(Mix, self).__init__(args, xml)
    self.repeat = get_attribute_value(xml, 'repeat', '1', int)

  def get_samples(self, sample_rate):
    samples = []
    num_samples = 0
    for child in self.children:
      child_samples = child.get_samples(sample_rate).copy()
      samples.append(child_samples)
      num_samples = max(num_samples, len(child_samples))

    # Resize all arrays to arrays of the same length
    resized_samples = []
    for child, a in zip(self.children, samples):
      if child.extend:
        # Extend and repeat
        a = np.resize(a, (num_samples))
      else:
        # Extend and add zeros
        a.resize((num_samples), refcheck=False)

      resized_samples.append(a)

    # Combine into a single multi-dimensional array
    samples = np.vstack(resized_samples)

    # Scale and sum to mix
    num_children = len(self.children)
    # np.divide(samples, float(num_children))
    samples = np.sum(samples, axis=0)

    samples = self.apply_repeat(samples)
    samples = self.apply_length(samples, sample_rate)
    return samples


class Silence(Base):
  """ Handle a silence: the user can define its length in seconds or samples
  """
  def __init__(self, args, xml):
    super(Silence, self).__init__(args, xml)
    if len(xml) != 0:
      print "ERROR: 'Silence' should have no sub-nodes"

  def get_samples(self, sample_rate):
    return self.apply_length(np.array([0.0]), sample_rate)

  def get_sample_rates(self, sample_rates):
    pass


class File(Base):
  """ Handle a file: The user can specify which channel from the original,
      whether to set the level up/down by a number of dBs and whether to
      repeat.
  """

  db_regexp = re.compile(r"^([+-]?\d+)[dD][bB]$")

  def __init__(self, args, xml):
    super(File, self).__init__(args, xml)

    if len(xml) != 0:
      print "ERROR: 'File' should have no sub-nodes"

    self.filename = os.path.join(args.wav_root, xml.text)

    if args.verbose:
      print 'Loading {}...'.format(self.filename)

    (self.sample_rate, samples) = load_wav_data(self.filename)
    num_channels = len(samples)

    # Get the attributes from the XML
    self.channel = get_attribute_value(xml, 'channel', '1', int)

    if self.channel > num_channels:
      print "ERROR: file {} selecting channel {} (file only has {} channels".format(
        filename, self.channel, num_channels)

    level_str = xml.get('level', '0dB')
    m = File.db_regexp.match(level_str)
    if m is None:
      print "ERROR: file {} has invalid level '{}'".format(filename, level_str)
    else:
      self.level = get_value('level', m.group(1), float)

    # Extract the selected channel
    channel_index = self.channel - 1
    samples = samples[channel_index]

    if self.level != 0:
      # Scale the audio
      linear_amp = np.power(10.0, np.absolute(self.level)/20.0)
      if self.level >= 0:
        samples = np.multiply(samples, linear_amp)
      else:
        samples = np.divide(samples, linear_amp)

    self.samples = self.apply_repeat(samples)

  def get_samples(self, sample_rate):
    return self.apply_length(self.samples, sample_rate)

  def get_sample_rates(self, sample_rates):
    sample_rates.add(self.sample_rate)

def xml_to_objects(args):
  channels = []
  parser = lxml.etree.XMLParser(remove_comments=True)
  xml = lxml.objectify.parse(args.xml_file, parser=parser)
  root = xml.getroot()
  for child in root:
    if child.tag != 'Channel':
      print "ERROR: invalid top-level node '{}'".format(child.tag)
    else:
      channels.append(Channel(args, child))
  return channels

