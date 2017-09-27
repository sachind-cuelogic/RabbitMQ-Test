#!/usr/bin/env python
import pika
import pdb; pdb.set_trace()


connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.queue_declare(queue='hello')

def callback(ch, method, properties, body):

	print "ch==>",ch
	print "method==>",method
	print "properties==>",properties
	print "body==>",body

	print(" [x] Received %r" % body)

channel.basic_consume(callback,
                      queue='hello',
                      no_ack=True)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
