# MODULE: Network Asset and Stock Management - this file belongs to the code for this module.
# Business logic service layer for asset management, location hierarchy, switch port mapping, and stock inventory.

from datetime import datetime
from typing import List, Dict, Any, Optional
from backend.app.network_assets.models import (
    AssetCategory,
    AssetStatus,
    LocationType,
    MaintenanceRecord,
    StockItem,
    StockTransaction
)
from backend.app.network_assets.factory import AssetFactory
from backend.app.network_assets.repository import (
    NetworkAssetRepository,
    LocationRepository,
    SwitchPortRepository,
    StockRepository
)


class AssetService:
    """Service layer enforcing asset lifecycle business rules."""

    @staticmethod
    async def create_asset(data: Dict[str, Any]) -> str:
        """Validates uniqueness and creates a new asset document.

        Business Rule: serial_number and asset_tag must be unique.

        Args:
            data: Raw request dictionary.

        Returns:
            Inserted Mongo asset string ID.

        Raises:
            ValueError: If asset_tag or serial_number already exists.
        """
        # Validate unique serial_number
        existing_serial = await NetworkAssetRepository.find_asset_by_serial(data["serial_number"])
        if existing_serial:
            raise ValueError(f"An asset with serial number '{data['serial_number']}' already exists.")

        # Validate unique asset_tag
        existing_tag = await NetworkAssetRepository.find_asset_by_tag(data["asset_tag"])
        if existing_tag:
            raise ValueError(f"An asset with tag '{data['asset_tag']}' already exists.")

        # Instantiate OOP domain object via Factory
        asset_obj = AssetFactory.create(data["category"], data)

        # Record initial status in status_history
        init_status = asset_obj.status.value if hasattr(asset_obj.status, "value") else str(asset_obj.status)
        now_str = datetime.utcnow().isoformat()
        asset_obj.status_history.append({
            "status": init_status,
            "changed_at": now_str,
            "changed_by": data.get("installed_by", "admin"),
            "reason": "Initial asset creation"
        })

        asset_dict = asset_obj.to_dict()
        return await NetworkAssetRepository.create_asset(asset_dict)

    @staticmethod
    async def get_asset(asset_id: str) -> Dict[str, Any]:
        """Retrieves full asset record."""
        asset = await NetworkAssetRepository.find_asset_by_id(asset_id)
        if not asset:
            raise ValueError("Asset not found.")
        return asset

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
        """Queries asset list matching filters with pagination."""
        return await NetworkAssetRepository.list_assets(
            category=category,
            status=status,
            location_id=location_id,
            query=query,
            warranty_expiring_days=warranty_expiring_days,
            page=page,
            limit=limit
        )

    @staticmethod
    async def update_asset_status(asset_id: str, new_status_str: str, reason: str, changed_by: str) -> bool:
        """Transitions asset status enforcing transition constraints.

        Business Rule: FAULTY, REPLACED, RETIRED assets cannot be set IN_USE directly
        without first moving to SPARE or UNDER_REPAIR. Status changes require a reason.

        Args:
            asset_id: Target asset ID.
            new_status_str: New status enum string.
            reason: Required justification.
            changed_by: User changing status.

        Returns:
            True if modified.
        """
        asset_doc = await NetworkAssetRepository.find_asset_by_id(asset_id)
        if not asset_doc:
            raise ValueError("Asset not found.")

        # Instantiate OOP model to invoke business logic method
        asset_obj = AssetFactory.create(asset_doc["category"], asset_doc)
        new_status = AssetStatus(new_status_str)

        # Execute OOP method validation
        asset_obj.change_status(new_status=new_status, by=changed_by, reason=reason)

        # Persist updated status and status_history
        updated_dict = asset_obj.to_dict()
        return await NetworkAssetRepository.update_asset(
            asset_id,
            {
                "status": updated_dict["status"],
                "status_history": updated_dict["status_history"]
            }
        )

    @staticmethod
    async def update_asset_location(asset_id: str, location_id: str) -> bool:
        """Moves asset to a new campus location."""
        asset_doc = await NetworkAssetRepository.find_asset_by_id(asset_id)
        if not asset_doc:
            raise ValueError("Asset not found.")

        location = await LocationRepository.find_by_id(location_id)
        if not location:
            raise ValueError("Target location not found.")

        return await NetworkAssetRepository.update_asset(asset_id, {"location_id": location_id})

    @staticmethod
    async def replace_asset(asset_id: str, new_asset_id: str, reason: str, changed_by: str) -> bool:
        """Links and marks an existing asset REPLACED by a newer asset.

        Business Rule: Sets current asset status to REPLACED and references new_asset_id.
        """
        old_asset = await NetworkAssetRepository.find_asset_by_id(asset_id)
        if not old_asset:
            raise ValueError("Original asset not found.")

        new_asset = await NetworkAssetRepository.find_asset_by_id(new_asset_id)
        if not new_asset:
            raise ValueError("Replacement asset not found.")

        # Update old asset to REPLACED status and link replaced_by_id
        await AssetService.update_asset_status(asset_id, AssetStatus.REPLACED.value, reason, changed_by)
        return await NetworkAssetRepository.update_asset(asset_id, {"replaced_by_id": new_asset_id})

    @staticmethod
    async def add_maintenance_record(
        asset_id: str,
        date: str,
        type: str,
        description: str,
        performed_by: str,
        cost: Optional[float] = None
    ) -> bool:
        """Appends a maintenance record to an asset's history."""
        asset_doc = await NetworkAssetRepository.find_asset_by_id(asset_id)
        if not asset_doc:
            raise ValueError("Asset not found.")

        asset_obj = AssetFactory.create(asset_doc["category"], asset_doc)
        record = MaintenanceRecord(
            date=date,
            type=type,
            description=description,
            performed_by=performed_by,
            cost=cost
        )
        asset_obj.add_maintenance(record)

        updated_dict = asset_obj.to_dict()
        return await NetworkAssetRepository.update_asset(
            asset_id,
            {"maintenance_history": updated_dict["maintenance_history"]}
        )

    @staticmethod
    async def delete_asset(asset_id: str) -> Dict[str, Any]:
        """Deletes asset, or automatically retires it if maintenance history exists.

        Business Rule: An asset with maintenance history is retired instead of deleted.
        """
        asset_doc = await NetworkAssetRepository.find_asset_by_id(asset_id)
        if not asset_doc:
            raise ValueError("Asset not found.")

        m_history = asset_doc.get("maintenance_history", [])
        if m_history and len(m_history) > 0:
            # Asset has maintenance history -> retire instead of deleting
            await AssetService.update_asset_status(
                asset_id,
                AssetStatus.RETIRED.value,
                "Retired automatically due to existing maintenance history",
                "system"
            )
            return {"action": "retired", "message": "Asset has maintenance records; marked RETIRED instead of deleted."}

        # Safe to hard delete
        await NetworkAssetRepository.delete_asset(asset_id)
        return {"action": "deleted", "message": "Asset deleted successfully."}


