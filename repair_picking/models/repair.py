# Copyright 2023 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.exceptions import UserError


class RepairOrder(models.Model):
    _inherit = "repair.order"

    @api.model
    def _get_default_location_id(self):
        warehouse = self.env["stock.warehouse"].search(
            [("company_id", "=", self.env.company.id)], limit=1
        )
        return (
            warehouse.repair_location_id.id
            if warehouse and warehouse.repair_location_id
            else False
        )

    # Changing default value on existing field
    location_id = fields.Many2one(
        default=_get_default_location_id,
    )
    procurement_group_id = fields.Many2one(
        "procurement.group", "Procurement Group", copy=False
    )

    def action_repair_cancel(self):
        res = super().action_repair_cancel()
        for picking in self.picking_ids:
            if picking.state not in ["cancel", "done"]:
                picking.action_cancel()
        return res

    def _action_launch_stock_rule(self, repair_lines):
        for line in repair_lines:
            self.with_context(should_be_assigned=True)._run_procurement_repair(line)
        return True

    def _run_procurement_repair(self, line):
        procurements = []
        errors = []
        procurement = self._prepare_procurement_repair(line)
        procurements.append(procurement)
        try:
            self.env["procurement.group"].run(procurements)
        except UserError as error:
            errors.append(error.args[0])
        if errors:
            raise UserError("\n".join(errors))
        return True

    @api.model
    def _get_procurement_data_repair(self, line):
        warehouse = self.location_id.warehouse_id
        if not self.procurement_group_id:
            group_id = self.env["procurement.group"].create({"name": self.name})
            self.procurement_group_id = group_id
        procurement_data = {
            "name": self.name,
            "group_id": self.procurement_group_id,
            "origin": self.name,
            "date_planned": fields.Datetime.now(),
            "product_id": line.product_id.id,
            "product_qty": line.product_uom_qty,
            "product_uom": line.product_uom.id,
            "company_id": self.company_id,
            "warehouse_id": warehouse,
            "repair_line_id": line.id,
            "repair_id": line.repair_id.id,
        }
        if line.restrict_lot_id:
            procurement_data["restrict_lot_id"] = line.restrict_lot_id.id
        if line.repair_line_type == "remove":
            procurement_data[
                "source_repair_location_id"
            ] = line.repair_id.location_id.id
        return procurement_data

    @api.model
    def _prepare_procurement_repair(self, line):
        values = self._get_procurement_data_repair(line)
        warehouse = self.location_id.warehouse_id
        location = (
            self.location_id
            if line.repair_line_type == "add"
            else warehouse.remove_c_type_id.default_location_dest_id
        )
        procurement = self.env["procurement.group"].Procurement(
            line.product_id,
            line.product_uom_qty,
            line.product_uom,
            location,
            values.get("origin"),
            values.get("origin"),
            self.company_id,
            values,
        )
        return procurement

    def _update_stock_moves_and_picking_state(self):
        for repair in self:
            for picking in repair.picking_ids:
                if picking.location_dest_id.id == self.location_id.id:
                    for move_line in picking.move_ids_without_package:
                        stock_moves = repair.move_ids.filtered(
                            lambda m: m.repair_line_type == "add"
                            and m.location_id.id == self.location_id.id
                        )
                        if stock_moves:
                            stock_moves[0].write(
                                {
                                    "move_orig_ids": [(4, move_line.id)],
                                    "state": "waiting",
                                }
                            )
                if picking.location_id.id == self.location_id.id:
                    for move_line in picking.move_ids_without_package:
                        stock_moves = repair.move_ids.filtered(
                            lambda m: m.repair_line_type == "remove"
                            and m.location_dest_id.id == self.location_id.id
                        )
                        if stock_moves:
                            move_line.write(
                                {
                                    "move_orig_ids": [(4, stock_moves[0].id)],
                                    "state": "waiting",
                                }
                            )
                # We are using write here because
                # the repair_stock_move module does not use stock rules.
                # As a result, we manually link the stock moves
                # and then recompute the state of the picking.
                picking._compute_state()

    def _action_repair_confirm(self):
        res = super()._action_repair_confirm()
        for repair in self:
            warehouse = repair.location_id.warehouse_id
            if warehouse.repair_steps in ["2_steps", "3_steps"]:
                repair._action_launch_stock_rule(
                    repair.move_ids.filtered(
                        lambda move: move.repair_line_type == "add"
                    ),
                )
            if warehouse.repair_steps == "3_steps":
                repair._action_launch_stock_rule(
                    repair.move_ids.filtered(
                        lambda move: move.repair_line_type == "remove"
                    ),
                )
            repair._update_stock_moves_and_picking_state()
        return res

    @api.onchange("location_id")
    def _onchange_location_id(self):
        warehouse = self.location_id.warehouse_id
        for line in self.move_ids:
            if line.repair_line_type == "add":
                line.location_id = self.location_id
            elif (
                line.repair_line_type == "remove"
                and warehouse.repair_steps == "3_steps"
            ):
                line.location_dest_id = self.location_id
