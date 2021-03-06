#!/usr/bin/env python
#-*- coding: utf-8 -*-

'''
A testing of geonetwork's xml services.
'''

import re
from uuid import uuid1
import datetime as dt

import requests
from lxml import etree

class GeonetworkManager(object):

    _username = ''
    _password = ''
    _csw_suffix = 'srv/eng/csw'
    _csw_publication_suffix = 'srv/eng/csw-publication'
    _headers = {'content-type' : 'application/xml'}
    _security_queries = {
        'logout' : {
            'url_suffix' : 'j_spring_security_logout',
        },
        'login' : {
            'url_suffix' : 'j_spring_security_check',
            'data' : {'username' : None, 'password' : None},
        },
    }

    def __init__(self, base_url='', username='', password=''):
        self.csw_manager = CSWManager()
        self._session = requests.Session()
        self.base_url = base_url
        self.username = username
        self.password = password

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, new_name):
        self._username = new_name
        self._security_queries['login']['data']['username'] = new_name

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, new_password):
        self._password = new_password
        self._security_queries['login']['data']['password'] = new_password

    def _login(self):
        query = self._security_queries['login']
        url = '/'.join((self.base_url, query['url_suffix']))
        response = self._session.post(url, data=query['data'])
        return response

    def _logout(self):
        query = self._security_queries['logout']
        url = '/'.join((self.base_url, query['url_suffix']))
        response = self._session.post(url)
        return response

    def close(self):
        self._session.close()

    def parse_response(self, response):
        encoding_pattern = r' encoding="(?P<encoding>[\w-]*)"'
        encoding_obj = re.search(encoding_pattern, response.text)
        encoding = None
        if encoding_obj is not None:
            encoding = encoding_obj.groupdict()['encoding']
        stripped_text = re.sub(encoding_pattern, '', response.text)
        tree = etree.fromstring(stripped_text)
        return encoding, tree

    def get_capabilities(self):
        request = self.csw_manager.build_get_capabilities_request()
        url = '/'.join((self.base_url, self._csw_suffix))
        response = self._session.post(url, data=request, headers=self._headers)
        encoding, tree = self.parse_response(response)
        return response, encoding, tree

    def get_records_cql(self, cql, result_type, start_position=1,
                        max_records=10):
        request = self.csw_manager.build_get_records_CQL_request(
            cql,
            result_type,
            start_position,
            max_records
        )
        url = '/'.join((self.base_url, self._csw_suffix))
        response = self._session.post(url, data=request, headers=self._headers)
        encoding, tree = self.parse_response(response)
        return response, encoding, tree

    def get_record_by_id(self, id_):
        request = self.csw_manager.build_get_record_by_id_request(id_)
        url = '/'.join((self.base_url, self._csw_suffix))
        response = self._session.post(url, data=request, headers=self._headers)
        encoding, tree = self.parse_response(response)
        return response, encoding, tree

    def get_record_by_title(self, title):
        '''
        Inputs:

            title - A wildcard for use when searching the title of the
                metadata record to find. Wildcards use '%'.

        Returns an etree.Element with the metadata records in the IsoRecord
        output schema or None, if the record is not found.
        '''

        cql_text = "AnyText like '%s'" % title
        response, encoding, tree = self.get_records_cql(cql_text, 'results')
        search_result = tree.xpath('csw:SearchResults',
                                   namespaces=self.csw_manager.NAMESPACES)[0]
        matches = int(search_result.get('numberOfRecordsMatched', 0))
        record = None
        if matches > 0:
            if matches > 1:
                print('Warning: found multiple records. Was expecting to ' \
                      'find only one')
            ns = self.csw_manager.NAMESPACES
            ns.update(self.csw_manager.ISO_NAMESPACES)
            record = tree.xpath('csw:SearchResults/gmd:MD_Metadata[1]',
                                namespaces=ns)[0]
        return record

    def insert_records(self, metadata_files):
        '''
        Inputs:

            metadata_files - a list of xml files with the individual metadata
                for each record.

        Returns a boolean indicating if all the metadata files were inserted
        in the catalog.
        '''

        logout_response = self._logout()
        login_response = self._login()
        metadatas = []
        for file_path in metadata_files:
            try:
                tree = etree.parse(file_path)
                metadatas.append(tree.getroot())
            except IOError as err:
                print(err)
        request = self.csw_manager.build_insert_records_request(metadatas)
        url = '/'.join((self.base_url, self._csw_publication_suffix))
        response = self._session.post(url, data=request, headers=self._headers)
        encoding, tree = self.parse_response(response)
        summary = self._parse_transaction_summary(tree)
        result = False
        if summary['inserted'] == len(metadata_files):
            result = True
        return result

    def delete_records(self, uuids):
        '''
        Inputs:

            uuids - A list of UUIDs for each of the metadata records to
                delete from the catalogue.

        Returns a boolean indicating if all the requested records have been
        deleted from the catalog.
        '''

        logout_response = self._logout()
        login_response = self._login()
        cql_texts = ["AnyText like '%s'" % id_ for id_ in uuids]
        request = self.csw_manager.build_delete_records_request(cql_texts)
        url = '/'.join((self.base_url, self._csw_publication_suffix))
        response = self._session.post(url, data=request, headers=self._headers)
        encoding, tree = self.parse_response(response)
        summary = self._parse_transaction_summary(tree)
        result = False
        if summary['deleted'] == len(uuids):
            result = True
        return result

    def _parse_transaction_summary(self, tree):
        '''
        Inputs:

            tree - The response tree
        '''

        result = {
            'inserted' : int(tree.xpath('csw:TransactionSummary/csw:' \
                             'totalInserted/text()',
                             namespaces=self.csw_manager.NAMESPACES)[0]),
            'updated' : int(tree.xpath('csw:TransactionSummary/csw:' \
                            'totalUpdated/text()',
                            namespaces=self.csw_manager.NAMESPACES)[0]),
            'deleted' : int(tree.xpath('csw:TransactionSummary/csw:' \
                            'totalDeleted/text()',
                            namespaces=self.csw_manager.NAMESPACES)[0])
        }
        return result



