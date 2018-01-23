#!/usr/bin/env python

""" Wave file creator from a XML definition which can be of the form:
<Channels>
  <Channel>
    <Seq>
      <File level="-3dB" repeat="10">audio1.wav</File>
    </Seq>
  </Channel>
  <Channel>
    <Mix>
      <Seq>
        <Silence seconds="1"/>
        <File level="0dB" repeat="5">audio2.wav</File>
      </Seq>
      <Seq>
        <File level="-12dB" repeat="5">audio3.wav</File>
      </Seq>
    </Mix>
  </Channel>
</Channels>
"""
import argparse
import os
import platform
import re
import struct
import signal
import subprocess
import sys
import time
import numpy as np
from array import array
from utils.wav_handler import write_wav_file, load_wav_data
from utils.xml_to_object import xml_to_objects
from pprint import pprint

def check_sample_rates(channels):
  sample_rates = set()
  for channel in channels:
    channel.get_sample_rates(sample_rates)

  if len(sample_rates) != 1:
    print "ERROR: Different sample rates used {}".format(sample_rates)
    sys.exit(1)

  return next(iter(sample_rates))

def make_wav(args):
  channels = xml_to_objects(args)
  num_channels = len(channels)
  sample_rate = check_sample_rates(channels)


  channel_samples = [c.get_samples(sample_rate) for c in channels]

  # Ensure all channels have the same length
  track_len = max([len(cs) for cs in channel_samples])

  if args.verbose:
    print "Creating {}s ({} samples), {}-channel output with {} sample rate".format(
      track_len/float(sample_rate), track_len, num_channels, sample_rate)

  for samples in channel_samples:
    samples.resize(track_len, refcheck=False)

  data = np.dstack(channel_samples).flatten()

  # Clip the data rather than have it wrap
  data = np.clip(data, -1.0, 1.0)

  # Convert data into the 16-bit range
  int16max = np.iinfo(np.int16).max
  data = np.multiply(data, int16max)
  write_wav_file(args.output_filename, sample_rate, num_channels, data)


if __name__ == '__main__':
  argparser = argparse.ArgumentParser(description='XMOS WAV file creator')
  argparser.add_argument('xml_file',
                         help='XML file defining the audio to be generated',
                         metavar='xml')
  argparser.add_argument('-r', '--root', dest='wav_root',
                         help='The top-level for input WAV files', default='.')
  argparser.add_argument('-o', '--output-filename',
                         help='filename to use for the generated WAV (will use the xml filename if none specified)',
                         default=None)
  argparser.add_argument('-v', '--verbose', action='store_true',
                         help='Enable verbose output')

  args = argparser.parse_args()

  if args.output_filename is None:
    args.output_filename = os.path.splitext(args.xml_file)[0] + ".wav"

  make_wav(args)


