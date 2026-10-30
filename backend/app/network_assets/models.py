# MODULE: Network Asset and Stock Management - this file belongs to the code for this module.
# Defines OOP domain models, enums, value objects, and asset class hierarchy for network assets.

from abc import ABC
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any


class AssetCategory(str, Enum):
    """Supported network asset categories."""
    SWITCH = "SWITCH"
    ROUTER = "ROUTER"
    ACCESS_POINT = "ACCESS_POINT"
    FIREWALL = "FIREWALL"
    OPTICAL_DEVICE = "OPTICAL_DEVICE"
    CABLE = "CABLE"
    SFP_MODULE = "SFP_MODULE"
    RACK = "RACK"
    PATCH_PANEL = "PATCH_PANEL"
    UPS = "UPS"


class AssetStatus(str, Enum):
    """Lifecycle statuses for a network asset."""
    IN_USE = "IN_USE"
    SPARE = "SPARE"
    FAULTY = "FAULTY"
    UNDER_REPAIR = "UNDER_REPAIR"
    REPLACED = "REPLACED"
    RETIRED = "RETIRED"


class LocationType(str, Enum):
    """Hierarchy types for campus locations."""
    BUILDING = "BUILDING"
    LAB = "LAB"
    HOSTEL = "HOSTEL"
    ROOM = "ROOM"


class Warranty:
    """Value object representing asset warranty metadata."""

    def __init__(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        vendor: Optional[str] = None
    ):
        self.start_date = start_date
        self.end_date = end_date
        self.vendor = vendor

    def is_active(self) -> bool:
        if not self.end_date:
            return False
        try:
            exp = datetime.strptime(self.end_date[:10], "%Y-%m-%d")
            return datetime.utcnow() <= exp
        except Exception:
            return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start_date": self.start_date,
            "end_date": self.end_date,
            "vendor": self.vendor,
            "is_active": self.is_active()
        }


class MaintenanceRecord:
    """Value object representing a maintenance or repair event."""

    def __init__(
        self,
        date: str,
        type: str,
        description: str,
        performed_by: str,
        cost: Optional[float] = None,
        complaint_id: Optional[str] = None
    ):
        self.date = date
        self.type = type
        self.description = description
        self.performed_by = performed_by
        self.cost = cost
        self.complaint_id = complaint_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date,
            "type": self.type,
            "description": self.description,
            "performed_by": self.performed_by,
            "cost": self.cost,
            "complaint_id": self.complaint_id
        }


class StatusChangeRecord:
    """Value object tracking status history transitions."""

    def __init__(self, status: str, changed_at: str, changed_by: str, reason: str):
        self.status = status
        self.changed_at = changed_at
        self.changed_by = changed_by
        self.reason = reason

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "changed_at": self.changed_at,
            "changed_by": self.changed_by,
            "reason": self.reason
        }


class Asset(ABC):
    """Abstract base class representing a physical or logical network asset."""

    def __init__(
        self,
        id: Optional[str],
        asset_tag: str,
        category: AssetCategory,
        make: str,
        model: str,
        serial_number: str,
        location_id: str,
        installation_date: str,
        installed_by: str,
        status: AssetStatus = AssetStatus.SPARE,
        warranty: Optional[Warranty] = None,
        maintenance_history: Optional[List[MaintenanceRecord]] = None,
        status_history: Optional[List[StatusChangeRecord]] = None,
        replaced_by_id: Optional[str] = None
    ):
        self.id = id
        self.asset_tag = asset_tag
        self.category = category
        self.make = make
        self.model = model
        self.serial_number = serial_number
        self.location_id = location_id
        self.installation_date = installation_date
        self.installed_by = installed_by
        self.status = status
        self.warranty = warranty or Warranty()
        self.maintenance_history = maintenance_history or []
        self.status_history = status_history or []
        self.replaced_by_id = replaced_by_id

    def change_status(self, new_status: AssetStatus, by: str, reason: str) -> None:
        if new_status == AssetStatus.IN_USE:
            if self.status in [AssetStatus.FAULTY, AssetStatus.REPLACED, AssetStatus.RETIRED]:
                raise ValueError(
                    f"Cannot set status IN_USE directly from {self.status.value}. "
                    "Asset must be moved to SPARE or UNDER_REPAIR first."
                )

        self.status = new_status
        now_str = datetime.utcnow().isoformat()
        self.status_history.append(StatusChangeRecord(
            status=new_status.value,
            changed_at=now_str,
            changed_by=by,
            reason=reason
        ))

    def add_maintenance(self, record: MaintenanceRecord) -> None:
        self.maintenance_history.append(record)

    def move_to(self, location_id: str) -> None:
        self.location_id = location_id

    def is_under_warranty(self) -> bool:
        return self.warranty.is_active()

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "asset_tag": self.asset_tag,
            "category": self.category.value if isinstance(self.category, AssetCategory) else self.category,
            "make": self.make,
            "model": self.model,
            "serial_number": self.serial_number,
            "location_id": self.location_id,
            "installation_date": self.installation_date,
            "installed_by": self.installed_by,
            "status": self.status.value if isinstance(self.status, AssetStatus) else self.status,
            "warranty": self.warranty.to_dict() if self.warranty else None,
            "maintenance_history": [m.to_dict() for m in self.maintenance_history],
            "status_history": [s.to_dict() for s in self.status_history],
            "replaced_by_id": self.replaced_by_id
        }
        if self.id:
            data["_id"] = self.id
        return data