# TODO - Decode and reencode all the strings
class MetadataRecord(object):

    NS = {
        'gmd' : 'http://www.isotc211.org/2005/gmd',
        'gmx' : 'http://www.isotc211.org/2005/gmx',
        'gco' : 'http://www.isotc211.org/2005/gco',
        'gsr' : 'http://www.isotc211.org/2005/gsr',
        'gss' : 'http://www.isotc211.org/2005/gss',
        'gts' : 'http://www.isotc211.org/2005/gts',
        'gml' : 'http://www.opengis.net/gml',
        'xsi' : 'http://www.w3.org/2001/XMLSchema-instance',
    }

    uuid = None
    id_ = None
    encoding = 'utf8'
    language_code = u'eng'
    parent_id = None
    ci_responsible_party = None
    timeslot = None
    metadata_standard_name = 'ISO19115'
    metadata_standard_version = '2003/Cor.1:2006'
    md_georectified = None
    md_reference_system = None
    md_data_identification = None

    def __init__(self):
        '''
        This method should take the metadata settings from Django as input
        '''

        self.uuid = str(uuid1())
        self.ci_responsible_party = CI_ResponsibleParty()
        self.md_georectified = MD_Georectified()
        self.md_reference_system = MD_ReferenceSystem()
        self.md_data_identification = MD_DataIdentification()

    @staticmethod
    def from_xml(xml_element, encoding='utf-8'):
        record = MetadataRecord()
        record.NS = xml_element.nsmap
        record.uuid = xml_element.xpath(
            'gmd:fileIdentifier/gco:CharacterString',
            namespaces=record.NS)[0].text
        return record

    def serialize(self, format='xml'):
        result = None
        if format == 'xml':
            result = self._serialize_to_xml()
        return result

    def _serialize_to_xml(self):
        root = etree.Element('{%s}MD_Metadata' % self.NS['gmd'],
                             nsmap=self.NS)
        self._serialize_file_identifier(root)
        self._serialize_language(root)
        self._serialize_character_set(root)
        self._serialize_parent_identifier(root)
        self._serialize_hierarchy_level(root)
        self._serialize_contact(root)
        self._serialize_datestamp(root)
        self._serialize_metadata_standard_name(root)
        self._serialize_metadata_standard_version(root)
        self._serialize_spatial_representation_info(root)
        self._serialize_reference_system_info(root)
        self._serialize_identification_info(root)
        tree = etree.ElementTree(root)
        record = etree.tostring(tree, xml_declaration=True,
                                encoding=self.encoding, pretty_print=True)
        return record

    def _serialize_file_identifier(self, root_node):
        file_id_el = etree.Element('{%s}fileIdentifier' % self.NS['gmd'])
        self._gco_character_string(file_id_el, self.uuid)
        root_node.insert(0, file_id_el)

    def _serialize_language(self, root_node):
        codelist_uri = 'http://standards.iso.org/ittf/PubliclyAvailable' \
                       'Standards/ISO_19139_Schemas/resources/Codelist/' \
                       'ML_gmxCodelists.xml#LanguageCode'
        lang_el = etree.Element('Language')
        code_el = etree.SubElement(lang_el, 'LanguageCode',
                                   codelist=codelist_uri,
                                   codelistValue=self.language_code)
        code_el.text = unicode(self.language_code)
        root_node.insert(1, lang_el)

    def _serialize_character_set(self, root_node):
        codelist_uri = 'http://standards.iso.org/ittf/PubliclyAvailable' \
                       'Standards/ISO_19139_Schemas/resources/Codelist/' \
                       'ML_gmxCodelists.xml#MD_CharacterSetCode'
        char_set_el = etree.Element('{%s}characterSet' % self.NS['gmd'])
        code_el = etree.SubElement(char_set_el, '{%s}MD_CharacterSetCode' % \
                                   self.NS['gmd'], codeList=codelist_uri,
                                   codeListValue=self.encoding)
        code_el.text = unicode(self.encoding)
        root_node.insert(2, char_set_el)

    def _serialize_parent_identifier(self, root_node):
        parent_id_el = etree.Element('{%s}parentIdentifier' % self.NS['gmd'])
        self._gco_character_string(parent_id_el, self.parent_id)
        root_node.insert(3, parent_id_el)

    def _serialize_hierarchy_level(self, root_node):
        codelist_uri = 'http://standards.iso.org/ittf/PubliclyAvailable' \
                       'Standards/ISO_19139_Schemas/resources/Codelist/' \
                       'ML_gmxCodelists.xml#MD_ScopeCode'
        hierarchy_el = etree.Element('{%s}hierarchyLevel' % self.NS['gmd'])
        scope_code_el = etree.SubElement(hierarchy_el, '{%s}MD_ScopeCode' % \
                                         self.NS['gmd'], codeList=codelist_uri,
                                         codelistValue='dataset')
        scope_code_el.text = u'dataset'
        root_node.insert(4, hierarchy_el)

    def _serialize_contact(self, root_node):
        contact_el = etree.SubElement(root_node, '{%s}contact' % \
                                      self.NS['gmd'])
        contact_el.append(self.ci_responsible_party.serialize_xml())

    def _serialize_datestamp(self, root_node):
        datestamp_el = etree.SubElement(root_node, '{%s}dateStamp' % \
                                      self.NS['gmd'])
        the_date = self.timeslot.strftime('%Y-%m-%d')
        self._gco_date(datestamp_el, the_date)

    def _serialize_metadata_standard_name(self, root_node):
        md_standard_el = etree.SubElement(root_node,
                                          '{%s}metadataStandardName' % \
                                          self.NS['gmd'])
        md_standard_el.text = unicode(self.metadata_standard_name)

    def _serialize_metadata_standard_version(self, root_node):
        md_standard_el = etree.SubElement(root_node,
                                          '{%s}metadataStandardName' % \
                                          self.NS['gmd'])
        md_standard_el.text = unicode(self.metadata_standard_version)

    def _serialize_spatial_representation_info(self, root_node):
        spatial_rep_el = etree.SubElement(root_node,
                                          '{%s}spatialRepresentationInfo' % \
                                          self.NS['gmd'])
        spatial_rep_el.append(self.md_georectified.serialize_xml())

    def _serialize_reference_system_info(self, root_node):
        ref_system_el = etree.SubElement(root_node,
                                         '{%s}referenceSystemInfo' % \
                                         self.NS['gmd'])
        ref_system_el.append(self.md_reference_system.serialize_xml())

    def _serialize_identification_info(self, root_node):
        identification_el = etree.SubElement(root_node,
                                             '{%s}identificationInfo' % \
                                             self.NS['gmd'])
        identification_el.append(self.md_data_identification.serialize_xml())

    def _gco_character_string(self, parent_el, text):
        cs_el = etree.SubElement(parent_el,
                                 '{%s}CharacterString' % \
                                 self.NS['gco'])
        cs_el.text = unicode(text)

    def _gco_date(self, parent_el, text):
        date_el = etree.SubElement(parent_el,
                                   '{%s}Date' % self.NS['gco'])
        date_el.text = unicode(text)

    def _gco_integer(self, parent_el, text):
        integer_el = etree.SubElement(parent_el,
                                      '{%s}Integer' % self.NS['gco'])
        integer_el.text = unicode(text)

    def _gco_angle(self, parent_el, text, unit):
        angle_el = etree.SubElement(parent_el,
                                    '{%s}Angle' % self.NS['gco'],
                                    uom=unit)
        angle_el.text = unicode(text)

    def _gco_boolean(self, parent_el, value):
        angle_el = etree.SubElement(parent_el,
                                    '{%s}Boolean' % self.NS['gco'])
        angle_el.text = unicode(value)


