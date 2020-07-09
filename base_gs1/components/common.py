# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import xmlschema

from odoo import modules

from odoo.addons.component.core import AbstractComponent

BUSINESS_DOC_HEADER_URI = (
    "http://www.unece.org/cefact/namespaces/StandardBusinessDocumentHeader"
)
XSI_URI = "http://www.w3.org/2001/XMLSchema-instance"


class GS1Mixin(AbstractComponent):
    """Abstract component mixin to generate GS1 compliant XML files."""

    _name = "gs1.mixin"
    _collection = "gs1.backend"
    # Enable validation of work context attributes
    _work_context_validate_attrs = []
    # Module containing XSD schema for validation
    _xsd_schema_module = "base_gs1"
    # Path to static file in a module containing XSD schema for validation
    _xsd_schema_path = None

    def __init__(self, work_context):
        super().__init__(work_context)
        for key in self._work_context_validate_attrs:
            if not hasattr(work_context, key):
                raise AttributeError(f"`{key}` is required for this component!")

    @property
    def _xmlns(self):
        """Declare mapping of common namespace prefix and URI.

        Not mandatory but useful for:

        * documenting which NS hare handle by the component.
        * reuse long common URI where needed.

        It also helps to add namespace on non root elements when needed
        (see business header tests).
        """
        return {
            "sh": BUSINESS_DOC_HEADER_URI,
            "xsi": XSI_URI,
        }

    def _get_xsd_schema(self):
        """Lookup for XSD schema via `_xsd_schema_path` attributed."""
        return modules.get_resource_path(self._xsd_schema_module, self._xsd_schema_path)

    def validate_schema(self, xml_content, xsd_full_path=None, raise_on_fail=False):
        """Validate XML content against XSD schema.

        Raises `XMLSchemaValidationError` if `raise_on_fail` is True.

        :param xml_content: str containing xml data to validate
        :param xsd_full_path: overrides `self._xsd_schema_path`
        :raise_on_fail: turn on/off validation error exception on fail

        :return:
            * None if validation is ok
            * error string if `raise_on_fail` is False
        """
        if not self._xsd_schema_path and not xsd_full_path:
            raise AttributeError("No XSD schema provided!")

        xsd_full_path = xsd_full_path or self._get_xsd_schema()
        if not xsd_full_path:
            raise FileNotFoundError("XSD schema not found at {}".format(xsd_full_path))
        schema = xmlschema.XMLSchema(xsd_full_path)
        try:
            return schema.validate(xml_content)
        except xmlschema.validators.exceptions.XMLSchemaValidationError as err:
            if raise_on_fail:
                raise
            return str(err)
