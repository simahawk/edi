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
        delegate=True,
        ondelete="cascade",
    )
    type_id = fields.Many2one(
        string="EDI Exchange type",
        comodel_name="edi.exchange.type",
        required=True,
        ondelete="cascade",
        auto_join=True,
    )
    backend_id = fields.Many2one(
        comodel_name="edi.backend", related="type_id.backend_id",
    )

    def generate_output(self, record):
        tmpl = self.template_id
        values = self._get_render_values(record)
        return tmpl.render(values)

    def _get_render_values(self, record):
        values = {
            "exchange_record": record,
            "record": record.record_id,
            "backend": record.backend_id,
        }
        return values
