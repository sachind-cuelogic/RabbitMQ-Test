#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding('utf8')

import functools
import difflib
import logging.config
import re
import requests
import json
import time
import urllib
import operator
import functools
import requests
from StringIO import StringIO
from requests.packages.urllib3.exceptions import InsecureRequestWarning

import tldextract
from lxml import html
from tornado import ioloop, httpclient

from config import Config, BLACKLISTED_DOMAINS, COMPANY_SUFFIX_LIST
from domainIdentifier.utils import *

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

conf = Config()
logging.config.dictConfig(conf.LOGGING)
logger = logging.getLogger('domain_crawler_logger')

ignoredEmails = []
identifiers = []
emailRegex = r''
urlSet = list()
domainSet = list()
pendingEmailResponseCount = 0
verifiedDomainSet = list()
finalBlacklistedDomains = []
crunchbaseUrlSet = list()
crunchbaseDomainSet = list()
linkedUrlSet = list()
pendingLinkedInResponseCount = 0
find_web_count = 1
getValueList = functools.partial(map, operator.itemgetter(r'domain'))

from brokerService.Publisher import RabbitMQPublisher
from brokerService.rabbitmq_config import *


def publishMessage(message, exchangeName):
    import pdb; pdb.set_trace()
    print "inside publish message"
    logger.info(r'Publishing message %s ,%s' % (message, exchangeName))
    publisher = RabbitMQPublisher(exchange_name=exchangeName,
                                  host=RabbitMQ_Host)
    publisher.publish(message, exchangeName)
    logger.info(r'-' * 50)
    publisher.close()

def validateDomain(domainName, companyName):
    """
        Validating domainName against verifiedDomainSet & BLACKLISTED_DOMAINS
        Scenario 1: Query Domain = 'Cuelogic'
        Solution : If domainName is in BLACKLISTED_DOMAINS, & skip domainName
        Scenario 2: Query Domain = 'Facebook'
        Solution : If domainName is substring of any domain in BLACKLISTED_DOMAINS,
                    add that domain to verifiedDomainSet since its the 
                    parent organizations of query domain
    """
    import pdb; pdb.set_trace()
    logger.info(r'*' * 10)
    logger.info('In validate domain(domainName,companyName) ->> %s , %s'
                 % (domainName, companyName))
    global finalBlacklistedDomains, verifiedDomainSet
    try:
        logger.info(str(domainName
                    not in getValueList(verifiedDomainSet)))
        if domainName not in getValueList(verifiedDomainSet):
            if companyName.find(domainName.split('.')[0]) != 0:
                finalBlacklistedDomains = BLACKLISTED_DOMAINS
                logger.info('original blacklisted domain')
            else:
                logger.info(r'*' * 10)
                finalBlacklistedDomains = list(set(BLACKLISTED_DOMAINS)
                        - set([domainName]))
                logger.info('updating blacklisted domain')
                logger.info(finalBlacklistedDomains)
            if not any(domainName in eachDomain for eachDomain in
                       finalBlacklistedDomains):
                logger.info('Not in blacklisted domains')
                return True
            else:
                logger.info('In blacklisted domains')
                return False
        return True
    except Exception, e:
        logger.error('Error: %s' % str(e))

def removeUserNameFromEmail(
    emails,
    companyName,
    domainSource,
    message,
    ):
    """
        Parse email domain from email addresses
        by stripping username
        eg: [account@cuelogic.co.in]
        domain : [cuelogic.co.in]
    """
    import pdb; pdb.set_trace()

    logger.info('in removeUserNameFromEmail %s' % str([emails,
                companyName, domainSource]))
    global verifiedDomainSet, finalBlacklistedDomains, domainSet
    for email in emails:
        emailDomain = email.split('@')[-1].lower().strip('.')
        cleanEmailDomain = getCleanDomainName(emailDomain)
        if validateDomain(emailDomain, companyName) and emailDomain \
            not in getValueList(domainSet) and emailDomain \
            not in getValueList(verifiedDomainSet):
            isValidDomain = \
                validateDomainAgainstCompanyName(cleanEmailDomain,
                    companyName)
            if isValidDomain and cleanEmailDomain \
                not in getValueList(verifiedDomainSet):
                verifiedDomainSet.append({r'domain': cleanEmailDomain,
                        r'source': domainSource})
                logger.info(type(message))
                message['domainName'] = cleanEmailDomain
                message['domainSource'] = domainSource
                domainMxRecord = getMxRecordForDomain(message['domainName'])
                message['domainMxRecord'] = str(domainMxRecord)
                if not len(domainMxRecord):
                    logger.info(domainMxRecord)
                    message['domainName'] = ''
                    publishMessage(message, Status_Exchange)
                else:
                    publishMessage(message, Status_Exchange)
                    publishMessage(message, Pattern_Exchange)
                addNewDomain(companyName, cleanEmailDomain,
                             domainSource)


