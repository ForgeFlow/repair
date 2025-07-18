# Copyright 2025 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Repair Sale Consolidate",
    "version": "18.0.1.0.0",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/repair",
    "summary": "Repair type",
    "category": "Repair",
    "depends": ["repair"],
    "data": [
        "security/ir.model.access.csv",
        "views/repair_order_views.xml",
        "wizards/repair_link_to_sale_order_wizard.xml",
    ],
    "installable": True,
    "development_status": "Alpha",
    "license": "AGPL-3",
    "maintainers": ["AaronHForgeFlow"],
}
