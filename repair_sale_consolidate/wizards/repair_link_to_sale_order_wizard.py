# Copyright 2025 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.fields import Command


class RepairLinkToSaleOrderWizard(models.TransientModel):
    _name = "repair.link.to.sale.order.wizard"
    _description = "Link Repair Orders to Existing Quotation"

    sale_order_id = fields.Many2one("sale.order", string="Quotation", required=True)
    repair_order_ids = fields.Many2many("repair.order")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_ids = self.env.context.get("active_ids")
        if active_ids:
            res["repair_order_ids"] = [(6, 0, active_ids)]
        return res

    def action_link_repairs(self):
        for repair in self.repair_order_ids:
            if repair.sale_order_id:
                raise UserError(
                    self.env._(
                        f"Repair order {repair.name} is already linked to a sale order."
                    )
                )
            if repair.partner_id != self.sale_order_id.partner_id:
                raise UserError(
                    self.env._(
                        f"Partner mismatch: Repair order {repair.name} is "
                        "for {repair.partner_id.display_name,}, but the "
                        "quotation is for {self.sale_order_id.partner_id.display_name}."
                    )
                )

        self.sale_order_id.write(
            {"repair_order_ids": [Command.link(ro.id) for ro in self.repair_order_ids]}
        )
        return self.repair_order_ids.action_view_sale_order()
