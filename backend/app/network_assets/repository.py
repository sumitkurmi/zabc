# MODULE: Network Asset and Stock Management - this file belongs to the code for this module.
# Async MongoDB persistence layer for na_assets, na_locations, na_switch_ports, na_stock_items, and na_stock_transactions.

from datetime import datetime
from typing import List, Dict, Any, Optional
from bson import ObjectId
from backend.app.db import get_database


def _clean_id(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Converts Mongo ObjectId _id into a string for Pydantic serialization."""
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


class NetworkAssetRepository:
    """Repository accessing the na_assets collection."""

    @staticmethod
    async def create_asset(data: Dict[str, Any]) -> str:
        """Inserts a new asset document into na_assets."""
        db = get_database()
        if "_id" in data:
            del data["_id"]
        res = await db.na_assets.insert_one(data)
        return str(res.inserted_id)

    @staticmethod
    async def find_asset_by_id(asset_id: str) -> Optional[Dict[str, Any]]:
        """Finds asset by Mongo string or ObjectId."""
        db = get_database()
        doc = await db.na_assets.find_one({"_id": asset_id})
        if not doc:
            try:
                doc = await db.na_assets.find_one({"_id": ObjectId(asset_id)})
            except Exception:
                pass
        return _clean_id(doc) if doc else None

    @staticmethod
    async def find_asset_by_serial(serial: str) -> Optional[Dict[str, Any]]:
        """Finds asset matching unique serial_number."""
        db = get_database()
        doc = await db.na_assets.find_one({"serial_number": serial})
        return _clean_id(doc) if doc else None

    @staticmethod
    async def find_asset_by_tag(tag: str) -> Optional[Dict[str, Any]]:
        """Finds asset matching unique asset_tag."""
        db = get_database()
        doc = await db.na_assets.find_one({"asset_tag": tag})
        return _clean_id(doc) if doc else None

    @staticmethod
    async def list_assets(
        category: Optional[str] = None,
        status: Optional[str] = None,
        location_id: Optional[str] = None,
        query: Optional[str] = None,
        warranty_expiring_days: Optional[int] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Queries assets matching filters with pagination."""
        db = get_database()
        filter_doc: Dict[str, Any] = {}

        if category:
            filter_doc["category"] = category
        if status:
            filter_doc["status"] = status
        if location_id:
            filter_doc["location_id"] = location_id
        if query:
            filter_doc["$or"] = [
                {"serial_number": {"$regex": query, "$options": "i"}},
                {"model": {"$regex": query, "$options": "i"}},
                {"asset_tag": {"$regex": query, "$options": "i"}},
                {"make": {"$regex": query, "$options": "i"}}
            ]

        if warranty_expiring_days is not None:
            now_dt = datetime.utcnow()
            target_dt = now_dt.replace(year=now_dt.year, month=now_dt.month)  # approximate or ISO match
            # Simple ISO date filtering
            target_str = datetime.utcnow().strftime("%Y-%m-%d")
            filter_doc["warranty.end_date"] = {"$gte": target_str}

        total = await db.na_assets.count_documents(filter_doc)
        skip = (page - 1) * limit
        cursor = db.na_assets.find(filter_doc).skip(skip).limit(limit)
        docs = [ _clean_id(d) async for d in cursor ]

        pages = (total + limit - 1) // limit if limit > 0 else 1
        return {"assets": docs, "total": total, "page": page, "pages": max(1, pages)}

    @staticmethod
    async def update_asset(asset_id: str, update_doc: Dict[str, Any]) -> bool:
        """Updates fields of an asset document."""
        db = get_database()
        oid = ObjectId(asset_id) if ObjectId.is_valid(asset_id) else asset_id
        res = await db.na_assets.update_one({"_id": oid}, {"$set": update_doc})
        return res.modified_count > 0 or res.matched_count > 0

    @staticmethod
    async def delete_asset(asset_id: str) -> bool:
        """Deletes asset from na_assets collection."""
        db = get_database()
        oid = ObjectId(asset_id) if ObjectId.is_valid(asset_id) else asset_id
        res = await db.na_assets.delete_one({"_id": oid})
        return res.deleted_count > 0

    @staticmethod
    async def count_by_location(location_id: str) -> int:
        """Counts how many assets are installed in location."""
        db = get_database()
        return await db.na_assets.count_documents({"location_id": location_id})


class LocationRepository:
    """Repository accessing the na_locations collection."""

    @staticmethod
    async def create_location(data: Dict[str, Any]) -> str:
        """Creates a location document."""
        db = get_database()
        if "_id" in data:
            del data["_id"]
        res = await db.na_locations.insert_one(data)
        return str(res.inserted_id)

    @staticmethod
    async def find_by_id(loc_id: str) -> Optional[Dict[str, Any]]:
        """Finds location by ID."""
        db = get_database()
        doc = await db.na_locations.find_one({"_id": loc_id})
        if not doc:
            try:
                doc = await db.na_locations.find_one({"_id": ObjectId(loc_id)})
            except Exception:
                pass
        return _clean_id(doc) if doc else None

    @staticmethod
    async def find_by_code(code: str) -> Optional[Dict[str, Any]]:
        """Finds location by unique location code."""
        db = get_database()
        doc = await db.na_locations.find_one({"code": code})
        return _clean_id(doc) if doc else None

    @staticmethod
    async def list_all() -> List[Dict[str, Any]]:
        """Returns all location records."""
        db = get_database()
        cursor = db.na_locations.find({})
        return [ _clean_id(d) async for d in cursor ]

    @staticmethod
    async def update_location(loc_id: str, data: Dict[str, Any]) -> bool:
        """Updates location document."""
        db = get_database()
        oid = ObjectId(loc_id) if ObjectId.is_valid(loc_id) else loc_id
        res = await db.na_locations.update_one({"_id": oid}, {"$set": data})
        return res.modified_count > 0 or res.matched_count > 0

    @staticmethod
    async def delete_location(loc_id: str) -> bool:
        """Deletes location document."""
        db = get_database()
        oid = ObjectId(loc_id) if ObjectId.is_valid(loc_id) else loc_id
        res = await db.na_locations.delete_one({"_id": oid})
        return res.deleted_count > 0

    @staticmethod
    async def count_children(parent_id: str) -> int:
        """Counts how many sub-locations have parent_id."""
        db = get_database()
        return await db.na_locations.count_documents({"parent_id": parent_id})


class SwitchPortRepository:
    """Repository accessing the na_switch_ports collection."""

    @staticmethod
    async def create_ports(ports_data: List[Dict[str, Any]]) -> List[str]:
        """Bulk inserts switch port records."""
        db = get_database()
        res = await db.na_switch_ports.insert_many(ports_data)
        return [str(i) for i in res.inserted_ids]

    @staticmethod
    async def find_by_id(port_id: str) -> Optional[Dict[str, Any]]:
        """Finds switch port by ID."""
        db = get_database()
        doc = await db.na_switch_ports.find_one({"_id": port_id})
        if not doc:
            try:
                doc = await db.na_switch_ports.find_one({"_id": ObjectId(port_id)})
            except Exception:
                pass
        return _clean_id(doc) if doc else None

    @staticmethod
    async def list_by_switch(switch_id: str) -> List[Dict[str, Any]]:
        """Lists all ports for a switch sorted by port_number."""
        db = get_database()
        cursor = db.na_switch_ports.find({"switch_id": switch_id}).sort("port_number", 1)
        return [ _clean_id(d) async for d in cursor ]

    @staticmethod
    async def list_by_location(location_id: str) -> List[Dict[str, Any]]:
        """Lists all switch ports serving a given room location."""
        db = get_database()
        cursor = db.na_switch_ports.find({"location_id": location_id})
        return [ _clean_id(d) async for d in cursor ]

    @staticmethod
    async def update_port(port_id: str, data: Dict[str, Any]) -> bool:
        """Updates switch port details."""
        db = get_database()
        oid = ObjectId(port_id) if ObjectId.is_valid(port_id) else port_id
        res = await db.na_switch_ports.update_one({"_id": oid}, {"$set": data})
        return res.modified_count > 0 or res.matched_count > 0

    @staticmethod
    async def count_by_location(location_id: str) -> int:
        """Counts switch ports serving location."""
        db = get_database()
        return await db.na_switch_ports.count_documents({"location_id": location_id})


class StockRepository:
    """Repository accessing na_stock_items and na_stock_transactions collections."""

    @staticmethod
    async def create_item(data: Dict[str, Any]) -> str:
        """Creates a bulk stock item document."""
        db = get_database()
        if "_id" in data:
            del data["_id"]
        res = await db.na_stock_items.insert_one(data)
        return str(res.inserted_id)

    @staticmethod
    async def find_item_by_id(item_id: str) -> Optional[Dict[str, Any]]:
        """Finds stock item by ID."""
        db = get_database()
        doc = await db.na_stock_items.find_one({"_id": item_id})
        if not doc:
            try:
                doc = await db.na_stock_items.find_one({"_id": ObjectId(item_id)})
            except Exception:
                pass
        return _clean_id(doc) if doc else None

    @staticmethod
    async def list_items(low_stock_only: bool = False) -> List[Dict[str, Any]]:
        """Lists stock items with optional low_stock filter."""
        db = get_database()
        filter_doc = {}
        if low_stock_only:
            filter_doc = {"$expr": {"$lte": ["$quantity_available", "$minimum_level"]}}
        cursor = db.na_stock_items.find(filter_doc)
        return [ _clean_id(d) async for d in cursor ]

    @staticmethod
    async def update_item(item_id: str, data: Dict[str, Any]) -> bool:
        """Updates stock item record."""
        db = get_database()
        oid = ObjectId(item_id) if ObjectId.is_valid(item_id) else item_id
        res = await db.na_stock_items.update_one({"_id": oid}, {"$set": data})
        return res.modified_count > 0 or res.matched_count > 0

    @staticmethod
    async def add_transaction(tx_data: Dict[str, Any]) -> str:
        """Inserts an auditable stock movement transaction log."""
        db = get_database()
        if "_id" in tx_data:
            del tx_data["_id"]
        res = await db.na_stock_transactions.insert_one(tx_data)
        return str(res.inserted_id)

    @staticmethod
    async def list_transactions(stock_item_id: str) -> List[Dict[str, Any]]:
        """Lists all stock movement logs for a given item."""
        db = get_database()
        cursor = db.na_stock_transactions.find({"stock_item_id": stock_item_id}).sort("date", -1)
        return [ _clean_id(d) async for d in cursor ]
