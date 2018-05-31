from xml.dom import minidom
import sys
import requests
import random


def loadNodes(xml_path):
    dom = minidom.parse(xml_path)\
            .getElementsByTagName('node')
    mylist = []
    for u in dom:
        mylist.append([
            int(u.getAttribute('id')),
            float(u.getAttribute('x')),
            float(u.getAttribute('y'))
        ])
    return mylist


def publish_on_platform(node):
    node_id, location = node
    lat, lon = location

    host = "localhost:8000"
    print("[I] Creating traffic board in node {0}".format(node_id))

    board_json = { "data": {
                            "description": "***",
                            "capabilities": [ "traffic_board" ],
                            "status": "active",
                            "lat": lat,
                            "lon": lon
                         }
               }

    print("Creating board with the following json: %s" % board_json)
    
    response = requests.post('http://' + host + '/catalog/resources',
                             json=board_json)
    if response.status_code == 404:
        print("[E] Traffic board at node {0} was not created".format(node[0]))
    else:
        print("Resource publish'd...")


if (len(sys.argv) > 1):
    xml_path = sys.argv[1]
    how_many = sys.argv[2]
    nodes = loadNodes(xml_path)
    picks = set()
    for u in range(0, int(how_many)):
        pick = random.choice(nodes)
        picks.add((pick[0], (pick[1], pick[2])))
    print("picks => %s" % picks)
    for u in picks:
        publish_on_platform(u)

else:
    raise Exception("Usage: `generate_and_publish_signs.py xml_path number`")

