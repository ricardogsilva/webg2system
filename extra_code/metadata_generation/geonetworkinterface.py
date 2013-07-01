#!/usr/bin/env python
#-*- coding: utf-8 -*-

'''
A testing of geonetwork's xml services.
'''

import re
import requests
from lxml import etree

class GeonetworkManager(object):
    '''
    Example usage:

    gn_url = 'http://geoland2.meteo.pt/geonetwork'
    user = 'admin'
    passw = 'admin'
    manager = GeonetworkManager(gn_url, user, passw)
    guest_users_response = manager.execute_query('info')
    encoding, users_tree = manager.parse_response(guest_users_response)
    print(etree.tostring(users_tree, encoding=encoding, pretty_print=True))
    '''

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
    _queries = {
        'info_users' : {
            'url_suffix' : 'srv/eng/xml.info',
            'data' : {'type' : 'users'},
        },
    }

    def __init__(self, base_url='', username='', password=''):
        self._csw_manager = CSWManager()
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
        request = self._csw_manager.build_get_capabilities_request()
        url = '/'.join((self.base_url, self._csw_suffix))
        response = self._session.post(url, data=request, headers=self._headers)
        encoding, tree = self.parse_response(response)
        return response, encoding, tree

    def get_records_cql(self, cql, result_type, start_position=1,
                        max_records=10):
        request = self._csw_manager.build_get_records_CQL_request(
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
        request = self._csw_manager.build_get_record_by_id_request(id_)
        url = '/'.join((self.base_url, self._csw_suffix))
        response = self._session.post(url, data=request, headers=self._headers)
        encoding, tree = self.parse_response(response)
        return response, encoding, tree


class CSWManager(object):

    _NAMESPACES = {
        'csw' : 'http://www.opengis.net/cat/csw/2.0.2',
        'ows' : 'http://www.opengis.net/ows',
    }

    def build_get_capabilities_request(self, encoding='utf-8'):
        root = etree.Element('{%s}GetCapabilities' % self._NAMESPACES['csw'],
                             attrib={'service':'CSW'}, nsmap=self._NAMESPACES)
        accept_versions = etree.SubElement(
            root,
            '{%s}AcceptVersions' % self._NAMESPACES['ows']
        )
        version = etree.SubElement(
            accept_versions,
            '{%s}Version' % self._NAMESPACES['ows']
        )
        version.text = '2.0.2'
        accept_formats = etree.SubElement(
            root,
            '{%s}AcceptFormats' % self._NAMESPACES['ows']
        )
        output_format = etree.SubElement(
            accept_formats,
            '{%s}OutputFormat' % self._NAMESPACES['ows']
        )
        output_format.text = 'application/xml'
        request = self._finish_request(root, encoding)
        return request

    def build_describe_record_request(self, encoding='utf-8'):
        root = etree.Element(
            '{%s}DescribeRecord' % self._NAMESPACES['csw'],
            attrib = {
                'service' : 'CSW',
                'version' : '2.0.2',
                'outputFormat' : 'application/xml',
                'schemaLanguage' : 'http://www.w3.org/XML/Schema',
            },
            nsmap=self._NAMESPACES
        )
        request = self._finish_request(root, encoding)
        return request

    def build_get_record_by_id_request(self, id_, encoding='utf-8'):
        root = etree.Element(
            '{%s}GetRecordById' % self._NAMESPACES['csw'],
            attrib={'service':'CSW', 'version':'2.0.2'},
            nsmap=self._NAMESPACES
        )
        id_element = etree.SubElement(root, '{%s}Id' % self._NAMESPACES['csw'])
        id_element.text = id_
        element_set_name = etree.SubElement(root, '{%s}ElementSetName' % \
                                            self._NAMESPACES['csw'])
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
            '{%s}GetRecords' % self._NAMESPACES['csw'],
            attrib={
                'service':'CSW',
                'version':'2.0.2',
                'maxRecords':unicode(max_records),
                'startPosition':unicode(start_position),
                'resultType':result_type,
            },
            nsmap=self._NAMESPACES
        )
        query_el = etree.SubElement(
            root,
            '{%s}Query' % self._NAMESPACES['csw'],
            attrib={'typeNames':'csw:Record'},
        )
        constraint_el = etree.SubElement(
            query_el,
            '{%s}Constraint' % self._NAMESPACES['csw'],
            attrib={'version':'1.1.0'}
        )
        text_el = etree.SubElement(
            constraint_el,
            '{%s}CqlText' % self._NAMESPACES['csw']
        )
        text_el.text = cql_text
        request = self._finish_request(root, encoding)
        return request

    def build_insert_records_request(self, metadata_list, encoding='utf-8'):
        '''
        Inputs:

            metadata_list - A list of lxml.etree.Element objects
        '''

        root = etree.Element(
            '{%s}Transaction' % self._NAMESPACES['csw'],
            attrib={'version' : '2.0.2', 'service' : 'CSW'},
            nsmap=self._NAMESPACES
        )
        for metadata in metadata_list:
            insert_el = etree.SubElement(root, '{%s}Insert' % \
                                       self._NAMESPACES['csw'])
            insert_el.append(metadata)
        request = self._finish_request(root, encoding)

    def build_update_record_request(self, record_id, new_record,
                                    encoding='utf-8'):
        raise NotImplementedError

    def build_delete_record_request(self, record_id, encoding='utf-8'):
        raise NotImplementedError

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
    guest_users_response = manager.execute_query('info_users')
    encoding, guest_users_tree = manager.parse_response(guest_users_response)
    print(etree.tostring(guest_users_tree,
          encoding=encoding, pretty_print=True))
    print('----------------')
    admin_users_response = manager.execute_query('info_users', login_first=True)
    encoding, admin_users_tree = manager.parse_response(admin_users_response)
    print(etree.tostring(admin_users_tree,
          encoding=encoding, pretty_print=True))
    manager.close()
