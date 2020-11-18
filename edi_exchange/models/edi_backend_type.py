# Copyright 2020 ACSONE SA
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class EDIBackendType(models.Model):
    """Define a kind of backend.
    """

    _name = "edi.backend.type"
    _description = "EDI Backend Type"

    name = fields.Char(required=True)
    # TODO: make it unique
    code = fields.Char(required=True)