# DONE
class CI_ResponsibleParty(MetadataRecord):

    def __init__(self, organization_name='', ci_contact=None, role='',
                 position_name=None):
        self.organization_name = organization_name
        self.ci_contact = ci_contact
        self.role = role
        self.position_name = position_name

    def _serialize_to_xml(self):
        ns = self.NS.copy()
        ns[None] = ns['gmd']
        ci_resp_party_el = etree.Element('{%s}CI_ResponsibleParty' % \
                                         ns['gmd'], nsmap=ns)
        org_name_el = etree.SubElement(ci_resp_party_el,
                                       '{%s}organisationName' % \
                                       ns['gmd'])
        self._gco_character_string(org_name_el, self.organization_name)
        if self.position_name is not None:
            pos_name_el = etree.SubElement(ci_resp_party_el,
                                           '{%s}positionName' % \
                                           ns['gmd'])
            self._gco_character_string(pos_name_el, self.position_name)
        contact_info_el = etree.SubElement(ci_resp_party_el,
                                           '{%s}contactInfo' % ns['gmd'])
        contact_info_el.append(self.ci_contact._serialize_to_xml())
        codelist_uri = 'http://standards.iso.org/ittf/PubliclyAvailable' \
                       'Standards/ISO_19139_Schemas/resources/Codelist/' \
                       'ML_gmxCodelists.xml#CI_RoleCode'
        role_el = etree.SubElement(ci_resp_party_el,
                                   '{%s}role' % ns['gmd'],
                                   codeList=codelist_uri,
                                   codeListValue=self.role)
        role_el.text = unicode(self.role, self.encoding)
        return ci_resp_party_el

    @staticmethod
    def from_xml(xml_element, encoding='utf-8'):
        c = CI_ResponsibleParty()
        org_name = xml_element.xpath('gmd:organisationName/gco:'
                                     'CharacterString/text()',
                                     namespaces=c.NS)[0]
        position_name_list = xml_element.xpath('gmd:positionName/gco:'
                                               'CharacterString/text()',
                                               namespaces=c.NS)
        if any(position_name_list):
            c.position_name = position_name_list[0]
        ci_contact_el = xml_element.xpath('gmd:contactInfo/gmd:CI_Contact',
                                          namespaces=c.NS)[0]
        c.role = xml_element.xpath('gmd:role/gmd:CI_RoleCode/text()',
                                   namespaces=c.NS)[0]
        c.organization_name = org_name
        c.ci_contact = CI_Contact.from_xml(ci_contact_el)
        return c


#DONE, needs testing
class CI_Citation(MetadataRecord):

    title = ''
    ci_date = None
    md_identifier = None
    other_citation_details = ''

    def __init__(self, title='', ci_date=None, md_identifier=None,
                 other_citation_details=''):
        self.title = title
        self.ci_date = ci_date
        self.md_identifier = md_identifier
        self.other_citation_details = other_citation_details
        self.edition = Edition('v1', '2013-06-20')

    def serialize_xml(self):
        ns = self.NS.copy()
        ns[None] = ns['gmd']
        ci_citation_el = etree.Element('{%s}CI_Citation' % ns['gmd'], nsmap=ns)
        title_el = etree.SubElement(ci_citation_el, '{%s}title' % \
                                    ns['gmd'])
        self._gco_character_string(title_el, self.title)
        date_el = etree.SubElement(ci_citation_el, '{%s}date' % \
                                   ns['gmd'])
        date_el.append(self.ci_date.serialize_xml())
        self.edition.serialize_xml(ci_citation_el)
        if self.md_identifier is not None:
            identifier_el = etree.SubElement(ci_citation_el, '{%s}identifier' \
                                             % ns['gmd'])
            identifier_el.append(self.md_identifier.serialize_xml())
        if self.other_citation_details != '':
            other_citation_details_el = etree.SubElement(
                ci_citation_el,
                '{%s}otherCitationDetails' % ns['gmd']
            )
            self._gco_character_string(other_citation_details_el,
                                       self.otherCitationDetails)
        return ci_citation_el

    @staticmethod
    def from_xml(xml_element, encoding='utf-8'):
        c = CI_Citation()
        c.title = xml_element.xpath('gmd:title/gco:CharacterString/text()',
                                    namespaces=c.NS)[0]
        ci_date_el = xml_element.xpath('gmd:date/gmd:CI_Date',
                                       namespaces=c.NS)[0]
        c.ci_date = CI_Date.from_xml(ci_date_el)
        md_identifier_el = xml_element.xpath('gmd:identifier/gmd:'
                                             'MD_Identifier',
                                             namespaces=c.NS)[0]
        c.md_identifier = MD_Identifier.from_xml(md_identifier_el)
        c.other_citation_details = xml_element.xpath('gmd:otherCitation'
                                                     'Details/gco:Character'
                                                     'String/text()',
                                                     namespaces=c.NS)[0]
        return c


