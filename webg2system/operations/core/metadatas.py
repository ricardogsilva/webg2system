#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
A module for implementing metadata related functionality for the Geoland-2 
processing system.
"""

import logging
from lxml import etree
import urllib
import urllib2
import cookielib

class MetadataGenerator(object):

    def __init__(self, template):
        self.logger = logging.getLogger(
                '.'.join((__name__, self.__class__.__name__)))
        self.tree = etree.parse(template)
        self.ns = self.tree.getroot().nsmap.copy()
        # in order to use this dictionary for XPATH queries the default 
        # entry has to be deleted
        del self.ns[None] 
        self.changeableElements = {
                #01 - MD_Metadata
                #02 - fileIdentifier
                'fileIdentifier' : self.tree.xpath(
                    'gmd:fileIdentifier/gco:CharacterString', 
                    namespaces=self.ns)[0], # the XML uuid
                #03 - language (language used in the metadata)
                    # english, no need to change anything
                #04 - characterSet
                    # utf8, no need to change anything
                #05 - parentIdentifier
                    # uuid of the dataset series
                'parentIdentifier' : self.tree.xpath('gmd:parentIdentifier'\
                    '/gco:CharacterString', namespaces=self.ns)[0],
                #06 - hierarchyLevel
                'hierarchyLevel' : self.tree.xpath(
                    'gmd:hierarchyLevel/gmd:MD_ScopeCode', 
                    namespaces=self.ns)[0],
                #07 - contact (Metadata on Metadata)
                #   This section deals with who is responsible for the 
                #   metadata.
                #       
                #   Consider adding (or removing) the rest of the tags used 
                #   in the global template. 
                #   The 'role' elment is to left as pointOfContact, as is in 
                #   the template.
                'organisationName' : self.tree.xpath('gmd:contact/*'\
                    '/gmd:organisationName/gco:CharacterString', 
                    namespaces=self.ns)[0],
                'organisationAddress' : self.tree.xpath('gmd:contact/*/'\
                    'gmd:contactInfo/*/gmd:address/*/gmd:deliveryPoint/'\
                    'gco:CharacterString', namespaces=self.ns)[0],
                'organisationCity' : self.tree.xpath('gmd:contact/*/'\
                    'gmd:contactInfo/*/gmd:address/*/gmd:city/'\
                    'gco:CharacterString', namespaces=self.ns)[0],
                'organisationPostalCode' : self.tree.xpath('gmd:contact/*/'\
                    'gmd:contactInfo/*/gmd:address/*/gmd:postalCode/'\
                    'gco:CharacterString', namespaces=self.ns)[0],
                'electronicMailAddress' : self.tree.xpath('gmd:contact/*'\
                    '/gmd:contactInfo/*/gmd:address/*/gmd:'\
                    'electronicMailAddress/gco:CharacterString', 
                    namespaces=self.ns)[0],
                #08 - dateStamp (date stamp for when the metadata was created)
                'dateStamp' : self.tree.xpath('gmd:dateStamp/gco:Date', 
                    namespaces=self.ns)[0],
                #09 - metadataStandardName
                    # untouched, no need to change anything
                #10 - metadataStandardVersion
                    # untouched, no need to change anything
                #11 - spatialRepresentationInfo
                'rowSize' : self.tree.xpath('gmd:spatialRepresentationInfo/*'\
                    '/gmd:axisDimensionProperties[1]/*/gmd:dimensionSize'\
                    '/gco:Integer', namespaces=self.ns)[0],
                'rowResolution' : self.tree.xpath('gmd:spatialRepresentation'\
                    'Info/*/gmd:axisDimensionProperties[1]/*/gmd:resolution'\
                    '/gco:Angle', namespaces=self.ns)[0],

                'colSize' : self.tree.xpath('gmd:spatialRepresentationInfo/*'\
                    '/gmd:axisDimensionProperties[2]/*/gmd:dimensionSize'\
                    '/gco:Integer', namespaces=self.ns)[0],
                'colResolution' : self.tree.xpath('gmd:spatialRepresentation'\
                    'Info/*/gmd:axisDimensionProperties[2]/*/gmd:resolution'\
                    '/gco:Angle', namespaces=self.ns)[0],
                    # cell geometry does not need any modification
                    # transformationParameterAvailability does not need any 
                    #    modification
                    # checkPointAvailability does not need any modification
                    # checkPointDescription does not need any modification
                'cornerPoint' : self.tree.xpath('gmd:spatialRepresentation'\
                    'Info/*/gmd:cornerPoints/gml:Point/gml:pos', 
                    namespaces=self.ns)[0],
                    # pointInPixel does not need any modification
                #12 - referenceSystemInfo
                # EPSG code
                'referenceSystemIdentifier' : self.tree.xpath('gmd:reference'\
                    'SystemInfo[1]/*/gmd:referenceSystemIdentifier'\
                    '/gmd:RS_Identifier/gmd:code/gco:CharacterString', 
                    namespaces=self.ns)[0],
                    # the codeSpace tag does not need changing
                #13 - referenceSystemInfo <- TO BE REMOVED FROM THE TEMPLATE
                #14 - identificationInfo
                    # citation
                        # title
                'title' : self.tree.xpath('gmd:identificationInfo[1]'\
                    '/*/gmd:citation/gmd:CI_Citation/gmd:title'\
                    '/gco:CharacterString', namespaces=self.ns)[0],
                        # date (creation of the resource)
                'date' : self.tree.xpath('gmd:identificationInfo[1]/*'\
                    '/gmd:citation/*/gmd:date/*/gmd:date/gco:Date', 
                    namespaces=self.ns)[0],
                        # what is this? algorithm version?
                'edition' : self.tree.xpath('gmd:identificationInfo[1]/*'\
                    '/gmd:citation/*/gmd:edition/gco:CharacterString', 
                    namespaces=self.ns)[0],
                        # what is this? the date when the algorithm version became active?
                'editionDate' : self.tree.xpath('gmd:identificationInfo[1]/*'\
                    '/gmd:citation/*/gmd:editionDate/gco:Date', 
                    namespaces=self.ns)[0],
                        # identifier
                        # I.M. name
                'authorityTitle' : self.tree.xpath('gmd:identificationInfo[1]'\
                    '/*/gmd:citation/*/gmd:identifier/*/gmd:authority'\
                    '/*/gmd:title/gco:CharacterString', namespaces=self.ns)[0],
                        # What is this? Authority date?
                'authorityDate' : self.tree.xpath('gmd:identificationInfo[1]'\
                    '/*/gmd:citation/*/gmd:identifier/*/gmd:authority'\
                    '/*/gmd:date/*/gmd:date/gco:Date', namespaces=self.ns)[0],
                        # What is this? Authority date revision?
                'authorityDateRev' : self.tree.xpath('gmd:identificationInfo[1]'\
                    '/*/gmd:citation/*/gmd:identifier/*/gmd:authority'\
                    '/*/gmd:date/*/gmd:dateType/gmd:CI_DateTypeCode', 
                    namespaces=self.ns)[0],
                        # other citation details
                'otherDetails' : self.tree.xpath('gmd:identificationInfo[1]'\
                    '/*/gmd:citation/*/gmd:otherCitationDetails'\
                    '/gco:CharacterString', namespaces=self.ns)[0],
                    # abstract
                'abstract' : self.tree.xpath('gmd:identificationInfo[1]'\
                        '/*/gmd:abstract/gco:CharacterString', 
                        namespaces=self.ns)[0],
                    # purpose <- does not need changing
                    # credit
                'credit' : self.tree.xpath('gmd:identificationInfo[1]/*'\
                    '/gmd:credit/gco:CharacterString', namespaces=self.ns)[0],
                    # status (its a code list)
                'status' : self.tree.xpath('gmd:identificationInfo[1]/*'\
                    '/gmd:status/gmd:MD_ProgressCode', namespaces=self.ns)[0],
                    # pointOfContact
                    # pointOfContact
                    # resourceMaintenance
                    # graphicOverview
                    # resourceFormat
                    # descriptiveKeywords
                    # descriptiveKeywords
                    # descriptiveKeywords
                    # descriptiveKeywords
                    # descriptiveKeywords
                    # resourceconstraints
                    # resourceconstraints
                    # resourceconstraints
                    # aggregationInfo
                    # aggregationInfo
                    # aggregationInfo
                    # spatialRepresentationType
                    # spatialResolution
                    # language
                    # characterSet
                    # topicCategory
                    # topicCategory
                    # topicCategory
                    # topicCategory
                    # extent
                    # extent
                    # supplementalInformation
                #15 - contentInfo
                #16 - contentInfo
                #17 - contentInfo
                #18 - contentInfo
                #19 - contentInfo
                #20 - contentInfo
                #21 - distributionInfo
                #22 - dataQualityInfo
                #23 - metadataMaintenance
                'Resource type' : self.tree.xpath('gmd:hierarchyLevel'\
                        '/gmd:MD_ScopeCode', namespaces=self.ns)[0],
                'uuid' : self.tree.xpath(
                    'gmd:identificationInfo/gmd:MD_DataIdentification',
                    namespaces=self.ns)[0], # the XML uuid
                'idCode' : self.tree.xpath(
                    'gmd:identificationInfo/*/gmd:citation/*/gmd:identifier/'\
                            '*/gmd:code/gco:CharacterString', 
                    namespaces=self.ns)[0],# the XML uuid
                'idTitle' : self.tree.xpath(
                    'gmd:identificationInfo/*/gmd:citation/*/gmd:title/'\
                            'gco:CharacterString',
                    namespaces=self.ns),
                'quicklook' : self.tree.xpath(
                    'gmd:identificationInfo/*/gmd:graphicOverview/*/'\
                            'gmd:fileName/gco:CharacterString',
                    namespaces=self.ns),
                'westLongitude' : self.tree.xpath(
                    'gmd:identificationInfo/*/gmd:extent/*/*/*/'\
                            'gmd:westBoundLongitude/gco:Decimal',
                    namespaces=self.ns)[0],
                'eastLongitude' : self.tree.xpath(
                    'gmd:identificationInfo/*/gmd:extent/*/*/*/'\
                            'gmd:eastBoundLongitude/gco:Decimal',
                    namespaces=self.ns)[0],
                'southLatitude' : self.tree.xpath(
                    'gmd:identificationInfo/*/gmd:extent/*/*/*/'\
                            'gmd:southBoundLatitude/gco:Decimal',
                    namespaces=self.ns)[0],
                'northLatitude' : self.tree.xpath(
                    'gmd:identificationInfo/*/gmd:extent/*/*/*/'\
                            'gmd:northBoundLatitude/gco:Decimal',
                    namespaces=self.ns)[0],
                'download' : self.tree.xpath(
                    'gmd:distributionInfo/*/gmd:transferOptions/*/*/*/*/'\
                    'gmd:URL',
                    namespaces=self.ns),
            }

    def save_xml(self, path):
        '''
        Save the xml metadata to a file.
        '''

        self.tree.write(path)

    # FIXME
    # - This method is to replace most of the commands present in
    # operations.core.g2packages.WebDisseminator.generate_xml_metadata()
    def process_tile(self, tilePath):
        raise NotImplementedError

    def update_element(self, elementName, value):
        '''
        Update the element's value with the new setting.

        Inputs:

            elementName - The name of the element to update. It must be one of
                the keys defined in the changeableElements attribute.

            value - A string with the new value for the element.
        '''

        el = self.changeableElements.get(elementName)
        el.text = value
        return el

    # FIXME
    # this code is adapted from
    # http://trac.osgeo.org/geonetwork/wiki/HowToDoCSWTransactionOperations#Python
    def send_to_csw(self):
        gn_username = 'admin'
        gn_password = 'admin'
        gn_baseURL = 'http://geo4.meteo.pt/geonetwork'
        gn_loginURI = 'srv/en/xml.user.login'
        gn_logoutURI = 'srv/en/xml.user.logout'
        gn_cswURI = 'srv/en/csw'

        # HTTP header for authentication
        header_urlencode = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        # HTTP header for CSW request
        header_xml = {"Content-type": "application/xml", "Accept": "text/plain"}
        # authentication Post parameters
        post_parameters = urllib.urlencode({"username": gn_username, "password": gn_password})

        # Sample CSW transactions
        xml_request = "<?xml version=\"1.0\"?>\
               <csw:DescribeRecord xmlns:csw=\"http://www.opengis.net/cat/csw/2.0.2\"\
               service=\"CSW\" version=\"2.0.2\" outputFormat=\"application/xml\"\
               schemaLanguage=\"http://www.w3.org/XML/Schema\"/>"

        url_in = '/'.join((gn_baseURL, gn_loginURI))
        url_out = '/'.join((gn_baseURL, gn_logoutURI))
        url_csw = '/'.join((gn_baseURL, gn_cswURI))


        # first, always log out
        request = urllib2.Request(url_out)
        response = urllib2.urlopen(request)
        #print response.read()       # debug

        # send authentication request
        request = urllib2.Request(url_in, post_parameters, header_urlencode)
        response = urllib2.urlopen(request)
        # a basic memory-only cookie jar instance
        cookies = cookielib.CookieJar()
        cookies.extract_cookies(response,request)
        cookie_handler= urllib2.HTTPCookieProcessor( cookies )
        # a redirect handler
        redirect_handler= urllib2.HTTPRedirectHandler()
        # save cookie and redirect handler for future HTTP Posts
        opener = urllib2.build_opener(redirect_handler,cookie_handler)

        # CSW request
        request = urllib2.Request(url_csw, xml_request2, header_xml)
        response = opener.open(request)
        # CSW respons
        xml_response = response.read()
        print xml_response  # debug

        # Do something with the response. For example:
        #xmldoc = minidom.parseString(xml_response)
        #for node in xmldoc.getElementsByTagName('ows:ExceptionText'):       # display <ows:ExceptionText /> value(s)
        #    print "    EXCEPTION: "+node.firstChild.nodeValue
        #xmldoc.unlink()     # cleanup DOM for improved performance

        # more CSW requests if desired
        # Last, always log out
        request = urllib2.Request(url_out)
        response = opener.open(request)
        #print response.read()       # debug
