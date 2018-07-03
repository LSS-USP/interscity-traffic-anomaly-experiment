#!/usr/bin/env python
import pika
from kafka import KafkaConsumer
import json
import utm
import requests
from xml.dom import minidom

# rabbitmq config
connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()
channel.exchange_declare(exchange='traffic_sign', exchange_type='topic')

# kafka config
consumer = KafkaConsumer('anomalies')

def loadNodes():
    dom = minidom.parse("map.xml")\
            .getElementsByTagName('node')
    mylist = []
    for u in dom:
        mylist.append([
            int(u.getAttribute('id')),
            float(u.getAttribute('x')),
            float(u.getAttribute('y'))
        ])
    return mylist


print("Loading nodes...")
nodes = {}
for u in loadNodes():
    nodes[u[0]] = [u[1], u[2]]
print("Nodes loaded...")


for msg in consumer:
    print("***Anomaly detected***")
    print(msg)
    payload = msg.value
    anomaly = json.loads(payload)

    fromNodeId = anomaly.get("fromId")
    toNodeId = anomaly.get("toId")
    edgeId = anomaly.get("edgeId")

    # easting = float(nodes[fromNodeId][0])
    # northing = float(nodes[fromNodeId][1])
    # print("Easting: %s, Northing: %s => " % (easting, northing))
    #
    # host = "http://localhost:8000/discovery/"
    # coordinates = utm.to_latlon(easting/10, northing, 19, 'K')
    # print("Anomaly coordinates: ", coordinates)
    # endpoint = "resources?capability=traffic_board&lat={0}&lon={1}&radius=500"\
    #         .format(coordinates[0], coordinates[1])

    # try:
    #     resp = requests.get(host + endpoint)
    #     resources = json.loads(resp.text)["resources"]
    #
    #     for r in resources:
    #         print("Resource %s found!" % r)
    #         description = r.get("description")
    #         if (description == None):
    #             raise Exception("""
    #             Your board resources are incorrect. In their description
    #             you must have their ids.
    #             """)
    #
    #         board_id = 1 #json.loads(description) TODO: default avlue
    #         message = "%s.%s.%s" % (board_id, fromNodeId, toNodeId)
    #         channel.basic_publish(exchange='traffic_sign',
    #                               routing_key='#',
    #                               body=message)

    #print(" [x] Sent %r" % msg)
    # except:
    #     raise Exception("""
    #         Your resource_discovery looks weird.
    #         Usage: `$python3 kafka_to_rabbitmq.py {resource_discovery_url}`
    #         (default resource_discovery_url: http://localhost:8000/discovery/)
    #     """)
