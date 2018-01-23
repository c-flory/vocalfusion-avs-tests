
if __name__ == '__main__':
	argparser = argparse.ArgumentParser(description='SSH and execute script in Raspberry Pi')
	argparser.add_argument('--monitor-command',
                           default=None,
                           help ='the command-line to run to monitor for ')
	argparser.add_argument('--monitor-regex',
                           default=None,
                           help ='when monitoring: the regular expression to detect a trigger')
	argparser.add_argument('--monitor-command-startup-seconds',
                           default=10,
                           type=int,
                           help ='number of seconds to allow the device to start')

	args = argparser.parse_args()