def findEmailsInHtml(html, message):
    """
        Parsing all emails addresses from html page via email regex
    """
    import pdb; pdb.set_trace()

    if html == None:
        return set()
    email_set = set()
    logger.info(r'')
    logger.info(r'Finding Emails')
    global emailRegex
    for email in emailRegex.findall(html):
        email_set.add(email)
    return email_set


def crawlGoogleForCompanyName(companyName, message):
    """
        crawlGoogleForCompanyName is a function to get all data from google for companyName
        Tornado Async calls are intented to use for scrapping
    """
    import pdb; pdb.set_trace()
    logger.info('Google Search results to fetch : %s' % companyName)
    companyName = '"%s"' % companyName
    http_client = httpclient.AsyncHTTPClient()
    query = {'q': companyName}
    url = 'http://www.google.com/search?' + urllib.urlencode(query)+'&gl=us'
    request = getProxyRequest(url)
    logger.info('Crawling %s' % url)
    callback = functools.partial(findURL, companyName, 'google',message)
    http_client.fetch(request, callback)
    ioloop.IOLoop.instance().start()


def findLinkedInUrl(companyName, message):
    import pdb; pdb.set_trace()
    logger.info('Google Search results to fetch linked Url: %s'
                % companyName)
    companyName = '%s' % companyName
    http_client = httpclient.AsyncHTTPClient()
    searchString = urllib.urlencode({'q': '%s linkedin' % companyName})
    url = 'http://www.google.com/search?%s' % searchString
    request = getProxyRequest(url)
    logger.info('Crawling %s' % url)
    callback = functools.partial(crawlLinkedInForCompanyName,
                                 companyName,message)
    http_client.fetch(request, callback)
    ioloop.IOLoop.instance().start()


def crawlLinkedInForCompanyName(companyName, message, response):
    """
        crawlLinkedInForCompanyName is a function to get all data from google for companyName
        Tornado Async calls are intented to use for scrapping
    """
    import pdb; pdb.set_trace()
    logger.error('In crawlLinkedInForCompanyName')
    if response.error:
        count = 0
        while count <= 3:
            logger.error('crawlLinkedInForCompanyName - ERROR : %s'
                         % response.error)
            logger.info(r'')
            getDomains(message)
            count += 1
        ioloop.IOLoop.instance().stop()
    else:
        logger.info(r'LinkedIn URL : %s' % companyName)
        companyName = '"%s"' % companyName
        linkedUrl = getLinkedInWebsite(response, companyName)
        logger.info(str(linkedUrl))
        if linkedUrl is not None:
            linkedInProxyRequest(linkedUrl, companyName, message)
        else:
            ioloop.IOLoop.instance().stop()

