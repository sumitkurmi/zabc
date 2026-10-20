# MODULE: Network Asset and Stock Management - this file belongs to the code for this module.
# Updates demo seed data to clean up old placeholder locations and use real MNNIT campus locations.

import asyncio
from datetime import datetime
from backend.app.db import get_database, close_db_client
from scripts_db.seed_locations_helper import get_or_create_real_locations

# List of old placeholder location names and codes to clean up from earlier runs
OLD_PLACEHOLDER_NAMES = [
    "Academic Building 1",
    "Hostel Block A",
    "Computer Networks Lab",
    "Room 214",
    "Room 215"
]

OLD_PLACEHOLDER_CODES = [
    "AB1",
    "HBA",
    "AB1-CNLAB",
    "HBA-R214",
    "HBA-R215"
]

DEMO_ASSET_TAGS = [
    "MNNIT-SW-001",
    "MNNIT-SW-002",
    "MNNIT-SW-003",
    "MNNIT-AP-001",
    "MNNIT-RTR-001"
]

DEMO_STOCK_MODELS = [
    "NCB-C6UBLR-305",
    "GLC-SX-MMD",
    "RJ45-C6"
]


async def seed_network_assets_demo():
    """Cleanly replaces old placeholder demo data with real MNNIT campus location records."""
    db = get_database()

    print("Cleaning up old placeholder locations and associated demo records...")

    # 1. Identify old placeholder locations
    old_locs = await db.na_locations.find({
        "$or": [
            {"name": {"$in": OLD_PLACEHOLDER_NAMES}},
            {"code": {"$in": OLD_PLACEHOLDER_CODES}}
        ]
    }).to_list(length=100)

    old_loc_ids = [str(l["_id"]) for l in old_locs]

    # Delete switch ports attached to old locations or demo assets
    if old_loc_ids:
        await db.na_switch_ports.delete_many({"location_id": {"$in": old_loc_ids}})
    await db.na_switch_ports.delete_many({"notes": {"$regex": "Socket #"}})

    # Delete assets attached to old locations or matching demo asset tags
    await db.na_assets.delete_many({
        "$or": [
            {"location_id": {"$in": old_loc_ids}},
            {"asset_tag": {"$in": DEMO_ASSET_TAGS}}
        ]
    })

    # Delete demo stock items and transactions
    old_stock = await db.na_stock_items.find({"model": {"$in": DEMO_STOCK_MODELS}}).to_list(length=100)
    old_stock_ids = [str(s["_id"]) for s in old_stock]
    if old_stock_ids:
        await db.na_stock_transactions.delete_many({"stock_item_id": {"$in": old_stock_ids}})
    await db.na_stock_items.delete_many({"model": {"$in": DEMO_STOCK_MODELS}})

    # Delete the old placeholder location records
    if old_loc_ids:
        await db.na_locations.delete_many({"_id": {"$in": [l["_id"] for l in old_locs]}})

    print("Old placeholder cleanup complete.")

    # 2. Get or create real campus locations using helper
    loc_res = await get_or_create_real_locations(db)
    loc_map = loc_res["location_map"]
    room_map = loc_res["room_map"]

    academic_id = loc_map["academic_campus"]
    svbh_id = loc_map["svbh"]

    acad_rooms = room_map[academic_id]
    svbh_rooms = room_map[svbh_id]

    lab_room_id = acad_rooms[0]["id"]
    r214_id = svbh_rooms[0]["id"]
    r215_id = svbh_rooms[1]["id"]

    print("Real campus locations initialized.")

    # 3. Create Demo Assets using real location IDs
    sw1_res = await db.na_assets.insert_one({
        "asset_tag": "MNNIT-SW-001",
        "category": "SWITCH",
        "make": "Cisco",
        "model": "Catalyst 2960",
        "serial_number": "SN-SW-001",
        "location_id": lab_room_id,
        "installation_date": "2024-01-15",
        "installed_by": "MNNIT Admin",
        "status": "IN_USE",
        "ip_address": "172.16.1.10",
        "mac_address": "00:11:22:33:44:55",
        "firmware_version": "v15.2",
        "total_ports": 24,
        "warranty": {"start_date": "2024-01-01", "end_date": "2027-01-01", "vendor": "Cisco India", "is_active": True},
        "maintenance_history": [],
        "status_history": [{"status": "IN_USE", "changed_at": datetime.utcnow().isoformat(), "changed_by": "MNNIT Admin", "reason": "Initial deployment"}]
    })
    sw1_id = str(sw1_res.inserted_id)

    sw2_res = await db.na_assets.insert_one({
        "asset_tag": "MNNIT-SW-002",
        "category": "SWITCH",
        "make": "Aruba",
        "model": "CX 6000",
        "serial_number": "SN-SW-002",
        "location_id": svbh_id,
        "installation_date": "2024-02-10",
        "installed_by": "MNNIT Admin",
        "status": "IN_USE",
        "ip_address": "172.16.2.10",
        "mac_address": "00:11:22:33:44:66",
        "firmware_version": "v10.08",
        "total_ports": 24,
        "warranty": {"start_date": "2024-02-01", "end_date": "2027-02-01", "vendor": "Aruba Networks", "is_active": True},
        "maintenance_history": [],
        "status_history": [{"status": "IN_USE", "changed_at": datetime.utcnow().isoformat(), "changed_by": "MNNIT Admin", "reason": "Hostel switch installation"}]
    })
    sw2_id = str(sw2_res.inserted_id)

    # Spare switch
    await db.na_assets.insert_one({
        "asset_tag": "MNNIT-SW-003",
        "category": "SWITCH",
        "make": "D-Link",
        "model": "DGS-1210",
        "serial_number": "SN-SW-003",
        "location_id": lab_room_id,
        "installation_date": "2024-03-01",
        "installed_by": "MNNIT Admin",
        "status": "SPARE",
        "total_ports": 24,
        "warranty": {"start_date": "2024-03-01", "end_date": "2026-03-01", "vendor": "D-Link India", "is_active": True},
        "maintenance_history": [],
        "status_history": [{"status": "SPARE", "changed_at": datetime.utcnow().isoformat(), "changed_by": "MNNIT Admin", "reason": "Backup switch stock"}]
    })

    # Faulty AP with maintenance record
    await db.na_assets.insert_one({
        "asset_tag": "MNNIT-AP-001",
        "category": "ACCESS_POINT",
        "make": "Aruba",
        "model": "AP-505",
        "serial_number": "SN-AP-001",
        "location_id": r214_id,
        "installation_date": "2023-08-01",
        "installed_by": "MNNIT Admin",
        "status": "FAULTY",
        "ip_address": "172.16.2.50",
        "mac_address": "AA:BB:CC:DD:EE:01",
        "ssid_list": ["MNNIT-WiFi"],
        "coverage_area": "SVBH Hostel 2nd Floor",
        "warranty": {"start_date": "2023-08-01", "end_date": "2025-08-01", "vendor": "Aruba Networks", "is_active": True},
        "maintenance_history": [
            {
                "date": "2024-03-10",
                "type": "REPAIR",
                "description": "Replaced blown power IC after voltage surge",
                "performed_by": "Senior Technician",
                "cost": 1500.0
            }
        ],
        "status_history": [
            {"status": "IN_USE", "changed_at": "2023-08-01T00:00:00", "changed_by": "Admin", "reason": "Installed"},
            {"status": "FAULTY", "changed_at": datetime.utcnow().isoformat(), "changed_by": "Admin", "reason": "Power failure after storm"}
        ]
    })

    # Core router
    await db.na_assets.insert_one({
        "asset_tag": "MNNIT-RTR-001",
        "category": "ROUTER",
        "make": "Cisco",
        "model": "ISR 4331",
        "serial_number": "SN-RTR-001",
        "location_id": academic_id,
        "installation_date": "2023-01-01",
        "installed_by": "MNNIT Admin",
        "status": "IN_USE",
        "ip_address": "172.16.0.1",
        "mac_address": "00:11:22:00:00:01",
        "warranty": {"start_date": "2023-01-01", "end_date": "2028-01-01", "vendor": "Cisco", "is_active": True},
        "maintenance_history": [],
        "status_history": [{"status": "IN_USE", "changed_at": "2023-01-01T00:00:00", "changed_by": "Admin", "reason": "Core gateway"}]
    })

    print("Demo assets created with real location IDs.")

    # 4. Create Switch Ports mapped to real hostel rooms
    ports_data = []
    for p in range(1, 25):
        served_loc = r214_id if p <= 12 else (r215_id if p <= 20 else None)
        ports_data.append({
            "switch_id": sw2_id,
            "port_number": p,
            "status": "ACTIVE" if served_loc else "FREE",
            "vlan": 10 if served_loc == r214_id else (20 if served_loc == r215_id else 1),
            "location_id": served_loc,
            "notes": f"Socket #{p} in room" if served_loc else None
        })

    await db.na_switch_ports.insert_many(ports_data)
    print("Demo switch ports created.")

    # 5. Create Stock Items
    await db.na_stock_items.insert_one({
        "item_type": "Cat6 LAN Cable Box (305m)",
        "make": "D-Link",
        "model": "NCB-C6UBLR-305",
        "quantity_available": 1,
        "minimum_level": 3,
        "store_location_id": lab_room_id,
        "is_low": True
    })

    await db.na_stock_items.insert_one({
        "item_type": "1Gbps SX SFP Transceiver",
        "make": "Cisco",
        "model": "GLC-SX-MMD",
        "quantity_available": 12,
        "minimum_level": 4,
        "store_location_id": lab_room_id,
        "is_low": False
    })

    await db.na_stock_items.insert_one({
        "item_type": "RJ45 Connectors (Pack of 100)",
        "make": "Amphenol",
        "model": "RJ45-C6",
        "quantity_available": 15,
        "minimum_level": 5,
        "store_location_id": lab_room_id,
        "is_low": False
    })

    print("Demo stock items created.")
    print("Network assets demo dataset successfully updated with real location names.")
    close_db_client()


if __name__ == "__main__":
    asyncio.run(seed_network_assets_demo())
