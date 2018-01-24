import lxml.etree
import lxml.objectify

class IterableConfigItem(object):
    """ A generator that produces pairs of the parameter name and value
    """
    def __init__(self, name, options):
        self.name = name
        self.options = options

    def __iter__(self):
        return self

    def next(self):
        if self.options:
            option = self.options.pop()
            return (self.name, option)
        else:
            raise StopIteration()


def parse_parameters(args, xml):
    """ Convert the <Parameters> sub nodes to a list of (Name, [Values]).
    """
    parameters = []
    for child in xml:
      parameters.append(IterableConfigItem(child.tag, child.text.split()))
    return parameters


def xml_to_configurations(args):
  channels = []
  parser = lxml.etree.XMLParser(remove_comments=True)
  xml = lxml.objectify.parse(args.xml_file, parser=parser)
  root = xml.getroot()

  file = None
  delay = 0
  parameters = {}

  for child in root:
    if child.tag == 'Parameters':
      parameters = parse_parameters(args, child)
    elif child.tag == 'File':
      file = child.text
    elif child.tag == 'Delay':
      try:
        delay = int(child.text)
      except ValueError:
        print "ERROR: Unable to parse '{}' for Delay".format(xml.text)

  return (file, delay, parameters)
