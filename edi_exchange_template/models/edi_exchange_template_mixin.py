# Copyright 2020 ACSONE SA
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime
import logging
import time

import dateutil
import pytz

from odoo import fields, models
from odoo.tools import DotDict
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class EDIExchangeTemplateMixin(models.AbstractModel):
    """Define a common ground for EDI exchange templates.
    """

    _name = "edi.exchange.template.mixin"
    _description = "EDI Exchange Output Mixin"

    name = fields.Char(required=True)
    # TODO: make unique, autocompute slugified name
    code = fields.Char(required=True)
    backend_type_id = fields.Many2one(
        string="EDI Backend type", comodel_name="edi.backend.type", ondelete="restrict",
    )
    type_id = fields.Many2one(
        string="EDI Exchange type",
        comodel_name="edi.exchange.type",
        ondelete="cascade",
        auto_join=True,
    )
    backend_id = fields.Many2one(
        comodel_name="edi.backend",
        ondelete="cascade",
        # TODO: default to type_id if given, validate otherwise
    )
    # TODO: add default content w/ comment on what you can use
    code_snippet = fields.Text()

    # TODO: need a way to retrieve it by backend type and render the template
    # from within another template
    def get_template_for_record(self, record, code=None):
        if code:
            domain = [("code", "=", code)]
        else:
            domain = [("type_id", "=", record.type_id.id)]
        # TODO: if not type is given filter by backend
        # Eg: business header is a generic one and is not tied only to a specific type
        # domain.append(("backend_id", "=", record.backend_id.id))
        return self.search(domain, limit=1)

    @staticmethod
    def _utc_now():
        return datetime.datetime.utcnow().isoformat()

    @staticmethod
    def _date_to_string(dt, utc=True):
        if utc:
            dt = dt.astimezone(pytz.UTC)
        return fields.Date.to_string(dt)

    def _get_code_snippet_eval_context(self):
        """ Prepare the context used when evaluating python code
            :returns: dict -- evaluation context given to safe_eval
        """
        return {
            "datetime": datetime,
            "dateutil": dateutil,
            "time": time,
            "uid": self.env.uid,
            "user": self.env.user,
            "template": self,
            "DotDict": DotDict,
        }

    def _evaluate_code_snippet(self, **render_values):
        eval_ctx = dict(render_values, **self._get_code_snippet_eval_context())
        safe_eval(self.code_snippet, eval_ctx, mode="exec", nocopy=True)
        result = eval_ctx.get("result", {})
        if not isinstance(result, dict):
            _logger.error("code_snippet should return a dict into `result`")
            return {}
        return result

    def _get_validator(self, record):
        # TODO: lookup for validator (
        # can be to validate received file or generated file)
        pass

    def validate(self, record):
        pass
