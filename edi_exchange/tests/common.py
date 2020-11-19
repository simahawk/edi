# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os

from odoo.tests.common import SavepointCase, tagged

# from odoo.addons.component.tests.common import ComponentMixin


@tagged("-at_install", "post_install")
class EDIBackendCommonTestCase(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context, tracking_disable=True, test_queue_job_no_delay=True
            )
        )
        cls.backend = cls._get_backend()
        cls.exchange_type_in = cls._create_exchange_type(
            name="Test CSV input",
            code="test_csv_input",
            direction="input",
            exchange_file_ext="csv",
            exchange_filename_pattern="{record.ref}-{type.code}-{dt}",
        )
        cls.exchange_type_out = cls._create_exchange_type(
            name="Test CSV output",
            code="test_csv_output",
            direction="output",
            exchange_file_ext="csv",
            exchange_filename_pattern="{record.ref}-{type.code}-{dt}",
        )
        cls.partner = cls.env.ref("base.res_partner_1")
        cls.partner.ref = "EDI_EXC_TEST"

    def read_test_file(self, filename):
        path = os.path.join(os.path.dirname(__file__), "examples", filename)
        with open(path, "r") as thefile:
            return thefile.read()

    @classmethod
    def _get_backend(cls):
        return cls.env.ref("edi_exchange.demo_edi_backend")

    @classmethod
    def _create_exchange_type(cls, **kw):
        model = cls.env["edi.exchange.type"]
        vals = {
            "name": "Test CSV exchange",
            "backend_id": cls.backend.id,
            "backend_type_id": cls.backend.backend_type_id.id,
        }
        vals.update(kw)
        return model.create(vals)


# class BaseTestCase(SavepointCase, ComponentMixin):
#     @classmethod
#     def setUpClass(cls):
#         super().setUpClass()
#         cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
#         cls.setUpComponent()
#         cls.backend = cls._get_backend()
