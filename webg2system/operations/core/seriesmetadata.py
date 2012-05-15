import logging
from uuid import uuid1

from lxml import etree

class SeriesMetadataGenerator(object):

    def __init__(self, template, product):
        self.logger = logging.getLogger(
                '.'.join((__name__, self.__class__.__name__)))
        self.product = product
        self.tree = etree.parse(template)
        self.ns = self.tree.getroot().nsmap.copy()
        self.uuid = str(uuid1())

    def update_elements(self):
        self._update_file_identifier()
        self._update_language()
        self._update_hierarchy_level():
        self._update_contact():
        self._update_date_stamp():
        self._update_metadata_standard_name():
        self._update_metadata_standard_version():
        self._update_identification_info():
        self._update_distribution_info():


    def _update_file_identifier(self):
        el = self.tree.xpath('gmd:fileIdentifier/gco:CharacterString')[0]
        el.text = self.uuid

    def _update_language(self):
        # no update needed
        return

    def _update_hierarchy_level(self):
        # no update needed
        return

    def _update_contact(self, collaborator_settings):
        topEl = self.tree.xpath('gmd:contact/gmd:CI_ResponsibleParty', 
                                 namespaces=self.ns)[0]
        orgName = topEl.xpath('gmd:organisationName/gco:CharacterString',
                              namespaces=self.ns)[0]
        orgName.text = collaborator_settings.organization.name
        
    def _update_date_stamp(self):
        return

    def _update_metadata_standard_name(self):
        # no update needed
        return

    def _update_metadata_standard_version(self):
        # no update needed
        return

    def _update_identification_info(self):
        return

    def _update_distribution_info(self):
        return
