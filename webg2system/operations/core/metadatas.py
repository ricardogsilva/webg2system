#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
A module for implementing metadata related functionality for the Geoland-2 
processing system.
"""

from lxml import etree

class MetadataGenerator(object):

    def __init__(self, template):
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
                'parentIdentifier' : self.tree.xpath('gmd:parentIdentifier'\
                    '/gco:CharacterString', namespaces=self.ns)[0],
                #06 - hierarchyLevel
                'hierarchyLevel' : self.tree.xpath(
                    'gmd:hierarchyLevel/gmd:MD_ScopeCode', 
                    namespaces=self.ns),
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
                'cellGeometry' : self.tree.xpath('gmd:spatialRepresentation'\
                    'Info/*/gmd:cellGeometry/gmd:MD_CellGeometryCode', 
                    namespaces=self.ns)[0],
                #12 - referenceSystemInfo
                #13 - referenceSystemInfo
                #14 - identificationInfo
                #15 - contentInfo
                #16 - contentInfo
                #17 - contentInfo
                #18 - contentInfo
                #19 - contentInfo
                #20 - contentInfo
                #21 - distributionInfo
                #22 - dataQualityInfo
                #23 - metadataMaintenance
                'Resource title' : self.tree.xpath('gmd:identificationInfo[1]'\
                        '/*/gmd:citation/gmd:CI_Citation/gmd:title'\
                        '/gco:CharacterString', namespaces=self.ns)[0],
                'Resource abstract' : self.tree.xpath('gmd:identificationInfo[1]'\
                        '/*/gmd:abstract/gco:CharacterString', namespaces=self.ns)[0],
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

    # use owslib
    def send_to_csw(self):
        raise NotImplementedError