class LocationService:
    """Service layer for hierarchy locations and room mapping."""

    @staticmethod
    async def create_location(name: str, code: str, type_str: str, parent_id: Optional[str] = None) -> str:
        """Creates a location in the hierarchy preventing orphan rooms and cycles.

        Business Rules:
        - Location code must be unique.
        - Rooms must have a parent (building, hostel or lab).
        - Prevents parent assignment cycles.
        """
        existing = await LocationRepository.find_by_code(code)
        if existing:
            raise ValueError(f"Location with code '{code}' already exists.")

        loc_type = LocationType(type_str)
        if loc_type == LocationType.ROOM and not parent_id:
            raise ValueError("Rooms must have a parent building, hostel, or lab assigned.")

        if parent_id:
            parent = await LocationRepository.find_by_id(parent_id)
            if not parent:
                raise ValueError("Parent location not found.")

        doc = {
            "name": name,
            "code": code,
            "type": loc_type.value,
            "parent_id": parent_id
        }
        return await LocationRepository.create_location(doc)

    @staticmethod
    async def get_location_path(loc_id: str) -> str:
        """Computes breadcrumb path e.g. 'Hostel Block A > Room 214'."""
        parts = []
        curr_id: Optional[str] = loc_id
        visited = set()

        while curr_id and curr_id not in visited:
            visited.add(curr_id)
            loc = await LocationRepository.find_by_id(curr_id)
            if not loc:
                break
            parts.append(loc["name"])
            curr_id = loc.get("parent_id")

        parts.reverse()
        return " > ".join(parts) if parts else "Unknown Location"

    @staticmethod
    async def list_locations_tree() -> List[Dict[str, Any]]:
        """Returns location hierarchy structured as a nested tree."""
        all_locs = await LocationRepository.list_all()

        # Build path for each location
        loc_map = {}
        for l in all_locs:
            l["path"] = await LocationService.get_location_path(l["_id"])
            l["children"] = []
            loc_map[l["_id"]] = l

        root_nodes = []
        for l in all_locs:
            p_id = l.get("parent_id")
            if p_id and p_id in loc_map:
                loc_map[p_id]["children"].append(l)
            else:
                root_nodes.append(l)

        return root_nodes

    @staticmethod
    async def delete_location(loc_id: str) -> bool:
        """Deletes location ensuring no assets, ports, or child locations exist.

        Business Rule: A location cannot be deleted while assets, ports,
        or child locations exist in it.
        """
        # Check sub-locations
        child_count = await LocationRepository.count_children(loc_id)
        if child_count > 0:
            raise ValueError(f"Cannot delete location: contains {child_count} sub-location(s).")

        # Check installed assets
        asset_count = await NetworkAssetRepository.count_by_location(loc_id)
        if asset_count > 0:
            raise ValueError(f"Cannot delete location: contains {asset_count} installed asset(s).")

        # Check switch ports serving this location
        port_count = await SwitchPortRepository.count_by_location(loc_id)
        if port_count > 0:
            raise ValueError(f"Cannot delete location: served by {port_count} switch port(s).")

        return await LocationRepository.delete_location(loc_id)


