# Copyright 2020 ACSONE SA
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, exceptions, fields, models

# from odoo.addons.base_sparse_field.models.fields import Serialized
# from odoo.addons.http_routing.models.ir_http import slugify

_logger = logging.getLogger(__name__)


class EDIExchangeMixin(models.AbstractModel):
    """Basic features for a record that tracks an exchange.
    """

    _name = "edi.exchange.mixin"
    _description = "EDI Exchange Mixin"
    _order = "exchanged_on desc"

    name = fields.Char(compute="_compute_name")
    type_id = fields.Many2one(
        string="EDI Exchange type",
        comodel_name="edi.exchange.type",
        required=True,
        ondelete="cascade",
        auto_join=True,
    )
    direction = fields.Selection(related="type_id.direction",)
    backend_id = fields.Many2one(
        comodel_name="edi.backend", related="type_id.backend_id",
    )
    model = fields.Char(index=True, required=True, readonly=True)
    res_id = fields.Many2oneReference(
        string="Record ID",
        index=True,
        required=True,
        readonly=True,
        model_field="model",
    )
    record_id = fields.Reference(
        selection="_reference_models", compute="_compute_record_id", readonly=True
    )
    exchange_file = fields.Binary(attachment=True)
    exchange_filename = fields.Char(
        compute="_compute_exchange_filename", readonly=False, store=True
    )
    exchanged_on = fields.Datetime(
        string="Exchanged on", readonly=True, help="Sent or received on this date."
    )
    ack_received = fields.Boolean(default=False)
    ack_received_on = fields.Datetime(string="Received on", readonly=True)
    ack_file = fields.Binary(attachment=True)
    edi_exchange_state = fields.Selection(
        string="Exchange state",
        readonly=True,
        default="new",
        selection=[
            ("new", "New"),
            # output exchange states
            ("output_not_sent", "Not sent"),
            ("output_error_on_send", "error on send"),
            ("output_sent", "Sent"),
            ("output_sent_and_processed", "Sent and processed"),
            ("output_sent_and_error", "Sent and error"),
            # input exchange states
            ("input_received", "Received"),
            ("input_read_error", "error on read"),
            ("input_processed", "Processed"),
            ("input_processed_error", "error on process"),
        ],
    )
    exchange_error = fields.Text(string="Exchange error", readonly=True)

    @api.depends("type_id.code", "model", "record_id")
    def _compute_name(self):
        for rec in self:
            rec.name = "{0.type_id.name} - {0.record_id.name}".format(rec)

    @api.depends("model", "res_id")
    def _compute_record_id(self):
        for rec in self:
            rec.record_id = "{},{}".format(rec.model, rec.res_id or 0)

    @api.model
    def _reference_models(self):
        models = self.env["ir.model"].sudo().search([])
        return [(model.model, model.name) for model in models]

    @api.depends("type_id", "model")
    def _compute_exchange_filename(self):
        for rec in self:
            if not rec.exchange_filename:
                rec.exchange_filename = rec.type_id._make_exchange_filename(rec)

    @api.constrains("edi_exchange_state")
    def _constrain_edi_exchange_state(self):
        for rec in self:
            if rec.edi_exchange_state == "new":
                continue
            if not rec.edi_exchange_state.startswith(rec.direction):
                raise exceptions.ValidationError(
                    _("Exchange state must respect direction!")
                )

    def name_get(self):
        result = []
        for rec in self:
            dt = fields.Datetime.to_string(rec.exchanged_on) if rec.exchanged_on else ""
            name = "[{}] {} {}".format(rec.type_id.name, rec.record_id.name, dt)
            result.append((rec.id, name))
        return result

    def _exchange_sent_msg(self):
        return _("File %s sent") % self.exchange_filename

    def _exchange_processed_ok_msg(self):
        return _("File %s processed successfully ") % self.exchange_filename

    def _exchange_processed_ko_msg(self):
        return _("File %s processed with errors") % self.exchange_filename

    def _exchange_send_error_msg(self):
        return _("An error happened while sending. Please check exchange record info.")

    def action_exchange(self):
        self.ensure_one()
        return self.backend_id._exchange_send(self)
