# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    voxel_sale_order_login_id = fields.Many2one(
        string="Sale Order login", comodel_name="voxel.login"
    )
