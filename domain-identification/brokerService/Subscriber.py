#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import pika

from rabbitmq_config import *
from domainIdentifier.domain_crawler import logger


class RabbitMQSubscriber(object):

    def __init__(self, host):
        """
        Constructor. Initiate connection with the RabbitMQ server.
        @param exchange_name name of the exchange to send messages to
        @param host RabbitMQ server host
        """

        logger.debug('Initiating channel for rabbitmq')
        count = 0
        while count <= 3:
            try:
                self.host = host
                credentials = pika.PlainCredentials(RabbitMQ_User,
                        RabbitMQ_Password)
                self.connection = \
                    pika.BlockingConnection(pika.ConnectionParameters(credentials=credentials,
                        host=host, port=RabbitMQ_Port,
                        heartbeat_interval=Heartbeat_Interval))
                self.channel = self.connection.channel()
                self.error = False
                break
            except Exception, e:
                logger.debug('Exception in rabbitmq channel %s'
                             % str(e))
                self.error = True
            count += 1

    def declare_exchange(
        self,
        exchange_name,
        durable=True,
        auto_delete=False,
        exchange_type='topic',
        ):
        """
        Create exchange.
        @param exchange_name name of the exchange
        @param durable will the server survive a server restart
        @param auto_delete should the server delete the exchange when it is
        no longer in use
        """

        logger.debug('Declaring exchange: %s' % str(exchange_name))
        self.exchange_name = exchange_name
        self.channel.exchange_declare(exchange=self.exchange_name,
                type=exchange_type, durable=True, passive=False)
        logger.debug('Declared exchange: %s' % str(exchange_name))

    def declare_queue(
        self,
        queue_name,
        routing_key,
        durable=True,
        ):
        """
        Create a queue and bind it to the exchange.
     
        @param queue_name Name of the queue to create
        @param routing_key binding key
        @param durable will the queue service a server restart
        @param exclusive only 1 client can work with it
        @param auto_delete should the server delete the exchange when it is
               no longer in use
        """

        logger.debug('Declaring queue %s with routing key %s'
                     % (str(queue_name), str(routing_key)))
        self.queue_name = queue_name
        self.routing_key = routing_key
        self.channel.queue_declare(queue=self.queue_name,
                                   durable=durable)
        logger.debug(str(self.exchange_name))
        self.channel.queue_bind(queue=self.queue_name,
                                exchange=self.exchange_name,
                                routing_key=self.routing_key)
        logger.debug('Declared queue %s with routing key %s'
                     % (str(queue_name), str(routing_key)))

    def subscribing(self, callback, queue_name=None):
        """
        Start a consumer and register a function to be called when a message is consumed 

        @param callback function to call
        @param queue_name name of the queue
        @param consumer_tag a client-generated consumer tag to establish context
        """

        logger.debug('[*] Waiting for messages.')
        if hasattr(self, 'queue_name') or queue_name:
            self.channel.basic_consume(callback, queue=getattr(self,
                    'queue_name', queue_name))
            try:
                logger.debug('In try %s' % str(time.time()))
                self.channel.start_consuming()
            except:
                logger.debug('In exception %s' % str(time.time()))
                credentials = pika.PlainCredentials(RabbitMQ_User,
                        RabbitMQ_Password)
                self.connection = \
                    pika.BlockingConnection(pika.ConnectionParameters(credentials=credentials,
                        host=self.host, port=RabbitMQ_Port,
                        heartbeat_interval=Heartbeat_Interval))
                self.channel = self.connection.channel()
                self.channel.start_consuming()

    def close(self):
        """
        Close channel and connection
        """

        self.channel.close()
        self.connection.close()
