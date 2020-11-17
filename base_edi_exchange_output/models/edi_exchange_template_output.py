# Copyright 2020 ACSONE SA
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime
import logging
import time

import dateutil
import pytz
from lxml import etree

from odoo import fields, models
from odoo.tools import pycompat
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class EDIExchangeOutputTemplate(models.Model):
    """Define an output template to generate outgoing files
    """

    _name = "edi.exchange.template.output"
    _description = "EDI Exchange Output Template"

    name = fields.Char(required=True)
    # TODO: make unique, autocompute slugified name
    code = fields.Char(required=True)
    output_type = fields.Char(default="xml")
    # TODO: compute from type_id.backend when passed
    # compute selection from available backends
    backend_type = fields.Char()
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
    type_id = fields.Many2one(
        string="EDI Exchange type",
        comodel_name="edi.exchange.type",
        ondelete="cascade",
        auto_join=True,
    )
    backend_id = fields.Many2one(
        comodel_name="edi.backend",
        ondelete="cascade",
        # TODO: default to type_id if given, validate otherwise
    )
    # TODO: add default content w/ comment on what you can use
    code_snippet = fields.Text()

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
        }
        if self.code_snippet:
            values.update(self._evaluate_code_snippet(**values))
        values.update(kw)
        return values

    # TODO: need a way to retrieve it by backend type and render the template
    # from within another template
    def get_template_for_record(self, record, code=None):
        if code:
            domain = [("code", "=", code)]
        else:
            domain = [("type_id", "=", record.type_id.id)]
        # TODO: if not type is given filter by backend
        # Eg: business header is a generic one and is not tied only to a specific type
        # domain.append(("backend_id", "=", record.backend_id.id))
        return self.search(domain, limit=1)

    @staticmethod
    def _utc_now():
        return datetime.datetime.utcnow().isoformat()

    @staticmethod
    def _date_to_string(dt, utc=True):
        if utc:
            dt = dt.astimezone(pytz.UTC)
        return fields.Date.to_string(dt)

    def _get_code_snippet_eval_context(self):
        """ Prepare the context used when evaluating python code
            :returns: dict -- evaluation context given to safe_eval
        """
        return {
            "datetime": datetime,
            "dateutil": dateutil,
            "time": time,
            "uid": self.env.uid,
            "user": self.env.user,
            "template": self,
        }

    def _evaluate_code_snippet(self, **render_values):
        eval_ctx = dict(render_values, **self._get_code_snippet_eval_context())
        safe_eval(self.code_snippet, eval_ctx, mode="exec", nocopy=True)
        result = eval_ctx.get("result", {})
        if not isinstance(result, dict):
            _logger.error("code_snippet should return a dict into `result`")
            return {}
        return result

    def _post_process_output(self, output):
        if self.output_type == "xml":
            # TODO: lookup for components to handle this dynamically
            return self._cleanup_nswrapper(output)
        return output

    def _cleanup_nswrapper(self, xml_content):
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
