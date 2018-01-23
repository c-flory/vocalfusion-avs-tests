##!/usr/bin/env python
import sys
import os
import subprocess
import argparse
import play_record_wav
import time
import datetime

def call_to_play(args, playback_filename, results, firmware):
    print 'Testing: {} , {}'.format(firmware, playback_filename)
    test_case = firmware + ":" + playback_filename
    count = 0
    if args.sdk:
        wake_word_text = 'Listening...'
        shellcommand = './avsrun'
    else:
        wake_word_text = 'wake word detected'
        shellcommand = './shell_3'
    try:
        cmd = ['python', '-u', 'play_record_wav.py',
                '--playback-device-name', 'xCORE-AUDIO Hi-Res 2',
                os.path.join('..', '..', 'audio', 'v1p7', playback_filename),
                '--monitor-command', 'ssh pi@{} "{}"'.format(args.ip, shellcommand),
                '--monitor-regex', wake_word_text,
                '--monitor-command-startup-seconds', '3']
        #if args.debug:
        #    cmd += ['--debug']
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        for line in iter(proc.stdout.readline, b""):
            line = line.strip()
            print line
            if wake_word_text in line:
                if args.sdk:
                    count = count + 1
                    results[test_case] = count
                    print 'Count is: ', count
                else:
                    results[test_case] = line
        print "finished subprocess, count is {}\n".format(count)
        proc.stdout.close()
        return_code = proc.wait()

    except KeyboardInterrupt:
        print " WE FUCKED UP "

    with open(args.results_file, "a") as f:
        if test_case in results:
            f.write("{} got {}\n".format(test_case, results[test_case]))
        else:
            f.write("{} got No triggers\n".format(test_case))

def start_firmware(firmware):
    print "Starting firmware: {}".format(os.path.basename(firmware))
    cmd = ['xrun', firmware]
    return_code = subprocess.call(cmd)
    print "Allow time for Pi to detect USB device"
    time.sleep(10)
    print "Done starting firmware"

def test_firmware(firmware, args, results):
    kitchenlist = ['Kitchen-6dbv1.7_SoundRoomCalibrated.wav', 'Kitchen-3dbv1.7_SoundRoomCalibrated.wav', 'Kitchen-0dbv1.7_SoundRoomCalibrated.wav']
    musiclist = [ 'Music-6dbv1.7_SoundRoomCalibrated.wav', 'Music-3dbv1.7_SoundRoomCalibrated.wav', 'Music-0dbv1p7_SoundRoomCalibrated.wav']
    cleanlist = ['cleanv1p7_SoundRoomCalibrated.wav']
    alllist = musiclist + kitchenlist + cleanlist

    if firmware:
        start_firmware(firmware)

    if args.all_tracks:
        for test in alllist:
            call_to_play(args, test, results, firmware)
    else:
        if args.clean:
            call_to_play(args, cleanlist[0], results, firmware)

        if args.music_all:
            for test in musiclist:
                call_to_play(args, test, results, firmware)
        else:
            if args.music_0db:
                call_to_play(args, musiclist[2], results, firmware)
            if args.music_3db:
                call_to_play(args, musiclist[1], results, firmware)
            if args.music_6db:
                call_to_play(args, musiclist[0], results, firmware)

        if args.kitchen_all:
            for test in kitchenlist:
                call_to_play(args, test, results, firmware)
        else:
            if args.kitchen_0db:
                call_to_play(args, kitchenlist[2], results, firmware)
            if args.kitchen_3db:
                call_to_play(args, kitchenlist[1], results, firmware)
            if args.kitchen_6db:
                call_to_play(args, kitchenlist[0], results, firmware)

if __name__ == '__main__':

    argparser = argparse.ArgumentParser()
    argparser.add_argument('--all-tracks', action='store_true')
    argparser.add_argument('--music-all', action='store_true')
    argparser.add_argument('--kitchen-all', action='store_true')
    argparser.add_argument('--music_0db', action='store_true')
    argparser.add_argument('--music_3db', action='store_true')
    argparser.add_argument('--music_6db', action='store_true')
    argparser.add_argument('--kitchen_0db', action='store_true')
    argparser.add_argument('--kitchen_3db', action='store_true')
    argparser.add_argument('--kitchen_6db', action='store_true')
    argparser.add_argument('--clean', action='store_true')
    argparser.add_argument('--ip', default='10.0.98.87')
    argparser.add_argument('--firmware', nargs="+", default=[])
    argparser.add_argument('--results_file', default="test_results.txt")
    argparser.add_argument('--debug', action='store_true')
    argparser.add_argument('--sdk', action='store_true')
    args=argparser.parse_args()

    results = {}
    now = datetime.datetime.now()

    subprocess.call(["mosquitto_pub", "-t", "bored_room/door", "-m", "busy"])

    with open(args.results_file, "a") as f:
        f.write("Date : {} \n".format(now.strftime("%Y-%m-%d")))

    if args.firmware:
        for firmware in args.firmware:
            test_firmware(firmware, args, results)
    else:
        test_firmware("", args, results)

    for key in sorted(results.keys()):
        print "{} got {}".format(key, results[key])

    subprocess.call(["mosquitto_pub", "-t", "bored_room/door", "-m", "idle"])
