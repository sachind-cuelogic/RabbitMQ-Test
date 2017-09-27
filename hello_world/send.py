#!/usr/bin/env python
import pika


# Create our connection object
# Set the connection parameters to connect to rabbit-server1 on port 5672
connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.queue_declare(queue='hello')

channel.basic_publish(exchange='',
                      routing_key='hello',
                      body='Hello message')
print(" [x] Sent 'Hello World!'")
connection.close()