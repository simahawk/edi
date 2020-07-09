# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# import base64
import logging

from odoo import _, api, fields, models

from odoo.addons.http_routing.models.ir_http import slugify

_logger = logging.getLogger(__name__)


class GS1Backend(models.Model):
    _inherit = "gs1.backend"

    @api.model
    def get_backend_by_delivery(self, delivery):
        """Retrieve GS1 backend by given delivery order (stock.picking).

        You might have different LSP and pick up the right backend
        based on the delivery order.
        """
        # TODO: how do we handle this?
        # We could have a wizard of some special fields to set by record
        # which backend to use.
        return self.env.ref("base_gs1.default_gs1_backend")

    def send_wh_inbound_instruction(self, delivery):
        """Generate an Inbound Instruction for given delivery and send it.

        :param delivery: stock.picking browse record.
        """
        comp_usage = "gs1.warehousingInboundInstructionMessage"
        handler = self._get_component(
            work_ctx=dict(
                sender=self.env.company.partner_id,
                receiver=delivery.partner_id,
                record=delivery,
            ),
            usage=comp_usage,
        )
        file_content = handler.generate_xml()
        filename = self._inbound_instruction_filename(delivery)
        self._send(file_content, filename)

        attachments = [(filename, file_content)]
        delivery.message_post(
            body=_("Inbound Instruction sent"), attachments=attachments
        )

    def _inbound_instruction_filename(self, delivery):
        dt = fields.Date.to_string(fields.Date.today())
        name = slugify(self.name).upper()
        return f"InboundInstruction-{dt}-{name}.xml"

    # TODO: use job
    def _send(self, file_content, filename):
        # TODO: check storage
        # path = "inbound/" + filename
        # storage_backend = self.storage_id
        # storage_backend._add_b64_data(path, base64.b64encode(file_content))
        pass
