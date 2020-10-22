# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Base EDI Exchange",
    "summary": """Base module to handle EDI exchanges""",
    "version": "13.0.1.0.0",
    "development_status": "Alpha",
    "license": "AGPL-3",
    "author": "ACSONE,Odoo Community Association (OCA)",
    "depends": [
        "base_edi",
        "storage_backend",
        "component",
        "component_event",
        "queue_job",
    ],
    "data": [
        "security/ir_model_access.xml",
        "views/edi_backend_views.xml",
        "views/edi_exchange_type_views.xml",
        "views/edi_exchange_record_views.xml",
        "templates/exchange_chatter_msg.xml",
    ],
    "demo": ["demo/edi_backend_demo.xml"],
}
