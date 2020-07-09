# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class BusinessHeader(Component):
    """Generate GS1 StandardBusinessDocumentHeader.

    `base_jsonify.model.jsonify` is used whereever possible to transform data.
    """

    _name = "gs1.output.businessdocumentheader"
    _inherit = [
        "gs1.output.mixin",
    ]
    _usage = "gs1.StandardBusinessDocumentHeader"
    _xsd_schema_path = "static/schemas/sbdh/StandardBusinessDocumentHeader.xsd"
    # StandardBusinessDocumentHeader require the NS prefix on all the elements.
    # This is an exception compared to other elements of the standard.
    # This attr is used only by this component.
    _local_ns = "sh"

    _work_context_validate_attrs = [
        "record",
        "sender",
        "receiver",
        "instance_identifier",
    ]

    def _header_version(self):
        data = {"HeaderVersion": "1.0"}
        return self._apply_ns_and_value(data, self._local_ns)

    def _contact(self, contact_key, record):
        contact = {}
        contact.update(self._contact_identifier(record))
        contact.update({"ContactInformation": self._contact_information(record)})
        return {
            contact_key: contact,
        }

    def _contact_identifier(self, record):
        return {
            "Identifier": {"@attrs": {"Authority": "GS1"}},
        }

    def _contact_information(self, record):
        return record.jsonify(self._partner_parser(record))[0]

    def _partner_parser(self, record):
        # TODO: add more
        return ["name:Contact", "email:EmailAddress", "phone:TelephoneNumber"]

    def _sender(self):
        data = self._contact("Sender", self._get_sender_record())
        # TODO: shall be mapped to something?
        data["Sender"]["ContactInformation"]["ContactTypeIdentifier"] = "Buyer"
        return self._apply_ns_and_value(data, self._local_ns)

    def _get_sender_record(self):
        return self.work.sender

    def _receiver(self):
        data = self._contact("Receiver", self._get_receiver_record())
        # TODO: shall be mapped to something?
        data["Receiver"]["ContactInformation"]["ContactTypeIdentifier"] = "Seller"
        return self._apply_ns_and_value(data, self._local_ns)

    def _get_receiver_record(self):
        return self.work.receiver

    def _document_identification(self):
        doc_info = {
            "Standard": "GS1",
            "TypeVersion": "3.4",
            # TODO: unique identifier for current message -> get it from self.record
            "InstanceIdentifier": self._instance_identifier(),
            # TODO: where this comes from?
            "Type": "",
            # TODO: where this comes from?
            "MultipleType": "false",
            # TODO
            "CreationDateAndTime": self._utc_now(),
        }
        data = {"DocumentIdentification": doc_info}
        return self._apply_ns_and_value(data, self._local_ns)

    def _instance_identifier(self):
        return self.work.instance_identifier

    def generate_data(self):
        business_header = {
            "@ns": self._local_ns,
        }
        business_header.update(self._header_version())
        business_header.update(self._sender())
        business_header.update(self._receiver())
        business_header.update(self._document_identification())
        return {"StandardBusinessDocumentHeader": business_header}
