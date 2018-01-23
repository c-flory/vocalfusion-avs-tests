#!/usr/bin/env python
import subprocess
import os

if __name__ == '__main__':
  out_folder = 'out'
  tests = ['test_repeat_file', 'test_repeat_seq', 'test_repeat_mix', 'test_repeat_0',
           'test_seq', 'test_level',
           'test_mix', 'test_mix_mix',
           'test_seconds_seq', 'test_seconds_mix', 'test_samples_seq', 'test_samples_mix']
  for test in tests:
    print "Generating {}".format(test)
    subprocess.call(["../wav_creator.py", test + '.xml', '-o', os.path.join(out_folder, test + '.wav')])

  # Compare all the generated wav files with each other
  print "Checking outputs"
  reference = os.path.join(out_folder, tests[0] + '.wav')
  for test in tests[1:]:
    test_wav = os.path.join(out_folder, test + '.wav')
    diff = subprocess.call(["diff", reference, test_wav])
    if diff:
      print "ERROR: {} and {} differ".format(reference, test_wav)

  print "Done"
