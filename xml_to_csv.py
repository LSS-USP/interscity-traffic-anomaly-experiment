#!/usr/bin/python2

import xml.etree.ElementTree as ET
import uuid
from random import randint
from sys import argv

_, filename = argv

tree = ET.parse(filename)
trips = tree.getroot()

output_name = filename.split('.')
output = open(output_name[0] + '-with-uuid.csv', 'w')

for trip in trips.iter('trip'):
    for i in range(int(trip.attrib['count'])):
        start = int(trip.attrib['start'])
        uuid_trip = str(uuid.uuid4())
        print(uuid_trip)
        new_trip = "{};{};{};{};{};{};{};{}\n".format(
            trip.attrib['name'],
            trip.attrib['origin'],
            trip.attrib['destination'],
            trip.attrib['link_origin'],
            "1",
            str(randint(start, start+25)),
            trip.attrib['mode'],
            uuid_trip
        )
        output.write(new_trip)

output.close()
