# Copyright 2020 ACSONE SA
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class GS1Backend(models.Model):
    _name = "gs1.backend"
    _inherit = [
        "collection.base",
        # TODO:
        # "server.env.mixin"
    ]
    _description = "GS1 Backend"

    name = fields.Char(required=True)
    tech_name = fields.Char(required=True)
    # TODO: inherits from storage.backend instead?
    storage_id = fields.Many2one(
        string="Storage backend",
        comodel_name="storage.backend",
        help="Storage for in-out files",
    )
    lsp_partner_id = fields.Many2one(
        string="Logistic Services Provider (LSP)",
        comodel_name="res.partner",
        domain=[("is_lsp", "=", True)],
    )

    # TODO
    # @property
    # def _server_env_fields(self):
    #     return {}

    def _get_component(self, work_ctx=None, **kw):
        work_ctx = work_ctx or {}
        with self.work_on(self._name, **work_ctx) as work:
            return work.component(**kw)
