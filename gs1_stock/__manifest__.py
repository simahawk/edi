# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "GS1 EDI for stock",
    "summary": """
        Base module for GS1 standard EDI exchange related to stock.
    """,
    "version": "13.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE,Odoo Community Association (OCA)",
    "depends": [
        "base_gs1",
        "stock",
        "purchase_stock",
        "delivery",
        "base_edi_exchange_output",
    ],
    "data": [
        "views/stock_picking_view.xml",
        "data/inbound_instruction_edi_exchange_type.xml",
        "data/inbound_instruction_qweb_template.xml",
        "data/inbound_instruction_output_template.xml",
    ],
}
