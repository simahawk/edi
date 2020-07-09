# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def action_send_wh_inbound_instruction(self):
        backend = self.env["gs1.backend"].get_backend_by_delivery(self)
        backend.send_wh_inbound_instruction(self)