class PortMappingService:
    """Service layer managing switch port mappings."""

    @staticmethod
    async def bulk_create_ports(switch_id: str, start_port: int, end_port: int, vlan: int = 1) -> List[str]:
        """Bulk creates switch ports validating port number bounds.

        Business Rule: Port number must be between 1 and the switch's total_ports.
        """
        switch_asset = await NetworkAssetRepository.find_asset_by_id(switch_id)
        if not switch_asset:
            raise ValueError("Switch asset not found.")

        if switch_asset.get("category") != AssetCategory.SWITCH.value:
            raise ValueError("Target asset is not an Ethernet Switch.")

        max_ports = switch_asset.get("total_ports", 24)
        if start_port < 1 or end_port > max_ports or start_port > end_port:
            raise ValueError(f"Port range must be between 1 and switch total_ports ({max_ports}).")

        # Check existing ports for switch
        existing_ports = await SwitchPortRepository.list_by_switch(switch_id)
        existing_nums = {p["port_number"] for p in existing_ports}

        ports_to_create = []
        for num in range(start_port, end_port + 1):
            if num not in existing_nums:
                ports_to_create.append({
                    "switch_id": switch_id,
                    "port_number": num,
                    "status": "FREE",
                    "vlan": vlan,
                    "patch_panel_id": None,
                    "patch_panel_port": None,
                    "location_id": None,
                    "notes": None
                })

        if not ports_to_create:
            return []

        return await SwitchPortRepository.create_ports(ports_to_create)


class StockService:
    """Service layer for bulk stock items and transactions."""

    @staticmethod
    async def create_stock_item(
        item_type: str,
        make: str,
        model: str,
        quantity_available: int,
        minimum_level: int,
        store_location_id: str
    ) -> str:
        """Creates a bulk stock item entry."""
        if quantity_available < 0:
            raise ValueError("Quantity available cannot be negative.")

        doc = {
            "item_type": item_type,
            "make": make,
            "model": model,
            "quantity_available": quantity_available,
            "minimum_level": minimum_level,
            "store_location_id": store_location_id,
            "is_low": quantity_available <= minimum_level
        }
        return await StockRepository.create_item(doc)

    @staticmethod
    async def issue_stock(item_id: str, qty: int, reason: str, by: str) -> Dict[str, Any]:
        """Issues stock quantity enforcing non-negative inventory rule.

        Business Rule: Stock quantity can never go below zero. Log transaction.
        """
        item_doc = await StockRepository.find_item_by_id(item_id)
        if not item_doc:
            raise ValueError("Stock item not found.")

        stock_obj = StockItem(
            id=item_doc["_id"],
            item_type=item_doc["item_type"],
            make=item_doc["make"],
            model=item_doc["model"],
            quantity_available=item_doc["quantity_available"],
            minimum_level=item_doc["minimum_level"],
            store_location_id=item_doc["store_location_id"]
        )

        new_qty = stock_obj.issue(qty, by, reason)
        await StockRepository.update_item(item_id, {
            "quantity_available": new_qty,
            "is_low": stock_obj.is_low()
        })

        # Log transaction
        tx_doc = {
            "stock_item_id": item_id,
            "change": -qty,
            "reason": reason,
            "by": by,
            "date": datetime.utcnow().isoformat()
        }
        await StockRepository.add_transaction(tx_doc)

        return {"item_id": item_id, "new_quantity": new_qty, "is_low": stock_obj.is_low()}

    @staticmethod
    async def restock_stock(item_id: str, qty: int, by: str) -> Dict[str, Any]:
        """Restocks quantity into inventory."""
        item_doc = await StockRepository.find_item_by_id(item_id)
        if not item_doc:
            raise ValueError("Stock item not found.")

        stock_obj = StockItem(
            id=item_doc["_id"],
            item_type=item_doc["item_type"],
            make=item_doc["make"],
            model=item_doc["model"],
            quantity_available=item_doc["quantity_available"],
            minimum_level=item_doc["minimum_level"],
            store_location_id=item_doc["store_location_id"]
        )

        new_qty = stock_obj.restock(qty, by)
        await StockRepository.update_item(item_id, {
            "quantity_available": new_qty,
            "is_low": stock_obj.is_low()
        })

        tx_doc = {
            "stock_item_id": item_id,
            "change": qty,
            "reason": "Restock inventory",
            "by": by,
            "date": datetime.utcnow().isoformat()
        }
        await StockRepository.add_transaction(tx_doc)

        return {"item_id": item_id, "new_quantity": new_qty, "is_low": stock_obj.is_low()}
