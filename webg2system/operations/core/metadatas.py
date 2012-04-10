#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
A module for implementing metadata related functionality for the Geoland-2 
processing system.
"""

import os
import re
import logging
from lxml import etree
import urllib
import urllib2
import cookielib
from uuid import uuid1
import datetime as dt

import pycountry

import utilities
import systemsettings.models as ss

class MetadataGenerator(object):

    def __init__(self, template, timeslot, product):
        self.logger = logging.getLogger(
                '.'.join((__name__, self.__class__.__name__)))
        self.timeslot = timeslot
        self.product = product
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
                #07 - contact (Metadata on Metadata) <- handled by the _apply_contact_info() method 
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
                    # pointOfContact[1] <- handled by the _apply_contact_info() method 
                    # pointOfContact[2] <- handled by the _apply_contact_info() method 
                    # resourceMaintenance <- unchanged
                    # graphicOverview <- handled by the _apply_graphic_overview() method
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
                    # extent <- temporal extent <- to be removed from the template
                    # supplementalInformation
                'supplemental' : self.tree.xpath('gmd:identificationInfo/*/'\
                    'gmd:supplementalInformation/gco:CharacterString', 
                    namespaces=self.ns)[0],
                #15 - contentInfo <- the _apply_contentInfo method
                #21 - distributionInfo
                    # distribution format <- unchanged
                    # distributor
                        # distributorContact <- _apply_contact_info method
                        # distributionOrderProcess <- unchanged
                    # transfer options
                'linkage' : self.tree.xpath('gmd:distributionInfo/*/gmd:'\
                    'transferOptions[1]/*/gmd:onLine/*/gmd:linkage/gmd:URL', 
                    namespaces=self.ns)[0],
                #22 - dataQualityInfo
                    # scope <-unchanged
                    # report
                'thematicAccuracyTitle' : self.tree.xpath('gmd:' \
                    'dataQualityInfo/*/gmd:report/gmd:DQ_ThematicAccuracy/'\
                    'gmd:result/*/gmd:specification/*/gmd:title/'\
                    'gco:CharacterString', namespaces=self.ns)[0],
                'valReport' : self.tree.xpath('gmd:dataQualityInfo/*/gmd:'\
                    'report/gmd:DQ_ThematicAccuracy/gmd:result/*/gmd:'\
                    'explanation/gco:CharacterString', namespaces=self.ns)[0],
                #'thematicAccuracyDate' : self.tree.xpath('', namespaces=self.ns)[0],
                'lineage' : self.tree.xpath('gmd:dataQualityInfo/*/gmd:'\
                    'lineage/*/gmd:statement/gco:CharacterString', 
                    namespaces=self.ns)[0],
                #23 - metadataMaintenance <- unchanged
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
            vocab = k.controlled_vocabulary
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
            if len(keywordSettings) != 0:
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
                vocSettings = keySett.controlled_vocabulary
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
                codeElAttribs['codeList']= 'http://'\
                        'standards.iso.org/ittf/PubliclyAvailableStandards/'\
                        'ISO_19139_Schemas/resources/Codelist/'\
                        'ML_gmxCodelists.xml#CI_DateTypeCode'
                codeElAttribs['codeListValue'] = vocSettings.date_type
                dateTypeCodeEl.text = vocSettings.date_type

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
        codeElAttribs['codeList'] = 'http://'\
                'standards.iso.org/ittf/PubliclyAvailableStandards/'\
                'ISO_19139_Schemas/resources/Codelist/'\
                'ML_gmxCodelists.xml#CI_DateTypeCode'
        dateType = 'publication'
        codeElAttribs['codeListValue'] = dateType
        dateTypeCodeEl.text = dateType

    def _apply_keywords(self, productSettings):
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
        topicCategories = [t.name for t in product.topicCategories.all()]
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

    def _apply_contact_info(self, parentElement, contactElName, role, contact, 
                            positionName=None):
        '''

        Inputs:

            parentElement - lxml element with the parent element.

            contactElName - A string specifying the name of the contact
                info element to create.

            role - A string specifying the value for the 'role' xml element.

            contact - systemsettings.models.GeneralMetadata instance.

            positionName - A string specifying the value for the 'positionName'
                xml element. If None (the default) this element is ommited
                from the xml tree.
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
        if positionName is not None:
            positionEl = etree.SubElement(ciRespPartyEl, '{%s}positionName'\
                                          % self.ns['gmd'])
            gcoPositionNameEl = etree.SubElement(positionEl, '{%s}CharacterString'\
                                                 % self.ns['gco'])
            gcoPositionNameEl.text = positionName
        contactInfoEl = etree.SubElement(ciRespPartyEl, '{%s}contactInfo' \
                                         % self.ns['gmd'])
        ciContactEl = etree.SubElement(contactInfoEl, '{%s}CI_Contact' \
                                       % self.ns['gmd'])
        addressEl = etree.SubElement(ciContactEl, '{%s}address' \
                                     % self.ns['gmd'])
        ciAddressEl = etree.SubElement(addressEl, '{%s}CI_Address' \
                                       % self.ns['gmd'])
        delPointEl = etree.SubElement(ciAddressEl, '{%s}deliveryPoint' \
                                       % self.ns['gmd'])
        gcoDelPointEl = etree.SubElement(delPointEl, '{%s}CharacterString' \
                                       % self.ns['gco'])
        gcoDelPointEl.text = contact.organization.streetAddress
        cityEl = etree.SubElement(ciAddressEl, '{%s}city' \
                                       % self.ns['gmd'])
        gcoCityEl = etree.SubElement(cityEl, '{%s}CharacterString' \
                                       % self.ns['gco'])
        gcoCityEl.text = contact.organization.city
        postalCodeEl = etree.SubElement(ciAddressEl, '{%s}postalCode' \
                                       % self.ns['gmd'])
        gcoPostalEl = etree.SubElement(postalCodeEl, '{%s}CharacterString' \
                                       % self.ns['gco'])
        gcoPostalEl.text = contact.organization.postalCode
        countryEl = etree.SubElement(ciAddressEl, '{%s}country' \
                                       % self.ns['gmd'])
        countryListEl = etree.SubElement(countryEl, '{%s}Country' \
                                       % self.ns['gmd'])
        countryListElAttribs = countryListEl.attrib
        countryListElAttribs['codeList'] = 'http://'\
            'www.iso.org/iso/en/prods-services/iso3166ma/'\
            '02iso-3166-code-lists/index.html'
        countryListElAttribs['codeSpace'] = 'ISO 3166-1'
        countryCode = contact.organization.country
        countryListElAttribs['codeListValue'] = countryCode
        countryListEl.text = pycountry.countries.get(alpha2=countryCode).name
        emailEl = etree.SubElement(ciAddressEl, '{%s}electronicMailAddress' \
                                   % self.ns['gmd'])
        gcoEmailEl = etree.SubElement(emailEl, '{%s}CharacterString' \
                                      % self.ns['gco'])
        gcoEmailEl.text = contact.email
        onlineResourceEl = etree.SubElement(ciContactEl, '{%s}onlineResource' \
                                            % self.ns['gmd'])
        ciOnlineEl = etree.SubElement(onlineResourceEl, '{%s}CI_OnlineResource'\
                                      % self.ns['gmd'])
        linkageEl = etree.SubElement(ciOnlineEl, '{%s}linkage' % self.ns['gmd'])
        urlEl = etree.SubElement(linkageEl, '{%s}URL' % self.ns['gmd'])
        urlEl.text = contact.organization.url
        protocolEl = etree.SubElement(ciOnlineEl, '{%s}protocol' % \
                                      self.ns['gmd'])
        gcoProtocolEl = etree.SubElement(protocolEl, '{%s}CharacterString' % \
                                         self.ns['gco'])
        gcoProtocolEl.text = 'HTTP'
        nameEl = etree.SubElement(ciOnlineEl, '{%s}name' % self.ns['gmd'])
        gcoNameEl = etree.SubElement(nameEl, '{%s}CharacterString' % \
                                         self.ns['gco'])
        gcoNameEl.text = '%s website' % contact.organization.short_name
        descrEl = etree.SubElement(ciOnlineEl, '{%s}description' % self.ns['gmd'])
        gcoDescrEl = etree.SubElement(descrEl, '{%s}CharacterString' % \
                                         self.ns['gco'])
        gcoDescrEl.text = 'Organization website'
        functionEl = etree.SubElement(ciOnlineEl, '{%s}function' \
                                       % self.ns['gmd'])
        functionListEl = etree.SubElement(functionEl, '{%s}CI_OnlineFunctionCode' \
                                          % self.ns['gmd'])
        functionListElAttribs = functionListEl.attrib
        functionListElAttribs['codeList'] = 'http://'\
            'standards.iso.org/ittf/PubliclyAvailableStandards/'\
            'ISO_19139_Schemas/resources/Codelist/'\
            'ML_gmxCodelists.xml#CI_OnlineFunctionCode'
        functionListElAttribs['codeListValue'] = 'information'
        functionListEl.text = 'information'
        hoursServEl = etree.SubElement(ciContactEl, '{%s}hoursOfService' \
                                       % self.ns['gmd'])
        gcoHoursEl = etree.SubElement(hoursServEl, '{%s}CharacterString' % \
                                      self.ns['gco'])
        gcoHoursEl.text = 'Office hours, 5 days per week'
        instructionsEl = etree.SubElement(ciContactEl, '{%s}contactInstructions'\
                                          % self.ns['gmd'])
        gcoInstructionsEl = etree.SubElement(instructionsEl, '{%s}CharacterString'\
                                             % self.ns['gco'])
        gcoInstructionsEl.text = 'Preferrably by e-mail'
        roleEl = etree.SubElement(ciRespPartyEl, '{%s}role' % self.ns['gmd'])
        roleListEl = etree.SubElement(roleEl, '{%s}CI_RoleCode' % self.ns['gmd'])
        roleListAttribs = roleListEl.attrib
        roleListAttribs['codeList'] = 'http://standards.'\
                'iso.org/ittf/PubliclyAvailableStandards/ISO_19139_Schemas/'\
                'resources/Codelist/ML_gmxCodelists.xml#CI_RoleCode'
        roleListAttribs['codeListValue'] = role
        roleListEl.text = role

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

            filePath - the original HDF5 tile being processed.

            mapper - A Mapper instance.
        '''

        productVersion = re.search(r'GEO_(v\d)$', filePath).groups()[0]
        today = dt.date.today().strftime('%Y-%m-%d')
        fileName = os.path.basename(filePath)
        fileTimeslot = utilities.extract_timeslot(filePath)
        fs = utilities.get_file_settings(filePath)
        minx, miny, maxx, maxy = mapper.get_bounds(filePath, 
                                                   self.product.pixelSize)
        tileName = mapper._get_tile_name(filePath)
        uuid = str(uuid1())
        rootAttribs = self.tree.getroot().attrib
        rootAttribs['id'] = '%sMetadata' % self.product.short_name
        self.update_element('fileIdentifier', uuid)
        self.update_element('parentIdentifier', self.product.iParentIdentifier)
        self.update_element('hierarchyLevel', 'dataset')
        self._remove_contact_info(self.tree.getroot(), 'contact')
        self._apply_contact_info(self.tree.getroot(), 'contact', 
                                 role='pointOfContact', 
                                 contact=self.product.originator_collaborator)
        self.update_element('dateStamp', today)
        rowSize = fs.fileextrainfo_set.get(name='nLines').string
        self.update_element('rowSize', rowSize)
        self.update_element('rowResolution', '%.2f' % self.product.pixelSize)
        colSize = fs.fileextrainfo_set.get(name='nCols').string
        self.update_element('colSize', colSize)
        self.update_element('colResolution', '%.2f' % self.product.pixelSize)
        cornerPoint = '%.1f %.1f' % (maxy, minx)
        self.update_element('cornerPoint', cornerPoint)
        self.update_element('referenceSystemIdentifier', 
                            'EPSG:%s' % self.product.ireferenceSystemID)
        self._apply_citation(self.product, fileName, productVersion, uuid)
        self.update_element('abstract', self.product.iResourceAbstract)
        self.update_element('credit', self.product.iCredit)
        identInfoEl = self.tree.xpath('gmd:identificationInfo/'\
                                      'gmd:MD_DataIdentification', 
                                      namespaces=self.ns)[0]
        self._remove_contact_info(identInfoEl, 'pointOfContact')
        self._apply_contact_info(identInfoEl, 'pointOfContact', 
                                 role='principalInvestigator', 
                                 positionName='Researcher',
                                 contact=self.product.principal_investigator)
        self._apply_contact_info(identInfoEl, 'pointOfContact', 
                                 role='originator', 
                                 positionName='Geoland2 Help Desk',
                                 contact=self.product.originator_collaborator)
        self._apply_graphic_overview(tileName, self.product)
        self._apply_aggregation_infos()
        self._apply_temporal_extent(self.product, fileTimeslot)
        self._apply_keywords(self.product)
        self.update_element('resolution', '%.2f' % self.product.pixelSize)
        self._apply_topic_categories(self.product)
        self.update_element('westLongitude', '%.2f' % minx)
        self.update_element('eastLongitude', '%.2f' % maxx)
        self.update_element('southLatitude', '%.2f' % miny)
        self.update_element('northLatitude', '%.2f' % maxy)
        self.update_element('supplemental', self.product.supplemental_info)
        self._remove_contentInfo()
        for dataset in self.product.dataset_set.all():
            self._apply_contentInfo(dataset)
        distributorEl = self.tree.xpath('gmd:distributionInfo/*/' \
            'gmd:distributor/gmd:MD_Distributor', namespaces=self.ns)[0]
        self._remove_contact_info(distributorEl, 'distributorContact')
        self._apply_contact_info(distributorEl, 'distributorContact', 
                                 role='distributor',
                                 positionName='IM Geoland-2 Helpdesk',
                                 contact=self.product.distributor)
        self._apply_linkage(tileName, self.product)
        self.update_element('thematicAccuracyTitle', 'Internal validation report')
        self.update_element('valReport', self.product.validation_report)
        self.update_element('lineage', self.product.lineage)

    def _apply_linkage(self, tileName, product):
        baseURL = ss.WebServer.objects.get().public_URL
        ts = self.timeslot.strftime('%Y%m%d%H%M')
        url = '%s/operations/products/%s/%s/%s/product' % \
                (baseURL, product.short_name, tileName, ts)
        self.update_element('linkage', url)

    def _apply_graphic_overview(self, tileName, product):
        fileNameEl = self.tree.xpath('gmd:identificationInfo/*/'\
                                     'gmd:graphicOverview/*/'\
                                     'gmd:fileName/gco:CharacterString',
                                     namespaces=self.ns)[0]

        #filename is an URL that should mimic the regex in operations.urls.py
        baseURL = ss.WebServer.objects.get().public_URL
        ts = self.timeslot.strftime('%Y%m%d%H%M')
        url = '%s/operations/products/%s/%s/%s/quicklook' % \
                (baseURL, product.short_name, tileName, ts)
        fileNameEl.text = url
        fileDescEl = self.tree.xpath('gmd:identificationInfo/*/'\
                                     'gmd:graphicOverview/*/'\
                                     'gmd:fileDescription/gco:CharacterString',
                                     namespaces=self.ns)[0]
        fileDescEl.text = product.graphic_overview_description
        fileTypeEl = self.tree.xpath('gmd:identificationInfo/*/'\
                                     'gmd:graphicOverview/*/'\
                                     'gmd:fileType/gco:CharacterString',
                                     namespaces=self.ns)[0]
        fileTypeEl.text = product.graphic_overview_type

    def _apply_aggregation_infos(self):
        parentEl = self.tree.xpath('gmd:identificationInfo/'\
                                        'gmd:MD_DataIdentification', 
                                        namespaces=self.ns)[0]
        for previousAggInfo in parentEl.xpath('gmd:aggregationInfo', 
                namespaces=self.ns):
            dsAssocTypeCode = previousAggInfo.xpath(
                    'gmd:MD_AggregateInformation/gmd:associationType/gmd:'\
                        'DS_AssociationTypeCode', 
                    namespaces=self.ns)[0]
            if dsAssocTypeCode.text != 'partOfSeamlessDatabase':
                parentEl.remove(previousAggInfo)
        for sourceSett in self.product.sources.all():
            sourceName = sourceSett.name
            sensor = sourceSett.sourceextrainfo_set.get(name='sensor').string
            self._apply_aggreg_info(parentEl, 'platform', sourceName)
            self._apply_aggreg_info(parentEl, 'sensor', sensor)

    def _apply_aggreg_info(self, parentEl, initiative, initiativeValue): 
        '''
        Create new aggregationInfo elements.

        Inputs:

            parentEl - 

            initiative - The text that goes into the DS_InitiativeTypeCode 
                element. Should be either 'platform' or 'sensor'.

            initiativeValue - The value of the initiative.

        '''

        AggEl = etree.SubElement(parentEl, '{%s}aggregationInfo' % \
                                 self.ns['gmd'])
        mdEl = etree.SubElement(AggEl, '{%s}MD_AggregateInformation' % \
                                self.ns['gmd'])
        assocEl = etree.SubElement(mdEl, '{%s}associationType' % \
                                   self.ns['gmd'])
        dsAssocEl = etree.SubElement(assocEl, '{%s}DS_AssociationTypeCode'\
                                     % self.ns['gmd'])
        dsAssocEl.attrib['codeList'] = 'http://'\
                'www.isotc211.org/2005/resources/codelist/'\
                'gmxCodelists.xml#DS_AssociationTypeCode'
        dsAssocEl.attrib['codeListValue'] = 'source'
        dsAssocEl.text = 'source'
        initiEl = etree.SubElement(mdEl, '{%s}initiativeType'\
                                   % self.ns['gmd'])
        dsInitiEl = etree.SubElement(initiEl, '{%s}DS_InitiativeTypeCode'\
                                     % self.ns['gmd'])
        dsInitiEl.attrib['codeList'] = 'http://'\
                'www.isotc211.org/2005/resources/codelist/'\
                'gmxCodelists.xml#DS_InitiativeTypeCode'
        dsInitiEl.attrib['codeListValue'] = initiative
        dsInitiEl.text = initiativeValue

    def _remove_contentInfo(self):
        contentInfos = self.tree.xpath('gmd:contentInfo', namespaces=self.ns)
        for c in contentInfos:
            self.tree.getroot().remove(c)

    def _apply_contentInfo(self, dataset):
        ciEl = etree.SubElement(self.tree.getroot(), '{%s}contentInfo' % \
                                self.ns['gmd'])
        covEl = etree.SubElement(ciEl, '{%s}MD_CoverageDescription' \
                                 % self.ns['gmd'])
        covEl.attrib['uuid'] = dataset.name
        attrDescriptionEl = etree.SubElement(covEl, '{%s}attributeDescription' \
                                             % self.ns['gmd'])
        recordTypeEl = etree.SubElement(attrDescriptionEl, '{%s}RecordType' \
                                        % self.ns['gco'])
        recordTypeEl.text = dataset.name
        contentTypeEl = etree.SubElement(covEl, '{%s}contentType' % \
                                         self.ns['gmd'])
        contTypeAttr = contentTypeEl.attrib
        contTypeAttr['codeList'] = 'http://' \
            'www.isotc211.org/2005/resources/codelist/gmxCodelists.xml' \
            '#MD_CoverageContentTypeCode'
        contTypeAttr['codeListValue'] = dataset.coverage_content_type
        self._apply_content_info_dimension_digital_number(covEl, dataset)
        self._apply_content_info_dimension_physical_value(covEl, dataset)
        self._apply_content_info_dimension_invalid(covEl, dataset)

    def _apply_content_info_dimension_digital_number(self, parent, dataset):
        seqIDName = 'Digital Number'
        seqIDType = 'value type'
        descriptor = 'Significant digital value range'
        maxVal = str(dataset.max_value * dataset.scalingFactor)
        minVal = str(dataset.min_value * dataset.scalingFactor)
        bitDepth = str(dataset.bit_depth)
        scaleFactor = str(dataset.scalingFactor)
        offset = '0.0'
        self._apply_content_info_dimension(parent, seqIDName, seqIDType, 
                                           descriptor, maxVal, minVal,
                                           bitDepth, scaleFactor, offset)

    def _apply_content_info_dimension_physical_value(self, parent, dataset):
        seqIDName = 'Physical Value'
        seqIDType = 'value type'
        descriptor = dataset.name
        maxVal = str(dataset.max_value)
        minVal = str(dataset.min_value)
        #units are missing
        self._apply_content_info_dimension(parent, seqIDName, seqIDType,
                                           descriptor, maxVal, minVal)

    def _apply_content_info_dimension_invalid(self, parent, dataset):
        seqIDName = 'Invalid'
        seqIDType = 'flag type'
        descriptor = 'Invalid'
        maxVal = str(dataset.missingValue)
        minVal = str(dataset.missingValue)
        bitDepth = str(dataset.bit_depth)
        self._apply_content_info_dimension(parent, seqIDName, seqIDType,
                                           descriptor, maxVal, minVal, 
                                           bitDepth=bitDepth)

    def _apply_content_info_dimension(self, parent, seqIDName, seqIDType, 
                                      descriptor, maxVal, minVal, 
                                      bitDepth=None, scaleFactor=None, 
                                      offset=None):

        dimEl = etree.SubElement(parent, '{%s}dimension' % self.ns['gmd'])
        bandEl = etree.SubElement(dimEl, '{%s}MD_Band' % self.ns['gmd'])
        seqIdEl = etree.SubElement(bandEl, '{%s}sequenceIdentifier' % \
                                        self.ns['gmd'])
        memberNameEl = etree.SubElement(seqIdEl, '{%s}MemberName' % \
                                             self.ns['gco'])
        aNameEl = etree.SubElement(memberNameEl, '{%s}aName' % \
                                        self.ns['gco'])
        aNameGcoEl = etree.SubElement(aNameEl, '{%s}CharacterString' % \
                                           self.ns['gco'])
        aNameGcoEl.text = seqIDName
        attribTypeEl = etree.SubElement(memberNameEl, '{%s}attributeType'\
                                             % self.ns['gco'])
        typeNameEl = etree.SubElement(attribTypeEl, '{%s}TypeName'\
                                           % self.ns['gco'])
        aNameEl2 = etree.SubElement(typeNameEl, '{%s}aName' % \
                                         self.ns['gco'])
        aNameGcoEl2 = etree.SubElement(aNameEl2, '{%s}CharacterString' % \
                                           self.ns['gco'])
        aNameGcoEl2.text = seqIDType
        descriptorEl = etree.SubElement(bandEl, '{%s}descriptor' % \
                                             self.ns['gmd'])
        descGco = etree.SubElement(descriptorEl, '{%s}CharacterString' % \
                                        self.ns['gco'])
        descGco.text = descriptor
        maxValEl = etree.SubElement(bandEl, '{%s}maxValue' % \
                                         self.ns['gmd'])
        maxGco = etree.SubElement(maxValEl, '{%s}Real' % self.ns['gco'])
        maxGco.text = maxVal
        minValEl = etree.SubElement(bandEl, '{%s}minValue' % \
                                         self.ns['gmd'])
        minGco = etree.SubElement(minValEl, '{%s}Real' % self.ns['gco'])
        minGco.text = minVal
        if bitDepth is not None:
            bitsEl = etree.SubElement(bandEl, '{%s}bitsPerValue' % \
                                           self.ns['gmd'])
            bitDepthGco = etree.SubElement(bitsEl, '{%s}Integer' % \
                                                self.ns['gco'])
            bitDepthGco.text = bitDepth
        if scaleFactor is not None:
            scaleFactorEl = etree.SubElement(bandEl, '{%s}scaleFactor' % \
                                                  self.ns['gmd'])
            scaleFactorGco = etree.SubElement(scaleFactorEl, '{%s}Real' %\
                                                   self.ns['gco'])
            scaleFactorGco.text = scaleFactor
        if offset is not None:
            offsetEl = etree.SubElement(bandEl, '{%s}offset' % \
                                             self.ns['gmd'])
            offsetGco = etree.SubElement(offsetEl, '{%s}Real' % \
                                              self.ns['gco'])
            offsetGco.text = offset

    def _apply_citation(self, productSettings, fileName, prodVersion, uuid):
        today = dt.date.today().strftime('%Y-%m-%d')
        citationEl = self.tree.xpath('gmd:identificationInfo/*/gmd:citation/*',
                                     namespaces=self.ns)[0]
        titleEl = citationEl.xpath('gmd:title/gco:CharacterString', namespaces=self.ns)[0]
        #titleEl.text = productSettings.iResourceTitle
        titleEl.text = fileName

        theDateEl = citationEl.xpath('gmd:date/*', namespaces=self.ns)[0]
        dateEl = theDateEl.xpath('gmd:date/gco:Date', namespaces=self.ns)[0]
        dateEl.text = today
        #dateTypeEl = theDateEl.xpath('gmd:dateType/gmd:CI_DateTypeCode', namespaces=self.ns)[0]
        editionEl = citationEl.xpath('gmd:edition/gco:CharacterString', namespaces=self.ns)[0]
        editionEl.text = prodVersion
        editionDateEl = citationEl.xpath('gmd:editionDate/gco:Date', namespaces=self.ns)[0]
        editionDateEl.text = today

        identifierEl = citationEl.xpath('gmd:identifier/*', namespaces=self.ns)[0]
        authTitleEl = identifierEl.xpath('gmd:authority/gmd:CI_Citation/'\
                                            'gmd:title/gco:CharacterString', 
                                            namespaces=self.ns)[0]
        authTitleEl.text = productSettings.originator_collaborator.organization.name

        authDateEl = identifierEl.xpath('gmd:authority/*/gmd:date/*/gmd:date/'\
                                      'gco:Date', namespaces=self.ns)[0]
        authDateEl.text = today
        authDateTypeEl = identifierEl.xpath('gmd:authority/*/gmd:date/*/'\
                                            'gmd:dateType/gmd:CI_DateTypeCode', 
                                            namespaces=self.ns)[0]
        authDateTypeEl.attrib['codeListValue'] = 'publication'
        authDateTypeEl.text = 'publication'
        identifierCodeEl = identifierEl.xpath('gmd:code/gco:CharacterString', 
                                              namespaces=self.ns)[0]
        identifierCodeEl.text = uuid
        otherDetailsEl = citationEl.xpath('gmd:otherCitationDetails/'\
                                          'gco:CharacterString', 
                                          namespaces=self.ns)[0]
        otherDetailsEl.text = productSettings.iOtherDetails

    def _apply_temporal_extent(self, productSettings, timeslot):
        parentEl = self.tree.xpath('gmd:identificationInfo/*/gmd:extent/'\
                                   'gmd:EX_Extent/gmd:temporalElement/'\
                                   'gmd:EX_TemporalExtent/gmd:extent/'\
                                   'gml:TimePeriod', namespaces=self.ns)[0]
        descriptionEl = parentEl.xpath('gml:description', namespaces=self.ns)[0]
        descriptionEl.text = productSettings.temporal_extent
        nameEl = parentEl.xpath('gml:name', namespaces=self.ns)[0]
        nameEl.text = 'timeslot'
        beginEl = parentEl.xpath('gml:beginPosition', namespaces=self.ns)[0]
        theTimeslot = timeslot.strftime('%Y-%m-%dT%H:%M:%S')
        beginEl.text = theTimeslot
        endEl = parentEl.xpath('gml:endPosition', namespaces=self.ns)[0]
        endEl.text = theTimeslot
        
    # FIXME
    # - test this method
    def insert_csw(self, csw_url, login_url, logout_url, username,
                    password, filePaths=None):
        '''
        Insert metadata records in the catalogue server.

        This code is adapted from
        http://trac.osgeo.org/geonetwork/wiki/HowToDoCSWTransactionOperations#Python

        Inputs:
            
            csw_url - URL for the CSW entry point.

            login_url - URL for the CSW log in page.

            logout_url - URL for the CSW log out page.

            username - username for the catalogue server's insert operation.

            password - password for the user

            filePaths - A list of xml files with the metadata to insert in the
                catalogue. If None (the default), this instance's own tree
                will be used.
        '''

        headers_auth = {
            "Content-type": "application/x-www-form-urlencoded", 
            "Accept": "text/plain"
        }
        headers_xml = {
            "Content-type": "application/xml", 
            "Accept": "text/plain"
        }
        data = urllib.urlencode({"username": username, "password": password})
        logoutReq = urllib2.Request(logout_url) # first, always log out
        response = urllib2.urlopen(logoutReq)
        print response.read() # debug
        # send authentication request
        loginReq = urllib2.Request(login_url, data, headers_auth)
        response = urllib2.urlopen(loginReq)
        # a basic memory-only cookie jar instance
        cookies = cookielib.CookieJar()
        cookies.extract_cookies(response,loginReq)
        cookie_handler= urllib2.HTTPCookieProcessor(cookies)
        # a redirect handler
        redirect_handler= urllib2.HTTPRedirectHandler()
        # save cookie and redirect handler for future HTTP Posts
        opener = urllib2.build_opener(redirect_handler,cookie_handler)
        if filePaths is not None:
            # Process up to 30 files in each transaction in order to
            # prevent out of memory errors on the CSW server
            requestList = []
            for index, fp in enumerate(filePaths):
                requestList.append(fp)
                if (index + 1) % 30 == 0:
                    self._execute_csw_insert_request(requestList, csw_url, 
                                                     headers_xml, opener)
                    requestList = []
            else:
                self._execute_csw_insert_request(requestList, csw_url, 
                                                 headers_xml, opener)
        else:
            self._execute_csw_insert_request([self.tree], csw_url, 
                                             headers_xml, opener)
        logoutReq = urllib2.Request(logout_url) # Last, always log out
        response = opener.open(logoutReq)
        print response.read() # debug

    def _execute_csw_insert_request(self, fileList, url, headers, opener):
        theRequest = '<?xml version="1.0" encoding="UTF-8"?>'\
            '<csw:Transaction service="CSW" version="2.0.2" '\
            'xmlns:csw="http://www.opengis.net/cat/csw/2.0.2">'
        for filePath in fileList:
            theXML = etree.parse(filePath)
            theRequest += '<csw:Insert>' + etree.tostring(theXML) + '</csw:Insert>'
        theRequest += '</csw:Transaction>'
        try:
            insertReq = urllib2.Request(url, theRequest, headers)
            response = opener.open(insertReq)
            # CSW response
            xml_response = response.read()
            print('insertReq response:')
            print xml_response  # debug
            print('------')
        except urllib2.HTTPError, error:
            print(error.read())
