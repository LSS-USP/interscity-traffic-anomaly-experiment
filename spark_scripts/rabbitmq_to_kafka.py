#!/usr/bin/env python
from kafka import KafkaProducer
import pika
from xml.dom import minidom
import json

producer = KafkaProducer(bootstrap_servers='localhost:9092')
connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.exchange_declare(exchange='data_stream',
                         exchange_type='topic')


result = channel.queue_declare(exclusive=True)

queue_name = result.method.queue

channel.queue_bind(exchange='data_stream',
                    routing_key = '*.current_location.simulated',
                   queue=queue_name)


print(' [*] Waiting for logs. To exit press CTRL+C')


def load_edges():
    dom = minidom.parse("map_reduced.xml")\
            .getElementsByTagName('link')
    results = {}
    for u in dom:
        results[(int(u.getAttribute("from")), int(u.getAttribute("to")))] = [
            int(u.getAttribute('id')),
            float(u.getAttribute('length'))
        ]
    return results


db = {}
edges = load_edges()
print("Edges loading completed...")

def callback(ch, method, properties, body):
    payload = json.loads(body)
    prev_point = db.get(payload["uuid"])
    if (prev_point != None):
        prev_tick, from_nodeid = prev_point
        new_tick, to_nodeid = (payload["tick"], payload["nodeID"])
        if (new_tick > prev_tick):
            result = edges.get((int(from_nodeid), int(to_nodeid)))
            if (result == None):
                return
            edge_id, edge_length = result

            velocity_data = {
                "to": to_nodeid,
                "from": from_nodeid,
                "edge_id": edge_id,
                "avg_speed": edge_length / (new_tick - prev_tick)
            }
            print("Posting this data to Kafka: ", velocity_data)
            producer.send('data_stream', json.dumps(velocity_data).encode())
        else:
            print("Wrong tick arrived! WARNING")
    db[payload["uuid"]] = (payload["tick"], payload["nodeID"])

channel.basic_consume(callback,
                      queue=queue_name,
                      no_ack=True)


print("Queue consuming starting...")
channel.start_consuming()
