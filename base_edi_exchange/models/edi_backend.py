# Copyright 2020 ACSONE SA
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from pathlib import PurePath

from odoo import _, exceptions, fields, models
from odoo.tools import pycompat

from odoo.addons.queue_job.job import job

_logger = logging.getLogger(__name__)


class EDIBackend(models.Model):
    """Generic backend to control EDI exchanges.

    We assume the exchanges happen it 2 ways (input, output)
    and we have a hierarchy of directory like:

        from_A_to_B
            |- pending
            |- done
            |- error
        from_B_to_A
            |- pending
            |- done
            |- error

    where A and B are the partners exchanging data and they are in turn
    sender and receiver and vice versa.
    """

    _name = "edi.backend"
    _description = "EDI Backend"
    _inherit = ["collection.base"]

    name = fields.Char(required=True)
    storage_id = fields.Many2one(
        string="Storage backend",
        comodel_name="storage.backend",
        help="Storage for in-out files",
        required=True,
        ondelete="restrict",
    )
    input_dir_pending = fields.Char(
        "Input pending directory", help="Path to folder for pending operations"
    )
    input_dir_done = fields.Char(
        "Input done directory", help="Path to folder for doneful operations"
    )
    input_dir_error = fields.Char(
        "Input error directory", help="Path to folder for error operations"
    )
    output_dir_pending = fields.Char(
        "Output pending directory", help="Path to folder for pending operations"
    )
    output_dir_done = fields.Char(
        "Output done directory", help="Path to folder for doneful operations"
    )
    output_dir_error = fields.Char(
        "Output error directory", help="Path to folder for error operations"
    )

    def _dir_by_state(self, direction, state):
        """Return remote directory path by direction and state.

        :param direction: string stating direction of the exchange
        :param state: string stating state of the exchange
        :return: PurePath object
        """
        assert direction in ("input", "output")
        assert state in ("pending", "done", "error")
        return PurePath((self[direction + "_dir_" + state] or "").strip())

    def _remote_file_path(self, direction, state, filename):
        """Return remote file path by direction and state for give filename.

        :param direction: string stating direction of the exchange
        :param state: string stating state of the exchange
        :param filename: string for file name
        :return: PurePath object
        """
        return self._dir_by_state(direction, state) / filename.strip("/ ")

    @property
    def exchange_record_model(self):
        return self.env["edi.exchange.record"]

    def create_record(self, type_code, values):
        """Create an exchange record for current backend.

        :param type_code: edi.exchange.type code
        :param values: edi.exchange.record values
        :return: edi.exchange.record record
        """
        self.ensure_one()
        export_type = self.env["edi.exchange.type"].search(
            [("code", "=", type_code), ("backend_id", "=", self.id)], limit=1
        )
        export_type.ensure_one()
        values["type_id"] = export_type.id
        return self.exchange_record_model.create(values)

    def _get_component(self, work_ctx=None, **kw):
        work_ctx = work_ctx or {}
        with self.work_on(self._name, **work_ctx) as work:
            return work.component(**kw)

    def _get_remote_file(self, record, state, filename=None, b64=False):
        """Get file for record in the given destination state.

        :param record: edi.exchange.record record
        :param state: string ("pending", "done", "error")
        :param filename: custom file name, record filename used by default
        :return: remote file content as string
        """
        filename = filename or record.exchange_filename
        path = self._remote_file_path(record.direction, state, filename)
        getter = self.storage_id._get_bin_data
        if b64:
            getter = self.storage_id._get_b64_data
        try:
            # FIXME: support match via pattern (eg: filename-prefix-*)
            # otherwise is impossible to retrieve input files and acks
            # (the date will never match)
            return getter(path.as_posix())
        except FileNotFoundError:
            return None

    def _exchange_output_check(self, record):
        """Check status output exchange and update state field.

        1. check if the file has been processed already (done)
        2. if yes, post message and exit
        3. if not, check for errors
        4. if no errors, return

        :param record: edi.exchange.record record
        :return: boolean
            * False if there's nothing else to be done
            * True if file still need action
        """
        if self._get_remote_file(record, "done"):
            _logger.info("%s done for: %s", (record.model, record.name))
            if not record.exchange_state == "output_sent_and_processed":
                record.exchange_state = "output_sent_and_processed"
                self._exchange_notify_record(
                    record, record._exchange_processed_ok_msg()
                )
                self._trigger_edi_event(record)
                if record.type_id.ack_needed:
                    self._exchange_output_handle_ack(record)
            return False

        error = self._get_remote_file(record, "error")
        if error:
            _logger.info("%s error for: %s", (record.model, record.name))
            # Assume a text file will be placed there w/ the same name and error suffix
            err_filename = record.exchange_filename + ".error"
            error_report = self._get_remote_file(record, "error", filename=err_filename)
            if record.exchange_state == "output_sent":
                record.update(
                    {
                        "exchange_state": "output_sent_and_error",
                        "exchange_error": pycompat.to_text(error_report),
                    }
                )
                self._exchange_notify_record(
                    record, record._exchange_processed_ko_msg(), level="error"
                )
                self._trigger_edi_event(record)
            return False
        return True

    def _exchange_output_handle_ack(self, record):
        ack_file = self._get_remote_file(
            record, "done", filename=record.ack_filename, b64=True
        )
        if ack_file:
            record.ack_file = ack_file
            self._trigger_edi_event(record, suffix="ack_received")
        else:
            self._exchange_notify_record(
                record,
                record._exchange_processed_ack_needed_missing_msg(),
                level="warning",
            )

    def _get_output_pending_records_domain(self):
        states = ("output_sent", "output_sent_and_error")
        return [
            ("type_id.direction", "=", "output"),
            ("exchange_state", "in", states),
        ]

    def _cron_check_output_exchange_sync(self):
        records = self.exchange_record_model.search(
            self._get_output_pending_records_domain()
        )
        _logger.info(
            "EDI Exchange output sync cron running. Found %d records to process.",
            len(records),
        )
        for rec in records:
            self._exchange_output_check(rec)

    @job(default_channel="root.edi.exchange.send")
    def exchange_send(self, record):
        """Send exchange file."""
        self.ensure_one()
        record.ensure_one()
        if not record.exchange_file:
            raise exceptions.UserError(
                _("Record ID=%d has no file to send!") % record.id
            )

        # In case already sent: skip sending and check the state
        check = self._exchange_output_check(record)
        if not check:
            return False
        return self._exchange_send(record)

    def _exchange_send(self, record):
        backend = self
        storage_backend = backend.storage_id
        direction = record.direction
        path = backend._remote_file_path(direction, "pending", record.exchange_filename)
        res = False
        error = message = state = None
        try:
            storage_backend._add_b64_data(path.as_posix(), record.exchange_file)
        # TODO: delegate this to generic storage backend
        # except paramiko.ssh_exception.AuthenticationException:
        #     # TODO this exc handling should be moved to sftp backend IMO
        #     error = _("Authentication error")
        #     state = "error_on_send"
        # TODO: catch other specific exceptions
        # this will swallow all the exceptions!
        except Exception as err:
            error = str(err)
            state = "output_error_on_send"
            message = record._exchange_send_error_msg()
            res = False
        else:
            message = record._exchange_sent_msg()
            error = None
            state = "output_sent"
            res = True
        finally:
            record.exchange_state = state
            record.exchange_error = error
            if message:
                backend._exchange_notify_record(record, message)
        return res

    def _exchange_notify_record(self, record, message, level="info"):
        """Attach exported file to current PO."""
        record.record_id.message_post_with_view(
            "base_edi_exchange.message_edi_exchange_link",
            values={
                "backend": self,
                "exchange_record": record,
                "message": message,
                "level": level,
            },
            subtype_id=self.env.ref("mail.mt_note").id,
        )

    def _cron_check_exchange_sync(self, check_in=True, check_out=True):
        if check_out:
            self._cron_check_output_exchange_sync()
        if check_in:
            self._cron_check_input_exchange_sync()

    def _get_input_pending_records_domain(self):
        states = ("input_pending", "input_processed_error")
        return [
            ("type_id.direction", "=", "input"),
            ("exchange_state", "in", states),
        ]

    def _cron_check_input_exchange_sync(self):
        records = self.exchange_record_model.search(
            self._get_input_pending_records_domain()
        )
        _logger.info(
            "EDI Exchange input sync cron running. Found %d records to process.",
            len(records),
        )
        for rec in records:
            self._exchange_input_check(rec)

    def _exchange_input_check(self, record):
        """Check status input exchange and update state field.

        1. check if the file has been placed in the input folder
        2. if yes, load it
        3. if not, skip

        :param record: edi.exchange.record record
        :return: boolean
            * False if there's nothing else to be done
            * True if file still need action
        """
        if self._get_remote_file(record, "pending"):
            _logger.info("%s done for: %s", (record.model, record.name))
            if not record.exchange_state == "input_received":
                record.exchange_state = "input_received"
                self._exchange_notify_record(
                    record, record._exchange_processed_ok_msg()
                )
                # TODO: generate and send back hack file
                self._trigger_edi_event(record)
            return False
        return True

    def _trigger_edi_event_make_name(self, record, suffix=None):
        return "on_edi_{type.code}_{record.exchange_state}{suffix}".format(
            record=record, type=record.type_id, suffix=("_" + suffix) if suffix else ""
        )

    def _trigger_edi_event(self, record, name=None, suffix=None):
        name = name or self._trigger_edi_event_make_name(record, suffix=suffix)
        self._event(name).notify(record)
