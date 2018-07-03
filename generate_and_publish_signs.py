from xml.dom import minidom
import sys
import requests
from scipy import spatial
import random


def load_nodes(xml_path):
    dom = minidom.parse(xml_path)\
            .getElementsByTagName('node')
    list_with_id = []
    list_without_id = []
    for u in dom:
        list_without_id.append([
            float(u.getAttribute('x')),
            float(u.getAttribute('y'))
        ])
        list_with_id.append([
            int(u.getAttribute('id')),
            float(u.getAttribute('x')),
            float(u.getAttribute('y'))
        ])
    return [list_with_id, list_without_id]


def publish_on_platform(node):
    node_id, x, y = node

    host = "localhost:8000"
    print("[I] Creating traffic board in node {0}".format(node_id))

    board_json = { "data": {
                            "description": node_id,
                            "capabilities": [ "traffic_board" ],
                            "status": "active",
                            "lat": x,
                            "lon": y
                         }
               }

    print("Creating board with the following json: %s" % board_json)
    
    response = requests.post('http://' + host + '/catalog/resources',
                             json=board_json)
    if response.status_code == 404:
        print("[E] Traffic board at node {0} was not created".format(node_id))
    else:
        print("Resource publish'd...")


def closest_point(kd_tree, point, points):
    distance, closest_neighbor = kd_tree.query([point])
    idx = closest_neighbor[0]
    return points[idx]


def mount_kd_tree(points):
    return spatial.KDTree(points)


def grant_capability_exist():
    url = "http://localhost:8000/catalog/capabilities"
    requests.post(url, {"name": "traffic_board", "capability_type": "sensor"})

if __name__ == '__main__':
    if (len(sys.argv) > 1):
        grant_capability_exist()
        # xml_path = sys.argv[1]
        # nodes_with_id, nodes_without_id = load_nodes(xml_path)
        # tree = mount_kd_tree(nodes_without_id)

        node_id = sys.argv[1]
        x = sys.argv[2]
        y = sys.argv[3]
        # url = "https://epsg.io/trans?data={0},{1}&s_srs=4326&t_srs=32719".format(lat, lon)
        # coords = requests.get(url).json()[0]
        point = [int(node_id), float(x), float(y)]

        # rounded_coord = closest_point(tree, point, nodes_with_id)
        publish_on_platform(point)

    else:
        raise Exception("Usage: `generate_and_publish_signs.py node_id x y`")
