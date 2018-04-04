#!/usr/bin/python2

import xml.etree.ElementTree as ET
import uuid
import copy
from sys import argv

_, filename = argv

tree = ET.parse(filename)
trips = tree.getroot()

data = ET.Element('scsimulator_matrix')  

for trip in trips.iter('trip'):
    for i in range(int(trip.attrib['count'])):
        trip_copy = copy.deepcopy(trip)
        uuid_trip = str(uuid.uuid4())
        print(uuid_trip)
        trip_copy.set('count', '1')
        trip_copy.set('uuid', uuid_trip)
        data.append(trip_copy)

content = str(ET.tostring(data))
output_name = filename.split('.')
output = open(output_name[0] + '-with-uuid.xml', 'w')
output.write(content)
output.close()
