#!/usr/bin/env python
from kafka import KafkaProducer
import pika

producer = KafkaProducer(bootstrap_servers='localhost:9092')
connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.exchange_declare(exchange='data_stream',
                         exchange_type='topic')

result = channel.queue_declare(exclusive=True)
queue_name = result.method.queue

channel.queue_bind(exchange='data_stream',
                   queue=queue_name,
                   routing_key='#')

print(' [*] Waiting for logs. To exit press CTRL+C')

def callback(ch, method, properties, body):
    print(" [x] %r" % body)
    producer.send('data_stream', body)

channel.basic_consume(callback,
                      queue=queue_name,
                      no_ack=True)

channel.start_consuming()
