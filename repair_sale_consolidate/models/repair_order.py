# Copyright 2025 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import models
from odoo.exceptions import UserError
from odoo.fields import Command


class RepairOrder(models.Model):
    _inherit = "repair.order"

    def action_view_sale_order(self):
        sale_orders = self.mapped("sale_order_id").filtered(lambda so: so)

        if not sale_orders:
            return {"type": "ir.actions.act_window_close"}

        if len(sale_orders) == 1:
            return super().action_view_sale_order()

        return {
            "type": "ir.actions.act_window",
            "name": "Quotations",
            "res_model": "sale.order",
            "view_mode": "list,form",
            "domain": [("id", "in", sale_orders.ids)],
            "context": {"create": False},
        }

    def action_create_combined_sale_order(self):
        if not self:
            return
        # Validate that no repair order is already linked to a sale order
        already_linked = self.filtered("sale_order_id")
        if already_linked:
            ref_str = "\n".join(ro.name for ro in already_linked)
            raise UserError(
                self.env._(
                    f"You cannot create a quotation for repair orders already linked to a sale order:\n{ref_str}",
                )
            )
        picking_types = self.mapped("picking_type_id")
        if not picking_types or len(picking_types) != 1:
            raise UserError(
                self.env._(
                    "All selected repair orders must have the same picking type."
                )
            )

        partners = self.mapped("partner_id")
        if not partners or len(partners) != 1:
            raise UserError(
                self.env._(
                    "All selected repair orders must have the same " "customer defined."
                )
            )

        self.env["sale.order"].create(
            {
                "company_id": self.company_id.id,
                "partner_id": partners.id,
                "warehouse_id": picking_types.warehouse_id.id,
                "repair_order_ids": [Command.link(ro.id) for ro in self],
            }
        )

        # Create the sale order lines from all move_ids
        self.mapped("move_ids")._create_repair_sale_order_line()

        return self.action_view_sale_order()
