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
                'fileIdentifier' : self.tree.xpath(
                    'gmd:fileIdentifier/gco:CharacterString', 
                    namespaces=self.ns), # the XML uuid
                'uuid' : self.tree.xpath(
                    'gmd:identificationInfo/gmd:MD_DataIdentification',
                    namespaces=self.ns), # the XML uuid
                'idCode' : self.tree.xpath(
                    'gmd:identificationInfo/*/gmd:citation/*/gmd:identifier/'\
                            '*/gmd:code/gco:CharacterString', 
                    namespaces=self.ns),# the XML uuid
                'hierarchyLevel' : self.tree.xpath(
                    'gmd:hierarchyLevel/gmd:MD_ScopeCode', 
                    namespaces=self.ns),
                'hierarchyLevelName' : self.tree.xpath(
                    'gmd:hierarchyLevelName/gco:CharacterString',
                    namespaces=self.ns),
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
                    namespaces=self.ns),
                'eastLongitude' : self.tree.xpath(
                    'gmd:identificationInfo/*/gmd:extent/*/*/*/'\
                            'gmd:eastBoundLongitude/gco:Decimal',
                    namespaces=self.ns),
                'southLatitude' : self.tree.xpath(
                    'gmd:identificationInfo/*/gmd:extent/*/*/*/'\
                            'gmd:southBoundLatitude/gco:Decimal',
                    namespaces=self.ns),
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

    # use lxml's ability to output directly to an url
    def send_to_csw(self):
        raise NotImplementedError
