import xml.etree.cElementTree as ET
import argparse
import sys

if __name__ == '__main__':
	argparser = argparse.ArgumentParser()
	argparser.add_argument('--channels', default=1, type=int)
	argparser.add_argument('--file')
	argparser.add_argument("--noise")
	argparser.add_argument('--filelevel', default='0')
	argparser.add_argument('--noiselevel', default='0')
	args=argparser.parse_args()

	channels = ET.Element("Channels")

	channel = ET.SubElement(channels, "Channel")
	ET.SubElement(channel, "File", level=args.filelevel + "dB").text = args.file

	if args.channels is 2:
		channel = ET.SubElement(channels, "Channel")
		ET.SubElement(channel, "File", level=args.noiselevel + "dB").text = args.noise

	tree = ET.ElementTree(channels)
	filewrite = args.file.strip(".wav")
	if args.channels is 1:
		tree.write(("{}_{}.xml").format(filewrite, args.filelevel))
	if args.channels is 2:
		tree.write(("{}_{}_{}.xml").format(filewrite, args.noise, args.noiselevel))