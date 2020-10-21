# Copyright 2020 ACSONE SA
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class EDIExchangeConsumerMixin(models.AbstractModel):
    """Common features for models relying on EDI exchange records.
    """

    _name = "edi.exchange.consumer.mixin"
    _description = "EDI exchange consumer mixin"

    # TODO: is this really needed?
    edi_exchange_record_ids = fields.Many2many(
        comodel_name="edi.exchange.record", compute="_compute_edi_exchange_record_ids",
    )

    def _compute_edi_exchange_record_ids(self):
        exchange_records = self.env["edi.exchange.record"].search(
            [("res_id", "in", self.ids), ("model", "=", self._name)]
        )
        for rec in self:
            rec.edi_exchange_record_ids = exchange_records.filtered(
                lambda x: x.res_id == rec.id
            )

    def _action_view_exchance_records(self, **kw):
        action = {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "edi.exchange.record",
            "domain": [("res_id", "in", self.ids), ("model", "=", self._name)],
            "context": {"search_default_group_by_type_id": 1},
        }
        action.update(kw)
        return self._action_view_records()

    def action_view_records(self):
        self.ensure_one()
        return self._action_view_records()
