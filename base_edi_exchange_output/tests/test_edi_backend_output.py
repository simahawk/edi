# Copyright 2020 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import base64

from lxml import etree

from odoo.addons.base_edi_exchange.tests.common import EDIBackendCommonTestCase


class TestEDIBackendOutputBase(EDIBackendCommonTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_records()

    @classmethod
    def _setup_records(cls):
        cls.type_out1 = cls._create_exchange_type(
            name="Template output 1",
            direction="output",
            code="test_type_out1",
            exchange_file_ext="txt",
            exchange_filename_pattern="{record.ref}-{type.code}-{dt}",
        )
        model = cls.env["edi.exchange.template.output"]
        qweb_tmpl = cls.env["ir.ui.view"].create(
            {
                "type": "qweb",
                "key": "base_edi_exchange.test_output1",
                "arch": """
            <t t-name="base_edi_exchange.test_output1">
                <t t-esc="record.ref" /> - <t t-esc="record.name" />
            </t>
            """,
            }
        )
        cls.tmpl_out1 = model.create(
            {"name": "Out 1", "type_id": cls.type_out1.id, "template_id": qweb_tmpl.id}
        )
        vals = {
            "model": cls.partner._name,
            "res_id": cls.partner.id,
            "type_id": cls.type_out1.id,
        }
        cls.record1 = cls.backend.create_record("test_type_out1", vals)

        cls.type_out2 = cls._create_exchange_type(
            name="Template output 2",
            direction="output",
            code="test_type_out2",
            exchange_file_ext="xml",
            exchange_filename_pattern="{record.ref}-{type.code}-{dt}",
        )
        qweb_tmpl = cls.env["ir.ui.view"].create(
            {
                "type": "qweb",
                "key": "base_edi_exchange.test_output2",
                "arch": """
            <t t-name="base_edi_exchange.test_output2">
                <t t-name="base_edi_exchange.test_output2">
                    <Record t-att-ref="record.ref">
                        <Name t-esc="record.name" />
                    </Record>
                </t>
            </t>
            """,
            }
        )
        cls.tmpl_out2 = model.create(
            {"name": "Out 2", "type_id": cls.type_out2.id, "template_id": qweb_tmpl.id}
        )
        vals = {
            "model": cls.partner._name,
            "res_id": cls.partner.id,
            "type_id": cls.type_out2.id,
        }
        cls.record2 = cls.backend.create_record("test_type_out2", vals)


class TestEDIBackendOutput(TestEDIBackendOutputBase):
    def test_get_template(self):
        self.assertEqual(self.backend._get_template(self.record1), self.tmpl_out1)
        self.assertEqual(self.backend._get_template(self.record2), self.tmpl_out2)

    def test_generate_file(self):
        output = self.backend.generate_output(self.record1)
        expected = "{0.ref} - {0.name}".format(self.partner)
        self.assertEqual(output.strip(), expected)
        file_content = base64.b64decode(self.record1.exchange_file).decode()
        self.assertEqual(file_content.strip(), expected)
        output = self.backend.generate_output(self.record2)
        doc = etree.fromstring(output)
        self.assertEqual(doc.tag, "Record")
        self.assertEqual(doc.attrib, {"ref": self.partner.ref})
        self.assertEqual(doc.getchildren()[0].text, self.partner.name)