#DONE
class CI_Date(MetadataRecord):

    date = None
    date_type_code = ''

    def __init__(self, date=None, date_type_code=''):
        self.date = date
        self.date_type_code = date_type_code

    def _serialize_to_xml(self):
        ns = self.NS.copy()
        ns[None] = ns['gmd']
        ci_date_el = etree.Element('{%s}CI_Date' % ns['gmd'], nsmap=ns)
        date_el = etree.SubElement(ci_date_el, '{%s}date' % \
                                   ns['gmd'])
        self._gco_date(date_el, self.date.strftime('%Y-%m-%d'))
        date_type_el = etree.SubElement(ci_date_el, '{%s}dateType' % \
                                        ns['gmd'])
        codelist_uri = 'http://standards.iso.org/ittf/PubliclyAvailable' \
                       'Standards/ISO_19139_Schemas/resources/Codelist/' \
                       'ML_gmxCodelists.xml#CI_DateTypeCode'
        ci_datetype_code_el = etree.SubElement(
            date_type_el,
            '{%s}CI_DateTypeCode' % ns['gmd'],
            codeList=codelist_uri,
            codeListValue=self.date_type_code
        )
        ci_datetype_code_el.text = unicode(self.date_type_code)
        return ci_date_el

    @staticmethod
    def from_xml(xml_element, encoding='utf-8'):
        ci_date = CI_Date()
        date = xml_element.xpath('gmd:date/gco:Date/text()',
                                 namespaces=ci_date.NS)[0]
        date_type_code = xml_element.xpath('gmd:dateType/gmd:CI_DateTypeCode/'
                                           'text()', namespaces=ci_date.NS)[0]
        ci_date.date = dt.datetime.strptime(date, '%Y-%m-%d')
        ci_date.date_type_code = date_type_code
        return ci_date


#DONE
class CI_Contact(MetadataRecord):

    def __init__(self, ci_address=None, ci_online_resource=None,
                 hours_of_service='', contact_instructions=''):
        self.ci_address = ci_address
        self.ci_online_resource = ci_online_resource
        self.hours_of_service = hours_of_service
        self.contact_instructions = contact_instructions

    def _serialize_to_xml(self):
        ns = self.NS.copy()
        ns[None] = ns['gmd']
        ci_contact_el = etree.Element('{%s}CI_Contact' % ns['gmd'], nsmap=ns)
        address_el = etree.SubElement(ci_contact_el, '{%s}address' % \
                                      ns['gmd'])
        address_el.append(self.ci_address._serialize_to_xml())
        online_resource_el = etree.SubElement(ci_contact_el,
                                              '{%s}onlineResource' % \
                                              ns['gmd'])
        online_resource_el.append(self.ci_online_resource._serialize_to_xml())
        hours_service_el = etree.SubElement(ci_contact_el,
                                            '{%s}hoursOfService' % \
                                            ns['gmd'])
        self._gco_character_string(hours_service_el, self.hours_of_service)
        contact_instr_el = etree.SubElement(ci_contact_el,
                                            '{%s}contactInstructions' % \
                                            ns['gmd'])
        self._gco_character_string(contact_instr_el, self.contact_instructions)
        return ci_contact_el

    @staticmethod
    def from_xml(xml_element, encoding='utf-8'):
        c = CI_Contact()
        ci_address_el = xml_element.xpath('gmd:address/gmd:CI_Address',
                                          namespaces=c.NS)[0]
        ci_online_resource_el = xml_element.xpath('gmd:onlineResource/'
                                                  'gmd:CI_OnlineResource',
                                                  namespaces=c.NS)[0]
        c.hours_of_service = xml_element.xpath('gmd:hoursOfService/gco:'
                                               'CharacterString/text()',
                                               namespaces=c.NS)[0]
        c.contact_instructions = xml_element.xpath('gmd:contactInstructions/gc'
                                                   'o:CharacterString/text()',
                                                   namespaces=c.NS)[0]
        c.ci_address = CI_Address.from_xml(ci_address_el)
        c.ci_online_resource = CI_OnlineResource.from_xml(ci_online_resource_el)
        return c


#DONE
class CI_OnlineResource(MetadataRecord):

    def __init__(self, name='', description='', function='',
                 url='', protocol='HTTP'):
        self.name = name
        self.description = description
        self.function = function
        self.url = url
        self.protocol = protocol

    def _serialize_to_xml(self):
        ns = self.NS.copy()
        ns[None] = ns['gmd']
        ci_online_res_el = etree.Element('{%s}CI_OnlineResource' % \
                                         ns['gmd'], nsmap=ns)
        linkage_el = etree.SubElement(ci_online_res_el, '{%s}linkage' % \
                                      ns['gmd'])
        url_el = etree.SubElement(linkage_el, '{%s}URL' % ns['gmd'])
        url_el.text = unicode(self.url)
        protocol_el = etree.SubElement(ci_online_res_el, '{%s}protocol' % \
                                      ns['gmd'])
        self._gco_character_string(protocol_el, self.protocol)
        name_el = etree.SubElement(ci_online_res_el, '{%s}name' % \
                                      ns['gmd'])
        self._gco_character_string(name_el, self.name)
        description_el = etree.SubElement(ci_online_res_el,
                                          '{%s}description' % ns['gmd'])
        self._gco_character_string(description_el,
                                   self.description)
        codelist_uri = 'http://standards.iso.org/ittf/PubliclyAvailable' \
                       'Standards/ISO_19139_Schemas/resources/Codelist/' \
                       'ML_gmxCodelists.xml#CI_OnLineFunctionCode'
        function_el = etree.SubElement(ci_online_res_el,
                                       '{%s}function' % ns['gmd'],
                                       codeList=codelist_uri,
                                       codeListValue=self.function)
        function_el.text = unicode(self.function, self.encoding)
        return ci_online_res_el

    @staticmethod
    def from_xml(xml_element, encoding='utf-8'):
        c = CI_OnlineResource()
        c.name = xml_element.xpath('gmd:name/gco:CharacterString/text()',
                                   namespaces=c.NS)[0]
        c.description = xml_element.xpath('gmd:description/gco:CharacterString/'
                                          'text()', 
                                          namespaces=c.NS)[0]
        c.function = xml_element.xpath('gmd:function/gmd:CI_OnLineFunctionCode'
                                       '/text()',
                                       namespaces=c.NS)[0]
        c.url = xml_element.xpath('gmd:linkage/gmd:URL/text()',
                                  namespaces=c.NS)[0]
        c.protocol = xml_element.xpath('gmd:protocol/gco:CharacterString/'
                                       'text()',
                                       namespaces=c.NS)[0]
        return c


