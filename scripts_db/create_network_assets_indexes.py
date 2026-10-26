# MODULE: Network Asset and Stock Management - this file belongs to the code for this module.
# Creates database indexes for na_assets, na_locations, na_switch_ports, and na_stock_items collections.

import asyncio
from backend.app.db import get_database, close_db_client


async def create_network_assets_indexes():
    """Creates performance and uniqueness indexes for network_assets module collections."""
    db = get_database()

    # na_assets indexes
    print("Creating indexes on 'na_assets'...")
    await db.na_assets.create_index("serial_number", unique=True)
    await db.na_assets.create_index("asset_tag", unique=True)
    await db.na_assets.create_index([("category", 1), ("status", 1)])
    await db.na_assets.create_index("location_id")

    # na_locations indexes
    print("Creating indexes on 'na_locations'...")
    await db.na_locations.create_index("code", unique=True)
    await db.na_locations.create_index("parent_id")

    # na_switch_ports indexes
    print("Creating indexes on 'na_switch_ports'...")
    await db.na_switch_ports.create_index([("switch_id", 1), ("port_number", 1)], unique=True)

    # na_stock_items indexes
    print("Creating indexes on 'na_stock_items'...")
    await db.na_stock_items.create_index("item_type")

    print("Network assets indexes successfully created.")
    close_db_client()


if __name__ == "__main__":
    asyncio.run(create_network_assets_indexes())
