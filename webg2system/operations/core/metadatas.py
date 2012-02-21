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
from uuid import uuid1
import datetime as dt

import pycountry

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
                    # pointOfContact[1]
                'pc1OrganisationName' : self.tree.xpath('gmd:'\
                    'identificationInfo[1]/*/gmd:pointOfContact[1]/*/'\
                    'gmd:organisationName/gco:CharacterString', 
                    namespaces=self.ns)[0],
                'pc1PositionName' : self.tree.xpath('gmd:'\
                    'identificationInfo[1]/*/gmd:pointOfContact[1]/*/'\
                    'gmd:positionName/gco:CharacterString', 
                    namespaces=self.ns)[0],
                'pc1OrgAddress' : self.tree.xpath('gmd:'\
                    'identificationInfo[1]/*/gmd:pointOfContact[1]/*/'\
                    'gmd:contactInfo/*/gmd:address/*/gmd:deliveryPoint/'\
                    'gco:CharacterString', namespaces=self.ns)[0],
                'pc1OrgCity' : self.tree.xpath('gmd:'\
                    'identificationInfo[1]/*/gmd:pointOfContact[1]/*/'\
                    'gmd:contactInfo/*/gmd:address/*/gmd:city/'\
                    'gco:CharacterString', namespaces=self.ns)[0],
                'pc1OrgPostal' : self.tree.xpath('gmd:'\
                    'identificationInfo[1]/*/gmd:pointOfContact[1]/*/'\
                    'gmd:contactInfo/*/gmd:address/*/gmd:postalCode/'\
                    'gco:CharacterString', namespaces=self.ns)[0],
                    # the next element is a list
                'pc1OrgCountry' : self.tree.xpath('gmd:'\
                    'identificationInfo[1]/*/gmd:pointOfContact[1]/*/'\
                    'gmd:contactInfo/*/gmd:address/*/gmd:country/'\
                    'gmd:Country', namespaces=self.ns)[0],
                'pc1OrgEmail' : self.tree.xpath('gmd:'\
                    'identificationInfo[1]/*/gmd:pointOfContact[1]/*/'\
                    'gmd:contactInfo/*/gmd:address/*/gmd:electronicMailAddress/'\
                    'gco:CharacterString', namespaces=self.ns)[0],
                'pc1OrgURL' : self.tree.xpath('gmd:'\
                    'identificationInfo[1]/*/gmd:pointOfContact[1]/*/'\
                    'gmd:contactInfo/*/gmd:onlineResource/*/gmd:linkage/'\
                    'gmd:URL', namespaces=self.ns)[0],
                'pc1LinkageProtocol' : self.tree.xpath('gmd:'\
                    'identificationInfo[1]/*/gmd:pointOfContact[1]/*/'\
                    'gmd:contactInfo/*/gmd:onlineResource/*/gmd:protocol/'\
                    'gco:CharacterString', namespaces=self.ns)[0],
                'pc1LinkageSiteName' : self.tree.xpath('gmd:'\
                    'identificationInfo[1]/*/gmd:pointOfContact[1]/*/'\
                    'gmd:contactInfo/*/gmd:onlineResource/*/gmd:name/'\
                    'gco:CharacterString', namespaces=self.ns)[0],
                        # description <- unchanged
                        # function <- unchanged
                        # hoursOfService <- unchanged
                        # contactInstructions <- unchanged
                        #the next element is a list
                'pc1Role' : self.tree.xpath('gmd:identificationInfo[1]/*/'\
                    'gmd:pointOfContact[1]/*/gmd:role/gmd:CI_RoleCode', 
                    namespaces=self.ns)[0],
                
                    # pointOfContact[2]
                'pc2OrganisationName' : self.tree.xpath('gmd:'\
                    'identificationInfo[1]/*/gmd:pointOfContact[1]/*/'\
                    'gmd:organisationName/gco:CharacterString', 
                    namespaces=self.ns)[0],
                'pc2PositionName' : self.tree.xpath('gmd:'\
                    'identificationInfo[1]/*/gmd:pointOfContact[1]/*/'\
                    'gmd:positionName/gco:CharacterString', 
                    namespaces=self.ns)[0],
                'pc2OrgAddress' : self.tree.xpath('gmd:'\
                    'identificationInfo[1]/*/gmd:pointOfContact[1]/*/'\
                    'gmd:contactInfo/*/gmd:address/*/gmd:deliveryPoint/'\
                    'gco:CharacterString', namespaces=self.ns)[0],
                'pc2OrgCity' : self.tree.xpath('gmd:'\
                    'identificationInfo[1]/*/gmd:pointOfContact[1]/*/'\
                    'gmd:contactInfo/*/gmd:address/*/gmd:city/'\
                    'gco:CharacterString', namespaces=self.ns)[0],
                'pc2OrgPostal' : self.tree.xpath('gmd:'\
                    'identificationInfo[1]/*/gmd:pointOfContact[1]/*/'\
                    'gmd:contactInfo/*/gmd:address/*/gmd:postalCode/'\
                    'gco:CharacterString', namespaces=self.ns)[0],
                    # the next element is a list
                'pc2OrgCountry' : self.tree.xpath('gmd:'\
                    'identificationInfo[1]/*/gmd:pointOfContact[1]/*/'\
                    'gmd:contactInfo/*/gmd:address/*/gmd:country/'\
                    'gmd:Country', namespaces=self.ns)[0],
                'pc2OrgEmail' : self.tree.xpath('gmd:'\
                    'identificationInfo[1]/*/gmd:pointOfContact[1]/*/'\
                    'gmd:contactInfo/*/gmd:address/*/gmd:electronicMailAddress/'\
                    'gco:CharacterString', namespaces=self.ns)[0],
                'pc2OrgURL' : self.tree.xpath('gmd:'\
                    'identificationInfo[1]/*/gmd:pointOfContact[1]/*/'\
                    'gmd:contactInfo/*/gmd:onlineResource/*/gmd:linkage/'\
                    'gmd:URL', namespaces=self.ns)[0],
                'pc2LinkageProtocol' : self.tree.xpath('gmd:'\
                    'identificationInfo[1]/*/gmd:pointOfContact[1]/*/'\
                    'gmd:contactInfo/*/gmd:onlineResource/*/gmd:protocol/'\
                    'gco:CharacterString', namespaces=self.ns)[0],
                'pc2LinkageSiteName' : self.tree.xpath('gmd:'\
                    'identificationInfo[1]/*/gmd:pointOfContact[1]/*/'\
                    'gmd:contactInfo/*/gmd:onlineResource/*/gmd:name/'\
                    'gco:CharacterString', namespaces=self.ns)[0],
                        # description <- unchanged
                        # function <- unchanged
                        # hoursOfService <- unchanged
                        # contactInstructions <- unchanged
                        #the next element is a list
                'pc2Role' : self.tree.xpath('gmd:identificationInfo[1]/*/'\
                    'gmd:pointOfContact[1]/*/gmd:role/gmd:CI_RoleCode', 
                    namespaces=self.ns)[0],
                    # resourceMaintenance <- unchanged
                    # graphicOverview
                'quicklookName' : self.tree.xpath('gmd:identificationInfo/*/'\
                    'gmd:graphicOverview/*/gmd:fileName/gco:CharacterString',
                    namespaces=self.ns)[0],
                        # fileDescription <- to be changed in the profile
                        # fileType <- to be changed in the profile
                    # resourceFormat <- unchanged
                    # descriptiveKeywords <- the _apply_keywords() method takes care of these
                    # resourceconstraints <- unchanged
                    # resourceconstraints <- unchanged
                    # resourceconstraints <- unchanged
                    # aggregationInfo <- unchanged
                    # aggregationInfo <- to be removed from the template
                    # aggregationInfo <- to be removed from the template
                    # spatialRepresentationType <- unchanged
                    # spatialResolution
                'resolution' : self.tree.xpath('gmd:identificationInfo/*/'\
                                               'gmd:spatialResolution/*/'\
                                               'gmd:distance/gco:Distance', 
                                               namespaces=self.ns)[0],
                    # language <- unchanged
                    # characterSet <- unchanged
                    # topicCategory <- the _apply_topic_categories() method takes care of these
                    # extent <- Geographhic location
                'westLongitude' : self.tree.xpath('gmd:identificationInfo/*/'\
                    'gmd:extent/*/*/*/gmd:westBoundLongitude/gco:Decimal', 
                    namespaces=self.ns)[0],
                'eastLongitude' : self.tree.xpath('gmd:identificationInfo/*/'\
                    'gmd:extent/*/*/*/gmd:eastBoundLongitude/gco:Decimal', 
                    namespaces=self.ns)[0],
                'southLatitude' : self.tree.xpath('gmd:identificationInfo/*/'\
                    'gmd:extent/*/*/*/gmd:southBoundLatitude/gco:Decimal',
                    namespaces=self.ns)[0],
                'northLatitude' : self.tree.xpath('gmd:identificationInfo/*/'\
                    'gmd:extent/*/*/*/gmd:northBoundLatitude/gco:Decimal',
                    namespaces=self.ns)[0],
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
    
    def _sort_keywords(self, productSettings):
        vocabularies = {None : []}
        for k in productSettings.keywords.all():
            vocab = k.controlledVocabulary
            if vocab is None:
                vocabularies[None].append(k)
            else:
                if vocabularies.get(vocab.title) is None:
                    vocabularies[vocab.title] = []
                entry = vocabularies.get(vocab.title)
                entry.append(k)
        return vocabularies

    def _apply_other_keywords(self, productSettings):
        '''
        Apply the keywords to the object's metadata tree.
        '''

        parentElement = self.tree.xpath('gmd:identificationInfo/'\
                                        'gmd:MD_DataIdentification', 
                                        namespaces=self.ns)[0]
        vocabularyDict = self._sort_keywords(productSettings)
        for vocab, keywordSettings in vocabularyDict.iteritems():
            descKeywordsEl = etree.SubElement(parentElement, 
                                              '{%s}descriptiveKeywords' % \
                                              self.ns['gmd'])
            mdKeywordsEl = etree.SubElement(descKeywordsEl, 
                                            '{%s}MD_Keywords' % \
                                            self.ns['gmd'])
            for keySett in keywordSettings:
                keywordEl = etree.SubElement(mdKeywordsEl, '{%s}keyword' % \
                                             self.ns['gmd'])
                charStringEl = etree.SubElement(keywordEl, 
                                                '{%s}CharacterString' % \
                                                self.ns['gco'])
                charStringEl.text = keySett.name
            if vocab is not None:
                vocSettings = keySett.controlledVocabulary
                thesaurusEl = etree.SubElement(mdKeywordsEl, 
                                               '{%s}thesaurusName' % \
                                               self.ns['gmd'])
                ciCitationEl = etree.SubElement(thesaurusEl, 
                                                '{%s}CI_Citation' % \
                                                self.ns['gmd'])
                titleEl = etree.SubElement(ciCitationEl, '{%s}title' % \
                                           self.ns['gmd'])
                titleEl.text = vocSettings.title
                dateEl = etree.SubElement(ciCitationEl, '{%s}date' % \
                                          self.ns['gmd'])
                ciDateEl = etree.SubElement(dateEl, '{%s}CI_Date' % \
                                            self.ns['gmd'])
                subDateEl = etree.SubElement(ciDateEl, '{%s}date' % \
                                             self.ns['gmd'])
                gcoDateEl = etree.SubElement(subDateEl, '{%s}Date' % \
                                             self.ns['gco'])
                gcoDateEl.text = vocSettings.date.strftime('%Y-%m-%d')
                dateTypeEl = etree.SubElement(ciDateEl, '{%s}dateType' % \
                                              self.ns['gmd'])
                dateTypeCodeEl = etree.SubElement(dateTypeEl, 
                                                  '{%s}CI_DateTypeCode' % \
                                                  self.ns['gmd'])
                codeElAttribs = dateTypeCodeEl.attrib
                codeElAttribs['{%s}codeList' % self.ns['gmd']] = 'http://'\
                        'standards.iso.org/ittf/PubliclyAvailableStandards/'\
                        'ISO_19139_Schemas/resources/Codelist/'\
                        'ML_gmxCodelists.xml#CI_DateTypeCode'
                codeElAttribs['{%s}codeListValue' % self.ns['gmd']] = vocSettings.dateType
                dateTypeCodeEl.text = vocSettings.dateType

    def _apply_INSPIRE_keyword(self, productSettings):
        '''
        Insert the INSPIRE keyword in the tree.

        INSPIRE keywords are defined in the GEMET INSPIRE themes controlled 
        vocabulary.
        '''

        parentElement = self.tree.xpath('gmd:identificationInfo/'\
                                        'gmd:MD_DataIdentification', 
                                        namespaces=self.ns)[0]
        descKeywordsEl = etree.SubElement(parentElement, 
                                          '{%s}descriptiveKeywords' % \
                                          self.ns['gmd'])
        mdKeywordsEl = etree.SubElement(descKeywordsEl, 
                                        '{%s}MD_Keywords' % \
                                        self.ns['gmd'])
        keywordEl = etree.SubElement(mdKeywordsEl, '{%s}keyword' % \
                                     self.ns['gmd'])
        charStringEl = etree.SubElement(keywordEl, 
                                        '{%s}CharacterString' % \
                                        self.ns['gco'])
        charStringEl.text = productSettings.inspireKeyword.name
        thesaurusEl = etree.SubElement(mdKeywordsEl, 
                                       '{%s}thesaurusName' % \
                                       self.ns['gmd'])
        ciCitationEl = etree.SubElement(thesaurusEl, 
                                        '{%s}CI_Citation' % \
                                        self.ns['gmd'])
        titleEl = etree.SubElement(ciCitationEl, '{%s}title' % \
                                   self.ns['gmd'])
        titleEl.text = 'GEMET - INSPIRE themes version 1.0'
        dateEl = etree.SubElement(ciCitationEl, '{%s}date' % \
                                  self.ns['gmd'])
        ciDateEl = etree.SubElement(dateEl, '{%s}CI_Date' % \
                                    self.ns['gmd'])
        subDateEl = etree.SubElement(ciDateEl, '{%s}date' % \
                                     self.ns['gmd'])
        gcoDateEl = etree.SubElement(subDateEl, '{%s}Date' % \
                                     self.ns['gco'])
        gcoDateEl.text = '2010-01-13'
        dateTypeEl = etree.SubElement(ciDateEl, '{%s}dateType' % \
                                      self.ns['gmd'])
        dateTypeCodeEl = etree.SubElement(dateTypeEl, 
                                          '{%s}CI_DateTypeCode' % \
                                          self.ns['gmd'])
        codeElAttribs = dateTypeCodeEl.attrib
        codeElAttribs['{%s}codeList' % self.ns['gmd']] = 'http://'\
                'standards.iso.org/ittf/PubliclyAvailableStandards/'\
                'ISO_19139_Schemas/resources/Codelist/'\
                'ML_gmxCodelists.xml#CI_DateTypeCode'
        dateType = 'publication'
        codeElAttribs['{%s}codeListValue' % self.ns['gmd']] = dateType
        dateTypeCodeEl.text = dateType

    def apply_keywords(self):
        self._remove_original_keywords()
        self._apply_INSPIRE_keyword(productSettings)
        self._apply_other_keywords(productSettings)

    def _remove_original_keywords(self):
        parent = self.tree.xpath('gmd:identificationInfo/'\
                                 'gmd:MD_DataIdentification', 
                                 namespaces=self.ns)[0]
        keywords = parent.xpath('gmd:descriptiveKeywords', namespaces=self.ns)
        for k in keywords:
            parent.remove(k)

    def _remove_original_topic_categories(self):
        parent = self.tree.xpath('gmd:identificationInfo/'\
                                 'gmd:MD_DataIdentification', 
                                 namespaces=self.ns)[0]
        topicCats = parent.xpath('gmd:topicCategory', namespaces=self.ns)
        for t in topicCats:
            parent.remove(t)

    def _apply_topic_categories(self, product):
        '''
        Apply the defined ISO Topic Categories.

        NOTE: Most of the time the INSPIRE keyword has a correspondence
        to one ISO topic category. As such, the resulting topic category set 
        is composed of user defined categories plus the INSPIRE correspondent.

        Inputs:

            product - A systemsettings.models.Product instance
        '''

        self._remove_original_topic_categories()
        topicCategories = [t.name for f in product.topicCategories.all()]
        topicCategories.append(product.inspireKeyword.isoTopicCategory.name)
        parentElement = self.tree.xpath('gmd:identificationInfo/'\
                                        'gmd:MD_DataIdentification', 
                                        namespaces=self.ns)[0]
        for t in topicCategories:
            topicCatEl = etree.SubElement(parentElement, '{%s}topicCategory' % \
                                          self.ns['gmd'])
            MDTopicCatCode = etree.SubElement(topicCatEl, 
                                              '{%s}MD_TopicCategoryCode' % \
                                              self.ns['gmd'])
            MDTopicCatCode.text = t

    def _apply_contact_info(self, parentElement, contactElName, positionName, 
                            role, contact):
        '''

        Inputs:

            parentElement - lxml element with the parent element.

            contactElName - A string specifying the name of the contact
                info element to create.

            positionName - A string specifying the value for the 'positionName'
                xml element.

            role - A string specifying the value for the 'role' xml element.

            contact - systemsettings.models.GeneralMetadata instance.
        '''

        contactEl = etree.SubElement(parentElement, '{%s}%s' % (self.ns['gmd'],
                                     contactElName))
        ciRespPartyEl = etree.SubElement(contactEl, '{%s}CI_ResponsibleParty'\
                                         % self.ns['gmd'])
        orgNameEl = etree.SubElement(ciRespPartyEl, '{%s}organisationName'\
                                     % self.ns['gmd'])
        gcoOrgNameEl = etree.SubElement(orgNameEl, '{%s}CharacterString'\
                                        % self.ns['gco'])
        gcoOrgNameEl.text = contact.organization.name
        positionEl = etree.SubElement(ciRespPartyEl, '{%s}positionName'\
                                      % self.ns['gmd'])
        gcoPositionNameEl = etree.SubElement(positionEl, '{%s}CharacterString'\
                                             % self.ns['gco'])
        gcoPositionNameEl.text = positionName
        contactInfoEl = etree.SubElement(ciRespPartyEl, '{%}contactInfo' \
                                         % self.ns['gmd'])
        ciContactEl = etree.SubElement(contactInfoEl, '{%}CI_Contact' \
                                       % self.ns['gmd'])
        addressEl = etree.SubElement(ciContactEl, '{%}address' \
                                     % self.ns['gmd'])
        ciAddressEl = etree.SubElement(addressEl, '{%}CI_Address' \
                                       % self.ns['gmd'])
        delPointEl = etree.SubElement(ciAddressEl, '{%}deliveryPoint' \
                                       % self.ns['gmd'])
        gcoDelPointEl = etree.SubElement(delPointEl, '{%}CharacterString' \
                                       % self.ns['gco'])
        gcoDelPointEl.text = contact.organization.streetAddress
        cityEl = etree.SubElement(ciAddressEl, '{%}city' \
                                       % self.ns['gmd'])
        gcoCityEl = etree.SubElement(cityEl, '{%}CharacterString' \
                                       % self.ns['gco'])
        gcoCityEl.text = contact.organization.city
        postalCodeEl = etree.SubElement(ciAddressEl, '{%}postalCode' \
                                       % self.ns['gmd'])
        gcoPostalEl = etree.SubElement(postalCodeEl, '{%}CharacterString' \
                                       % self.ns['gco'])
        gcoPostalEl.text = contact.organization.postalCode
        countryEl = etree.SubElement(ciAddressEl, '{%}country' \
                                       % self.ns['gmd'])
        countryListEl = etree.SubElement(countryEl, '{%}Country' \
                                       % self.ns['gmd'])
        countryListElAttribs = countryListEl.attrib
        countryListElAttribs['{%s}codeList' % self.ns['gmd']] = 'http://'\
            'www.iso.org/iso/en/prods-services/iso3166ma/'\
            '02iso-3166-code-lists/index.html'
        countryListElAttribs['{%s}codeSpace' % self.ns['gmd']] = 'ISO 3166-1'
        countryCode = contact.organization.country
        countryListElAttribs['{%s}codeListValue' % self.ns['gmd']] = countryCode
        countryListEl.text = pycountry.countries.get(alpha2=countryCode)
        emailEl = etree.SubElement(ciAddressEl, '{%}electronicMailAddress' \
                                   % self.ns['gmd'])
        gcoEmailEl = etree.SubElement(emailEl, '{%}CharacterString' \
                                      % self.ns['gco'])
        gcoEmailEl.text = contact.email
        onlineResourceEl = etree.SubElement(ciContactEl, '{%}onlineResource' \
                                            % self.ns['gmd'])
        ciOnlineEl = etree.SubElement(onlineResourceEl, '{%}CI_OnlineResource'\
                                      % self.ns['gmd'])
        linkageEl = etree.SubElement(ciOnlineEl, '{%}linkage' % self.ns['gmd'])
        urlEl = etree.SubElement(linkageEl, '{%}URL' % self.ns['gmd'])
        urlEl.text = contact.organization.url
        protocolEl = etree.SubElement(ciOnlineEl, '{%}protocol' % \
                                      self.ns['gmd'])
        gcoProtocolEl = etree.SubElement(protocolEl, '{%}CharacterString' % \
                                         self.ns['gco'])
        gcoProtocolEl.text = 'HTTP'
        nameEl = etree.SubElement(ciOnlineEl, '{%}name' % self.ns['gmd'])
        gcoNameEl = etree.SubElement(nameEl, '{%}CharacterString' % \
                                         self.ns['gco'])
        gcoNameEl.text = '%s website' % contact.organization.short_name
        descrEl = etree.SubElement(ciOnlineEl, '{%}description' % self.ns['gmd'])
        gcoDescrEl = etree.SubElement(descrEl, '{%}CharacterString' % \
                                         self.ns['gco'])
        gcoDescrEl.text = 'Organization website'
        functionEl = etree.SubElement(ciOnlineEl, '{%}function' \
                                       % self.ns['gmd'])
        functionListEl = etree.SubElement(functionEl, 'CI_OnlineFunctionCode' \
                                          % self.ns['gmd'])
        functionListElAttribs = functionListEl.attrib
        functionListElAttribs['{%s}codeList' % self.ns['gmd']] = 'http://'\
            'standards.iso.org/ittf/PubliclyAvailableStandards/'\
            'ISO_19139_Schemas/resources/Codelist/'\
            'ML_gmxCodelists.xml#CI_OnlineFunctionCode'
        functionListElAttribs['{%s}codeListValue' % self.ns['gmd']] = 'information'
        functionListElAttribs.text = 'information'
        hoursServEl = etree.SubElement(ciContactEl, '{%}hoursOfService' \
                                       % self.ns['gmd'])
        gcoHoursEl = etree.SubElement(hoursServEl, '{%}CharacterString' % \
                                      self.ns['gco'])
        gcoHoursEl.text = 'Office hours, 5 days per week'
        instructionsEl = etree.SubElement(ciContactEl, '{%}contactInstructions'\
                                          % self.ns['gmd'])
        gcoInstructionsEl = etree.SubElement(instructionsEl, '{%}CharacterString'\
                                             % self.ns['gco'])
        gcoInstructionsEl.text = 'Preferrably by e-mail'
        roleEl = etree.SubElement(ciRespPartyEl, '{%}role' % self.ns['gmd'])
        roleListEl = etree.SubElement(roleEl, '{%}CI_RoleCode' % self.ns['gmd'])
        roleListAttribs = roleListEl.attrib
        roleListAttribs['{%}codeList' % self.ns['gmd']] = 'http://standards.'\
                'iso.org/ittf/PubliclyAvailableStandards/ISO_19139_Schemas/'\
                'resources/Codelist/ML_gmxCodelists.xml#CI_RoleCode'
        roleListAttribs['{%}codeListValue' % self.ns['gmd']] = role

    def _remove_contact_info(self, parentElement, contactElName):
        '''
        Delete the contact_info element from the xml tree.
        '''

        contactEls = parentElement.xpath('gmd:%s' % contactElName, 
                                         namespaces=self.ns)
        for c in contactEls:
            parentElement.remove(c)

    def apply_changes(self, filePath, mapper):
        '''
        Aplpy the changes to the XML tree.

        Inputs:

            filePath - the original HDF5 tile being processed
        '''

        fs = utilities.get_file_settings(filePath)
        minx, miny, maxx, maxy = mapper.get_bounds(filePath)
        uuid = uuid1()
        self.update_element('fileIdentifier', str(uuid))
        self.update_element('parentIdentifier', fs.product.iParentIdentifier)
        self.update_element('hierarchyLevel', fs.product.iResourceType)


        
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
