# Copyright (C) 2024 APSL-Nagarro Antoni Marroig
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if not openupgrade.table_exists(env.cr, "repair_type"):
        return
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE stock_picking_type
        ADD COLUMN old_repair_type_id_legacy INTEGER;
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        INSERT INTO stock_picking_type
        (create_date, default_location_dest_id, default_remove_location_dest_id,
        name,default_add_location_src_id, default_remove_location_src_id,
        old_repair_type_id_legacy)
        SELECT create_date, destination_location_add_part_id,
        destination_location_remove_part_id, jsonb_build_object('en_US', name) as name,
        source_location_add_part_id, source_location_remove_part_id, id
        FROM repair_type;
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
            UPDATE repair_order ro
            SET picking_type_id = spt.id
            FROM stock_picking_type spt
            WHERE ro.repair_type_id = spt.old_repair_type_id_legacy;
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE repair_order
        DROP COLUMN repair_type_id;
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        DROP TABLE repair_type;
        """,
    )