#DONE
class CI_Address(MetadataRecord):

    def __init__(self, delivery_point='', city='', postal_code='',
                 country='', email=''):
        self.delivery_point = delivery_point
        self.city = city
        self.postal_code = postal_code
        self.country = country
        self.email = email

    def _serialize_to_xml(self):
        ns = self.NS.copy()
        ns[None] = ns['gmd']
        ci_address_el = etree.Element('{%s}CI_Address' % ns['gmd'], nsmap=ns)
        delivery_pt_el = etree.SubElement(ci_address_el, '{%s}deliveryPoint' \
                                          % ns['gmd'])
        self._gco_character_string(delivery_pt_el, self.delivery_point)
        city_el = etree.SubElement(ci_address_el, '{%s}city' % ns['gmd'])
        self._gco_character_string(city_el, self.city)
        postal_code_el = etree.SubElement(ci_address_el, '{%s}postalCode' \
                                          % ns['gmd'])
        self._gco_character_string(postal_code_el, self.postal_code)
        country_el = etree.SubElement(ci_address_el, '{%s}country' \
                                          % ns['gmd'])
        self._gco_character_string(country_el, self.country)
        email_el = etree.SubElement(ci_address_el,
                                    '{%s}electronicMailAddress' % \
                                    ns['gmd'])
        self._gco_character_string(email_el, self.email)
        return ci_address_el

    @staticmethod
    def from_xml(xml_element, encoding='utf-8'):
        ci_address = CI_Address()
        delivery_point = xml_element.xpath('gmd:deliveryPoint/gco:'
                                           'CharacterString/text()',
                                           namespaces=ci_address.NS)[0]
        city = xml_element.xpath('gmd:city/gco:CharacterString/text()',
                                 namespaces=ci_address.NS)[0]
        postal_code = xml_element.xpath('gmd:postalCode/gco:CharacterString/'
                                        'text()', namespaces=ci_address.NS)[0]
        country = xml_element.xpath('gmd:country/gco:CharacterString/text()',
                                    namespaces=ci_address.NS)[0]
        email = xml_element.xpath('gmd:electronicMailAddress/gco:'
                                  'CharacterString/text()',
                                  namespaces=ci_address.NS)[0]
        ci_address.delivery_point = delivery_point
        ci_address.city = city
        ci_address.postal_code = postal_code
        ci_address.country = country
        ci_address.email = email
        return ci_address


class CI_Role(MetadataRecord):

    def __init__(self, role_code=''):
        self.role_code = role_code

    def serialize_xml(self):
        codelist_uri = 'http://standards.iso.org/ittf/PubliclyAvailable' \
                       'Standards/ISO_19139_Schemas/resources/Codelist/' \
                       'ML_gmxCodelists.xml#CI_RoleCode'
        ci_role_code_el = etree.Element('{%s}CI_RoleCode' % self.NS['gmd'],
                                        codeList=codelist_uri,
                                        codeListValue=self.role_code)
        ci_role_code_el.text = unicode(self.role_code)
        return ci_role_code_el


class MD_Georectified(MetadataRecord):

    dimensions = []
    cell_geometry = 'area'
    transformation_parameters = False
    checkpoint = None
    pixel_orientation = 'center'

    def __init__(self, dimensions=[], cell_geometry='area',
                 transformation_parameters=False,
                 checkpoint=None, pixel_orientation='center'):
        self.dimensions = dimensions
        self.cell_geometry = cell_geometry
        self.transformation_parameters = transformation_parameters
        self.checkpoint = checkpoint
        self.pixel_orientation = pixel_orientation

    def add_dimension(self, name, size, resolution, resolution_unit):
        dim = MD_Dimension(name, size, resolution, resolution_unit)
        self.dimensions.append(dim)

    def serialize_xml(self):
        md_georectifed_el = etree.Element('{%s}MD_Georectified' % \
                                          self.NS['gmd'])
        num_dimensions_el = etree.SubElement(md_georectifed_el,
                                             '{%s}numberOfDimensions' % \
                                             self.NS['gmd'])
        self._gco_integer(num_dimensions_el, len(self.dimensions))
        for dim in self.dimensions:
            axis_dim_props_el = etree.SubElement(md_georectifed_el,
                                                 '{%s}axisDimensionProperties'\
                                                 % self.NS['gmd'])
            axis_dim_props_el.append(dim.serialize_xml())
        cell_geom_el = etree.SubElement(md_georectifed_el,
                                        '{%s}cellGeometry' % self.NS['gmd'])
        codelist_uri = 'http://www.isotc211.org/2005/resources/codelist/' \
                       'gmxCodelists.xml#MD_CellGeometryCode'
        md_cell_geom_code_el = etree.SubElement(cell_geom_el,
                                                '{%s}MD_CellGeometryCode' % \
                                                self.NS['gmd'],
                                                codeList=codelist_uri,
                                                codeListValue=self.cell_geometry)
        md_cell_geom_code_el.text = self.cell_geometry
        transf_params_el = etree.SubElement(md_georectifed_el,
                                            '{%s}transformationParameter' \
                                            'Availability' % self.NS['gmd'])
        self._gco_boolean(transf_params_el, self.transformation_parameters)
        self.checkpoint.serialize_xml(md_georectifed_el)
        point_in_pixel_el = etree.SubElement(md_georectifed_el,
                                             '{%s}pointInPixel' % \
                                             self.NS['gmd'])
        pixel_orientation_el = etree.SubElement(point_in_pixel_el,
                                             '{%s}MD_PixelOrientationCode' % \
                                             self.NS['gmd'])
        pixel_orientation_el.text = unicode(self.pixel_orientation)
        return md_georectifed_el


