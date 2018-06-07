#!/usr/bin/python2

import xml.etree.ElementTree as ET
import copy
from sys import argv

_, filename, begin, end = argv

begin = int(begin)
end = int(end)

tree = ET.parse(filename)
trips = tree.getroot()

data = ET.Element('scsimulator_matrix')

output_name = filename.split('.')
output = open(output_name[0] + '-splited.xml', 'w')

for trip in trips.iter('trip'):
    start = int(trip.attrib['start'])
    if(start >= begin and start <= end):
        data.append(trip)

content = str(ET.tostring(data))
output.write(content)
data = ET.Element('scsimulator_matrix')
output.close()
