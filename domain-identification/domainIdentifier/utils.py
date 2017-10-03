#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding('utf8')

import re
from random import randint

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

import dns.resolver
import tldextract
from lxml import html
from tornado import ioloop, httpclient

from config import (Config, BLACKLISTED_DOMAINS, COMPANY_SUFFIX_LIST, 
                    STOPWORD_DOMAIN_LIST, domainSuffixList)
import domain_crawler
from domainIdentifier.models import Domains, Websites


def getMxRecordForDomain(domainName):
    import pdb; pdb.set_trace()
    mxRecordList = list()
    try:
        mxRecords = dns.resolver.query(domainName, 'MX')
        for eachRecord in mxRecords:
            mxRecordList.append({'Host':str(eachRecord.exchange),'Preference':eachRecord.preference})
        return mxRecordList
    except Exception, e:
        domain_crawler.logger.error('%s' % str(e))
        return mxRecordList

def parseDomain(website):
    import pdb; pdb.set_trace()
    domain_crawler.logger.info('parseDomain from Company Website: %s' % website)
    website = str(website)
    currentDomain = None
    parseSubDomain = 0
    if not (website.startswith('https') or website.startswith('http')):
        website = 'https://%s' % website
    cleanUrl = re.search("(?P<url>https?://[^\s]+)", website)
    domain_crawler.logger.info(str(r'-' * 50))
    domain_crawler.logger.info(str(cleanUrl))
    domain_crawler.logger.info(str(r'-' * 50))
    if cleanUrl is not None:
        cleanUrl = cleanUrl.group('url')
        domain_crawler.logger.info(str(r'*' * 50))
        domain_crawler.logger.info(str(cleanUrl))
        url = tldextract.extract(cleanUrl)
        if url.subdomain is not '':
            parseSubDomain = 1
        if parseSubDomain:
            if any(str(url.subdomain).lower() in domainStopWord.lower() for domainStopWord in STOPWORD_DOMAIN_LIST):
                currentDomain = url.domain + '.' + url.suffix
            else:
                currentDomain = url.subdomain + '.' + url.domain + '.' + url.suffix
        else:
            currentDomain = url.domain + '.' + url.suffix
    domain_crawler.logger.info('Domain from Company Website: %s' % currentDomain)
    return currentDomain


def removeCompanySuffix(companyName):
    # import pdb; pdb.set_trace() 
    cleanCompanySuffix1 = companyName.lower()
    for each in COMPANY_SUFFIX_LIST:
        replaceString = "\b" +each.lower()+ "\b"
        cleanCompanySuffix1 = re.sub(replaceString,"", cleanCompanySuffix1)
    return cleanCompanySuffix1.strip()


def getCleanCompanyName(companyName):
    import pdb; pdb.set_trace()

    cleanCompanyName = removeCompanySuffix(companyName.lower())
    return r''.join(e for e in cleanCompanyName.strip() if e.isalnum())


def getCompanyInitials(companyName):
    # import pdb; pdb.set_trace()

    initialList = []
    cleanCompanyName = removeCompanySuffix(companyName)
    import pdb; pdb.set_trace()
    domain_crawler.logger.info(cleanCompanyName)
    for each in cleanCompanyName.split(r' '):
        if each:
            initialList.append(each[0].lower())
    return r''.join(initialList)


def getCleanDomainName(domainName):
    import pdb; pdb.set_trace()

    domain_crawler.logger.info('In getCleanDomainName %s' % str(domainName))
    (newDomainName, domainSuffix) = (domainName.split('.')[0],
            domainName.split('.')[-1])
    domain_crawler.logger.info(str([newDomainName, domainSuffix]))
    newDomainName = newDomainName.replace(r'-', r'')
    if len(domainSuffix) > 3:
        domainSuffix = domainSuffix[:3]
        if domainSuffix.lower() not in domainSuffixList:
            newDomainSuffix = domainSuffix[:2]
            domain_crawler.logger.info('Domain found %s, Get first two characters for domain %s'
                         % (str(domainName), str(newDomainSuffix)))
            return '.'.join([newDomainName, newDomainSuffix])
    return '.'.join([newDomainName, domainSuffix])


def getProxyRequest(url):
    """
        Returns the proxy request that would be made if the operation was invoked. 
        This method does not actually issue the request.

    """
    # import pdb; pdb.set_trace()
    request = httpclient.HTTPRequest(
        url,
        r'GET',
        user_agent=domain_crawler.conf.USER_AGENTS[randint(0, \
                len(domain_crawler.conf.USER_AGENTS)
                                    - 1)],
        proxy_host=r'proxy.crawlera.com',
        proxy_port=8010,
        proxy_username=r'7376f12e3a8d40ebbd378dc67529b71a',
        request_timeout=50,
        validate_cert=False,
        )
    return request


def getRequest(url):
    """
        Returns the request that would be made if the operation was invoked. 
        This method does not actually issue the request.

    """
    import pdb; pdb.set_trace()

    request = httpclient.HTTPRequest(url, r'GET',
            user_agent=domain_crawler.conf.USER_AGENTS[randint(0,
            len(domain_crawler.conf.USER_AGENTS) - 1)])
    return request