class MD_ReferenceSystem(MetadataRecord):

    epsg_code = '4326'

    def __init__(self, epsg_code=4326):
        self.epsg_code = epsg_code

    def serialize_xml(self):
        md_ref_system_el = etree.Element('{%s}MD_ReferenceSystem' % \
                                         self.NS['gmd'])
        ref_system_id_el = etree.SubElement(md_ref_system_el,
                                            '{%s}referenceSystemIdentifier' % \
                                            self.NS['gmd'])
        rs_identifier_el = etree.SubElement(ref_system_id_el,
                                            '{%s}RS_Identifier' % \
                                            self.NS['gmd'])
        code_el = etree.SubElement(rs_identifier_el, '{%s}code' % \
                                   self.NS['gmd'])
        self._gco_character_string(code_el, 'EPSG:%s' % self.epsg_code)
        codespace_el = etree.SubElement(rs_identifier_el, '{%s}codeSpace' % \
                                        self.NS['gmd'])
        self._gco_character_string(codespace_el, 'EPSG Geodetic Parameter ' \
                                   'Dataset')
        return md_ref_system_el


class MD_DataIdentification(MetadataRecord):

    def __init__(self, ci_citation=None, abstract='', purpose='', credit='',
                 status='', ci_responsible_parties=[], 
                 md_maintenance_information=None,
                 md_browse_graphic=None, md_format=None): # not done
        self.ci_citation = ci_citation
        self.abstract = abstract
        self.purpose = purpose
        self.credit = credit
        self.status = status
        self.ci_responsible_parties = ci_responsible_parties
        self.md_maintenance_information = md_maintenance_information

    def serialize_xml(self):
        ns = self.NS.copy()
        ns[None] = ns['gmd']
        md_data_id_el = etree.Element('{%s}MD_DataIdentification' % \
                                      ns['gmd'], nsmap=ns)
        citation_el = etree.SubElement(md_data_id_el, '{%s}citation' % \
                                       ns['gmd'])
        citation_el.append(self.ci_citation.serialize_xml())
        abstract_el = etree.SubElement(md_data_id_el, '{%s}abstract' % \
                                       ns['gmd'])
        self._gco_character_string(abstract_el, self.abstract)
        purpose_el = etree.SubElement(md_data_id_el, '{%s}purpose' % \
                                       ns['gmd'])
        self._gco_character_string(purpose_el, self.purpose)
        credit_el = etree.SubElement(md_data_id_el, '{%s}credit' % \
                                     ns['gmd'])
        self._gco_character_string(credit_el, self.credit)
        status_el = etree.SubElement(md_data_id_el, '{%s}status' % \
                                     ns['gmd'])
        codelist_uri = 'http://standards.iso.org/ittf/PubliclyAvailable' \
                       'Standards/ISO_19139_Schemas/resources/Codelist/' \
                       'ML_gmxCodelists.xml#MD_ProgressCode'
        md_progress_code_el = etree.SubElement(
            status_el,
            '{%s}MD_ProgressCode' % ns['gmd'],
            codeList=codelist_uri,
            codeListValue=self.status)
        md_progress_code_el.text = unicode(self.status)
        for party in self.ci_responsible_parties:
            point_of_contact_el = etree.SubElement(md_data_id_el,
                                                   '{%s}pointOfContact' % \
                                                   ns['gmd'])
            point_of_contact_el.append(party._serialize_to_xml())
        resource_maintenance_el = etree.SubElement(md_data_id_el,
                                                   '{%s}resourceMaintenance' \
                                                   % ns['gmd'])
        resource_maintenance_el.append(
            self.md_maintenance_information._serialize_to_xml()
        )
        #graphic_overview_el
        #resource_format_el
        #for keyword in self.descriptive_keywords:
        #    descriptive_keyword_el
        #for constraint in self.resource_constraints:
        #    resource_constraint_el
        #for aggreg in self.aggregation_infos:
        #    aggregation_info_el
        #spatial_representation_type_el
        #spatial_resolution_el
        #language_el
        #character_set_el
        #for topic in self.topic_categories:
        #    topic_category_el
        #for extent in self.extents:
        #    extent_el
        #supplemental_information_el
        return md_data_id_el


#DONE, needs testing
class MD_Identifier(MetadataRecord):

    def __init__(self, code, ci_citation):
        self.code = code # UUID of the metadata record
        self.ci_citation = ci_citation

    def _serialize_to_xml(self):
        ns = self.NS.copy()
        ns[None] = ns['gmd']
        md_identifier_el = etree.Element('{%s}MD_Identifier' % ns['gmd'],
                                         nsmap=ns)
        authority_el = etree.SubElement(md_identifier_el, '{%s}authority' % \
                                       ns['gmd'])
        authority_el.append(self.ci_citation.serialize_xml())
        code_el = etree.SubElement(md_identifier_el, '{%s}code' % \
                                       ns['gmd'])
        self._gco_character_string(code_el, self.code)
        return md_identifier_el

    @staticmethod
    def from_xml(xml_element, encoding='utf-8'):
        m = MD_Identifier()
        ci_citation_el = xml_element.xpath('gmd:authority/gmd:CI_Citation',
                                           namespaces=m.NS)
        m.ci_citation = CI_Citation.from_xml(ci_citation_el)
        m.code = xml_element.xpath('gmd:code/gco:CharacterString/text()',
                                   namespaces=m.NS)
        return m


