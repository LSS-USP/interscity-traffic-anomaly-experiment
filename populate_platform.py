#!/usr/bin/python2

import xml.etree.ElementTree as ET
from sys import argv
import os
import requests

_, filename = argv

if os.environ['INTERSCITY_HOST']:
    host = os.environ['INTERSCITY_HOST']
else:
    host = 'localhost:8000'

print("[I] Check if parking_monitoring capability exists")
reponse = requests.get('http://' + host +
                       '/catalog/capabilities/current_location')

if reponse.status_code == 404:
    print("[I] Creating parking_monitoring capability")
    capability_json = { "name": "current_location",
                        "description": "current location",
                        "capability_type": "sensor" }

    response = requests.post('http://' + host + '/catalog/capabilities',
                             json=capability_json)

    if response.status_code == 422:
        print("[E] The capability parking_monitoring was not created")
        exit(-1)

tree = ET.parse(filename)
trips = tree.getroot()

print("[I] Parsing XML file")
for trip in trips.iter('trip'):
    uuid = trip.attrib['uuid']

    print("[I] Check if car {0} exists".format(uuid))
    response = requests.get('http://' + host +
                            '/catalog/resources/{0}'.format(uuid))

    if response.status_code == 404:
        print("[I] Create car {0}".format(uuid))
        car_json = { "data": {
                                "description": "Car",
                                "uuid": uuid,
                                "capabilities": [ "current_location" ],
                                "status": "active",
                                "lat": -23,
                                "lon": -46
                             }
                   }
        
        response = requests.post('http://' + host + '/catalog/resources',
                                 json=car_json)

        if response.status_code == 404:
            print("[E] The car {0} was not created".format(uuid))

print("[I] Finish \o/")
