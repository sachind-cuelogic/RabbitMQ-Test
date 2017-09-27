import json
import uuid
import time, threading
from domainIdentifier import app
from domainIdentifier.domain_crawler import (getDomains, logger, getCompanyDomainList ,
                                publishMessage,removeCompanySuffix)
from domainIdentifier.utils import getMxRecordForDomain

from brokerService.Subscriber import RabbitMQSubscriber
from brokerService.rabbitmq_config import *

domain_subscriber = RabbitMQSubscriber(host=RabbitMQ_Host)

def listen():
    domain_subscriber.declare_exchange(exchange_name=Domain_Exchange)
    domain_subscriber.declare_queue(queue_name=Domain_Queue, routing_key=Domain_Exchange)
    domain_subscriber.subscribing(messageCallback)
    domain_subscriber.connection.process_data_events()

def scheduler():
    logger.info(time.ctime())
    logger.info(' [*] Waiting for messages. To exit press CTRL+C')
    listen()
    threading.Timer(10, scheduler).start()

def findDomains(message):
    CleanCompanyName = removeCompanySuffix(message['companyName']) 
    domainList = getCompanyDomainList(CleanCompanyName)
    if  not domainList.count():
        domainList = getCompanyDomainList(message['companyName'])
    if domainList.count() > 0:
        for each in domainList:
            message['domainName'] = each.domain
            message['domainSource'] = each.source
            domainMxRecord = getMxRecordForDomain(message['domainName'])
            message['domainMxRecord'] = domainMxRecord
            if not len(domainMxRecord):
                logger.info(domainMxRecord)
                message['domainName'] = ''
                publishMessage(message, Status_Exchange)
            else:
                publishMessage(message, Status_Exchange)
                publishMessage(message, Pattern_Exchange)
    else:
        getDomains(message)

def messageCallback(ch, method, properties, body):
    try:
        logger.info('Request Payload : %s' % body)
        logger.info("-"*30)
        try:
            message = json.loads(body, strict=False)
            message['currentPhase'] = 1
            logger.info('Payload : %s' % message)
            findDomains(message)
            logger.info("-"*30)
        except Exception,e:
            logger.info(str(e))
        domain_subscriber.channel.basic_ack(delivery_tag = method.delivery_tag)
    except Exception,e:
        logger.error(e)

if __name__ == "__main__":
    scheduler()
