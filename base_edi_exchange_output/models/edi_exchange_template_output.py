# Copyright 2020 ACSONE SA
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class EDIExchangeOutputTemplate(models.Model):
    """Define an output template to generate outgoing files
    """

    _name = "edi.exchange.template.output"
    _description = "EDI Exchange Output Template"

    name = fields.Char(required=True)
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

    def generate_output(self, record, **kw):
        tmpl = self.template_id
        values = self._get_render_values(record, **kw)
        return tmpl.render(values)

    def _get_render_values(self, record, **kw):
        values = {
            "exchange_record": record,
            "record": record.record_id,
            "backend": record.backend_id,
            "template": self,
        }
        values.update(kw)
        return values

    def get_template_for_record(self, record, key=None):
        if key:
            # by key
            domain = [("key", "=", key)]
        else:
            # by type
            domain = [("type_id", "=", record.type_id.id)]
        # TODO: if not type is given filter by backend
        # domain.append(("backend_id", "=", record.backend_id.id))
        return self.search(domain, limit=1)