def getLinkedInWebsite(response, companyName):
    """
        getLinkedInWebsite is a function to get linkedin url for 
        companyName if and only if companyName is substring of 
        title
    """
    import pdb; pdb.set_trace()
    global urlSet
    companyName = companyName.strip('"')
    CleanCompanyName = removeCompanySuffix(companyName)
    if response.error:

        count = 0
        while count <= 3:
            logger.error('In getLinkedInWebsite - ERROR : %s'
                         % response.error)
            logger.info(r'')
            getDomains(message)
            count += 1
    else:
        # import pdb; pdb.set_trace()
        logger.info(r'Received response %s' % response.code)
        tree = html.fromstring(response.body)
        eachTitleXpath = \
            r'//*[@id="rso"]/div/div/div[1]/div/div/h3/a'
        eachDescriptionXpath = \
            '//*[@id="rso"]/div/div/div[1]/div/div/div/div/span/em'
        eachUrlXpath = \
            r'//*[@id="rso"]/div/div/div[1]/div/div/div/div/div[1]/cite'
        title = r''
        for anchor in tree.xpath(eachTitleXpath):
            logger.info(r'*' * 30)
            title = anchor.text
        descp = r' '
        for desc in tree.xpath(eachDescriptionXpath):
            descp += r' '
            descp += desc.text.lower()
        logger.info('+' * 30)
        logger.info(descp)
        logger.info(title)
        logger.info('+' * 30)
        cleanTitle = removeCompanySuffix(title)
        titleList = [each.lower().replace("'","").replace(",","") for each in title.split(" ")]
        CleanCompanyName = removeCompanySuffix(companyName)
        companyNameFirstPart = (CleanCompanyName.split(" ")[0]).lower().replace("'","").replace(",","")
        companyInitial = getCompanyInitials(companyName)
        logger.info("Removing Stopwords from CompanyName: %s"%(str([companyName, 
                                                CleanCompanyName])))
        logger.info("Title List to match: %s"%(([companyName, titleList])))
        if (companyNameFirstPart in titleList) or \
            (CleanCompanyName in title) or \
                (companyInitial in title):
            for each in tree.xpath(eachUrlXpath):
                print each.text
                return each.text
        return None



def linkedInProxyRequest(linkedUrl, companyName, message):
    import pdb; pdb.set_trace()
    
    global pendingLinkedInResponseCount
    logger.info('In linkedInProxyRequest')
    http_client = httpclient.AsyncHTTPClient()
    url = 'https://googleweblight.com/?lite_url=' + linkedUrl
    request = getProxyRequest(url)
    logger.info('Crawling %s' % url)
    callback = functools.partial(findWebsite, companyName, message)
    http_client.fetch(request, callback)
    url1 = 'https://googleweblight.com/?lite_url=' \
        + linkedUrl.replace('www.linkedin', 'in.linkedin')
    request1 = getProxyRequest(url1)
    logger.info('Crawling %s' % url1)
    http_client.fetch(request1, callback)
    pendingLinkedInResponseCount += 2

# def check_response(url, message, companyName):
#     http_client = httpclient.AsyncHTTPClient()

#     request = getProxyRequest(url)
#     callback = functools.partial(findWebsite, companyName, message)
#     http_client.fetch(request, callback)
#     # print "response==>",response.code
        


def findWebsite(companyName, message, response):
    """
        findURL is a function to get all urlSet from google result 
        page if and only if companyName is substring of 
        title, snippet for each google result
    """
    import pdb; pdb.set_trace()

    global verifiedDomainSet, pendingLinkedInResponseCount, find_web_count
    companyName = companyName.strip('"')
    domainSource = 'linkedin'
    pendingLinkedInResponseCount -= 1
    
    


    if response.error:

        http_client = httpclient.AsyncHTTPClient()

        if find_web_count <= 3:
            request = getProxyRequest(response.effective_url)
            callback = functools.partial(findWebsite, companyName, message)
            http_client.fetch(request, callback)

            find_web_count += 1

        # count = 0
        # while count < 3:
        #     check_response(response.effective_url,message, companyName)
        #     count += 1

        logger.error('findWebsite - ERROR : %s' % response.error)
        logger.info(r'')

    else:
        logger.info(r'findWebsite Received response %s' % response.code)
        tree = html.fromstring(response.body)
        websiteXpath = [r'//*[@id="a-company"]/div[2]/div[2]/a/p/text()',
                        r'//*[@id="a-company"]/div[2]/div[3]/a/p/text()'
                        , r'//*[@id="a-webSite_presentation_0"]',
                        r'//*[@id="a-company"]/div[2]/div[1]/a/p/text()']
        for each in websiteXpath:
            companyWebsite = tree.xpath(each)
            if len(companyWebsite):
                break
        if len(companyWebsite):
            emailDomain = parseDomain(companyWebsite[0])
            # Need to update this for all blacklisted domains
            if emailDomain not in getValueList(verifiedDomainSet) and emailDomain not in 'bit.ly':
                addNewDomain(companyName, emailDomain, domainSource)
                addNewWebsite(companyName, each.strip(r'/'), domainSource)
                logger.info(str(emailDomain))
                logger.info('URL FOUND %s' % str(companyWebsite))
                verifiedDomainSet.append({r'domain': emailDomain,
                        r'source': 'linkedin'})
                logger.info(type(message))
                message[r'domainName'] = emailDomain
                message['domainSource'] = domainSource
                domainMxRecord = getMxRecordForDomain(message['domainName'])
                message['domainMxRecord'] = str(domainMxRecord)
                if not len(domainMxRecord):
                    logger.info(domainMxRecord)
                    message['domainName'] = ''
                    publishMessage(message, Status_Exchange)
                else:
                    publishMessage(message, Status_Exchange)
                    publishMessage(message, Pattern_Exchange)
    if pendingLinkedInResponseCount == 0 and find_web_count == 4:
        ioloop.IOLoop.instance().stop()







