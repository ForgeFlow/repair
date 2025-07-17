# wizards/repair_link_to_sale_order_wizard.py

from odoo import fields, models
from odoo.exceptions import UserError


class RepairLinkToSaleOrderWizard(models.TransientModel):
    _name = "repair.link.to.sale.order.wizard"
    _description = "Link Repair Order to Existing Quotation"

    repair_order_id = fields.Many2one(
        "repair.order", required=True, string="Repair Order"
    )
    sale_order_id = fields.Many2one(
        "sale.order",
        domain=[("state", "=", "draft")],
        required=True,
        string="Quotation",
    )

    def action_link_to_quotation(self):
        self.ensure_one()
        if self.repair_order_id.sale_order_id:
            raise UserError(
                self.env._("This repair order is already linked to a quotation.")
            )
        self.repair_order_id.write(
            {
                "sale_order_id": self.sale_order_id.id,
            }
        )
