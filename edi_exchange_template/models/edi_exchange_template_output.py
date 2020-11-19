# Copyright 2020 ACSONE SA
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from lxml import etree

from odoo import fields, models
from odoo.tools import pycompat

_logger = logging.getLogger(__name__)


class EDIExchangeOutputTemplate(models.Model):
    """Define an output template to generate outgoing files
    """

    _name = "edi.exchange.template.output"
    _inherit = "edi.exchange.template.mixin"
    _description = "EDI Exchange Output Template"

    output_type = fields.Char(required=True)
    template_id = fields.Many2one(
        string="Qweb Template",
        comodel_name="ir.ui.view",
        required=True,
        ondelete="restrict",
    )
    template_arch = fields.Text(
        string="QWeb arch", related="template_id.arch_db", readonly=False,
    )
    template_key = fields.Char(related="template_id.key")

    def generate_output(self, record, **kw):
        tmpl = self.template_id
        # TODO: validate render values (eg: sender/receiver are mandatory for BH)
        values = self._get_render_values(record, **kw)
        output = tmpl.render(values)
        return self._post_process_output(output)

    def _get_render_values(self, record, **kw):
        values = {
            "exchange_record": record,
            "record": record.record_id,
            "backend": record.backend_id,
            "template": self,
            "utc_now": self._utc_now,
            "date_to_string": self._date_to_string,
            "render_edi_template": self._render_template,
        }
        if self.code_snippet:
            values.update(self._evaluate_code_snippet(**values))
        values.update(kw)
        return values

    def _render_template(self, record, code, **kw):
        tmpl = self.get_template_for_record(record, code=code)
        return tmpl.generate_output(record, **kw)

    def _post_process_output(self, output):
        if self.output_type == "xml":
            # TODO: lookup for components to handle this dynamically
            return self._cleanup_nswrapper(output)
        return output

    def _cleanup_nswrapper(self, xml_content):
        if not (xml_content and xml_content.strip()):
            return xml_content
        root = etree.XML(xml_content)
        # deeper elements come after, keep the root element at the end (if any)
        for nswrapper in reversed(root.xpath("//nswrapper")):
            parent = nswrapper.getparent()
            if not parent:
                return "".join(
                    [
                        pycompat.to_text(etree.tostring(el))
                        for el in nswrapper.getchildren()
                    ]
                )
            parent.extend(nswrapper.getchildren())
            parent.remove(nswrapper)
        return etree.tostring(root)