def findEmails(
    companyName,
    domainSource,
    message,
    response,
    ):
    """
        findEmails is a handler function to all the asynchronous calls
    """
    import pdb; pdb.set_trace()

    global verifiedDomainSet, pendingEmailResponseCount
    logger.error('In findEmails')
    if response.error:

        count = 0
        while count <= 3:
            logger.error('findEmails - ERROR : %s' % response.error)
            logger.info(r'')
            getDomains(message)
            count += 1



    else:
        emailSet = findEmailsInHtml(response.body, message)
        if len(emailSet) > 0:
            logger.info(r'Found %s emails found on google search page.'
                        % len(emailSet))
            logger.info(r'Found %s emails found on google search page.'
                        % emailSet)
            removeUserNameFromEmail(emailSet, companyName,
                                    domainSource, message)
        else:
            logger.error(r'No emails found')
    pendingEmailResponseCount -= 1
    if pendingEmailResponseCount == 0:
        logger.info(r'Terminating IOLoop')
        ioloop.IOLoop.instance().stop()


def getDomainFromWebsite(companyName, domainSource):
    """
        getDomainFromWebsite is a function get to domain from an webaddress/ website
    """
    import pdb; pdb.set_trace()
    global domainSet, urlSet
    try:
        logger.info(r'Get Domain from Company Website: %s' % urlSet)
        urlList = urlSet
        logger.info('Company Websites: %s' % str(urlList))
        tempDomainSet = domainSet
        for each in urlList:
            logger.info(r'Get Domain from Company Website: %s' % each)
            if each is not None:
                currentDomain = parseDomain(each)
                if currentDomain is not None:
                    if currentDomain not in getValueList(tempDomainSet) \
                        and validateDomain(currentDomain, companyName):
                        currentDomain = currentDomain.strip(r'/')
                        domainSet.append({r'domain': currentDomain,
                                r'source': domainSource})
                        addNewDomain(companyName, currentDomain,
                                domainSource)
                        addNewWebsite(companyName, each.strip(r'/'),
                                domainSource)
                        logger.info('Domain from Company Website: %s'
                                    % currentDomain)
    except Exception, e:
        logger.error('Error: %s' % str(e))


def crawlGoogleForDomainNamePhase1(companyName, message):
    """
        crawlGoogleForDomainNamePhase1 is a step 1 to verfiy domain names 
        using google query for pattern: "info@companyName" OR "emailcompanyName"
    """
    import pdb; pdb.set_trace()

    global pendingEmailResponseCount, verifiedDomainSet, domainSet
    logger.info('Domain Verification for company[Pattern1] : %s'
                % str(companyName))
    CleanCompanyName = removeCompanySuffix(message['companyName']) 
    domainList = getCompanyDomainList(CleanCompanyName)
    if  not domainList.count():
        domainList = getCompanyDomainList(message['companyName'])
    http_client = httpclient.AsyncHTTPClient()
    for eachDomain in domainSet:
        print eachDomain
        currentDomain = eachDomain['domain']
        message[r'domainName'] = currentDomain
        message['domainSource'] = eachDomain['source']
        verifiedDomainSet.append({r'domain': currentDomain,
                r'source': eachDomain['source']})
        domainMxRecord = getMxRecordForDomain(message['domainName'])
        message['domainMxRecord'] = str(domainMxRecord)
        if not len(domainMxRecord):
            logger.info(domainMxRecord)
            message['domainName'] = ''
            publishMessage(message, Status_Exchange)
        else:
            publishMessage(message, Status_Exchange)
            publishMessage(message, Pattern_Exchange)