# --- Device Abstract & Concrete Subclasses ---

class NetworkDevice(Asset, ABC):
    def __init__(
        self,
        ip_address: Optional[str] = None,
        mac_address: Optional[str] = None,
        firmware_version: Optional[str] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.ip_address = ip_address
        self.mac_address = mac_address
        self.firmware_version = firmware_version

    def to_dict(self) -> Dict[str, Any]:
        res = super().to_dict()
        res.update({
            "ip_address": self.ip_address,
            "mac_address": self.mac_address,
            "firmware_version": self.firmware_version
        })
        return res


class Switch(NetworkDevice):
    def __init__(self, total_ports: int = 24, **kwargs):
        kwargs["category"] = AssetCategory.SWITCH
        super().__init__(**kwargs)
        self.total_ports = total_ports

    def to_dict(self) -> Dict[str, Any]:
        res = super().to_dict()
        res["total_ports"] = self.total_ports
        return res


class Router(NetworkDevice):
    def __init__(self, **kwargs):
        kwargs["category"] = AssetCategory.ROUTER
        super().__init__(**kwargs)


class AccessPoint(NetworkDevice):
    def __init__(
        self,
        ssid_list: Optional[List[str]] = None,
        coverage_area: Optional[str] = None,
        **kwargs
    ):
        kwargs["category"] = AssetCategory.ACCESS_POINT
        super().__init__(**kwargs)
        self.ssid_list = ssid_list or []
        self.coverage_area = coverage_area

    def to_dict(self) -> Dict[str, Any]:
        res = super().to_dict()
        res.update({
            "ssid_list": self.ssid_list,
            "coverage_area": self.coverage_area
        })
        return res


class Firewall(NetworkDevice):
    def __init__(self, **kwargs):
        kwargs["category"] = AssetCategory.FIREWALL
        super().__init__(**kwargs)


class OpticalDevice(NetworkDevice):
    def __init__(self, device_type: str = "MEDIA_CONVERTER", **kwargs):
        kwargs["category"] = AssetCategory.OPTICAL_DEVICE
        super().__init__(**kwargs)
        self.device_type = device_type

    def to_dict(self) -> Dict[str, Any]:
        res = super().to_dict()
        res["device_type"] = self.device_type
        return res


class Cable(Asset):
    def __init__(self, cable_type: str = "LAN", length_m: float = 1.0, **kwargs):
        kwargs["category"] = AssetCategory.CABLE
        super().__init__(**kwargs)
        self.cable_type = cable_type
        self.length_m = length_m

    def to_dict(self) -> Dict[str, Any]:
        res = super().to_dict()
        res.update({
            "cable_type": self.cable_type,
            "length_m": self.length_m
        })
        return res


class Accessory(Asset, ABC):
    pass


class SFPModule(Accessory):
    def __init__(self, speed: str = "1Gbps", wavelength: str = "850nm", **kwargs):
        kwargs["category"] = AssetCategory.SFP_MODULE
        super().__init__(**kwargs)
        self.speed = speed
        self.wavelength = wavelength

    def to_dict(self) -> Dict[str, Any]:
        res = super().to_dict()
        res.update({"speed": self.speed, "wavelength": self.wavelength})
        return res


class Rack(Accessory):
    def __init__(self, units: int = 42, **kwargs):
        kwargs["category"] = AssetCategory.RACK
        super().__init__(**kwargs)
        self.units = units

    def to_dict(self) -> Dict[str, Any]:
        res = super().to_dict()
        res["units"] = self.units
        return res


class PatchPanel(Accessory):
    def __init__(self, port_count: int = 24, **kwargs):
        kwargs["category"] = AssetCategory.PATCH_PANEL
        super().__init__(**kwargs)
        self.port_count = port_count

    def to_dict(self) -> Dict[str, Any]:
        res = super().to_dict()
        res["port_count"] = self.port_count
        return res


class UPS(Accessory):
    def __init__(self, capacity_va: int = 1000, **kwargs):
        kwargs["category"] = AssetCategory.UPS
        super().__init__(**kwargs)
        self.capacity_va = capacity_va

    def to_dict(self) -> Dict[str, Any]:
        res = super().to_dict()
        res["capacity_va"] = self.capacity_va
        return res


# --- Location, SwitchPort, and Stock Classes ---

class Location:
    def __init__(
        self,
        id: Optional[str],
        name: str,
        code: str,
        type: LocationType,
        parent_id: Optional[str] = None
    ):
        self.id = id
        self.name = name
        self.code = code
        self.type = type
        self.parent_id = parent_id

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "name": self.name,
            "code": self.code,
            "type": self.type.value if isinstance(self.type, LocationType) else self.type,
            "parent_id": self.parent_id
        }
        if self.id:
            data["_id"] = self.id
        return data


