# Copyright 2020 ACSONE SA
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class EDIExchangeRecord(models.Model):
    """Define an exchange record.
    """

    _name = "edi.exchange.record"
    _inherit = "edi.exchange.mixin"
    _description = "EDI exchange Record"