# Done, needs testing
class MD_Maintenance_Information(MetadataRecord):

    def __init__(self, frequency_code='', update_scope=''):
        self.frequency_code = frequency_code
        self.update_scope = update_scope

    def _serialize_to_xml(self):
        ns = self.NS.copy()
        ns[None] = ns['gmd']
        md_maintenance_info_el = etree.Element('{%s}MD_MaintenanceInformation'\
                                               % ns['gmd'], nsmap=ns)
        maint_and_update_freq_el = etree.SubElement(
            md_maintenance_info_el,
           '{%s}maintenanceAndUpdateFrequency' % ns['gmd']
        )
        codelist_uri = 'http://standards.iso.org/ittf/PubliclyAvailable' \
                       'Standards/ISO_19139_Schemas/resources/Codelist/' \
                       'ML_gmxCodelists.xml#MD_MaintenanceFrequencyCode'
        md_maint_freq_code = etree.SubElement(
            maint_and_update_freq_el,
            '{%s}MD_MaintenanceFrequencyCode' % ns['gmd'],
            codeList=codelist_uri,
            codeListValue=unicode(self.frequency_code)
        )
        md_maint_freq_code.text = unicode(self.frequency_code)
        update_scope_el = etree.SubElement(md_maintenance_info_el,
                                           '{%s}updateScope' % ns['gmd'])
        codelist_uri = 'http://standards.iso.org/ittf/PubliclyAvailable' \
                       'Standards/ISO_19139_Schemas/resources/Codelist/' \
                       'ML_gmxCodelists.xml#MD_ScopeCode'
        md_scope_code_el = etree.SubElement(
            update_scope_el,
            '{%s}MD_ScopeCode' % ns['gmd'],
            codeList=codelist_uri,
            codeListValue=unicode(self.update_scope)
        )
        md_scope_code_el.text = unicode(self.update_scope)
        return md_maintenance_info_el

    @staticmethod
    def from_xml(xml_element, encoding='utf-8'):
        m = MD_MaintenanceInformation()
        m.frequency_code = xml_element.xpath('gmd:maintenanceAndUpdate'
                                             'Frequency/gmd:MD_Maintenance'
                                             'FrequencyCode/text()',
                                             namespaces=m.NS)[0]
        m.update_scope = xml_element.xpath('gmd:updateScope/gmd:MD_ScopeCode/'
                                           'text()', namespaces=m.NS)
        return m


class CheckPoint(MetadataRecord):

    def __init__(self, description='', corner_point=None):
        self.description = description
        self.corner_point = corner_point

    def serialize_xml(self, parent_el):
        checkpoint_avail_el = etree.SubElement(parent_el,
                                            '{%s}checkPointAvailability' \
                                            % self.NS['gmd'])
        self._gco_boolean(checkpoint_avail_el, True)
        checkpoint_desc_el = etree.SubElement(md_georectifed_el,
                                            '{%s}checkPointDescription' \
                                            % self.NS['gmd'])
        self._gco_character_string(checkpoint_desc_el,
                                   self.checkpoint.description)
        corner_points_el = etree.SubElement(parent_el,
                                            '{%s]cornerPoints' % \
                                            self.NS['gmd'])
        corner_points_el.append(self.corner_point.serialize_xml())


class Edition(MetadataRecord):

    def __init__(self, name='v1', date='2013-06-20'):
        self.name = name
        self.date = date

    def serialize_xml(self, parent):
        edition_el = etree.SubElement(parent, '{%s}edition' % self.NS['gmd'])
        self._gco_character_string(edition_el, self.name)
        edition_date_el = etree.SubElement(parent, '{%s}editionDate' % \
                                           self.NS['gmd'])
        self._gco_date(edition_date_el, self.date)


class CornerPoint(MetadataRecord):

    id_ = ''
    description = ''
    identifier = ''
    name = ''
    xx = 0
    yy = 0
    srs_name = ''

    def __init__(self, id_, description, identifier, name, xx, yy,
                 srs_name='WGS_1984'):
        self.id_ = id_
        self.description = description
        self.identifier = identifier
        self.name = name
        self.xx = xx
        self.yy = yy
        self.srs_name = srs_name

    def serialize_xml(self):
        point_el = etree.Element('{%s}Point' % self.NS['gml'])
        point_el.set('{%s}id' % self.NS['gml'], self.id_)
        description_el = etree.SubElement(point_el, '{%s}description' % \
                                          self.NS['gml'])
        description_el.text = unicode(self.description)
        identifier_el = etree.SubElement(point_el, '{%s}identifier' % \
                                         self.NS['gml'],
                                         codeSpace='')
        identifier_el.text = unicode(self.identifier)
        name_el = etree.SubElement(point_el, '{%s}name' % \
                                   self.NS['gml'])
        name_el.text = unicode(self.name)
        pos_el = etree.SubElement(point_el, '{%s}pos' % \
                                  self.NS['gml'],
                                  srsName=self.srs_name)
        pos_el.text = ' '.join((str(self.xx), str(self.yy)))
        return point_el


class MD_Dimension(MetadataRecord):

    name = ''
    size = 0
    resolution = 0
    resolution_unit = ''

    def __init__(self, name='', size=0, resolution=0, resolution_unit='deg'):
        self.name = name
        self.size = size
        self.resolution = resolution
        self.resolution_unit = resolution_unit

    def serialize_xml(self):
        md_dimension_el = etree.Element('{%s}MD_Dimension' % \
                                        self.NS['gmd'])
        dimension_name_el = etree.SubElement(md_dimension_el,
                                             '{%s}dimensionName' % \
                                             self.NS['gmd'])
        codelist_uri = 'http://www.isotc211.org/2005/resources/codelist/' \
                       'gmxCodelists.xml#MD_DimensionNameTypeCode'
        type_code_el = etree.SubElement(dimension_name_el,
                                        '{%s}MD_DimensionNameTypeCode' % \
                                        self.NS['gmd'],
                                        codeList=codelist_uri,
                                        codeListValue=unicode(self.name))
        type_code_el.text = unicode(self.name)
        dimension_size_el = etree.SubElement(md_dimension_el,
                                             '{%s}dimensionSize' % \
                                             self.NS['gmd'])
        self._gco_integer(dimension_size_el, self.size)
        resolution_el = etree.SubElement(md_dimension_el,
                                         '{%s}resolution' % \
                                         self.NS['gmd'])
        self._gco_angle(resolution_el, self.resolution, resolution_unit)