class SwitchPort:
    def __init__(
        self,
        id: Optional[str],
        switch_id: str,
        port_number: int,
        status: str = "FREE",
        vlan: int = 1,
        patch_panel_id: Optional[str] = None,
        patch_panel_port: Optional[int] = None,
        location_id: Optional[str] = None,
        notes: Optional[str] = None
    ):
        self.id = id
        self.switch_id = switch_id
        self.port_number = port_number
        self.status = status
        self.vlan = vlan
        self.patch_panel_id = patch_panel_id
        self.patch_panel_port = patch_panel_port
        self.location_id = location_id
        self.notes = notes

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "switch_id": self.switch_id,
            "port_number": self.port_number,
            "status": self.status,
            "vlan": self.vlan,
            "patch_panel_id": self.patch_panel_id,
            "patch_panel_port": self.patch_panel_port,
            "location_id": self.location_id,
            "notes": self.notes
        }
        if self.id:
            data["_id"] = self.id
        return data


class StockItem:
    def __init__(
        self,
        id: Optional[str],
        item_type: str,
        make: str,
        model: str,
        quantity_available: int,
        minimum_level: int,
        store_location_id: str
    ):
        self.id = id
        self.item_type = item_type
        self.make = make
        self.model = model
        self.quantity_available = quantity_available
        self.minimum_level = minimum_level
        self.store_location_id = store_location_id

    def issue(self, qty: int, by: str, reason: str) -> int:
        if qty <= 0:
            raise ValueError("Issue quantity must be greater than zero.")
        if self.quantity_available < qty:
            raise ValueError(f"Insufficient stock: requested {qty}, available {self.quantity_available}.")
        self.quantity_available -= qty
        return self.quantity_available

    def restock(self, qty: int, by: str) -> int:
        if qty <= 0:
            raise ValueError("Restock quantity must be greater than zero.")
        self.quantity_available += qty
        return self.quantity_available

    def is_low(self) -> bool:
        return self.quantity_available <= self.minimum_level

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "item_type": self.item_type,
            "make": self.make,
            "model": self.model,
            "quantity_available": self.quantity_available,
            "minimum_level": self.minimum_level,
            "store_location_id": self.store_location_id,
            "is_low": self.is_low()
        }
        if self.id:
            data["_id"] = self.id
        return data


class StockTransaction:
    """Auditable log entry for stock movements with optional complaint tracking."""

    def __init__(
        self,
        id: Optional[str],
        stock_item_id: str,
        change: int,
        reason: str,
        by: str,
        date: str,
        complaint_id: Optional[str] = None,
        used_by: Optional[str] = None,
        location_id: Optional[str] = None
    ):
        self.id = id
        self.stock_item_id = stock_item_id
        self.change = change
        self.reason = reason
        self.by = by
        self.date = date
        self.complaint_id = complaint_id
        self.used_by = used_by
        self.location_id = location_id

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "stock_item_id": self.stock_item_id,
            "change": self.change,
            "reason": self.reason,
            "by": self.by,
            "date": self.date,
            "complaint_id": self.complaint_id,
            "used_by": self.used_by,
            "location_id": self.location_id
        }
        if self.id:
            data["_id"] = self.id
        return data
