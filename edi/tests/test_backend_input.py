# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

import mock
import psycopg2
from freezegun import freeze_time

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import tagged
from odoo.tools import mute_logger

from .common import EDIBackendCommonTestCase


@tagged("-at_install", "post_install")
class EDIBackendTestCase(EDIBackendCommonTestCase):

    def test_process_record(self):
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
            "edi_exchange_state": "input_received",
            "exchange_file": base64.b64encode(b"1234"),
        }
        record = self.backend.create_record("test_csv_input", vals)
        with mock.patch.object(type(self.backend), "_exchange_process") as patch:
            patch.return_value = "AAA"
            self.backend.exchange_process(record)
            patch.assert_called()
        self.assertEqual(record.edi_exchange_state, "input_processed")

    def test_process_record_with_error(self):
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
            "edi_exchange_state": "input_received",
            "exchange_file": base64.b64encode(b"1234"),
        }
        record = self.backend.create_record("test_csv_input", vals)
        self.backend.exchange_process(record)
        self.assertEqual(record.edi_exchange_state, "input_processed_error")

    def test_process_no_file_record(self):
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
            "edi_exchange_state": "input_received",
        }
        record = self.backend.create_record("test_csv_input", vals)
        with mock.patch.object(type(self.backend), "_exchange_process") as patch:
            patch.return_value = "AAA"
            with self.assertRaises(UserError):
                self.backend.exchange_process(record)
            patch.assert_not_called()

    def test_process_outbound_record(self):
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
        }
        record = self.backend.create_record("test_csv_output", vals)
        with mock.patch.object(type(self.backend), "_exchange_process") as patch:
            patch.return_value = "AAA"
            with self.assertRaises(UserError):
                self.backend.exchange_process(record)
            patch.assert_not_called()
