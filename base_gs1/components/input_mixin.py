# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import io
from contextlib import closing

import xmlschema

from odoo.addons.component.core import AbstractComponent

# from lxml import etree


class GS1InputMixin(AbstractComponent):
    """Abstract component mixin to generate GS1 compliant XML files."""

    _name = "gs1.input.mixin"
    _inherit = "gs1.mixin"

    def _parse_xml(self, file_obj, **kw):
        """Read xml_content and return a data dict.

        :param file_obj: file obj of XML file
        """
        # TODO: we could use bare lxml like
        # etree.fromstring(file_content.encode())
        xsd_full_path = self._get_xsd_schema()
        schema = xmlschema.XMLSchema(xsd_full_path)
        return schema.to_dict(file_obj, **kw)

    def parse_xml(self, file_content, **kw):
        """Read XML content.

        :param file_content: str of XML file
        :return: dict with final data
        """
        with closing(io.StringIO(file_content)) as fd:
            return self._parse_xml(fd)
