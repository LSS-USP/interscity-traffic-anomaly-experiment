#!/usr/bin/python2

import xml.etree.ElementTree as ET
import copy
from sys import argv
from math import ceil

_, filename, begin, end = argv

begin = int(begin)
end = int(end)

tree = ET.parse(filename)
trips = tree.getroot()

data = ET.Element('scsimulator_matrix')

output_name = filename.split('.')
output = open(output_name[0] + '-splitted.xml', 'w')

for trip in trips.iter('trip'):
    start = int(trip.attrib['start'])
    count = int(trip.attrib['count'])
    if(start >= begin and start <= end):
        trip_copy = copy.deepcopy(trip)
        trip_copy.set('start', str(start - begin))
        trip_copy.set('count', str(int(ceil(count/2.0))))
        data.append(trip_copy)

content = str(ET.tostring(data))
output.write(content)
data = ET.Element('scsimulator_matrix')
output.close()
