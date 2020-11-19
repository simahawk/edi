# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import xmlschema

from odoo import modules

from odoo.addons.component.core import AbstractComponent


class EDIExchangeInfoMixin(AbstractComponent):
    """Abstract component mixin provide info for exchanges."""

    _name = "edi.info.provider.mixin"
    _collection = "edi.backend"
    # Enable validation of work context attributes
    _work_context_validate_attrs = []

    def __init__(self, work_context):
        super().__init__(work_context)
        for key in self._work_context_validate_attrs:
            if not hasattr(work_context, key):
                raise AttributeError(f"`{key}` is required for this component!")

    # TODO: adapt
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
