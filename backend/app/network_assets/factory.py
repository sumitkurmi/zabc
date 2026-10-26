# MODULE: Network Asset and Stock Management - this file belongs to the code for this module.
# Implements factory pattern for instantiating concrete Asset subclasses based on category.

from typing import Dict, Any, List
from backend.app.network_assets.models import (
    Asset,
    AssetCategory,
    AssetStatus,
    Warranty,
    MaintenanceRecord,
    StatusChangeRecord,
    Switch,
    Router,
    AccessPoint,
    Firewall,
    OpticalDevice,
    Cable,
    SFPModule,
    Rack,
    PatchPanel,
    UPS
)


class AssetFactory:
    """Factory class to create concrete Asset instance based on AssetCategory."""

    @staticmethod
    def create(category: str, data: Dict[str, Any]) -> Asset:
        """Instantiates and returns the appropriate Asset subclass.

        Args:
            category: String or AssetCategory enum value.
            data: Dictionary containing asset fields.

        Returns:
            Concrete instance of Asset subclass.

        Raises:
            ValueError: If category string is unsupported.
        """
        cat_enum = AssetCategory(category) if isinstance(category, str) else category

        # Extract common warranty
        w_data = data.get("warranty") or {}
        warranty = Warranty(
            start_date=w_data.get("start_date"),
            end_date=w_data.get("end_date"),
            vendor=w_data.get("vendor")
        )

        # Extract maintenance history
        m_history: List[MaintenanceRecord] = []
        for m in data.get("maintenance_history", []):
            m_history.append(MaintenanceRecord(
                date=m.get("date", ""),
                type=m.get("type", ""),
                description=m.get("description", ""),
                performed_by=m.get("performed_by", ""),
                cost=m.get("cost")
            ))

        # Extract status history
        s_history: List[StatusChangeRecord] = []
        for s in data.get("status_history", []):
            s_history.append(StatusChangeRecord(
                status=s.get("status", ""),
                changed_at=s.get("changed_at", ""),
                changed_by=s.get("changed_by", ""),
                reason=s.get("reason", "")
            ))

        common_kwargs = {
            "id": str(data["_id"]) if "_id" in data and data["_id"] else data.get("id"),
            "asset_tag": data["asset_tag"],
            "make": data["make"],
            "model": data["model"],
            "serial_number": data["serial_number"],
            "location_id": data["location_id"],
            "installation_date": data.get("installation_date", ""),
            "installed_by": data.get("installed_by", ""),
            "status": AssetStatus(data.get("status", "SPARE")),
            "warranty": warranty,
            "maintenance_history": m_history,
            "status_history": s_history,
            "replaced_by_id": data.get("replaced_by_id")
        }

        if cat_enum == AssetCategory.SWITCH:
            return Switch(
                total_ports=data.get("total_ports", 24),
                ip_address=data.get("ip_address"),
                mac_address=data.get("mac_address"),
                firmware_version=data.get("firmware_version"),
                **common_kwargs
            )

        elif cat_enum == AssetCategory.ROUTER:
            return Router(
                ip_address=data.get("ip_address"),
                mac_address=data.get("mac_address"),
                firmware_version=data.get("firmware_version"),
                **common_kwargs
            )

        elif cat_enum == AssetCategory.ACCESS_POINT:
            return AccessPoint(
                ssid_list=data.get("ssid_list", []),
                coverage_area=data.get("coverage_area"),
                ip_address=data.get("ip_address"),
                mac_address=data.get("mac_address"),
                firmware_version=data.get("firmware_version"),
                **common_kwargs
            )

        elif cat_enum == AssetCategory.FIREWALL:
            return Firewall(
                ip_address=data.get("ip_address"),
                mac_address=data.get("mac_address"),
                firmware_version=data.get("firmware_version"),
                **common_kwargs
            )

        elif cat_enum == AssetCategory.OPTICAL_DEVICE:
            return OpticalDevice(
                device_type=data.get("device_type", "MEDIA_CONVERTER"),
                ip_address=data.get("ip_address"),
                mac_address=data.get("mac_address"),
                firmware_version=data.get("firmware_version"),
                **common_kwargs
            )

        elif cat_enum == AssetCategory.CABLE:
            return Cable(
                cable_type=data.get("cable_type", "LAN"),
                length_m=data.get("length_m", 1.0),
                **common_kwargs
            )

        elif cat_enum == AssetCategory.SFP_MODULE:
            return SFPModule(
                speed=data.get("speed", "1Gbps"),
                wavelength=data.get("wavelength", "850nm"),
                **common_kwargs
            )

        elif cat_enum == AssetCategory.RACK:
            return Rack(
                units=data.get("units", 42),
                **common_kwargs
            )

        elif cat_enum == AssetCategory.PATCH_PANEL:
            return PatchPanel(
                port_count=data.get("port_count", 24),
                **common_kwargs
            )

        elif cat_enum == AssetCategory.UPS:
            return UPS(
                capacity_va=data.get("capacity_va", 1000),
                **common_kwargs
            )

        else:
            raise ValueError(f"Unsupported asset category: {category}")
