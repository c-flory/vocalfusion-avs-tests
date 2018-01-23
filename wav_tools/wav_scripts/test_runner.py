#!/usr/bin/env python

""" Test runner. Runs one wav file against a number of configuation options.
    Allows the user to specify the Delay between tests, and the different
    paramameter values.
<Test>
  <File>noise_plus_voice.wav</File>
  <Delay>30</Delay>
  <Parameters>
      <Distance>1m 3m 5m</Distance>
      <Angle>30 45 90</Angle>
  </Parameters>
</Test>
"""
import argparse
import os
import itertools
import subprocess
import time
from utils.xml_to_configurations import xml_to_configurations
from pprint import pprint

def run_tests(args):
  if not os.path.exists(args.recording_directory):
    try:
      os.makedirs(args.recording_directory)
    except OSError:
      print "ERROR: Failed to create recording directory '{}'".format(args.recording_directory)
  else:
    if not os.path.isdir(args.recording_directory):
      print "ERROR: recording directory '{}' is a file".format(args.recording_directory)

  # Extract the configuration from the xml file
  (file, delay, parameters) = xml_to_configurations(args)
  file = os.path.join(args.wav_root, file)

  combinations = itertools.product(*parameters)

  for i in combinations:
    test_name = "_".join(["{}_{}".format(param, value) for (param,value) in i])
    print "Running: {}".format(test_name)

    command = ["./play_record_wav.py",
              '--playback-device-name', args.playback_device_name,
              '--recording-device-name', args.recording_device_name,
              '--recording-directory', args.recording_directory,
              '--recording-filename', test_name,
              '--recording-channel-count', '7',
              file]
    print ' '.join(command)
    if not args.preview:
      res = subprocess.call(command)
      if res:
        print "ERROR: failed to run test '{}'".format(test_name + '.wav')

    print "Done: {}".format(test_name)

    if delay:
      print "Delay: {}".format(delay)
      if not args.preview:
        time.sleep(delay)

if __name__ == '__main__':
  argparser = argparse.ArgumentParser(description='XMOS WAV file creator')
  argparser.add_argument('xml_file',
                         help='XML file defining the audio to be generated',
                         metavar='xml')
  argparser.add_argument('-r', '--root', dest='wav_root',
                         help='The top-level for input WAV files', default='.')
  argparser.add_argument('--playback-device-name',
                         default='Built-in Output',
                         help ='name of the playback device')
  argparser.add_argument('--recording-directory',
                         default='.',
                         help='directory where recorded file will be placed')
  argparser.add_argument('--recording-filename',
                         help='filename to use for the recorded WAV')
  argparser.add_argument('--recording-device-name',
                         # default='Built-in Microphone',
                         default='XMOS',
                         help ='name of the recording device')
  argparser.add_argument('--preview',
                         action='store_true',
                         help ='simply show what will be done')

  args = argparser.parse_args()

  run_tests(args)
