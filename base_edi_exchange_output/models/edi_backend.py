# Copyright 2020 ACSONE SA
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, tools


class EDIBackend(models.Model):
    _inherit = "edi.backend"

    def generate_output(self, record):
        tmpl = self._get_template(record)
        if tmpl:
            return tools.pycompat.to_text(tmpl.generate_output(record))
        # TODO: lookup for specific component
        return None

    def _get_template(self, record):
        return self.env["edi.exchange.template.output"].get_template_for_record(record)
