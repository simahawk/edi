# Copyright 2020 ACSONE SA
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from odoo import models, tools


class EDIBackend(models.Model):
    _inherit = "edi.backend"

    def generate_output(self, record, template_code=None, store=True, **kw):
        output = None
        tmpl = self._get_template(record, code=template_code)
        if tmpl:
            output = tmpl.generate_output(record, **kw)
        if output and store:
            if not isinstance(output, bytes):
                output = output.encode()
            record.exchange_file = base64.b64encode(output)
        # TODO: lookup for specific component
        return tools.pycompat.to_text(output)

    def _get_template(self, record, code=None):
        return self.env["edi.exchange.template.output"].get_template_for_record(
            record, code=code
        )
