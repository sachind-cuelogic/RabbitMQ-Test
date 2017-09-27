#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
##################################################
# RabbitMQ CONFIGURATION#
##################################################

# RabbitMQ server host

RabbitMQ_Host = str(os.environ['RABBITMQ_HOST'])

# RabbitMQ server port
RabbitMQ_Port = int(os.environ['RABBITMQ_PORT'])

##################################################
# The heartbeat timeout value defines after what
# period of time the peer TCP connection should be
# considered unreachable (down) by RabbitMQ and
# client libraries
##################################################

Heartbeat_Interval = 30

###################################################
# Predefined exchanges bound to specific queues
##################################################

Status_Exchange = 'statusExchange'
Pattern_Exchange = 'patternExchange'
Domain_Exchange = 'domainExchange'
NodeServer_Exchange = 'nodeServerExchange'
EmailComposer_Exchange = 'emailComposerExchange'
EmailVerification_Exchange = 'emailVerificationExchange'
EmailPostfix_Exchange = 'emailPostfixExchange'

###################################################
# Predefined queues bound to specific exchanges
##################################################

Status_Queue = 'statusQueue'
Pattern_Queue = 'patternQueue'
Domain_Queue = 'domainQueue'
Node_Server_Queue = 'nodeServerQueue'
EmailComposer_Queue = 'emailComposerQueue'
EmailVerification_Queue = 'emailVerificationQueue'
EmailPostfix_Queue = 'emailPostfixQueue'

###################################################
# RabbitMQ Crendentials
###################################################

RabbitMQ_User = str(os.environ['RABBITMQ_USER'])
RabbitMQ_Password = str(os.environ['RABBITMQ_PASSWORD'])

Payload_Exchange_Keys = [
    'companyName',
    'firstName',
    'lastName',
    'middleName',
    'domainName',
    'emailPattern',
    'emailId',
    'batchId',
    'jobId',
    'isEmailVerified',
    'currentPhase',
    'isEmailCatchAll',
    'domainSource',
    'domainMxRecord',
    'countryName'
    ]
