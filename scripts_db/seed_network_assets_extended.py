# MODULE: Network Asset and Stock Management - this file belongs to the code for this module.
# Extended seed script generating a comprehensive dataset (~70 assets, ports, stock, warranties, maintenance) for module testing.

import sys
import asyncio
import random
from datetime import datetime, timedelta
from backend.app.db import get_database, close_db_client
from scripts_db.seed_locations_helper import get_or_create_real_locations


async def seed_network_assets_extended(remove_only: bool = False):
    """Inserts or removes extended test dataset for network assets, ports, and stock items."""
    random.seed(42)
    db = get_database()

    print("Cleaning up any existing extended seed records (prefix 'EXT-')...")

    # 1. Find existing extended assets
    ext_assets = await db.na_assets.find({
        "$or": [
            {"serial_number": {"$regex": "^EXT-"}},
            {"asset_tag": {"$regex": "^EXT-"}}
        ]
    }).to_list(length=1000)

    ext_asset_ids = [str(a["_id"]) for a in ext_assets]

    # Delete switch ports for extended assets
    if ext_asset_ids:
        await db.na_switch_ports.delete_many({"switch_id": {"$in": ext_asset_ids}})
    await db.na_switch_ports.delete_many({"notes": {"$regex": "^EXT-"}})

    # Delete extended assets
    await db.na_assets.delete_many({
        "$or": [
            {"serial_number": {"$regex": "^EXT-"}},
            {"asset_tag": {"$regex": "^EXT-"}}
        ]
    })

    # Find and delete extended stock items and transactions
    ext_stock = await db.na_stock_items.find({
        "$or": [
            {"model": {"$regex": "^EXT-"}},
            {"item_type": {"$regex": "^EXT-"}}
        ]
    }).to_list(length=500)

    ext_stock_ids = [str(s["_id"]) for s in ext_stock]

    if ext_stock_ids:
        await db.na_stock_transactions.delete_many({"stock_item_id": {"$in": ext_stock_ids}})

    await db.na_stock_items.delete_many({
        "$or": [
            {"model": {"$regex": "^EXT-"}},
            {"item_type": {"$regex": "^EXT-"}}
        ]
    })

    print("Cleanup of extended seed records complete.")

    if remove_only:
        print("Removal flag '--remove' specified. Exiting without inserting new extended dataset.")
        close_db_client()
        return

    # 2. Get or create real locations
    loc_res = await get_or_create_real_locations(db)
    loc_map = loc_res["location_map"]
    room_map = loc_res["room_map"]

    all_location_ids = list(loc_map.values())
    all_room_ids = []
    for r_list in room_map.values():
        for r in r_list:
            all_room_ids.append(r["id"])

    print(f"Locations ready: {loc_res['reused_count']} reused, {loc_res['created_count']} created/checked.")

    # Dates and Personnel setup
    today = datetime.utcnow().date()
    technicians = ["Technician A", "Technician B", "Network Eng C", "MNNIT Staff D", "Senior Tech E"]

    # 3. Create ~70 Assets across all 10 categories
    categories = [
        "SWITCH", "ROUTER", "ACCESS_POINT", "FIREWALL", "OPTICAL_DEVICE",
        "CABLE", "SFP_MODULE", "RACK", "PATCH_PANEL", "UPS"
    ]

    makes_by_cat = {
        "SWITCH": [("Cisco", "Catalyst 9300"), ("HPE Aruba", "CX 6200"), ("D-Link", "DGS-3130"), ("Netgear", "GSM4230P")],
        "ROUTER": [("Cisco", "ISR 4451"), ("Juniper", "MX204"), ("Huawei", "AR6121")],
        "ACCESS_POINT": [("HPE Aruba", "AP-635"), ("Ubiquiti", "UniFi U6 Pro"), ("TP-Link", "EAP670")],
        "FIREWALL": [("Fortinet", "FortiGate 100F"), ("Palo Alto", "PA-440"), ("Sophos", "XGS 2100")],
        "OPTICAL_DEVICE": [("Huawei", "MA5608T OLT"), ("D-Link", "DPN-100 ONT"), ("TP-Link", "MC220L Media Converter")],
        "CABLE": [("Schneider", "Actassi Cat6A"), ("CommScope", "SYSTIMAX Cat6"), ("Molex", "Fibre Patch Cord")],
        "SFP_MODULE": [("Cisco", "SFP-10G-SR"), ("HPE", "10G SFP+ Transceiver"), ("FS.com", "1000BASE-SX")],
        "RACK": [("APC", "NetShelter SX 42U"), ("Valrack", "Server Rack 24U")],
        "PATCH_PANEL": [("D-Link", "Cat6 24-Port"), ("Schneider", "48-Port Keystone")],
        "UPS": [("APC", "Smart-UPS 3000VA"), ("Schneider", "Easy UPS 5000VA"), ("Eaton", "5PX 2000VA")]
    }

    inserted_assets = []
    switches_for_ports = []
    patch_panels_for_ports = []

    asset_counter = 1

    # First, create 1 pair of switches for failure/repair/replacement story
    # Switch B (Replacement)
    sw_repl_doc = {
        "asset_tag": f"EXT-TAG-{asset_counter:03d}",
        "category": "SWITCH",
        "make": "Cisco",
        "model": "Catalyst 9300-24P",
        "serial_number": f"EXT-SN-SW-REPL",
        "location_id": loc_map["academic_campus"],
        "installation_date": (today - timedelta(days=30)).isoformat(),
        "installed_by": "Senior Tech E",
        "status": "IN_USE",
        "ip_address": "172.16.10.99",
        "mac_address": "00:AA:BB:CC:99:99",
        "firmware_version": "v17.3",
        "total_ports": 24,
        "warranty": {
            "start_date": (today - timedelta(days=30)).isoformat(),
            "end_date": (today + timedelta(days=1065)).isoformat(),
            "vendor": "Cisco Systems",
            "is_active": True
        },
        "maintenance_history": [],
        "status_history": [{"status": "IN_USE", "changed_at": (today - timedelta(days=30)).isoformat(), "changed_by": "Senior Tech E", "reason": "Installed as replacement for failed switch"}]
    }
    sw_repl_res = await db.na_assets.insert_one(sw_repl_doc)
    sw_repl_id = str(sw_repl_res.inserted_id)
    switches_for_ports.append({"id": sw_repl_id, "ports": 24, "loc": loc_map["academic_campus"]})
    asset_counter += 1

    # Switch A (Failed, Repaired twice, then Replaced)
    sw_failed_doc = {
        "asset_tag": f"EXT-TAG-{asset_counter:03d}",
        "category": "SWITCH",
        "make": "Cisco",
        "model": "Catalyst 2960X",
        "serial_number": f"EXT-SN-SW-FAILED",
        "location_id": loc_map["academic_campus"],
        "installation_date": (today - timedelta(days=1200)).isoformat(),
        "installed_by": "Technician A",
        "status": "REPLACED",
        "replaced_by_id": sw_repl_id,
        "ip_address": "172.16.10.98",
        "mac_address": "00:AA:BB:CC:98:98",
        "firmware_version": "v15.0",
        "total_ports": 24,
        "warranty": {
            "start_date": (today - timedelta(days=1200)).isoformat(),
            "end_date": (today - timedelta(days=105)).isoformat(),
            "vendor": "Cisco Systems",
            "is_active": False
        },
        "maintenance_history": [
            {"date": (today - timedelta(days=400)).isoformat(), "type": "REPAIR", "description": "Replaced blown capacitor in PSU", "performed_by": "Technician A", "cost": 1200.0},
            {"date": (today - timedelta(days=180)).isoformat(), "type": "REPAIR", "description": "Repaired port controller IC chips", "performed_by": "Network Eng C", "cost": 2500.0},
            {"date": (today - timedelta(days=30)).isoformat(), "type": "REPLACEMENT", "description": "Unrepairable motherboard fault; swapped out for EXT-SN-SW-REPL", "performed_by": "Senior Tech E", "cost": 0.0}
        ],
        "status_history": [
            {"status": "IN_USE", "changed_at": (today - timedelta(days=1200)).isoformat(), "changed_by": "Technician A", "reason": "Initial deployment"},
            {"status": "UNDER_REPAIR", "changed_at": (today - timedelta(days=400)).isoformat(), "changed_by": "Technician A", "reason": "PSU fault"},
            {"status": "IN_USE", "changed_at": (today - timedelta(days=395)).isoformat(), "changed_by": "Technician A", "reason": "Repaired"},
            {"status": "UNDER_REPAIR", "changed_at": (today - timedelta(days=180)).isoformat(), "changed_by": "Network Eng C", "reason": "Port error"},
            {"status": "IN_USE", "changed_at": (today - timedelta(days=175)).isoformat(), "changed_by": "Network Eng C", "reason": "Repaired second time"},
            {"status": "REPLACED", "changed_at": (today - timedelta(days=30)).isoformat(), "changed_by": "Senior Tech E", "reason": "Swapped out for new hardware"}
        ]
    }
    await db.na_assets.insert_one(sw_failed_doc)
    asset_counter += 1

    # Now generate remaining ~68 assets
    statuses_pool = ["IN_USE", "IN_USE", "IN_USE", "IN_USE", "SPARE", "FAULTY", "UNDER_REPAIR", "RETIRED"]

    for i in range(1, 69):
        cat = categories[i % len(categories)]
        make, model = random.choice(makes_by_cat[cat])
        asset_tag = f"EXT-TAG-{asset_counter:03d}"
        serial_num = f"EXT-SN-{cat[:3]}-{i:03d}"
        status = random.choice(statuses_pool)
        loc_id = random.choice(all_room_ids if random.random() > 0.3 else all_location_ids)
        install_days = random.randint(30, 2000)
        install_date = (today - timedelta(days=install_days)).isoformat()
        tech = random.choice(technicians)

        # Warranty variety
        w_type = random.choice(["active_long", "expiring_30", "expiring_60", "expired", "none"])
        if w_type == "active_long":
            w_start = install_date
            w_end = (today + timedelta(days=random.randint(180, 730))).isoformat()
            warranty = {"start_date": w_start, "end_date": w_end, "vendor": f"{make} Care", "is_active": True}
        elif w_type == "expiring_30":
            w_start = install_date
            w_end = (today + timedelta(days=random.randint(5, 25))).isoformat()
            warranty = {"start_date": w_start, "end_date": w_end, "vendor": f"{make} Care", "is_active": True}
        elif w_type == "expiring_60":
            w_start = install_date
            w_end = (today + timedelta(days=random.randint(32, 58))).isoformat()
            warranty = {"start_date": w_start, "end_date": w_end, "vendor": f"{make} Care", "is_active": True}
        elif w_type == "expired":
            w_start = install_date
            w_end = (today - timedelta(days=random.randint(10, 300))).isoformat()
            warranty = {"start_date": w_start, "end_date": w_end, "vendor": f"{make} Care", "is_active": False}
        else:
            warranty = {"start_date": None, "end_date": None, "vendor": None, "is_active": False}

        # Maintenance history for ~1/3 of assets
        m_history = []
        if random.random() < 0.35:
            m_count = random.randint(1, 4)
            for m_idx in range(m_count):
                m_days = random.randint(10, install_days)
                m_type = random.choice(["REPAIR", "SERVICE", "INSPECTION", "REPLACEMENT"])
                m_history.append({
                    "date": (today - timedelta(days=m_days)).isoformat(),
                    "type": m_type,
                    "description": f"Routine {m_type.lower()} operation on hardware",
                    "performed_by": random.choice(technicians),
                    "cost": float(random.choice([0, 500, 1200, 3500]))
                })

        # Status history
        s_history = [
            {"status": "IN_USE", "changed_at": install_date, "changed_by": tech, "reason": "Initial installation"}
        ]
        if status != "IN_USE":
            s_history.append({
                "status": status,
                "changed_at": (today - timedelta(days=random.randint(1, 60))).isoformat(),
                "changed_by": tech,
                "reason": f"Status updated to {status} during audit"
            })

        doc = {
            "asset_tag": asset_tag,
            "category": cat,
            "make": make,
            "model": model,
            "serial_number": serial_num,
            "location_id": loc_id,
            "installation_date": install_date,
            "installed_by": tech,
            "status": status,
            "warranty": warranty,
            "maintenance_history": m_history,
            "status_history": s_history
        }

        # Category specific fields
        if cat == "SWITCH":
            ports_cnt = random.choice([24, 48])
            doc.update({
                "ip_address": f"172.16.{i % 20}.{10 + i}",
                "mac_address": f"00:11:22:33:{i % 99:02x}:{(i * 3) % 99:02x}",
                "firmware_version": "v16.12",
                "total_ports": ports_cnt
            })
        elif cat == "ROUTER":
            doc.update({
                "ip_address": f"172.16.0.{10 + i}",
                "mac_address": f"00:11:22:00:{i % 99:02x}:{(i * 5) % 99:02x}",
                "firmware_version": "v17.1"
            })
        elif cat == "ACCESS_POINT":
            doc.update({
                "ip_address": f"172.16.50.{10 + i}",
                "mac_address": f"00:11:22:50:{i % 99:02x}:{(i * 7) % 99:02x}",
                "firmware_version": "v8.10",
                "ssid_list": ["MNNIT-WiFi", "MNNIT-Guest"],
                "coverage_area": "Floor level coverage radius ~30m"
            })
        elif cat == "FIREWALL":
            doc.update({
                "ip_address": f"172.16.254.{10 + i}",
                "mac_address": f"00:11:22:FE:{i % 99:02x}:{(i * 2) % 99:02x}",
                "firmware_version": "FortiOS v7.2"
            })
        elif cat == "OPTICAL_DEVICE":
            doc.update({
                "device_type": random.choice(["ONT", "OLT", "MEDIA_CONVERTER"]),
                "ip_address": f"172.16.100.{10 + i}",
                "firmware_version": "v2.1"
            })
        elif cat == "CABLE":
            doc.update({
                "cable_type": random.choice(["LAN", "FIBRE"]),
                "length_m": float(random.choice([1, 3, 5, 10, 50, 100]))
            })
        elif cat == "SFP_MODULE":
            doc.update({
                "speed": random.choice(["1Gbps", "10Gbps"]),
                "wavelength": random.choice(["850nm", "1310nm", "1550nm"])
            })
        elif cat == "RACK":
            doc.update({"units": random.choice([24, 42])})
        elif cat == "PATCH_PANEL":
            doc.update({"port_count": random.choice([24, 48])})
        elif cat == "UPS":
            doc.update({"capacity_va": random.choice([1000, 2000, 3000, 5000])})

        res = await db.na_assets.insert_one(doc)
        a_id = str(res.inserted_id)
        inserted_assets.append(doc)

        if cat == "SWITCH" and status == "IN_USE":
            switches_for_ports.append({"id": a_id, "ports": doc.get("total_ports", 24), "loc": loc_id})
        elif cat == "PATCH_PANEL":
            patch_panels_for_ports.append(a_id)

        asset_counter += 1

    print(f"Inserted {asset_counter - 1} total assets across all 10 categories.")

    # 4. Create Switch Ports mapped to rooms
    total_ports_created = 0
    port_status_counts = {"ACTIVE": 0, "FREE": 0, "FAULTY": 0}

    for sw in switches_for_ports:
        p_count = sw["ports"]
        ports_batch = []
        for p_num in range(1, p_count + 1):
            p_stat = random.choice(["ACTIVE", "ACTIVE", "FREE", "FREE", "FAULTY"])
            p_vlan = random.choice([1, 10, 20, 30, 100])
            p_loc = random.choice(all_room_ids) if p_stat == "ACTIVE" else None
            pp_id = random.choice(patch_panels_for_ports) if patch_panels_for_ports and random.random() > 0.5 else None
            pp_port = random.randint(1, 24) if pp_id else None
            notes = "EXT- Port note" if p_stat == "FAULTY" else None

            ports_batch.append({
                "switch_id": sw["id"],
                "port_number": p_num,
                "status": p_stat,
                "vlan": p_vlan,
                "patch_panel_id": pp_id,
                "patch_panel_port": pp_port,
                "location_id": p_loc,
                "notes": notes
            })
            port_status_counts[p_stat] += 1

        if ports_batch:
            await db.na_switch_ports.insert_many(ports_batch)
            total_ports_created += len(ports_batch)

    print(f"Created {total_ports_created} switch ports across {len(switches_for_ports)} switches.")

    # 5. Create ~16 Extended Stock Items with Transactions
    stock_items_spec = [
        ("Cat6 Cable Box 305m", "EXT-Schneider", "EXT-ACT-C6-305", 2, 5, True),      # Low
        ("Cat6A Shielded Cable Box", "EXT-CommScope", "EXT-CS-C6A-305", 1, 3, True), # Low
        ("1G SX SFP Transceiver", "EXT-FS.com", "EXT-SFP-1G-SX", 0, 4, True),        # Zero
        ("10G SR SFP+ Module", "EXT-Cisco", "EXT-SFP-10G-SR", 2, 6, True),          # Low
        ("RJ45 Connectors (Pack 100)", "EXT-Amphenol", "EXT-RJ45-100", 15, 5, False),
        ("Cat6 Patch Cord 1m", "EXT-D-Link", "EXT-PC-C6-1M", 25, 10, False),
        ("Cat6 Patch Cord 3m", "EXT-D-Link", "EXT-PC-C6-3M", 18, 10, False),
        ("LC-LC Duplex Fibre Cord 5m", "EXT-Molex", "EXT-FC-LC-5M", 3, 5, True),     # Low
        ("LC-SC Fibre Cord 10m", "EXT-Molex", "EXT-FC-LCSC-10M", 8, 4, False),
        ("Keystone Jacks Cat6 (Pack 20)", "EXT-Schneider", "EXT-KJ-C6-20", 12, 5, False),
        ("UPS Battery 12V 9Ah", "EXT-Exide", "EXT-BAT-12V9AH", 6, 4, False),
        ("Rack Mount Power Strip PDU", "EXT-APC", "EXT-PDU-8WAY", 4, 2, False),
        ("Cabinet Spare Fan Tray", "EXT-Valrack", "EXT-FAN-TRAY", 5, 2, False),
        ("Gigabit Media Converter", "EXT-TP-Link", "EXT-MC200CM", 7, 3, False),
        ("48-Port Cable Manager Panel", "EXT-D-Link", "EXT-CM-48P", 9, 3, False),
        ("Fiber Optic Splice Tray", "EXT-CommScope", "EXT-ST-24F", 10, 4, False)
    ]

    store_loc_id = loc_map["academic_campus"]
    low_stock_count = 0
    zero_stock_count = 0

    for name, make, model, final_qty, min_lvl, is_low in stock_items_spec:
        if final_qty <= 0:
            zero_stock_count += 1
        if final_qty <= min_lvl:
            low_stock_count += 1

        item_doc = {
            "item_type": f"EXT- {name}",
            "make": make,
            "model": model,
            "quantity_available": final_qty,
            "minimum_level": min_lvl,
            "store_location_id": store_loc_id,
            "is_low": final_qty <= min_lvl
        }
        item_res = await db.na_stock_items.insert_one(item_doc)
        item_id = str(item_res.inserted_id)

        # Create transactions whose sum matches final_qty
        # Example: initial restock +100, then issues/restocks resulting in final_qty
        initial_qty = final_qty + 50
        txs = [
            {"stock_item_id": item_id, "change": initial_qty, "reason": "EXT- Initial bulk procurement", "by": "MNNIT Admin", "date": (today - timedelta(days=120)).isoformat()},
            {"stock_item_id": item_id, "change": -30, "reason": "EXT- Issued for hostel cabling maintenance", "by": "Technician A", "date": (today - timedelta(days=90)).isoformat()},
            {"stock_item_id": item_id, "change": -20, "reason": "EXT- Issued for lab installation", "by": "Technician B", "date": (today - timedelta(days=60)).isoformat()},
        ]
        curr_sum = initial_qty - 50
        diff = final_qty - curr_sum
        txs.append({"stock_item_id": item_id, "change": diff, "reason": "EXT- Inventory adjustment", "by": "Senior Tech E", "date": (today - timedelta(days=10)).isoformat()})

        await db.na_stock_transactions.insert_many(txs)

    print("Extended stock items and transactions seeded.")

    # 6. Generate Summary
    total_assets_count = await db.na_assets.count_documents({"$or": [{"serial_number": {"$regex": "^EXT-"}}, {"asset_tag": {"$regex": "^EXT-"}}]})

    by_cat_agg = await db.na_assets.aggregate([
        {"$match": {"$or": [{"serial_number": {"$regex": "^EXT-"}}, {"asset_tag": {"$regex": "^EXT-"}}]}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}}
    ]).to_list(length=50)

    by_stat_agg = await db.na_assets.aggregate([
        {"$match": {"$or": [{"serial_number": {"$regex": "^EXT-"}}, {"asset_tag": {"$regex": "^EXT-"}}]}},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]).to_list(length=50)

    # Warranties expiring within 60 days
    cutoff_60 = (today + timedelta(days=60)).isoformat()
    today_str = today.isoformat()
    w_exp_count = await db.na_assets.count_documents({
        "$or": [{"serial_number": {"$regex": "^EXT-"}}, {"asset_tag": {"$regex": "^EXT-"}}],
        "warranty.end_date": {"$gte": today_str, "$lte": cutoff_60}
    })

    print("\n=======================================================")
    print("      EXTENDED NETWORK ASSETS SEED SUMMARY            ")
    print("=======================================================")
    print(f"Total Extended Assets Created  : {total_assets_count}")
    print("\nAssets by Category:")
    for row in by_cat_agg:
        print(f"  - {row['_id']:<15}: {row['count']}")

    print("\nAssets by Status:")
    for row in by_stat_agg:
        print(f"  - {row['_id']:<15}: {row['count']}")

    print(f"\nSwitch Ports Created           : {total_ports_created}")
    print(f"  - ACTIVE                      : {port_status_counts['ACTIVE']}")
    print(f"  - FREE                        : {port_status_counts['FREE']}")
    print(f"  - FAULTY                      : {port_status_counts['FAULTY']}")

    print(f"\nStock Items Created            : {len(stock_items_spec)}")
    print(f"  - Low Stock Alerts            : {low_stock_count}")
    print(f"  - Zero Stock Items            : {zero_stock_count}")
    print(f"\nWarranties Expiring (<60 Days) : {w_exp_count}")
    print("=======================================================\n")

    close_db_client()


if __name__ == "__main__":
    remove_flag = "--remove" in sys.argv
    asyncio.run(seed_network_assets_extended(remove_only=remove_flag))
