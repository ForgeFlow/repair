# Copyright 2023 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _should_be_assigned(self):
        if self.repair_id and self._context.get("should_be_assigned", False):
            return True
        return super()._should_be_assigned()

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        if not self._context.get("should_be_assigned", False):
            for move in moves:
                if move.repair_id.state in ["confirmed", "under_repair"]:
                    move.repair_id._action_launch_stock_rule(move)
        return moves
