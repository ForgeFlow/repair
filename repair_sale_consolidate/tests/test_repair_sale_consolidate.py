from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestRepairQuoteFromMultiple(TransactionCase):
    def setUp(self):
        super().setUp()
        self.RepairOrder = self.env["repair.order"]
        self.SaleOrder = self.env["sale.order"]
        self.Move = self.env["stock.move"]
        self.Product = self.env["product.product"]

        self.partner = self.env.ref("base.res_partner_1")
        self.uom_unit = self.env.ref("uom.product_uom_unit")
        self.picking_type = self.env.ref("stock.picking_type_internal")

        self.product = self.Product.create(
            {
                "name": "Test Spare Part",
                "type": "consu",
                "is_storable": True,
                "uom_id": self.uom_unit.id,
            }
        )

        self.src_location = self.env.ref("stock.stock_location_stock")
        self.dest_location = self.env.ref("stock.stock_location_customers")
        self.parts_location = self.env.ref("stock.stock_location_stock")
        self.warehouse = self.env["stock.warehouse"].search([], limit=1)

        self.repair_picking_type = self.StockPickingType.create(
            {
                "name": "Repair Picking Type",
                "code": "repair",
                "warehouse_id": self.warehouse.id,
                "sequence_code": "REPAIR",
                "default_location_src_id": self.warehouse.lot_stock_id.id,
                "default_location_dest_id": self.env.ref(
                    "stock.stock_location_stock"
                ).id,
                "default_remove_location_id": self.env.ref(
                    "stock.stock_location_stock"
                ).id,  # removed parts location
                "default_location_scrap_id": self.env.ref(
                    "stock.stock_location_scrap"
                ).id,
                "use_create_lots": True,
                "use_existing_lots": True,
                "show_reserved": True,
                "active": True,
            }
        )
        self.repair_1 = self.RepairOrder.create(
            {
                "name": "Repair A",
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "product_location_src_id": self.src_location.id,
                "product_location_dest_id": self.dest_location.id,
                "parts_location_id": self.parts_location.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1.0,
                            "product_uom": self.uom_unit.id,
                            "state": "draft",
                            "repair_line_type": "add",
                            "company_id": self.env.company.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 2.0,
                            "product_uom": self.uom_unit.id,
                            "state": "draft",
                            "repair_line_type": "add",
                            "company_id": self.env.company.id,
                        },
                    ),
                ],
            }
        )
        self.repair_2 = self.RepairOrder.create(
            {
                "name": "Repair B",
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "product_location_src_id": self.src_location.id,
                "product_location_dest_id": self.dest_location.id,
                "parts_location_id": self.parts_location.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 3.0,
                            "product_uom": self.uom_unit.id,
                            "state": "draft",
                            "repair_line_type": "add",
                            "company_id": self.env.company.id,
                        },
                    ),
                ],
            }
        )

    def test_create_single_quote_from_multiple_repairs(self):
        sale_order = (
            self.repair_1 + self.repair_2
        ).create_single_sale_order_from_repairs()

        self.assertTrue(sale_order)
        self.assertEqual(
            set(sale_order.repair_order_ids.ids), {self.repair_1.id, self.repair_2.id}
        )
        self.assertEqual(self.repair_1.sale_order_id.id, sale_order.id)
        self.assertEqual(self.repair_2.sale_order_id.id, sale_order.id)

        lines = sale_order.order_line.filtered(
            lambda sol: sol.product_id == self.product
        )
        self.assertEqual(len(lines), 3)
        self.assertEqual(sum(lines.mapped("product_uom_qty")), 6.0)

    def test_link_and_unlink_repair_to_sale_order(self):
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
            }
        )

        link_wizard = self.env["repair.link.to.sale.order.wizard"].create(
            {
                "sale_order_id": sale_order.id,
                "repair_order_ids": [(6, 0, [self.repair_1.id])],
            }
        )
        link_wizard.action_link()

        self.assertEqual(self.repair_1.sale_order_id, sale_order)
        self.assertIn(self.repair_1, sale_order.repair_order_ids)

        self.repair_1.action_unlink_sale_order()
        self.repair_1.invalidate_recordset()
        sale_order.invalidate_recordset()

        self.assertFalse(self.repair_1.sale_order_id)
        self.assertNotIn(self.repair_1, sale_order.repair_order_ids)
