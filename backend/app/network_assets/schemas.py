# MODULE: Network Asset and Stock Management - this file belongs to the code for this module.
# Defines Pydantic validation schemas for Network Asset and Stock API payloads.

from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from backend.app.network_assets.models import AssetCategory, AssetStatus, LocationType


class WarrantySchema(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    vendor: Optional[str] = None
    is_active: Optional[bool] = False


class MaintenanceRecordSchema(BaseModel):
    date: str
    type: str  # REPAIR | SERVICE | REPLACEMENT | INSPECTION
    description: str
    performed_by: str
    cost: Optional[float] = None


class StatusChangeRecordSchema(BaseModel):
    status: str
    changed_at: str
    changed_by: str
    reason: str


class AssetCreateRequest(BaseModel):
    asset_tag: str
    category: AssetCategory
    make: str
    model: str
    serial_number: str
    location_id: str
    installation_date: str
    installed_by: str
    status: Optional[AssetStatus] = AssetStatus.SPARE
    warranty: Optional[WarrantySchema] = None

    # Subclass specific optional attributes
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    firmware_version: Optional[str] = None
    total_ports: Optional[int] = 24
    ssid_list: Optional[List[str]] = None
    coverage_area: Optional[str] = None
    device_type: Optional[str] = None
    cable_type: Optional[str] = None
    length_m: Optional[float] = None
    speed: Optional[str] = None
    wavelength: Optional[str] = None
    units: Optional[int] = None
    port_count: Optional[int] = None
    capacity_va: Optional[int] = None


class AssetUpdateRequest(BaseModel):
    asset_tag: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    location_id: Optional[str] = None
    installation_date: Optional[str] = None
    installed_by: Optional[str] = None
    warranty: Optional[WarrantySchema] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    firmware_version: Optional[str] = None
    total_ports: Optional[int] = None
    ssid_list: Optional[List[str]] = None
    coverage_area: Optional[str] = None
    device_type: Optional[str] = None
    cable_type: Optional[str] = None
    length_m: Optional[float] = None
    speed: Optional[str] = None
    wavelength: Optional[str] = None
    units: Optional[int] = None
    port_count: Optional[int] = None
    capacity_va: Optional[int] = None


class AssetStatusPatchRequest(BaseModel):
    status: AssetStatus
    reason: str
    changed_by: Optional[str] = "admin"


class AssetLocationPatchRequest(BaseModel):
    location_id: str


class AssetReplaceRequest(BaseModel):
    new_asset_id: str
    reason: Optional[str] = "Replaced by newer hardware"
    changed_by: Optional[str] = "admin"


class AssetResponse(BaseModel):
    id: str = Field(alias="_id")
    asset_tag: str
    category: str
    make: str
    model: str
    serial_number: str
    location_id: str
    installation_date: str
    installed_by: str
    status: str
    warranty: Optional[WarrantySchema] = None
    maintenance_history: List[MaintenanceRecordSchema] = []
    status_history: List[StatusChangeRecordSchema] = []
    replaced_by_id: Optional[str] = None

    # Subclass specific fields
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    firmware_version: Optional[str] = None
    total_ports: Optional[int] = None
    ssid_list: Optional[List[str]] = None
    coverage_area: Optional[str] = None
    device_type: Optional[str] = None
    cable_type: Optional[str] = None
    length_m: Optional[float] = None
    speed: Optional[str] = None
    wavelength: Optional[str] = None
    units: Optional[int] = None
    port_count: Optional[int] = None
    capacity_va: Optional[int] = None

    class Config:
        populate_by_name = True


class AssetListResponse(BaseModel):
    assets: List[AssetResponse]
    total: int
    page: int
    pages: int


class LocationCreateRequest(BaseModel):
    name: str
    code: str
    type: LocationType
    parent_id: Optional[str] = None


class LocationUpdateRequest(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    type: Optional[LocationType] = None
    parent_id: Optional[str] = None


class LocationResponse(BaseModel):
    id: str = Field(alias="_id")
    name: str
    code: str
    type: str
    parent_id: Optional[str] = None
    path: Optional[str] = None

    class Config:
        populate_by_name = True


class LocationTreeNode(LocationResponse):
    children: List["LocationTreeNode"] = []


LocationTreeNode.model_rebuild()


class LocationDetailResponse(BaseModel):
    location: LocationResponse
    assets: List[AssetResponse] = []
    ports: List[Dict[str, Any]] = []


class SwitchPortCreateBulkRequest(BaseModel):
    start_port: int = 1
    end_port: int = 24
    vlan: Optional[int] = 1


class SwitchPortUpdateRequest(BaseModel):
    status: Optional[str] = None  # ACTIVE | FREE | FAULTY
    vlan: Optional[int] = None
    patch_panel_id: Optional[str] = None
    patch_panel_port: Optional[int] = None
    location_id: Optional[str] = None
    notes: Optional[str] = None


class SwitchPortResponse(BaseModel):
    id: str = Field(alias="_id")
    switch_id: str
    port_number: int
    status: str
    vlan: int
    patch_panel_id: Optional[str] = None
    patch_panel_port: Optional[int] = None
    location_id: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        populate_by_name = True


class StockCreateRequest(BaseModel):
    item_type: str
    make: str
    model: str
    quantity_available: int
    minimum_level: int
    store_location_id: str


class StockUpdateRequest(BaseModel):
    item_type: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    quantity_available: Optional[int] = None
    minimum_level: Optional[int] = None
    store_location_id: Optional[str] = None


class StockIssueRequest(BaseModel):
    quantity: int
    reason: str
    by: Optional[str] = "admin"


class StockRestockRequest(BaseModel):
    quantity: int
    by: Optional[str] = "admin"


class StockResponse(BaseModel):
    id: str = Field(alias="_id")
    item_type: str
    make: str
    model: str
    quantity_available: int
    minimum_level: int
    store_location_id: str
    is_low: bool

    class Config:
        populate_by_name = True


class StockTransactionResponse(BaseModel):
    id: str = Field(alias="_id")
    stock_item_id: str
    change: int
    reason: str
    by: str
    date: str

    class Config:
        populate_by_name = True


class SummaryReportResponse(BaseModel):
    total_assets: int
    by_category: Dict[str, int]
    by_status: Dict[str, int]
    spare_total: int
    faulty_total: int
    under_repair_total: int
    low_stock_count: int
    warranty_expiring_soon_count: int
