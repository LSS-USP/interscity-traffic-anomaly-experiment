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
    dom = minidom.parse("map.xml")\
            .getElementsByTagName('link')
    results = {}
    for u in dom:
        results[int(u.getAttribute('id'))] = float(u.getAttribute('length'))
    return results


db = {}
edges = load_edges()
# print("edges => ", edges)
print("Edges loading completed...")

def callback(ch, method, properties, body):
    payload = json.loads(body)
    prev_point = db.get(payload["uuid"])
    if (prev_point != None):
        prev_tick, prev_edge_id = prev_point
        new_tick, edge_id = (payload["tick"], payload["nodeID"])
        if (new_tick > prev_tick):
            print("edge_id => ", edge_id)
            edge_length = edges.get(int(edge_id), None)

            if (edge_length == None):
                print("%")
                return

            velocity_data = {
                "edge_id": edge_id,
                "avg_speed": edge_length / (new_tick - prev_tick)
            }
            print("Posting this data to Kafka: ", velocity_data)
            producer.send('data_stream', json.dumps(velocity_data).encode())
        else:
            print("Wrong tick arrived! WARNING")
    else:
        print("X")
    db[payload["uuid"]] = (payload["tick"], payload["nodeID"])

channel.basic_consume(callback,
                      queue=queue_name,
                      no_ack=True)


print("Queue consuming starting...")
channel.start_consuming()