def crawlGoogleForDomainNamePhase2(companyName, message, queryPhase=1):
    """
        crawlGoogleForDomainNamePhase2 is a step 2 to verfiy domain names 
        using google query for 
        Pattern 2:q=email " <companyName> " & 
        Pattern 3:q=" @<companyName> "email details
    """
    import pdb; pdb.set_trace()

    global pendingEmailResponseCount
    http_client = httpclient.AsyncHTTPClient()
    if queryPhase == 1:
        logger.info('Domain Verification for company[Pattern2]: %s'
                    % str(companyName))
        emailDomainName = 'email "* %s *"' % companyName
    else:
        logger.info('Domain Verification for company[Pattern3]: %s'
                    % str(companyName))
        emailDomainName = '" %s "email details' % companyName
    query = {'q': '%s' % emailDomainName}
    url = 'http://www.google.com/search?' + urllib.urlencode(query)
    logger.info('Crawling %s' % url)
    request = getProxyRequest(url)
    callback = functools.partial(findEmails, companyName, 'google',
                                 message)
    http_client.fetch(request, callback)
    pendingEmailResponseCount += 1
    ioloop.IOLoop.instance().start()


def getDomainFromCrunchBase(companyName, message):
    """
        Get domain name from crunchbase api for given companyName
    """
    import pdb; pdb.set_trace()

    global crunchbaseUrlSet, crunchbaseDomainSet, verifiedDomainSet
    logger.info('Get all domains from CrunchBase: %s'
                % str(companyName))
    CRUNCHBASE_API = \
        'https://api.crunchbase.com/v/3/odm-organizations?user_key=%s&name=%s'
    crunchbase_request = requests.get(CRUNCHBASE_API
            % (conf.CRUNCHBASE_API_KEY, companyName))
    try:
        crunchbase_response = crunchbase_request.json()
        for each_item in crunchbase_response['data']['items']:
            currentDomain = each_item['properties'][r'domain']
            homePageUrl = each_item['properties']['homepage_url']
            logger.info(r'-' * 10)
            logger.info('CrunchBase Response for company: %s'
                        % str(companyName))
            logger.info('Domain Found: %s' % currentDomain)
            logger.info('Website Found: %s' % homePageUrl)
            logger.info(r'')
            if homePageUrl not in crunchbaseUrlSet:
                addNewWebsite(companyName, homePageUrl, r'crunchbase')
            if currentDomain:
                if currentDomain not in crunchbaseDomainSet and \
                        currentDomain not in getValueList(verifiedDomainSet):
                    crunchbaseDomainSet.append(currentDomain)
                    verifiedDomainSet.append({r'domain': currentDomain,
                            r'source': r'crunchbase'})
                    message[r'domainName'] = currentDomain
                    message['domainSource'] = r'crunchbase'
                    domainMxRecord = getMxRecordForDomain(message['domainName'])
                    message['domainMxRecord'] = str(domainMxRecord)
                    if not len(domainMxRecord):
                        logger.info(domainMxRecord)
                        message['domainName'] = ''
                        publishMessage(message, Status_Exchange)
                    else:
                        publishMessage(message, Status_Exchange)
                        publishMessage(message, Pattern_Exchange)
                    addNewDomain(companyName, currentDomain,
                                 r'crunchbase')
    except Exception, e:
        logger.error(str(e))
    logger.info('Domain List for %s : %s' % (str(companyName),
                str(crunchbaseDomainSet)))
    logger.info('Website List for %s : %s' % (str(companyName),
                str(crunchbaseUrlSet)))


