#!/usr/bin/env python
#-*- coding: utf-8 -*-

'''
A testing of geonetwork's xml services.
'''

import re
from uuid import uuid1

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

    def query_list(self):
        return self._queries.keys()

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

    def __init__(self):
        self.uuid = str(uuid1())

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
        code_el.text = self.language_code
        root_node.insert(1, lang_el)

    def _serialize_character_set(self, root_node):
        codelist_uri = 'http://standards.iso.org/ittf/PubliclyAvailable' \
                       'Standards/ISO_19139_Schemas/resources/Codelist/' \
                       'ML_gmxCodelists.xml#MD_CharacterSetCode'
        char_set_el = etree.Element('{%s}characterSet' % self.NS['gmd'])
        code_el = etree.SubElement(char_set_el, '{%s}MD_CharacterSetCode' % \
                                   self.NS['gmd'], codeList=codelist_uri,
                                   codeListValue=self.encoding)
        code_el.text = self.encoding
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

    def _gco_character_string(self, parent_el, text):
        cs_el = etree.SubElement(parent_el,
                                 '{%s}CharacterString' % \
                                 self.NS['gco'])
        cs_el.text = text


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
