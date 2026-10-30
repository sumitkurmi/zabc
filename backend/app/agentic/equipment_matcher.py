# MODULE: Agentic Classification and Assignment (Module 2) - this file belongs to the code for this module.
# Best-effort network asset equipment matcher associating complaints with switches and access points.

import logging
from typing import List, Optional, Dict, Any
from backend.app.db import get_database
from backend.app.network_assets.models import AssetStatus, AssetCategory

logger = logging.getLogger("agentic.equipment_matcher")


async def find_affected_equipment(
    location_name: str,
    problem_category: str,
    address_room: Optional[str] = None
) -> List[str]:
    """Finds up to 5 IN_USE network asset IDs related to a complaint's location and category.

    Args:
        location_name: Name of the complaint location (e.g. "Tandon Hostel").
        problem_category: Routing category (WIFI_PROBLEM, LAN_PROBLEM, LAN_PORT_BROKEN, etc.).
        address_room: Optional room identifier (e.g. "Room 102").

    Returns:
        List of up to 5 asset string IDs. Safe against any repository errors.
    """
    try:
        db = get_database()
        if not location_name:
            return []

        category_upper = problem_category.upper() if problem_category else ""
        if category_upper not in ["WIFI_PROBLEM", "LAN_PROBLEM", "LAN_PORT_BROKEN"]:
            return []

        # 1. Match location in na_locations
        loc_cursor = db.na_locations.find({
            "name": {"$regex": f"^{location_name.strip()}$", "$options": "i"}
        })
        matching_locs = [doc async for doc in loc_cursor]

        if not matching_locs:
            # Partial match search
            loc_cursor = db.na_locations.find({
                "name": {"$regex": location_name.strip(), "$options": "i"}
            })
            matching_locs = [doc async for doc in loc_cursor]

        if not matching_locs:
            return []

        loc_ids = [str(loc["_id"]) for loc in matching_locs]

        # Find child locations (e.g. rooms under building)
        child_cursor = db.na_locations.find({"parent_id": {"$in": loc_ids}})
        child_locs = [doc async for doc in child_cursor]
        all_loc_ids = loc_ids + [str(c["_id"]) for c in child_locs]

        asset_ids = []

        if category_upper == "WIFI_PROBLEM":
            # Find ACCESS_POINT assets IN_USE
            ap_cursor = db.na_assets.find({
                "location_id": {"$in": all_loc_ids},
                "category": AssetCategory.ACCESS_POINT.value,
                "status": AssetStatus.IN_USE.value
            }).limit(5)
            asset_ids = [str(doc["_id"]) async for doc in ap_cursor]

        elif category_upper in ["LAN_PROBLEM", "LAN_PORT_BROKEN"]:
            # If address_room specified, try to find room location first
            room_loc_id = None
            if address_room:
                for child in child_locs:
                    if address_room.lower() in child.get("name", "").lower() or address_room.lower() in child.get("code", "").lower():
                        room_loc_id = str(child["_id"])
                        break

            # If room location found, check switch ports
            switch_ids_from_ports = set()
            if room_loc_id:
                ports_cursor = db.na_switch_ports.find({"location_id": room_loc_id})
                async for port in ports_cursor:
                    if port.get("switch_id"):
                        switch_ids_from_ports.add(str(port["switch_id"]))

            if switch_ids_from_ports:
                switch_cursor = db.na_assets.find({
                    "_id": {"$in": list(switch_ids_from_ports)},
                    "status": AssetStatus.IN_USE.value
                }).limit(5)
                asset_ids = [str(doc["_id"]) async for doc in switch_cursor]

            if not asset_ids:
                # Direct switch search at location
                sw_cursor = db.na_assets.find({
                    "location_id": {"$in": all_loc_ids},
                    "category": AssetCategory.SWITCH.value,
                    "status": AssetStatus.IN_USE.value
                }).limit(5)
                asset_ids = [str(doc["_id"]) async for doc in sw_cursor]

        return asset_ids[:5]

    except Exception as err:
        logger.warning(f"[EquipmentMatcher] Error finding equipment: {err}")
        return []
