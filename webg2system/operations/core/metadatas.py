#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
A module for implementing metadata related functionality for the Geoland-2 
processing system.
"""

import os
import re
import logging
import datetime
import time
from lxml import etree
import urllib
import urllib2
import cookielib
from uuid import uuid1
from operator import itemgetter
import datetime as dt
import socket
import copy
socket.setdefaulttimeout(None) # don't timeout

import pycountry

import utilities
import systemsettings.models as ss
import inspiresettings.models as ii

# TODO
# Order the elements according to the element_order attribute
# Check the remaining xml errors

class MetadataHandler(object):

    def __init__(self, logger=None):
        if logger is None:
            self.logger = logging.getLogger(
                    '.'.join((__name__, self.__class__.__name__)))
        else:
            self.logger = logger


class SWIMetadataModifier(MetadataHandler):

    MD_Identification_order = {
        0 : 'citation',
        1 : 'abstract',
        2 : 'purpose',
        3 : 'credit',
        4 : 'status',
        5 : 'pointOfContact',
        6 : 'resourceMaintenance',
        7 : 'graphicOverview',
        8 : 'resourceFormat',
        9 : 'descriptiveKeywords',
        10 : 'resourceConstraints',
        11 : 'aggregationInfo',
        12 : 'spatialRepresentationType',
        13 : 'spatialResolution',
        14 : 'language',
        15 : 'characterSet',
        16 : 'topicCategory',
        17 : 'extent',
        18 : 'supplementalInformation',
    }

    def __init__(self, swi_settings, logger=None):
        super(SWIMetadataModifier, self).__init__(logger)
        self.product = swi_settings
        #self.tree = etree.parse(xml_file)
        #self.ns = self.tree.getroot().nsmap.copy()
        ## in order to use this dictionary for XPATH queries the default 
        ## entry has to be deleted
        #del self.ns[None] 

    def parse_file(self, xml_file):
        self.tree = etree.parse(xml_file)
        self.ns = self.tree.getroot().nsmap.copy()
        # in order to use this dictionary for XPATH queries the default 
        # entry has to be deleted
        del self.ns[None] 

    def modify_uuids(self):
        uuid = str(uuid1())
        self.modify_file_identifier(uuid)
        self.modify_id_info_modifier(uuid)
        self.modify_parent_identifier()

    def modify_parent_identifier(self):
        parent_uuid = self.product.iParentIdentifier
        parent_id_el = self.tree.xpath('gmd:parentIdentifier/gco:' \
                                       'CharacterString', 
                                       namespaces=self.ns)[0]
        parent_id_el.text = parent_uuid

    def modify_file_identifier(self, uuid):
        file_id_el = self.tree.xpath('gmd:fileIdentifier/gco:CharacterString',
                                namespaces=self.ns)[0]
        file_id_el.text = uuid

    def modify_id_info_modifier(self, uuid):
        el = self.tree.xpath('gmd:identificationInfo/'
                             'gmd:MD_DataIdentification/gmd:citation/'
                             'gmd:CI_Citation/gmd:identifier/'
                             'gmd:MD_Identifier/gmd:code/gco:CharacterString',
                             namespaces=self.ns)[0]
        el.text = uuid

    def modify_metadata_contact(self):
        vito_org = ii.Organization.objects.get(short_name='VITO')
        vito_helpdesk = vito_org.collaborator_set.get(name='helpdesk')
        role = 'pointOfContact'
        position = None
        xpath = self.tree.xpath('gmd:contact/gmd:CI_ResponsibleParty',
                                namespaces=self.ns)[0]
        self._modify_ci_responsible_party(xpath, vito_helpdesk, role, position)

    def modify_principalIvestigator_contact(self):
        contact = self.product.principal_investigator
        role = 'principalInvestigator'
        position = 'Researcher'
        xpath = self.tree.xpath('gmd:identificationInfo/gmd:' \
                                'MD_DataIdentification/gmd:' \
                                'pointOfContact/gmd:CI_ResponsibleParty', 
                                namespaces=self.ns)[0]
        self._modify_ci_responsible_party(xpath, contact, role, position)

    def modify_originator_contact(self):
        contact = self.product.originator
        role = 'originator'
        position = 'Geoland2 Help Desk'
        xpath = self.tree.xpath('gmd:identificationInfo/gmd:' \
                                'MD_DataIdentification/gmd:' \
                                'pointOfContact/gmd:CI_ResponsibleParty', 
                                namespaces=self.ns)[1]
        self._modify_ci_responsible_party(xpath, contact, role, position)

    def modify_citation(self, timeslot):
        ipma_org = ii.Organization.objects.get(short_name='IPMA')
        citation_el = self.tree.xpath('gmd:identificationInfo/*/gmd:citation/*',
                                     namespaces=self.ns)[0]
        ci_citation_el = citation_el.xpath('gmd:identifier/*/gmd:authority/'
                                           'gmd:CI_Citation',
                                           namespaces=self.ns)[0]
        authority_title_el = ci_citation_el.xpath('gmd:title/gco:Character'
                                                  'String',
                                                  namespaces=self.ns)[0]
        authority_title_el.text = ipma_org.short_name
        authority_date_el = ci_citation_el.xpath('gmd:date/*/gmd:date/gco:'
                                                 'Date', namespaces=self.ns)[0]
        authority_date_el.text = timeslot.strftime('%Y-%m-%d')
        code_list_value = 'publication'
        authority_date_type_el = ci_citation_el.xpath('gmd:date/*/gmd:dateType'
                                                      '/gmd:CI_DateTypeCode',
                                                      namespaces=self.ns)[0]
        authority_date_type_el.set('codeListValue', code_list_value)
        authority_date_type_el.text = code_list_value
        otherDetailsEl = citation_el.xpath('gmd:otherCitationDetails/'\
                                          'gco:CharacterString', 
                                          namespaces=self.ns)[0]
        otherDetailsEl.text = self.product.user_manual

    def modify_abstract(self):
        abstract_el = self.tree.xpath('gmd:identificationInfo/*/gmd:abstract/'
                                      'gco:CharacterString',
                                      namespaces=self.ns)[0]
        abstract_el.text = self.product.iResourceAbstract

    def modify_purpose(self):
        purpose_text = 'This product is first designed to fit the ' \
                       'requirements of the Global Land component of Land ' \
                       'Service of GMES-Copernicus. It can be also useful ' \
                       'for all applications related to environment ' \
                       'monitoring.'
        purpose_el = self.tree.xpath('gmd:identificationInfo/*/gmd:purpose/'
                                     'gco:CharacterString',
                                     namespaces=self.ns)[0]
        purpose_el.text = purpose_text

    def modify_credit(self):
        credit_text = 'The research leading to these results has ' \
                      'received funding from the European Community\'s ' \
                      'Seventh Framework Program (FP7/2007-2013) and is ' \
                      'maintained through the Copernicus European Earth ' \
                      'monitoring program, more particularly through the ' \
                      'Global Land Component of the GMES Initial ' \
                      'Operations. This product is the joint property of the ' \
                      'Technical University of Wien and IPMA under ' \
                      'copyright Copernicus. It has been generated from ' \
                      'Metop/ASCAT surface soil moisture data distributed ' \
                      'by Eumetsat.'
        credit_el = self.tree.xpath('gmd:identificationInfo/*/gmd:credit/'
                                    'gco:CharacterString',
                                    namespaces=self.ns)[0]
        credit_el.text = credit_text

    def modify_points_of_contact(self):
        originator_el = self.tree.xpath('gmd:identificationInfo/*/gmd:point'
                                        'OfContact/gmd:CI_ResponsibleParty',
                                        namespaces=self.ns)[1]
        ipma_org = ii.Organization.objects.get(short_name='IPMA')
        originator_contact = ipma_org.collaborator_set.get(name='Sandra Coelho')
        self._modify_ci_responsible_party(originator_el, originator_contact,
                                          'originator', position='producer')
        # adding three new pointOfcontact elements
        vito_org = ii.Organization.objects.get(short_name='VITO')
        vito_collab = vito_org.collaborator_set.get(name='helpdesk')
        ec_dgei_org = ii.Organization.objects.get(short_name='EC-DGEI')
        ec_dgei_collab = ec_dgei_org.collaborator_set.get(name='helpdesk')
        jrc_org = ii.Organization.objects.get(short_name='EC-DGJRC')
        jrc_collab = jrc_org.collaborator_set.get(name='helpdesk')
        self._add_point_of_contact(vito_collab, 'pointOfContact',
                                   'GIO-Global Land Help Desk')
        self._add_point_of_contact(ec_dgei_collab, 'owner', 'owner')
        self._add_point_of_contact(jrc_collab, 'custodian', 'responsible')
        parent_el = self.tree.xpath('gmd:identificationInfo/gmd:MD_Data'
                                    'Identification', namespaces=self.ns)[0]
        self._re_order(parent_el, self.MD_Identification_order)

    def _add_point_of_contact(self, contact, role, position):
        ident_info_els = self.tree.xpath('gmd:identificationInfo/*/*',
                                         namespaces=self.ns)
        last_index = 0
        for index, element in enumerate(ident_info_els):
            if element.tag == '{%s}pointOfContact' % self.ns['gmd']:
                last_index = index

        one_point_of_contact = self.tree.xpath('gmd:identificationInfo/*/'
                                               'gmd:pointOfContact',
                                               namespaces=self.ns)[0]
        pt_ct_el = copy.deepcopy(one_point_of_contact)
        ci_resp_el = pt_ct_el.xpath('gmd:CI_ResponsibleParty',
                                    namespaces=self.ns)[0]
        self._modify_ci_responsible_party(ci_resp_el, contact, role, position)
        ident_info_el_md = self.tree.xpath('gmd:identificationInfo/gmd:'
                                           'MD_DataIdentification',
                                           namespaces=self.ns)[0]
        ident_info_el_md.append(pt_ct_el)

    def modify_quicklook_url(self, timeslot):

        baseURL = ss.WebServer.objects.get().public_URL
        ts = timeslot.strftime('%Y%m%d%H%M')
        url = '%s/operations/products/%s/%s/quicklook/' % \
                (baseURL, self.product.short_name, ts)
        file_name_el = self.tree.xpath('gmd:identificationInfo/*/'\
                                     'gmd:graphicOverview/*/'\
                                     'gmd:fileName/gco:CharacterString',
                                     namespaces=self.ns)[0]
        file_name_el.text = url
        #file_desc_el = self.tree.xpath('gmd:identificationInfo/*/'\
        #                             'gmd:graphicOverview/*/'\
        #                             'gmd:fileDescription/gco:CharacterString',
        #                             namespaces=self.ns)[0]
        #file_desc_el.text = self.product.graphic_overview_description
        #file_type_el = self.tree.xpath('gmd:identificationInfo/*/'\
        #                             'gmd:graphicOverview/*/'\
        #                             'gmd:fileType/gco:CharacterString',
        #                             namespaces=self.ns)[0]
        #file_type_el.text = self.product.graphic_overview_type

    def modify_download_url(self, timeslot):
        baseURL = ss.WebServer.objects.get().public_URL
        ts = timeslot.strftime('%Y%m%d%H%M')
        vito_sdi_url = 'http://web.vgt.vito.be/download_g2.php?'
        url = '%s/operations/products/%s/%s/product/' % \
                (baseURL, self.product.short_name, ts)
        vito_url = '%sfile=&path=%s&serviceid=%s' % \
                   (vito_sdi_url, url, self.product.sdi_service_id)
        linkage_el = self.tree.xpath('gmd:distributionInfo/*/gmd:' \
                                     'transferOptions[1]/*/gmd:onLine/*/' \
                                     'gmd:linkage/gmd:URL', 
                                     namespaces=self.ns)[0]
        linkage_el.text = vito_url

    def modify_resource_constraints(self):
        use_limitations = self.tree.xpath('gmd:identificationInfo/*/gmd:'
                                          'resourceConstraints[1]/*/gmd:'
                                          'useLimitation/gco:CharacterString',
                                          namespaces=self.ns)[0]
        use_limitations.text = 'No limitations'
        use_constraints = self.tree.xpath('gmd:identificationInfo/*/gmd:'
                                          'resourceConstraints[2]/*/gmd:'
                                          'useConstraints/gmd:MD_Restriction'
                                          'Code', namespaces=self.ns)[0]
        use_constraints_url = 'http://standards.iso.org/ittf/Publicly' \
                              'AvailableStandards/ISO_19139_Schemas/' \
                              'resources/Codelist/ML_gmxCodelists.xml#' \
                              'MD_RestrictionCode'
        use_constraints_value = 'copyright'
        use_constraints.set('codeList', use_constraints_url)
        use_constraints.set('codeListValue', use_constraints_value)
        use_constraints.text = '@copernicus.eu'
        access_constraints = self.tree.xpath('gmd:identificationInfo/*/gmd:'
                                             'resourceConstraints[3]/*/gmd:'
                                             'accessConstraints/gmd:MD_'
                                             'RestrictionCode',
                                             namespaces=self.ns)[0]
        access_constraints_url = 'http://standards.iso.org/ittf/Publicly' \
                                 'AvailableStandards/ISO_19139_Schemas/' \
                                 'resources/Codelist/ML_gmxCodelists.xml#' \
                                 'MD_RestrictionCode'
        access_constraints_value = 'otherRestrictions'
        access_constraints.text = 'data policy @copernicus.eu'
        other_constraints = self.tree.xpath('gmd:identificationInfo/*/gmd:'
                                            'resourceConstraints[3]/*/gmd:'
                                            'otherConstraints/gco:'
                                            'CharacterString',
                                            namespaces=self.ns)[0]
        other_constraints.text = '(d) the confidentiality of commercial or ' \
                                 'industrial information, where such ' \
                                 'confidentiality is provided for by ' \
                                 'national or Community law to protect a ' \
                                 'legitimate economic interest, including ' \
                                 'the public interest in maintaining ' \
                                 'statistical confidentiality and tax secrecy.'

    def modify_distribution_info(self):
        base = self.tree.xpath('gmd:distributionInfo/gmd:MD_Distribution',
                               namespaces=self.ns)[0]
        dist_fmt_base = base.xpath('gmd:distributionFormat/gmd:MD_Format',
                                   namespaces=self.ns)[0]
        fmt_name = dist_fmt_base.xpath('gmd:name/gco:CharacterString',
                                       namespaces=self.ns)[0]
        fmt_name.text = 'ZIP archive'
        fmt_version = dist_fmt_base.xpath('gmd:version/gco:CharacterString',
                                       namespaces=self.ns)[0]
        fmt_version.text = 'v3.2'
        fmt_spec = dist_fmt_base.xpath('gmd:specification/gco:CharacterString',
                                       namespaces=self.ns)[0]
        fmt_spec.text = 'Standard PKZIP compatible Unix/Linux ZIP format'
        fmt_decompression = dist_fmt_base.xpath('gmd:fileDecompressionTechnique'
                                                '/gco:CharacterString',
                                                namespaces=self.ns)[0]
        fmt_decompression.text = 'unzip or pkunzip'
        distributor_base = base.xpath('gmd:distributor/gmd:MD_Distributor',
                                      namespaces=self.ns)[0]
        distributor_contact_ci = distributor_base.xpath(
            'gmd:distributorContact/gmd:CI_ResponsibleParty',
            namespaces=self.ns
        )[0]
        ipma_org = ii.Organization.objects.get(short_name='IPMA')
        ipma_contact = ipma_org.collaborator_set.get(name='Sandra Coelho')
        role = 'distributor'
        position = 'Distribution center'
        self._modify_ci_responsible_party(distributor_contact_ci, ipma_contact,
                                          role, position)
        instructions_el = distributor_base.xpath('gmd:distributionOrderProcess'
                                                 '/*/gmd:orderingInstructions/'
                                                 'gco:CharacterString',
                                                 namespaces=self.ns)[0]
        instructions_el.text = 'Products can be downloaded on-line via HTTP.' \
                               ' They are also available through EUMETCAST. ' \
                               'Bulk downloads and near-real time ' \
                               'dissemination can be requested at our ' \
                               'helpdesk.'

        xfer_ops_http_base = base.xpath('gmd:transferOptions',
                                        namespaces=self.ns)[0]
        units = xfer_ops_http_base.xpath('*/gmd:unitsOfDistribution/gco:'
                                         'CharacterString',
                                         namespaces=self.ns)[0]
        units.text = 'Per product'
        size_el = xfer_ops_http_base.xpath('*/gmd:transferSize',
                                           namespaces=self.ns)[0]
        name = xfer_ops_http_base.xpath('*/gmd:onLine/*/gmd:name/gco:'
                                     'CharacterString', namespaces=self.ns)[0]
        name.text = 'Copernicus Global Land Service'
        md_base = xfer_ops_http_base.xpath('gmd:MD_DigitalTransferOptions',
                                           namespaces=self.ns)[0]
        md_base.remove(size_el)
        xfer_ops_bundle = copy.deepcopy(xfer_ops_http_base)

        bundle_CI = xfer_ops_bundle.xpath('gmd:MD_DigitalTransferOptions/'
                                          'gmd:onLine/gmd:CI_OnlineResource',
                                          namespaces=self.ns)[0]
        protocol_el = bundle_CI.xpath('gmd:protocol', namespaces=self.ns)[0]
        function_el = bundle_CI.xpath('gmd:function', namespaces=self.ns)[0]
        bundle_CI.remove(protocol_el)
        bundle_CI.remove(function_el)
        units = xfer_ops_bundle.xpath('*/gmd:unitsOfDistribution/gco:'
                                      'CharacterString',
                                      namespaces=self.ns)[0]
        units.text = 'Product bundles'
        linkage = xfer_ops_bundle.xpath('*/gmd:onLine/*/gmd:linkage/gmd:URL',
                                        namespaces=self.ns)[0]
        linkage.text = 'mailto:helpdesk@vgt.vito.be'
        description = xfer_ops_bundle.xpath('*/gmd:onLine/*/gmd:description/gco:'
                                     'CharacterString', namespaces=self.ns)[0]
        description.text = 'Request to receive products via FTP'
        base.append(xfer_ops_bundle)
        xfer_ops_eumet = copy.deepcopy(xfer_ops_bundle)
        units = xfer_ops_eumet.xpath('*/gmd:unitsOfDistribution/gco:'
                                      'CharacterString',
                                      namespaces=self.ns)[0]
        units.text = 'Per product'
        description = xfer_ops_eumet.xpath('*/gmd:onLine/*/gmd:description/gco:'
                                     'CharacterString', namespaces=self.ns)[0]
        description.text = 'Receive products via EUMETCAST'
        base.append(xfer_ops_eumet)

    def modify_data_quality_info(self):
        base_el = self.tree.xpath('gmd:dataQualityInfo/gmd:DQ_DataQuality',
                                  namespaces=self.ns)[0]
        scope = base_el.xpath('gmd:scope/*/gmd:level/gmd:MD_ScopeCode',
                              namespaces=self.ns)[0]
        code_list_url = 'http://standards.iso.org/ittf/PubliclyAvailable' \
                        'Standards/ISO_19139_Schemas/resources/Codelist/' \
                        'ML_gmxCodelists.xml#MD_ScopeCode'
        code_list_value = 'dataset'
        scope.set('codeList', code_list_url)
        scope.set('codeListValue', code_list_value)
        scope.text = code_list_value
        dq_conformance = base_el.xpath('gmd:report/gmd:DQ_ThematicAccuracy/'
                                       'gmd:result/gmd:DQ_ConformanceResult',
                                       namespaces=self.ns)[0]
        explanation_el = etree.SubElement(dq_conformance, '{%s}explanation' % \
                                          self.ns['gmd'])
        cs_el = etree.SubElement(explanation_el, '{%s}CharacterString' % \
                                 self.ns['gco'])
        cs_el.text = self.product.validation_report
        lineage_el = base_el.xpath('gmd:lineage/gmd:LI_Lineage/gmd:statement/'
                                   'gco:CharacterString',
                                   namespaces=self.ns)[0]
        lineage_el.text = self.product.lineage

        #SANDRA
    def modify_temporal_extent(self, timeslot):

        parentEl = self.tree.xpath('gmd:identificationInfo/*/gmd:extent/'\
                               'gmd:EX_Extent/gmd:temporalElement/'\
                               'gmd:EX_TemporalExtent/gmd:extent/'\
                               'gml:TimePeriod', namespaces=self.ns)[0]
        
        bTimeslot = timeslot - datetime.timedelta(hours=12) 
        beginEl = parentEl.xpath('gml:beginPosition', namespaces=self.ns)[0]
        beginEl.text = bTimeslot.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        eTimeslot = timeslot + datetime.timedelta(hours=12)
        endEl = parentEl.xpath('gml:endPosition', namespaces=self.ns)[0]
        endEl.text = eTimeslot.strftime('%Y-%m-%dT%H:%M:%SZ')
        #SANDRA

        #SANDRA
    def modify_temporal_tags(self, timeslot):
        '''
        alterar este codigo para fazer as alteracoes ao xml nas tags relacionadas com tempoo.... 
        '''

        parentEl = self.tree.xpath('gmd:identificationInfo/*/gmd:extent/'\
                               'gmd:EX_Extent/gmd:temporalElement/'\
                               'gmd:EX_TemporalExtent/gmd:extent/'\
                               'gml:TimePeriod', namespaces=self.ns)[0]
        
        bTimeslot = timeslot - datetime.timedelta(hours=12) 
        beginEl = parentEl.xpath('gml:beginPosition', namespaces=self.ns)[0]
        beginEl.text = bTimeslot.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        eTimeslot = timeslot + datetime.timedelta(hours=12)
        endEl = parentEl.xpath('gml:endPosition', namespaces=self.ns)[0]
        endEl.text = eTimeslot.strftime('%Y-%m-%dT%H:%M:%SZ')
        #SANDRA

    def save_xml(self, path):
        self.logger.debug('save path: %s' % path)
        self.tree.write(path)

    def _modify_ci_responsible_party(self, xml_element, contact, role,
                                     position=None):
        # fields to modify:
        # - organisationName
        org_name_el = xml_element.xpath('gmd:organisationName/gco:CharacterString', 
                                        namespaces=self.ns)[0]
        org_name_el.text = contact.organization.name
        # - positionName (may be absent)
        if position is not None:
            position_name_el = xml_element.xpath('gmd:positionName/gco:CharacterString', 
                                                 namespaces=self.ns)[0]
            position_name_el.text = position
        # - contactInfo
        ci_contact_el = xml_element.xpath('gmd:contactInfo/gmd:CI_Contact', 
                                          namespaces=self.ns)[0]
        self._modify_ci_contact(ci_contact_el, contact)
        # - role
        role_el = xml_element.xpath('gmd:role/gmd:CI_RoleCode', 
                                    namespaces=self.ns)[0]
        role_el.attrib['codeListValue'] = role
        role_el.text = role

    def _modify_ci_contact(self, xml_element, contact):
        # fields to modify:
        # - address
        ci_address_el = xml_element.xpath('gmd:address/gmd:CI_Address', 
                                          namespaces=self.ns)[0]
        self._modify_ci_address(ci_address_el, contact)
        # - onlineResource
        ci_onlineResource_el = xml_element.xpath('gmd:onlineResource/gmd:CI_OnlineResource', 
                                                 namespaces=self.ns)[0]
        self._modify_ci_online_resource(
            xml_element=ci_onlineResource_el,
            url=contact.organization.url,
            protocol='HTTP',
            name='%s website' % contact.organization.short_name,
            description='Organization website',
            function='information'
        )
        # - hoursOfService
        hours_el = xml_element.xpath('gmd:hoursOfService/gco:CharacterString', 
                                     namespaces=self.ns)[0]
        hours_el.text = 'Office hours, 5 days per week'
        # - contactInstructions
        instructions_el = xml_element.xpath('gmd:contactInstructions/gco:CharacterString', 
                                            namespaces=self.ns)[0]
        instructions_el.text = 'Preferably by e-mail'

    def _modify_ci_address(self, xml_element, contact):
        # fields to modify:
        # - deliveryPoint
        delivery_point_el = xml_element.xpath('gmd:deliveryPoint/gco:CharacterString', 
                                              namespaces=self.ns)[0]
        delivery_point_el.text = contact.organization.streetAddress
        # - city
        city_el = xml_element.xpath('gmd:city/gco:CharacterString', 
                                    namespaces=self.ns)[0]
        city_el.text = contact.organization.city
        # - postalCode
        postal_el = xml_element.xpath('gmd:postalCode/gco:CharacterString', 
                                      namespaces=self.ns)[0]
        postal_el.text = contact.organization.postalCode
        # - Country
        country_code  = contact.organization.country
        country_el = xml_element.xpath('gmd:country/gmd:Country', 
                                       namespaces=self.ns)[0]
        country_el.attrib['codeListValue'] = country_code
        country_el.text = pycountry.countries.get(alpha2=country_code).name
        # - electronicMailAddress
        email_el = xml_element.xpath('gmd:electronicMailAddress/gco:CharacterString', 
                                      namespaces=self.ns)[0]
        email_el.text = contact.email

    def _modify_ci_online_resource(self, xml_element, url, protocol, name, 
                                   description, function):
        # fields to modify:
        # - linkage
        linkage_el = xml_element.xpath('gmd:linkage/gmd:URL', namespaces=self.ns)[0]
        linkage_el.text = url
        # - protocol
        protocol_el = xml_element.xpath('gmd:protocol/gco:CharacterString', 
                                        namespaces=self.ns)[0]
        protocol_el.text = protocol
        # - name
        name_el = xml_element.xpath('gmd:name/gco:CharacterString', 
                                    namespaces=self.ns)[0]
        name_el.text = name
        # - description
        desc_el = xml_element.xpath('gmd:description/gco:CharacterString', 
                                    namespaces=self.ns)[0]
        desc_el.text = description
        # - function
        function_el = xml_element.xpath('gmd:function/gmd:CI_OnLineFunctionCode', 
                                       namespaces=self.ns)[0]
        function_el.attrib['codeListValue'] = function
        function_el.text = function

    def _re_order(self, parent_element, order_dict):
        re_order = []
        for el in parent_element:
            the_index = None
            for k, v in order_dict.iteritems():
                full_tag = '{%s}%s' % (self.ns.get('gmd'), v)
                if full_tag == el.tag:
                    the_index = k
            re_order.append((el, the_index))
        a = sorted(re_order, key=itemgetter(1))
        for tup in a:
            parent_element.append(tup[0])


class MetadataGenerator(object):

    element_order = {
      0 : 'fileIdentifier',
      1 : 'language',
      2 : 'characterSet',
      3 : 'parentIdentifier',
      4 : 'hierarchyLevel',
      5 : 'contact',
      6 : 'dateStamp',
      7 : 'metadataStandardName',
      8 : 'metadataStandardVersion',
      9 : 'spatialRepresentationInfo',
      10 : 'referenceSystemInfo',
      11 : 'identificationInfo',
      12 : 'contentInfo',
      13 : 'distributionInfo',
      14 : 'dataQualityInfo',
      15 : 'metadataMaintenance',
    }

    MD_Identification_order = {
        0 : 'citation',
        1 : 'abstract',
        2 : 'purpose',
        3 : 'credit',
        4 : 'status',
        5 : 'pointOfContact',
        6 : 'resourceMaintenance',
        7 : 'graphicOverview',
        8 : 'resourceFormat',
        9 : 'descriptiveKeywords',
        10 : 'resourceConstraints',
        11 : 'aggregationInfo',
        12 : 'spatialRepresentationType',
        13 : 'spatialResolution',
        14 : 'language',
        15 : 'characterSet',
        16 : 'topicCategory',
        17 : 'extent',
        18 : 'supplementalInformation',
    }

    MD_Distributor_order = {
        0 : 'distributorContact',
        1 : 'distributionOrderProcess',
        2 : 'distributorFormat',
        3 : 'distributorTransferOptions',
    }

    def __init__(self, template, timeslot, product, logger=None):
        if logger is None:
            self.logger = logging.getLogger(
                    '.'.join((__name__, self.__class__.__name__)))
        else:
            self.logger = logger
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
                    # abstract <- handled by the _apply_abstract method()
                #'abstract' : self.tree.xpath('gmd:identificationInfo[1]'\
                #        '/*/gmd:abstract/gco:CharacterString', 
                #        namespaces=self.ns)[0],
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
                    # resourceConstraints <- unchanged
                    # resourceConstraints <- unchanged
                    # resourceConstraints <- unchanged
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

    def _prepare_extra_keywords(self, tile):
        re_obj = re.search(r'(?P<h>H\d{2})(?P<v>V\d{2})', tile)
        extra_keywords = [
            self.timeslot.strftime('%Y%m%d%H%M'),
        ]
        if re_obj is not None:
            extra_keywords.append(re_obj.group('h'))
            extra_keywords.append(re_obj.group('v'))
            extra_keywords.append(re_obj.string)
        else:
            extra_keywords.append(tile)
        return extra_keywords

    def _apply_other_keywords(self, productSettings, tile):
        '''
        Apply the keywords to the object's metadata tree.
        '''

        parentElement = self.tree.xpath('gmd:identificationInfo/'\
                                        'gmd:MD_DataIdentification', 
                                        namespaces=self.ns)[0]
        vocabularyDict = self._sort_keywords(productSettings)
        for vocab, keywordSettings in vocabularyDict.iteritems():
            if vocab is None:
                descKeywordsEl = etree.SubElement(parentElement, 
                                                  '{%s}descriptiveKeywords' % \
                                                  self.ns['gmd'])
                mdKeywordsEl = etree.SubElement(descKeywordsEl, 
                                                '{%s}MD_Keywords' % \
                                                self.ns['gmd'])
                for extra_key in self._prepare_extra_keywords(tile):
                    keywordEl = etree.SubElement(mdKeywordsEl, '{%s}keyword' % \
                                                 self.ns['gmd'])
                    charStringEl = etree.SubElement(keywordEl, 
                                                    '{%s}CharacterString' % \
                                                    self.ns['gco'])
                    charStringEl.text = extra_key
            else:
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
                charStringTitleEl = etree.SubElement(titleEl,
                                                     '{%s}CharacterString' % \
                                                     self.ns['gco'])
                charStringTitleEl.text = vocSettings.title
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
        charStringTitleEl = etree.SubElement(titleEl,
                                             '{%s}CharacterString' % \
                                             self.ns['gco'])
        charStringTitleEl.text = 'GEMET - INSPIRE themes version 1.0'
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

    def _apply_keywords(self, productSettings, tile=None):
        self._remove_original_keywords()
        self._apply_INSPIRE_keyword(productSettings)
        self._apply_other_keywords(productSettings, tile)

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
            positionName=None, online_resource_name=None,
            online_resource_description=None):
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

            online_resource_name - A string with the text of the element

            online_resource_description - A string with the text of the element

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

        countryCode = contact.organization.country
        cl_url = 'http://www.iso.org/iso/en/prods-services/iso3166ma/' \
                 '02iso-3166-code-lists/index.html'
        cl_value = countryCode
        cl_code_space = 'ISO 3166-1'
        country_codelist_el = etree.SubElement(countryEl, '{%s}Country' % \
                                               self.ns['gmd'], codeList=cl_url,
                                               codeListValue=cl_value,
                                               codeSpace=cl_code_space)
        country_codelist_el.text = pycountry.countries.get(
            alpha2=countryCode).name
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
        if online_resource_name is None:
            gcoNameEl.text = '%s website' % contact.organization.short_name
        else:
            gcoNameEl.text = online_resource_name
        descrEl = etree.SubElement(ciOnlineEl, '{%s}description' % self.ns['gmd'])
        gcoDescrEl = etree.SubElement(descrEl, '{%s}CharacterString' % \
                                         self.ns['gco'])
        if online_resource_description is None:
            gcoDescrEl.text = 'Organization website'
        else:
            gcoDescrEl.text = online_resource_description
        functionEl = etree.SubElement(ciOnlineEl, '{%s}function' \
                                       % self.ns['gmd'])
        functionListEl = etree.SubElement(functionEl, '{%s}CI_OnLineFunctionCode' \
                                          % self.ns['gmd'])
        functionListElAttribs = functionListEl.attrib
        functionListElAttribs['codeList'] = 'http://'\
            'standards.iso.org/ittf/PubliclyAvailableStandards/'\
            'ISO_19139_Schemas/resources/Codelist/'\
            'ML_gmxCodelists.xml#CI_OnLineFunctionCode'
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

        productVersion = re.search(r'GEO_(v\d)', filePath).groups()[0]
        productVersion = productVersion.replace('v', 'V')
        today = dt.date.today().strftime('%Y-%m-%d')
        fileName = os.path.splitext(os.path.basename(filePath))[0]
        fileTimeslot = utilities.extract_timeslot(filePath)
        #fs = utilities.get_file_settings(filePath)
        minx, miny, maxx, maxy = mapper.get_bounds(filePath, 
                                                   self.product.pixelSize)
        rowSize, colSize = mapper.get_lines_cols(filePath)
        tileName = utilities.get_tile_name(filePath)
        uuid = str(uuid1())
        rootAttribs = self.tree.getroot().attrib
        rootAttribs['id'] = '%sMetadata' % self.product.short_name
        self.update_element('fileIdentifier', uuid)
        if utilities.is_smal_tile(filePath):
            self.update_element('parentIdentifier', 
                                self.product.iParentIdentifier)
        else:
            self.update_element('parentIdentifier', 
                                self.product.parent_id_continental)
        self.update_element('hierarchyLevel', 'dataset')
        self._remove_contact_info(self.tree.getroot(), 'contact')
        vito_org = ii.Organization.objects.get(short_name='VITO')
        vito_helpdesk = vito_org.collaborator_set.get(name='helpdesk')
        ecdgei_org = ii.Organization.objects.get(short_name='EC-DGEI')
        ecdgei_helpdesk = ecdgei_org.collaborator_set.get(name='helpdesk')
        jrc_org = ii.Organization.objects.get(short_name='EC-DGJRC')
        jrc_helpdesk = jrc_org.collaborator_set.get(name='helpdesk')
        self._apply_contact_info(self.tree.getroot(), 'contact',
            role='pointOfContact',
            contact=vito_helpdesk,
            online_resource_name='GIO Global Land service',
            online_resource_description='GIO Global Land website'
        )
        self.update_element('dateStamp', today)
        self.update_element('rowSize', str(rowSize))
        self.update_element('rowResolution', '%.2f' % self.product.pixelSize)
        self.update_element('colSize', str(colSize))
        self.update_element('colResolution', '%.2f' % self.product.pixelSize)
        cornerPoint = '%.1f %.1f' % (maxy, minx)
        self.update_element('cornerPoint', cornerPoint)
        self.update_element('referenceSystemIdentifier', 
                            'EPSG:%s' % self.product.ireferenceSystemID)
        self._apply_citation(self.product, fileName, productVersion, uuid)
        self._apply_abstract(self.product.iResourceAbstract)
        #self.update_element('abstract', self.product.iResourceAbstract)
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
                                 positionName='IPMA GIO-Global Land Help Desk',
                                 contact=self.product.originator_collaborator)
        self._apply_contact_info(identInfoEl, 'pointOfContact', 
                                 role='pointOfContact', 
                                 positionName='GIO-Global Land Help Desk',
                                 contact=vito_helpdesk)
        self._apply_contact_info(identInfoEl, 'pointOfContact', 
                                 role='owner', 
                                 positionName='owner',
                                 contact=ecdgei_helpdesk)
        self._apply_contact_info(identInfoEl, 'pointOfContact', 
                                 role='custodian', 
                                 positionName='Responsible',
                                 contact=jrc_helpdesk)
        self._apply_graphic_overview(tileName, self.product)
        self._apply_aggregation_infos()
        self._apply_temporal_extent(self.product, fileTimeslot)
        self._apply_keywords(self.product, tileName)
        self.update_element('resolution', '%.2f' % self.product.pixelSize)
        self._apply_topic_categories(self.product)
        self.update_element('eastLongitude', '%.2f' % maxx)
        self.update_element('westLongitude', '%.2f' % minx)
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
                                 positionName='Distribution center',
                                 contact=self.product.distributor)
        self._apply_linkage(tileName, self.product)
        self.update_element('thematicAccuracyTitle', 'Validation results '
                            'conform CEOS LPV guidelines')
        self.update_element('valReport', self.product.validation_report)
        self.update_element('lineage', self.product.lineage)

        self._re_order(self.tree.getroot(), self.element_order)
        md_ident = self.tree.getroot().xpath(
            'gmd:identificationInfo/gmd:MD_DataIdentification', 
            namespaces=self.ns
        )[0]
        self._re_order(md_ident, self.MD_Identification_order)
        md_distrib = self.tree.getroot().xpath( 
            'gmd:distributionInfo/gmd:MD_Distribution/gmd:distributor/' \
            'gmd:MD_Distributor', 
            namespaces=self.ns
        )[0]
        self._re_order(md_distrib, self.MD_Distributor_order)

    def create_series_metadata(self):
        '''
        Create an xml metadata file for the dataset series
        '''
        # settings that are to come from django
        uuid = self.product.iParentIdentifier
        series_title = self.product.series_title
        series_status = self.product.series_status
        # fields that change from the dataset to dataset series
        self._series_update_status(series_status)
        self._series_update_citation(series_title)
        self._series_update_hierarchy('series')
        self._series_get_quicklook()
        self._series_update_uuid(uuid)
        self._series_apply_global_coordinates()
        self._series_change_linkage()
        # fields that get removed from the dataset file
        self._series_remove_unused_elements()

    def _series_update_status(self, status):
        
        statusEl = self.tree.xpath('gmd:identificationInfo[1]/*/gmd:status/'\
                                   'gmd:MD_ProgressCode', namespaces=self.ns)[0]
        statusEl.attrib['codeListValue'] = status
        statusEl.text = status

    def _series_update_citation(self, title):
        citationEl = self.tree.xpath('gmd:identificationInfo/*/gmd:citation/*',
                                     namespaces=self.ns)[0]
        titleEl = citationEl.xpath('gmd:title/gco:CharacterString', namespaces=self.ns)[0]
        #titleEl.text = productSettings.iResourceTitle
        titleEl.text = title

    def _series_change_linkage(self):
        self.update_element('linkage', 'http://www.geoland2.eu/portal/service/ListService.do?serviceCategoryId=CA80C981')

    def _series_update_uuid(self, uuid):
        elements = [
                self.tree.xpath('gmd:fileIdentifier/gco:CharacterString', 
                                namespaces=self.ns)[0],
                self.tree.xpath('gmd:identificationInfo/*/gmd:citation/*/'\
                                'gmd:identifier/*/gmd:code/'\
                                'gco:CharacterString', 
                                namespaces=self.ns)[0],
        ]
        for el in elements:
            el.text = uuid

    def _series_get_quicklook(self):
        fileNameEl = self.tree.xpath('gmd:identificationInfo/*/'\
                                     'gmd:graphicOverview/*/'\
                                     'gmd:fileName/gco:CharacterString',
                                     namespaces=self.ns)[0]
        #filename is an URL that should mimic the regex in operations.urls.py
        baseURL = ss.WebServer.objects.get().public_URL
        url = '%s/operations/products/%s/seriesquicklook' % \
                (baseURL, self.product.short_name)
        fileNameEl.text = url

    def _series_apply_global_coordinates(self):
        self.update_element('westLongitude', '-180.00')
        self.update_element('eastLongitude', '180.00')
        self.update_element('southLatitude', '80.00')
        self.update_element('northLatitude', '-70.00')

    def _series_remove_unused_elements(self):
        root = self.tree.getroot()
        elements = [
            root.xpath('gmd:parentIdentifier', 
                                      namespaces=self.ns),
            root.xpath('gmd:spatialRepresentationInfo', 
                                      namespaces=self.ns),
            root.xpath('gmd:contentInfo', 
                                      namespaces=self.ns),
        ]
        for els in elements:
            for el in els:
                root.remove(el)

    def _series_update_hierarchy(self, value):
        elements = [
            self.tree.getroot().xpath('gmd:hierarchyLevel/gmd:MD_ScopeCode', 
                                      namespaces=self.ns)[0],
            self.tree.getroot().xpath('gmd:identificationInfo/*/'\
                                      'gmd:resourceMaintenance/*/'\
                                      'gmd:updateScope/gmd:MD_ScopeCode', 
                                      namespaces=self.ns)[0],
            self.tree.getroot().xpath('gmd:dataQualityInfo/*/'\
                                      'gmd:scope/*/'\
                                      'gmd:level/gmd:MD_ScopeCode', 
                                      namespaces=self.ns)[0],
        ]
        for el in elements:
            el.attrib['codeList'] = 'http://standards.iso.org/ittf/'\
                'PubliclyAvailableStandards/ISO_19139_Schemas/resources/'\
                'Codelist/ML_gmxCodelists.xml#MD_ScopeCode'
            el.attrib['codeListValue'] = value
            el.text = value

    def _apply_linkage(self, tileName, product):
        baseURL = ss.WebServer.objects.get().public_URL
        ts = self.timeslot.strftime('%Y%m%d%H%M')
        vito_sdi_url = 'http://web.vgt.vito.be/download_g2.php?'
        url = '%s/operations/products/%s/%s/%s/product' % \
                (baseURL, product.short_name, tileName, ts)
        vito_url = '%sfile=&path=%s&serviceid=%s' % \
                   (vito_sdi_url, url, product.sdi_service_id)
        self.update_element('linkage', vito_url)

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
        mdContEl = etree.SubElement(
            contentTypeEl, 
            '{%s}MD_CoverageContentTypeCode' % self.ns['gmd']
        )
        contTypeAttr = mdContEl.attrib
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
                                           unit=dataset.unit, 
                                           bitDepth=bitDepth, 
                                           scaleFactor=scaleFactor, 
                                           offset=offset)

    def _apply_content_info_dimension_physical_value(self, parent, dataset):
        seqIDName = 'Physical Value'
        seqIDType = 'value type'
        descriptor = dataset.name
        maxVal = str(dataset.max_value)
        minVal = str(dataset.min_value)
        #units are missing
        self._apply_content_info_dimension(parent, seqIDName, seqIDType,
                                           descriptor, maxVal, minVal, 
                                           unit=dataset.unit)

    def _apply_content_info_dimension_invalid(self, parent, dataset):
        seqIDName = 'Invalid'
        seqIDType = 'flag type'
        descriptor = 'Invalid'
        maxVal = str(dataset.missingValue)
        minVal = str(dataset.missingValue)
        bitDepth = str(dataset.bit_depth)
        self._apply_content_info_dimension(parent, seqIDName, seqIDType,
                                           descriptor, maxVal, minVal, 
                                           unit=dataset.unit, 
                                           bitDepth=bitDepth)

    def _apply_content_info_dimension(self, parent, seqIDName, seqIDType, 
                                      descriptor, maxVal, minVal, unit=None,
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
        if unit is not None:
            unitEl = etree.SubElement(bandEl, '{%s}units' % \
                                      self.ns['gmd'])
            unitGco = etree.SubElement(unitEl, '{%s}CharacterString' % \
                                       self.ns['gco'])
            unitGco.text = unit
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
        otherDetailsEl.text = productSettings.user_manual

    def _apply_abstract(self, abstract_text):
        identInfoEl = self.tree.xpath('gmd:identificationInfo/gmd:MD_DataIdentification', namespaces=self.ns)[0]
        # first remove any abstract that may be present
        abstracts = identInfoEl.xpath('gmd:abstract', namespaces=self.ns)
        for a in abstracts:
            identInfoEl.remove(a)

        abstractEl = etree.SubElement(identInfoEl, '{%s}abstract' % self.ns['gmd'])
        charStringEl = etree.SubElement(abstractEl, '{%s}CharacterString' % self.ns['gco'])
        charStringEl.text = abstract_text

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
        theTimeslot = timeslot.strftime('%Y-%m-%dT%H:%M:%SZ')
        beginEl.text = theTimeslot
        endEl = parentEl.xpath('gml:endPosition', namespaces=self.ns)[0]
        endEl.text = theTimeslot

    def csw_login(self, login_url, username, password):
        headers_auth = {
            "Content-type": "application/x-www-form-urlencoded", 
            "Accept": "text/plain"
        }
        data = urllib.urlencode({"username": username, "password": password})
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
        return opener

    def csw_logout(self, logout_url):
        logoutReq = urllib2.Request(logout_url)
        response = urllib2.urlopen(logoutReq)
        #self.logger.debug(response.read())

    def _re_order(self, parent_element, order_dict):
        re_order = []
        for el in parent_element:
            the_index = None
            for k, v in order_dict.iteritems():
                full_tag = '{%s}%s' % (self.ns.get('gmd'), v)
                if full_tag == el.tag:
                    the_index = k
            re_order.append((el, the_index))
        a = sorted(re_order, key=itemgetter(1))
        for tup in a:
            parent_element.append(tup[0])
