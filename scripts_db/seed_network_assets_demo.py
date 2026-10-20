# MODULE: Network Asset and Stock Management - this file belongs to the code for this module.
# Seed script for inserting demo network assets, locations, switch ports, and stock items into MongoDB.

import asyncio
from datetime import datetime
from backend.app.db import get_database, close_db_client


async def seed_network_assets_demo():
    """Idempotent seed script inserting demo locations, assets, ports, and stock."""
    db = get_database()

    # Clear existing network asset collections
    await db.na_locations.delete_many({})
    await db.na_assets.delete_many({})
    await db.na_switch_ports.delete_many({})
    await db.na_stock_items.delete_many({})
    await db.na_stock_transactions.delete_many({})

    # 1. Create Locations (1 building, 1 hostel, 3 rooms)
    building_res = await db.na_locations.insert_one({
        "name": "Academic Building 1",
        "code": "AB1",
        "type": "BUILDING",
        "parent_id": None
    })
    b_id = str(building_res.inserted_id)

    hostel_res = await db.na_locations.insert_one({
        "name": "Hostel Block A",
        "code": "HBA",
        "type": "HOSTEL",
        "parent_id": None
    })
    h_id = str(hostel_res.inserted_id)

    lab_res = await db.na_locations.insert_one({
        "name": "Computer Networks Lab",
        "code": "AB1-CNLAB",
        "type": "LAB",
        "parent_id": b_id
    })
    lab_id = str(lab_res.inserted_id)

    room214_res = await db.na_locations.insert_one({
        "name": "Room 214",
        "code": "HBA-R214",
        "type": "ROOM",
        "parent_id": h_id
    })
    r214_id = str(room214_res.inserted_id)

    room215_res = await db.na_locations.insert_one({
        "name": "Room 215",
        "code": "HBA-R215",
        "type": "ROOM",
        "parent_id": h_id
    })
    r215_id = str(room215_res.inserted_id)

    print("Created demo locations.")

    # 2. Create Assets
    sw1_res = await db.na_assets.insert_one({
        "asset_tag": "MNNIT-SW-001",
        "category": "SWITCH",
        "make": "Cisco",
        "model": "Catalyst 2960",
        "serial_number": "SN-SW-001",
        "location_id": lab_id,
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
        "location_id": h_id,
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
        "location_id": lab_id,
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
        "coverage_area": "Hostel Block A 2nd Floor",
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

    # Router & AP 2
    await db.na_assets.insert_one({
        "asset_tag": "MNNIT-RTR-001",
        "category": "ROUTER",
        "make": "Cisco",
        "model": "ISR 4331",
        "serial_number": "SN-RTR-001",
        "location_id": b_id,
        "installation_date": "2023-01-01",
        "installed_by": "MNNIT Admin",
        "status": "IN_USE",
        "ip_address": "172.16.0.1",
        "mac_address": "00:11:22:00:00:01",
        "warranty": {"start_date": "2023-01-01", "end_date": "2028-01-01", "vendor": "Cisco", "is_active": True},
        "maintenance_history": [],
        "status_history": [{"status": "IN_USE", "changed_at": "2023-01-01T00:00:00", "changed_by": "Admin", "reason": "Core gateway"}]
    })

    print("Created demo assets.")

    # 3. Create Switch Ports mapped to rooms
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
    print("Created demo switch ports.")

    # 4. Create Stock Items (cables & SFPs, one below minimum_level)
    await db.na_stock_items.insert_one({
        "item_type": "Cat6 LAN Cable Box (305m)",
        "make": "D-Link",
        "model": "NCB-C6UBLR-305",
        "quantity_available": 1,  # Below minimum 3 -> Low stock alert
        "minimum_level": 3,
        "store_location_id": lab_id,
        "is_low": True
    })

    await db.na_stock_items.insert_one({
        "item_type": "1Gbps SX SFP Transceiver",
        "make": "Cisco",
        "model": "GLC-SX-MMD",
        "quantity_available": 12,
        "minimum_level": 4,
        "store_location_id": lab_id,
        "is_low": False
    })

    await db.na_stock_items.insert_one({
        "item_type": "RJ45 Connectors (Pack of 100)",
        "make": "Amphenol",
        "model": "RJ45-C6",
        "quantity_available": 15,
        "minimum_level": 5,
        "store_location_id": lab_id,
        "is_low": False
    })

    print("Created demo stock items.")
    print("Network assets demo dataset successfully seeded.")
    close_db_client()


if __name__ == "__main__":
    asyncio.run(seed_network_assets_demo())