def findURL(companyName, request_source, message, response):
    """
        findURL is a function to get all urlSet from google result 
        page if and only if companyName is substring of 
        title, snippet for each google result
    """
    import pdb; pdb.set_trace()

    global urlSet
    companyName = companyName.strip('"')
    if response.error:
        count = 0
        while count <= 3:
            logger.error('findUrlsAndEmails - ERROR : %s' % response.error)
            logger.info(r'')
                
            request = getProxyRequest(url)
            callback = functools.partial(findEmails, companyName, 'google',
                                     message)
            http_client.fetch(request, callback)
            count += 1
    else:
        logger.info(r'Received response %s' % response.code)
        tree = html.fromstring(response.body)
        title = r''
        titleXpath = r'//*[@id="rso"]/div[%d]/div/div/div/div/h3/a'
        descriptionXpath = \
            r'//*[@id="rso"]/div[%d]/div/div/div/div/div/div/span/text()'
        urlXpath = \
            r'//*[@id="rso"]/div[%d]/div/div/div/div/div/div/div/cite'
        flag = 1
        index = 1
        for anchor in tree.xpath(titleXpath % index):
            title = anchor.text
        description = []
        for desc in tree.xpath(descriptionXpath % index):
            description.append(desc)
        print title, description
        try:
            cleanTitle = removeCompanySuffix(title)
            titleList = [each.lower().replace("'","").replace(",","").replace(",","") for each in cleanTitle.split(" ")]
            CleanCompanyName = removeCompanySuffix(companyName)
            companyNameFirstPart = (CleanCompanyName.split(" ")[0]).lower().replace("'","").replace(",","")
            companyInitial = getCompanyInitials(companyName)
            logger.info("Removing Stopwords from CompanyName: %s"%(str([companyName, 
                                                    CleanCompanyName])))
            logger.info("Title List to match: %s"%(([companyName, titleList])))

            if (companyNameFirstPart in titleList) or \
                (CleanCompanyName in title) or \
                    (companyInitial in title):
                each = tree.xpath(urlXpath % index)[0]
                temp_url = each.text
                url = temp_url.split(r' ')[0]
                if 'linkedin' in url:
                    linkedInProxyRequest(url, companyName, message)
                else:
                    urlSet.append(url)
                    flag = 0
        except Exception, e:
            logger.error(str(e))
    logger.info('URL FOUND %s' % str(urlSet))
    ioloop.IOLoop.instance().stop()


def getDomains(message):
    import pdb; pdb.set_trace()

    companyName = message['companyName']
    logger.info(r'-' * 10)
    startTime = time.time()
    logger.info('Start time -->> ' + str(startTime))
    logger.info('Finding domain name for : %s' % companyName)
    logger.info(r'-' * 10)
    httpclient.AsyncHTTPClient.configure('tornado.curl_httpclient.CurlAsyncHTTPClient'
            )
    global domainSet, urlSet, verifiedDomainSet, emailRegex, \
        pendingEmailResponseCount, crunchbaseUrlSet, crunchbaseDomainSet
    emailRegex = \
        re.compile(r'[A-Z.]+[A-Z0-9*_-]+@[A-Z]+\.{1}[A-Z.]+[A-Z]',
                   re.IGNORECASE)
    companyName = companyName.encode('utf-8')
    findLinkedInUrl(companyName, message)
    if not len(verifiedDomainSet):
        crawlGoogleForCompanyName(companyName, message)
        getDomainFromWebsite(companyName, 'google')
        crawlGoogleForDomainNamePhase1(companyName, message)
    logger.info(r'-' * 10)
    logger.info('Resetting all globals')
    logger.info(r'-' * 10)
    resultDomainSet = verifiedDomainSet
    logger.info(str(verifiedDomainSet))
    if not len(verifiedDomainSet):
        publishMessage(message, Status_Exchange)
    logger.info(r'-' * 10)
    domainSet = list()
    verifiedDomainSet = list()
    pendingEmailResponseCount = 0
    finalBlacklistedDomains = []
    emailRegex = r''
    urlSet = list()
    crunchbaseUrlSet = list()
    crunchbaseDomainSet = list()
    endTime = time.time()
    logger.info(r'End time -->> ' + str(endTime))
    logger.info(r'Total time -->> ' + str(endTime - startTime))
    return resultDomainSet