def addNewDomain(companyName, newDomain, domainSource):
    """
        Saving domain to database on validating domain & 
        if it does not exists in database against companyName
    """
    import pdb; pdb.set_trace()
    domain_crawler.logger.info(r'In addNewDomain :%s, %s' % (str(companyName),
                str(newDomain)))
    isValidDomain = validateDomainAgainstCompanyName(newDomain,
            companyName)
    newCompanyName = removeCompanySuffix(companyName)
    if newDomain:
        if not getCompanyDomain(newCompanyName.lower(), newDomain):
            if isValidDomain and domainSource == 'google' \
                or domainSource != 'google':
                domain = \
                    Domains(company=newCompanyName.lower().decode('utf-8'
                            ), domain=newDomain.decode('utf-8'),
                            source=domainSource)
                domain_crawler.logger.info('Saving Domain for Company %s as %s '
                            % (newCompanyName, newDomain))
                domain.save()
                domain_crawler.logger.info('Saving new domain')
            else:
                domain_crawler.logger.info('Not Saving')
    else:
        domain_crawler.logger.info('Not Saving')


def addNewWebsite(companyName, newWebsite, domainSource):
    """
        Saving website to database 
        if it does not exists in database against companyName
    """

    import pdb; pdb.set_trace()

    domain_crawler.logger.info(r'In addNewWebsite :%s, %s' % (str(companyName),
                str(newWebsite)))
    newCompanyName = removeCompanySuffix(companyName)
    if newWebsite is not None:
        if not getCompanyWebAddress(newCompanyName, newWebsite) \
            and not any(companyName in currentDomain
                        for currentDomain in BLACKLISTED_DOMAINS):
            website = \
                Websites(company=newCompanyName.lower().decode('utf-8'
                         ), website=newWebsite, source=domainSource)
            domain_crawler.logger.info('Saving Webaddress for Company %s as %s '
                        % (companyName, newWebsite))
            website.save()
            domain_crawler.logger.info('Saving new web address')
    else:
        domain_crawler.logger.info('Not Saving')


def getCompanyDomain(companyName, currentDomain):
    """
        Check if domain exists against company_name in database
    """
    import pdb; pdb.set_trace()

    newCompanyName = removeCompanySuffix(companyName)
    domain = Domains.query.filter(Domains.company
                                  == newCompanyName.lower().decode('utf-8'
                                  ), Domains.domain == currentDomain)
    if domain.count() <= 0:
        domain_crawler.logger.info('New domain')
        return False
    else:
        domain_crawler.logger.info('Domain already exists in database')
        return True


def getCompanyWebAddress(companyName, url):
    """
        Check if website exists against company_name in database
    """
    import pdb; pdb.set_trace()

    newCompanyName = removeCompanySuffix(companyName)
    domain_crawler.logger.info('Get web address for company : %s' % str(companyName))
    website = Websites.query.filter(Websites.company
                                    == newCompanyName.lower().decode('utf-8'
                                    ), Websites.website == url)
    if website.count() <= 0:
        domain_crawler.logger.info('New Web address')
        return False
    else:
        domain_crawler.logger.info('Web address already exists in database')
        return True



def getCompanyDomainList(companyName):
    """
        Get all the domains from database for given companyName
    """
    # import pdb; pdb.set_trace()
    domain_crawler.logger.info(r'Get all domains for company : %s' % companyName)
    domainList = Domains.query.filter(Domains.company== companyName.decode('utf-8'))
    domain_crawler.logger.info('Exiting get all domains for %s' % str(companyName))
    return domainList


def validateDomainAgainstCompanyName(domainName, companyName):
    # domain_crawler.logger.info(r'In validateDomainAgainstCompanyName %s '
    #             % str([domainName, companyName]))
    # cleanCompanyName = getCleanCompanyName(companyName)
    # withoutSuffixCompanyName = removeCompanySuffix(companyName)
    # companyInitialList = getCompanyInitials(withoutSuffixCompanyName)
    # cleanDomainName = getCleanDomainName(domainName)
    # closest_match = difflib.get_close_matches(cleanCompanyName,
    #         [cleanDomainName])
    # domain_crawler.logger.info(r'*' * 20)
    # domain_crawler.logger.info('Company InitialList :%s' % str(companyInitialList))
    # domain_crawler.logger.info('cleanCompanyName :%s' % str(cleanCompanyName))
    # domain_crawler.logger.info('cleanDomainName :%s' % str(cleanDomainName))
    # domain_crawler.logger.info('closest_match :%s' % str(closest_match))
    # domain_crawler.logger.info(r'*' * 20)
    # if cleanCompanyName in cleanDomainName:
    #     domain_crawler.logger.info(str('Valid Domain'))
    #     return True
    # elif str(companyInitialList) == cleanDomainName:
    #     domain_crawler.logger.info(str('Valid Domain'))
    #     return True
    # elif len(closest_match):
    #     domain_crawler.logger.info(str('Closest Domain'))
    #     return True
    # else:
    #     domain_crawler.logger.info(str('Invalid Domain'))
    return True
