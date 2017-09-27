#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import json
import pika

from rabbitmq_config import *
from domainIdentifier.domain_crawler import logger

class RabbitMQPublisher(object):

    def __init__(self, exchange_name, host):
        """
        Constructor. Initiate connection with the RabbitMQ server.
        @param exchange_name name of the exchange to send messages to
        @param host RabbitMQ server host
        """

        count = 0
        while count <= 3:
            logger.debug('Initiating channel for rabbitmq')
            self.exchange_name = exchange_name
            self.host = host
            try:
                credentials = pika.PlainCredentials(RabbitMQ_User,
                        RabbitMQ_Password)
                self.connection = \
                    pika.BlockingConnection(pika.ConnectionParameters(credentials=credentials,
                        host=host, port=RabbitMQ_Port))
                self.channel = self.connection.channel()
                self.error = False
                break
            except Exception, e:
                logger.debug('Exception in rabbitmq channel %s'
                             % str(e))
                self.error = True
            count += 1

    def publish(self, message, routing_key):
        """
        Publish message to exchange using routing key
     
        @param text message to publish
        @param routing_key message routing key
        """

        logger.debug('Publishing message for exchange %s' % routing_key)
        msg = self.__getMessage__(message)
        self.channel.basic_publish(exchange=self.exchange_name,
                                   routing_key=routing_key, body=msg,
                                   properties=pika.BasicProperties(delivery_mode=2))
        logger.debug('Published message for exchange %s'
                     % str(routing_key))

    def close(self):
        """
        Close channel and connection
        """

        self.channel.close()
        self.connection.close()

    def __getMessage__(self, message):
        logger.debug('Get formatted message to publish %s'
                     % str(message))
        formatted_message = {}
        for each in Payload_Exchange_Keys:
            if message.has_key(each):
                formatted_message[each] = message[each]
            else:
                formatted_message[each] = ''
        formatted_message['requestInitiatedTime'] = \
            message['requestInitiatedTime']
        formatted_message['requestUpdatedTime'] = \
            str(datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'
                ))
        logger.info("Updating payload")
        logger.info(str(formatted_message))
        return json.dumps(formatted_message)
