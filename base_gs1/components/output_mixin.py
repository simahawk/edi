# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import datetime

import pytz

from odoo import fields

from odoo.addons.component.core import AbstractComponent

from ..xmler import dict2xml

BUSINESS_DOC_HEADER_URI = (
    "http://www.unece.org/cefact/namespaces/StandardBusinessDocumentHeader"
)
XSI_URI = "http://www.w3.org/2001/XMLSchema-instance"


def _apply_on_dict(data, ns):
    """Recursively add add a namespace to given data dict."""
    res = {}
    ns_dict = {"@ns": ns} if ns else {}
    for k, v in data.items():
        if k.startswith("@"):
            res[k] = v
            continue
        if isinstance(v, dict):
            v = _apply_on_dict(v, ns)
        elif isinstance(v, (list, tuple, set)):
            v = {"@value": _apply_on_iterable(v, ns)}
        elif isinstance(v, (str, int, float)):
            v = {"@value": str(v)}
        res[k] = dict(**ns_dict, **v)
    return res


def _apply_on_iterable(iterable, ns):
    """Recursively add add a namespace to given iterable data."""
    return [_apply_on_dict(item, ns) for item in iterable]


class GS1OutputMixin(AbstractComponent):
    """Abstract component mixin to generate GS1 compliant XML files."""

    _name = "gs1.output.mixin"
    _inherit = "gs1.mixin"
    # Path to static file in a module containing XSD schema for validation
    _xsd_schema_path = None
    # Enable validation of work context attributes
    _work_context_validate_attrs = ["record"]

    @property
    def record(self):
        return getattr(self.work, "record", None)

    def _apply_ns_and_value(self, data, ns):
        """Apply namespace and handle value keys on given data dict."""
        res = {}
        if isinstance(data, dict):
            res = _apply_on_dict(data, ns)
        elif isinstance(data, (list, tuple, set)):
            res = _apply_on_iterable(data, ns)
        return res

    def _generate_xml(self, data):
        """Produce the final XML based on give data dict."""
        return dict2xml(data)

    def generate_data(self):
        """Generate and return data for the final XML.

        Override this in specific GS1 component.

        :return: dict
        """
        raise NotImplementedError()

    def generate_xml(self):
        """Generate and return XML content.

        :return: str
        """
        data = self.generate_data()
        return self._generate_xml(data)

    # helper methods
    @staticmethod
    def _utc_now():
        return datetime.datetime.utcnow().isoformat()

    @staticmethod
    def date_to_string(dt, utc=True):
        if utc:
            dt = dt.astimezone(pytz.UTC)
        return fields.Date.to_string(dt)