class CSWManager(object):

    NAMESPACES = {
        'csw' : 'http://www.opengis.net/cat/csw/2.0.2',
        'ows' : 'http://www.opengis.net/ows',
    }

    ISO_NAMESPACES = {
            'gmd' : 'http://www.isotc211.org/2005/gmd',
            'gco' : 'http://www.isotc211.org/2005/gco'
    }

    def build_get_capabilities_request(self, encoding='utf-8'):
        root = etree.Element('{%s}GetCapabilities' % self.NAMESPACES['csw'],
                             attrib={'service':'CSW'}, nsmap=self.NAMESPACES)
        accept_versions = etree.SubElement(
            root,
            '{%s}AcceptVersions' % self.NAMESPACES['ows']
        )
        version = etree.SubElement(
            accept_versions,
            '{%s}Version' % self.NAMESPACES['ows']
        )
        version.text = '2.0.2'
        accept_formats = etree.SubElement(
            root,
            '{%s}AcceptFormats' % self.NAMESPACES['ows']
        )
        output_format = etree.SubElement(
            accept_formats,
            '{%s}OutputFormat' % self.NAMESPACES['ows']
        )
        output_format.text = 'application/xml'
        request = self._finish_request(root, encoding)
        return request

    def build_describe_record_request(self, encoding='utf-8'):
        root = etree.Element(
            '{%s}DescribeRecord' % self.NAMESPACES['csw'],
            attrib = {
                'service' : 'CSW',
                'version' : '2.0.2',
                'outputFormat' : 'application/xml',
                'schemaLanguage' : 'http://www.w3.org/XML/Schema',
            },
            nsmap=self.NAMESPACES
        )
        request = self._finish_request(root, encoding)
        return request

    def build_get_record_by_id_request(self, id_, encoding='utf-8'):
        root = etree.Element(
            '{%s}GetRecordById' % self.NAMESPACES['csw'],
            attrib={'service':'CSW', 'version':'2.0.2'},
            nsmap=self.NAMESPACES
        )
        id_element = etree.SubElement(root, '{%s}Id' % self.NAMESPACES['csw'])
        id_element.text = id_
        element_set_name = etree.SubElement(root, '{%s}ElementSetName' % \
                                            self.NAMESPACES['csw'])
        element_set_name.text = 'full'
        request = self._finish_request(root, encoding)
        return request

    def build_get_records_CQL_request(self, cql_text, result_type='hits',
                                      start_position=1, max_records=10,
                                      encoding='utf-8'):
        '''
        Return a CSW GetRecords request.

        Inputs:

            cql_text - 

            result_type - Accepted values: 'hits', 'results', 'validate'

            start_position - 

            max_records - 
        '''

        root = etree.Element(
            '{%s}GetRecords' % self.NAMESPACES['csw'],
            attrib={
                'service':'CSW',
                'version':'2.0.2',
                'maxRecords':unicode(max_records),
                'startPosition':unicode(start_position),
                'resultType':result_type,
                'outputFormat':'application/xml',
                'outputSchema':'csw:IsoRecord',
            },
            nsmap=self.NAMESPACES
        )
        query_el = etree.SubElement(
            root,
            '{%s}Query' % self.NAMESPACES['csw'],
            attrib={'typeNames':'gmd:MD_Metadata'},
        )
        constraint_el = etree.SubElement(
            query_el,
            '{%s}Constraint' % self.NAMESPACES['csw'],
            attrib={'version':'1.1.0'}
        )
        text_el = etree.SubElement(
            constraint_el,
            '{%s}CqlText' % self.NAMESPACES['csw']
        )
        text_el.text = cql_text
        request = self._finish_request(root, encoding)
        return request

    def build_insert_records_request(self, metadata_list, encoding='utf-8'):
        '''
        Inputs:

            metadata_list - A list of lxml.etree.Element objects
        '''

        root = self._start_transaction_request()
        for metadata in metadata_list:
            insert_el = etree.SubElement(root, '{%s}Insert' % \
                                       self.NAMESPACES['csw'])
            insert_el.append(metadata)
        request = self._finish_request(root, encoding)
        return request

    def build_update_record_request(self, record_id, new_record,
                                    encoding='utf-8'):
        raise NotImplementedError

    def build_delete_records_request(self, record_ids, encoding='utf-8'):
        '''
        Inputs:

            record_ids - A list of CQL queries each defining the UUID of a
                record to delete.
        '''

        root = self._start_transaction_request()
        for uuid in record_ids:
            delete_el = etree.SubElement(root, '{%s}Delete' % \
                                         self.NAMESPACES['csw'])
            constraint_el = etree.SubElement(
                delete_el,
                '{%s}Constraint' % self.NAMESPACES['csw'],
                attrib={'version':'1.1.0'}
            )
            text_el = etree.SubElement(
                constraint_el,
                '{%s}CqlText' % self.NAMESPACES['csw']
            )
            text_el.text = uuid
        request = self._finish_request(root, encoding)
        return request

    def _start_transaction_request(self):
        root = etree.Element(
            '{%s}Transaction' % self.NAMESPACES['csw'],
            attrib={'version':'2.0.2', 'service':'CSW'},
            nsmap=self.NAMESPACES
        )
        return root

    def _finish_request(self, root_element, encoding):
        tree = etree.ElementTree(root_element)
        request = etree.tostring(tree, encoding=encoding, xml_declaration=True,
                                 pretty_print=True)
        return request


if __name__ == '__main__':
    gn_url = 'http://geoland2.meteo.pt/geonetwork'
    user = 'admin'
    passw = 'g2admin1234'
    manager = GeonetworkManager(gn_url, user, passw)
    manager.close()
