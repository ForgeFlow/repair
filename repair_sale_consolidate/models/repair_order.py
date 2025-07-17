from odoo import models


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
