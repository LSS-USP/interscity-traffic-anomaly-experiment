#!/usr/bin/python2

import xml.etree.ElementTree as ET
from sys import argv
import os
import requests
import csv

_, filename = argv

if os.environ.get('INTERSCITY_HOST') is not None:
    host = os.environ['INTERSCITY_HOST']
else:
    host = 'localhost:8000'

print("[I] Check if current_location capability exists")
reponse = requests.get('http://' + host +
                       '/catalog/capabilities/current_location')

if reponse.status_code == 404:
    print("[I] Creating current_location capability")
    capability_json = { "name": "current_location",
                        "description": "current location",
                        "capability_type": "sensor" }

    response = requests.post('http://' + host + '/catalog/capabilities',
                             json=capability_json)

    if response.status_code == 422:
        print("[E] The capability current_location was not created")
        exit(-1)


with open(filename) as csvfile:
    reader = csv.reader(csvfile, delimiter=';')
    for row in reader:
        uuid = row[7] 

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
