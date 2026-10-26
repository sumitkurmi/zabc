# MODULE: Network Asset and Stock Management - this file belongs to the code for this module.
# Shared helper module providing real MNNIT campus location definitions and idempotent creation logic.

from typing import Dict, Any, List, Tuple
from backend.app.network_assets.models import LocationType


# Real campus location definitions matching the complaint form dropdown options
REAL_LOCATIONS_SPEC = [
    {"id_key": "sv_patel", "name": "SV Patel Hostel", "code": "SVPH", "type": LocationType.HOSTEL.value},
    {"id_key": "bg_tilak", "name": "BG Tilak Hostel", "code": "BGTH", "type": LocationType.HOSTEL.value},
    {"id_key": "mm_malviya", "name": "MM Malviya Hostel", "code": "MMMH", "type": LocationType.HOSTEL.value},
    {"id_key": "pd_tandon", "name": "PD Tandon Hostel", "code": "PDTH", "type": LocationType.HOSTEL.value},
    {"id_key": "cv_raman", "name": "CV Raman Hostel", "code": "CVRH", "type": LocationType.HOSTEL.value},
    {"id_key": "rn_tagore", "name": "RN Tagore Hostel", "code": "RNTH", "type": LocationType.HOSTEL.value},
    {"id_key": "svbh", "name": "SVBH Hostel", "code": "SVBH", "type": LocationType.HOSTEL.value},
    {"id_key": "pg_hostel", "name": "PG Hostel", "code": "PGH", "type": LocationType.HOSTEL.value},
    {"id_key": "sn_girls", "name": "SN Girls Hostel", "code": "SNGH", "type": LocationType.HOSTEL.value},
    {"id_key": "ih_b_hostel", "name": "IH-B Hostel", "code": "IHBH", "type": LocationType.HOSTEL.value},
    {"id_key": "kn_girls", "name": "KN Girls Hostel", "code": "KNGH", "type": LocationType.HOSTEL.value},
    {"id_key": "dj_girls", "name": "DJ Girls Hostel", "code": "DJGH", "type": LocationType.HOSTEL.value},
    {"id_key": "residential_colony", "name": "Residential Colony", "code": "RESCOL", "type": LocationType.BUILDING.value},
    {"id_key": "guest_house", "name": "Guest House", "code": "GUESTH", "type": LocationType.BUILDING.value},
    {"id_key": "academic_campus", "name": "Academic Campus", "code": "ACAD", "type": LocationType.BUILDING.value},
    {"id_key": "others", "name": "Others", "code": "OTH", "type": LocationType.BUILDING.value},
]


def get_real_location_types_summary() -> List[Tuple[str, str]]:
    """Returns a list of (location_name, location_type) tuples chosen for each real location."""
    return [(spec["name"], spec["type"]) for spec in REAL_LOCATIONS_SPEC]


async def get_or_create_real_locations(db) -> Dict[str, Any]:
    """Ensures all real MNNIT locations and child room locations exist in MongoDB.

    Args:
        db: Async Motor database instance.

    Returns:
        Dictionary containing created/reused location records mapped by id_key, code, and rooms.
    """
    location_map: Dict[str, str] = {}
    room_map: Dict[str, List[Dict[str, str]]] = {}
    created_count = 0
    reused_count = 0

    # Process parent locations
    for spec in REAL_LOCATIONS_SPEC:
        existing = await db.na_locations.find_one({"$or": [{"code": spec["code"]}, {"name": spec["name"]}]})
        if existing:
            loc_id = str(existing["_id"])
            reused_count += 1
        else:
            res = await db.na_locations.insert_one({
                "name": spec["name"],
                "code": spec["code"],
                "type": spec["type"],
                "parent_id": None
            })
            loc_id = str(res.inserted_id)
            created_count += 1

        location_map[spec["id_key"]] = loc_id
        location_map[spec["code"]] = loc_id
        room_map[loc_id] = []

        # Create 4 sub-rooms under each building / hostel
        room_numbers = [101, 102, 201, 202]
        for room_num in room_numbers:
            r_name = f"Room {room_num}"
            r_code = f"{spec['code']}-R{room_num}"
            existing_room = await db.na_locations.find_one({"code": r_code})
            if existing_room:
                r_id = str(existing_room["_id"])
            else:
                r_res = await db.na_locations.insert_one({
                    "name": r_name,
                    "code": r_code,
                    "type": LocationType.ROOM.value,
                    "parent_id": loc_id
                })
                r_id = str(r_res.inserted_id)
                created_count += 1

            room_map[loc_id].append({
                "id": r_id,
                "name": r_name,
                "code": r_code
            })

    return {
        "location_map": location_map,
        "room_map": room_map,
        "created_count": created_count,
        "reused_count": reused_count
    }
