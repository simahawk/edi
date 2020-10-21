# Copyright 2020 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import base64
import functools

import mock
from freezegun import freeze_time

from .common import EDIBackendCommonTestCase

MOD_PATH = "odoo.addons.storage_backend_sftp.components.sftp_adapter"
PARAMIKO_PATH = MOD_PATH + ".paramiko"


@freeze_time("2020-10-21 10:30:00")
class TestEDIBackendOutput(EDIBackendCommonTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.filedata = base64.b64encode(b"This is a simple file")
        vals = {
            "model": cls.partner._name,
            "res_id": cls.partner.id,
            "exchange_file": cls.filedata,
        }
        cls.record = cls.backend.create_record("test_csv_output", vals)

        cls.fakepath = "/tmp/{}".format(cls._filename(cls))
        with open(cls.fakepath, "w+b") as fakefile:
            fakefile.write(b"filecontent")
        cls.fakepath_error = "/tmp/{}.error".format(cls._filename(cls))
        with open(cls.fakepath_error, "w+b") as fakefile:
            fakefile.write(b"ERROR XYZ: line 2 broken on bla bla")

    def setUp(self):
        super().setUp()
        self._storage_backend_calls = []

    def _filename(self, record=None):
        record = record or self.record
        return record.exchange_filename

    def _file_fullpath(self, state, record=None):
        record = record or self.record
        fname = self._filename(record)
        if state == "error-report":
            # Exception as we read from the same path but w/ error suffix
            state = "error"
            fname += ".error"
        return (
            self.backend._remote_file_path(record.direction, state, fname)
        ).as_posix()

    def _mocked_backend_get(self, mocked_paths, path, **kwargs):
        self._storage_backend_calls.append(path)
        if mocked_paths.get(path):
            with open(mocked_paths.get(path), "rb") as remote_file:
                return remote_file.read()
        raise FileNotFoundError()

    def _mocked_backend_add(self, path, data, **kwargs):
        self._storage_backend_calls.append(path)

    def _mock_storage_backend_get(self, mocked_paths):
        mock_path = "odoo.addons.storage_backend.models.storage_backend.StorageBackend"
        mocked = functools.partial(self._mocked_backend_get, mocked_paths)
        return mock.patch(mock_path + "._get_bin_data", mocked)

    def _mock_storage_backend_add(self):
        mock_path = "odoo.addons.storage_backend.models.storage_backend.StorageBackend"
        return mock.patch(mock_path + "._add_bin_data", self._mocked_backend_add)

    def _test_result(
        self,
        record,
        expected_state,
        expected_msg=None,
        state_paths=None,
        attachment=False,
        error_msg=None,
    ):
        state_paths = state_paths or ("done", "pending", "error")
        # Paths will be something like:
        # [
        # 'demo_out/pending/$filename.csv',
        # 'demo_out/pending/$filename.csv',
        # 'demo_out/error/$filename.csv',
        # ]
        for state in state_paths:
            path = self._file_fullpath(state, record=record)
            self.assertIn(path, self._storage_backend_calls)
        self.assertEqual(record.edi_exchange_state, expected_state)
        if error_msg:
            self.assertEqual(record.exchange_error, error_msg)
        if expected_msg:
            self.assertEqual(len(record.record_id.message_ids), 1)
            msg = record.record_id.message_ids[0]
            self.assertIn(expected_msg, msg.body)
            if attachment:
                self.assertEqual(msg.attachment_ids[0].name, self._filename())

    def _test_send(self, record, mocked_paths=None):
        with self._mock_storage_backend_add():
            if mocked_paths:
                with self._mock_storage_backend_get(mocked_paths):
                    self.backend.exchange_send(record)
            else:
                self.backend.exchange_send(record)

    def _test_send_cron(self, mocked_paths):
        with self._mock_storage_backend_get(mocked_paths):
            self.backend._cron_check_exchange_sync()

    def test_export_file_sent(self):
        """Send, no errors."""
        mocked_paths = {self._file_fullpath("pending"): self.fakepath}
        self._test_send(self.record, mocked_paths=mocked_paths)
        self._test_result(
            self.record, "output_sent", expected_msg=self.record._exchange_sent_msg(),
        )

    def test_export_file_already_done(self):
        """Already sent, successfully."""
        mocked_paths = {self._file_fullpath("done"): self.fakepath}
        self._test_send(self.record, mocked_paths=mocked_paths)
        # As we simulate to find a file in `done` folder,
        # we should get the final good state
        # and only one call to ftp
        self._test_result(
            self.record,
            "output_sent_and_processed",
            expected_msg=self.record._exchange_processed_ok_msg(),
            state_paths=("done",),
        )

    def test_export_file_sent_and_error(self):
        """Already sent, error process."""
        self.record.edi_exchange_state = "output_sent"
        mocked_paths = {
            self._file_fullpath("error"): self.fakepath,
            self._file_fullpath("error-report"): self.fakepath_error,
        }
        self._test_send(self.record, mocked_paths)
        # As we simulate to find a file in `error` folder,
        # we should get a call for: done, error and then the read of the report.
        self._test_result(
            self.record,
            "output_sent_and_error",
            expected_msg=self.record._exchange_processed_ko_msg(),
            state_paths=("done", "error", "error-report"),
            error_msg="ERROR XYZ: line 2 broken on bla bla",
        )

    def test_export_file_cron(self):
        """Already sent, update the state via cron."""
        self.record.edi_exchange_state = "output_sent"
        rec1 = self.record
        partner2 = self.env.ref("base.res_partner_2")
        partner3 = self.env.ref("base.res_partner_3")
        rec2 = self.record.copy(
            {
                "model": partner2._name,
                "res_id": partner2.id,
                "exchange_filename": "rec2.csv",
            }
        )
        rec3 = self.record.copy(
            {
                "model": partner3._name,
                "res_id": partner3.id,
                "exchange_filename": "rec3.csv",
                "edi_exchange_state": "output_sent_and_error",
            }
        )
        mocked_paths = {
            self._file_fullpath("done", record=rec1): self.fakepath,
            self._file_fullpath("error", record=rec2): self.fakepath,
            self._file_fullpath("error-report", record=rec2): self.fakepath_error,
            self._file_fullpath("done", record=rec3): self.fakepath,
        }
        self._test_send_cron(mocked_paths)
        self._test_result(
            rec1,
            "output_sent_and_processed",
            expected_msg=rec1._exchange_processed_ok_msg(),
            state_paths=("done",),
        )
        self._test_result(
            rec2,
            "output_sent_and_error",
            expected_msg=rec2._exchange_processed_ko_msg(),
            state_paths=("done", "error", "error-report"),
            error_msg="ERROR XYZ: line 2 broken on bla bla",
        )
        self._test_result(
            rec3,
            "output_sent_and_processed",
            expected_msg=rec3._exchange_processed_ok_msg(),
            state_paths=("done",),
        )
