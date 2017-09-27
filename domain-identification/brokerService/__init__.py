#!/usr/bin/python
# -*- coding: utf-8 -*-
from rabbitmq_config import *
from Subscriber import RabbitMQSubscriber
from Publisher import RabbitMQPublisher

Subscriber = RabbitMQSubscriber(host=RabbitMQ_Host)
Subscriber.declare_exchange(exchange_name=Status_Exchange)
Subscriber.declare_queue(queue_name=Status_Queue,
                         routing_key=Status_Exchange)
Subscriber.declare_exchange(exchange_name=EmailVerification_Exchange)
Subscriber.declare_queue(queue_name=EmailVerification_Queue,
                         routing_key=EmailVerification_Exchange)
Subscriber.declare_exchange(exchange_name=EmailComposer_Exchange)
Subscriber.declare_queue(queue_name=EmailComposer_Queue,
                         routing_key=EmailComposer_Exchange)
Subscriber.declare_exchange(exchange_name=Pattern_Exchange)
Subscriber.declare_queue(queue_name=Pattern_Queue,
                         routing_key=Pattern_Exchange)
Subscriber.declare_exchange(exchange_name=Domain_Exchange)
Subscriber.declare_queue(queue_name=Domain_Queue,
                         routing_key=Domain_Exchange)
Subscriber.declare_exchange(exchange_name=EmailPostfix_Exchange)
Subscriber.declare_queue(queue_name=EmailPostfix_Queue,
                         routing_key=EmailPostfix_Exchange)
Subscriber.close()
