# MODULE: Network Asset and Stock Management - this file belongs to the code for this module.
# REST API endpoints for Network Asset and Stock Management under /api/admin/network-assets.

import io
import csv
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from backend.app.deps import require_admin
from backend.app.network_assets.models import AssetCategory, AssetStatus, LocationType
from backend.app.network_assets.schemas import (
    AssetCreateRequest,
    AssetUpdateRequest,
    AssetStatusPatchRequest,
    AssetLocationPatchRequest,
    AssetReplaceRequest,
    AssetResponse,
    AssetListResponse,
    MaintenanceRecordSchema,
    LocationCreateRequest,
    LocationUpdateRequest,
    LocationResponse,
    LocationTreeNode,
    LocationDetailResponse,
    SwitchPortCreateBulkRequest,
    SwitchPortUpdateRequest,
    SwitchPortResponse,
    StockCreateRequest,
    StockUpdateRequest,
    StockIssueRequest,
    StockRestockRequest,
    StockResponse,
    StockTransactionResponse,
    SummaryReportResponse
)
from backend.app.network_assets.services import (
    AssetService,
    LocationService,
    PortMappingService,
    StockService
)
from backend.app.network_assets.repository import (
    NetworkAssetRepository,
    LocationRepository,
    SwitchPortRepository,
    StockRepository
)

router = APIRouter(
    prefix="/admin/network-assets",
    tags=["admin_network_assets"],
    dependencies=[Depends(require_admin)]
)


# --- ASSET ENDPOINTS ---

@router.post("/assets", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def create_asset(payload: AssetCreateRequest):
    """Creates a new network asset record."""
    try:
        data = payload.model_dump(exclude_unset=True)
        asset_id = await AssetService.create_asset(data)
        asset = await AssetService.get_asset(asset_id)
        return AssetResponse(**asset)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/assets", response_model=AssetListResponse)
async def list_assets(
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    location_id: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    warranty_expiring_days: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Lists network assets with filters and pagination."""
    res = await AssetService.list_assets(
        category=category,
        status=status,
        location_id=location_id,
        query=q,
        warranty_expiring_days=warranty_expiring_days,
        page=page,
        limit=limit
    )
    assets_out = [AssetResponse(**a) for a in res["assets"]]
    return AssetListResponse(
        assets=assets_out,
        total=res["total"],
        page=res["page"],
        pages=res["pages"]
    )


@router.get("/assets/{asset_id}", response_model=AssetResponse)
async def get_asset_detail(asset_id: str):
    """Retrieves full asset details including warranty and history."""
    try:
        asset = await AssetService.get_asset(asset_id)
        return AssetResponse(**asset)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/assets/{asset_id}", response_model=AssetResponse)
async def update_asset(asset_id: str, payload: AssetUpdateRequest):
    """Edits basic details of an existing asset."""
    try:
        data = payload.model_dump(exclude_unset=True)
        if "warranty" in data and data["warranty"]:
            w = data["warranty"]
            # calculate active flag
            w_obj = Warranty(w.get("start_date"), w.get("end_date"), w.get("vendor"))
            w["is_active"] = w_obj.is_active()

        updated = await NetworkAssetRepository.update_asset(asset_id, data)
        if not updated:
            raise HTTPException(status_code=404, detail="Asset not found")

        asset = await AssetService.get_asset(asset_id)
        return AssetResponse(**asset)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/assets/{asset_id}")
async def delete_asset(asset_id: str):
    """Deletes asset, or marks RETIRED if maintenance history exists."""
    try:
        res = await AssetService.delete_asset(asset_id)
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/assets/{asset_id}/status", response_model=AssetResponse)
async def change_asset_status(asset_id: str, payload: AssetStatusPatchRequest):
    """Transitions asset status requiring a justification reason."""
    try:
        await AssetService.update_asset_status(
            asset_id=asset_id,
            new_status_str=payload.status.value,
            reason=payload.reason,
            changed_by=payload.changed_by or "admin"
        )
        asset = await AssetService.get_asset(asset_id)
        return AssetResponse(**asset)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/assets/{asset_id}/location", response_model=AssetResponse)
async def change_asset_location(asset_id: str, payload: AssetLocationPatchRequest):
    """Moves asset to a new campus location."""
    try:
        await AssetService.update_asset_location(asset_id, payload.location_id)
        asset = await AssetService.get_asset(asset_id)
        return AssetResponse(**asset)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/assets/{asset_id}/replace", response_model=AssetResponse)
async def replace_asset(asset_id: str, payload: AssetReplaceRequest):
    """Marks original asset REPLACED and links new asset ID."""
    try:
        await AssetService.replace_asset(
            asset_id=asset_id,
            new_asset_id=payload.new_asset_id,
            reason=payload.reason or "Replaced hardware",
            changed_by=payload.changed_by or "admin"
        )
        asset = await AssetService.get_asset(asset_id)
        return AssetResponse(**asset)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- MAINTENANCE ENDPOINTS ---

@router.post("/assets/{asset_id}/maintenance", response_model=AssetResponse)
async def add_maintenance_record(asset_id: str, payload: MaintenanceRecordSchema):
    """Adds a maintenance event to asset history."""
    try:
        await AssetService.add_maintenance_record(
            asset_id=asset_id,
            date=payload.date,
            type=payload.type,
            description=payload.description,
            performed_by=payload.performed_by,
            cost=payload.cost
        )
        asset = await AssetService.get_asset(asset_id)
        return AssetResponse(**asset)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/assets/{asset_id}/maintenance", response_model=List[MaintenanceRecordSchema])
async def list_maintenance_history(asset_id: str):
    """Lists maintenance history entries for an asset."""
    try:
        asset = await AssetService.get_asset(asset_id)
        return asset.get("maintenance_history", [])
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# --- LOCATION ENDPOINTS ---

@router.post("/locations", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(payload: LocationCreateRequest):
    """Creates a new campus location record."""
    try:
        loc_id = await LocationService.create_location(
            name=payload.name,
            code=payload.code,
            type_str=payload.type.value,
            parent_id=payload.parent_id
        )
        loc = await LocationRepository.find_by_id(loc_id)
        loc["path"] = await LocationService.get_location_path(loc_id)
        return LocationResponse(**loc)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/locations", response_model=List[LocationTreeNode])
async def list_locations():
    """Returns location hierarchy as a nested tree."""
    tree = await LocationService.list_locations_tree()
    return tree


@router.get("/locations/{loc_id}", response_model=LocationDetailResponse)
async def get_location_detail(loc_id: str):
    """Gets details, installed assets, and switch ports serving location."""
    loc = await LocationRepository.find_by_id(loc_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")

    loc["path"] = await LocationService.get_location_path(loc_id)
    assets_raw = (await NetworkAssetRepository.list_assets(location_id=loc_id, limit=100))["assets"]
    assets_out = [AssetResponse(**a) for a in assets_raw]

    ports = await SwitchPortRepository.list_by_location(loc_id)

    return LocationDetailResponse(
        location=LocationResponse(**loc),
        assets=assets_out,
        ports=ports
    )


@router.put("/locations/{loc_id}", response_model=LocationResponse)
async def update_location(loc_id: str, payload: LocationUpdateRequest):
    """Updates location name, code, type, or parent."""
    data = payload.model_dump(exclude_unset=True)
    if "type" in data and data["type"]:
        data["type"] = data["type"].value if hasattr(data["type"], "value") else str(data["type"])

    updated = await LocationRepository.update_location(loc_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Location not found")

    loc = await LocationRepository.find_by_id(loc_id)
    loc["path"] = await LocationService.get_location_path(loc_id)
    return LocationResponse(**loc)


@router.delete("/locations/{loc_id}")
async def delete_location(loc_id: str):
    """Deletes location if no assets, ports, or children exist in it."""
    try:
        await LocationService.delete_location(loc_id)
        return {"message": "Location deleted successfully."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- SWITCH PORT ENDPOINTS ---

@router.post("/switches/{switch_id}/ports", response_model=List[SwitchPortResponse], status_code=status.HTTP_201_CREATED)
async def bulk_create_ports(switch_id: str, payload: SwitchPortCreateBulkRequest):
    """Bulk creates ports for an Ethernet Switch."""
    try:
        created_ids = await PortMappingService.bulk_create_ports(
            switch_id=switch_id,
            start_port=payload.start_port,
            end_port=payload.end_port,
            vlan=payload.vlan or 1
        )
        ports = await SwitchPortRepository.list_by_switch(switch_id)
        return [SwitchPortResponse(**p) for p in ports]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/switches/{switch_id}/ports", response_model=List[SwitchPortResponse])
async def list_switch_ports(switch_id: str):
    """Lists port map of a switch."""
    ports = await SwitchPortRepository.list_by_switch(switch_id)
    return [SwitchPortResponse(**p) for p in ports]


@router.put("/ports/{port_id}", response_model=SwitchPortResponse)
async def update_port(port_id: str, payload: SwitchPortUpdateRequest):
    """Updates port assignment, VLAN, patch panel link, or status."""
    data = payload.model_dump(exclude_unset=True)
    updated = await SwitchPortRepository.update_port(port_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Port not found")

    port = await SwitchPortRepository.find_by_id(port_id)
    return SwitchPortResponse(**port)


@router.get("/locations/{loc_id}/ports", response_model=List[SwitchPortResponse])
async def list_ports_for_location(loc_id: str):
    """Lists switch ports serving a given room location."""
    ports = await SwitchPortRepository.list_by_location(loc_id)
    return [SwitchPortResponse(**p) for p in ports]


# --- STOCK ENDPOINTS ---

@router.post("/stock", response_model=StockResponse, status_code=status.HTTP_201_CREATED)
async def create_stock_item(payload: StockCreateRequest):
    """Creates a bulk stock item entry."""
    try:
        item_id = await StockService.create_stock_item(
            item_type=payload.item_type,
            make=payload.make,
            model=payload.model,
            quantity_available=payload.quantity_available,
            minimum_level=payload.minimum_level,
            store_location_id=payload.store_location_id
        )
        doc = await StockRepository.find_item_by_id(item_id)
        return StockResponse(**doc)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stock", response_model=List[StockResponse])
async def list_stock_items(low_stock: bool = Query(False)):
    """Lists stock items with optional low_stock filter."""
    items = await StockRepository.list_items(low_stock_only=low_stock)
    return [StockResponse(**i) for i in items]


@router.put("/stock/{item_id}", response_model=StockResponse)
async def update_stock_item(item_id: str, payload: StockUpdateRequest):
    """Edits stock item details."""
    data = payload.model_dump(exclude_unset=True)
    if "quantity_available" in data or "minimum_level" in data:
        item = await StockRepository.find_item_by_id(item_id)
        qty = data.get("quantity_available", item["quantity_available"])
        min_lvl = data.get("minimum_level", item["minimum_level"])
        data["is_low"] = qty <= min_lvl

    updated = await StockRepository.update_item(item_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Stock item not found")

    item = await StockRepository.find_item_by_id(item_id)
    return StockResponse(**item)


@router.post("/stock/{item_id}/issue", response_model=StockResponse)
async def issue_stock(item_id: str, payload: StockIssueRequest):
    """Issues quantity out of inventory."""
    try:
        await StockService.issue_stock(
            item_id=item_id,
            qty=payload.quantity,
            reason=payload.reason,
            by=payload.by or "admin"
        )
        item = await StockRepository.find_item_by_id(item_id)
        return StockResponse(**item)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stock/{item_id}/restock", response_model=StockResponse)
async def restock_stock(item_id: str, payload: StockRestockRequest):
    """Adds restock quantity to inventory."""
    try:
        await StockService.restock_stock(
            item_id=item_id,
            qty=payload.quantity,
            by=payload.by or "admin"
        )
        item = await StockRepository.find_item_by_id(item_id)
        return StockResponse(**item)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stock/{item_id}/transactions", response_model=List[StockTransactionResponse])
async def list_stock_transactions(item_id: str):
    """Lists movement history logs for a stock item."""
    txs = await StockRepository.list_transactions(item_id)
    return [StockTransactionResponse(**t) for t in txs]


# --- REPORT ENDPOINTS ---

@router.get("/reports/summary", response_model=SummaryReportResponse)
async def get_summary_report():
    """Generates counts by category, status, spare, faulty, and low-stock totals."""
    all_assets_res = await NetworkAssetRepository.list_assets(limit=1000)
    assets = all_assets_res["assets"]

    by_category = {}
    by_status = {}
    spare_total = 0
    faulty_total = 0
    under_repair_total = 0

    for a in assets:
        cat = a.get("category", "UNKNOWN")
        st = a.get("status", "UNKNOWN")

        by_category[cat] = by_category.get(cat, 0) + 1
        by_status[st] = by_status.get(st, 0) + 1

        if st == AssetStatus.SPARE.value:
            spare_total += 1
        elif st == AssetStatus.FAULTY.value:
            faulty_total += 1
        elif st == AssetStatus.UNDER_REPAIR.value:
            under_repair_total += 1

    stock_items = await StockRepository.list_items()
    low_stock_count = sum(1 for s in stock_items if s.get("is_low", False))

    return SummaryReportResponse(
        total_assets=len(assets),
        by_category=by_category,
        by_status=by_status,
        spare_total=spare_total,
        faulty_total=faulty_total,
        under_repair_total=under_repair_total,
        low_stock_count=low_stock_count,
        warranty_expiring_soon_count=0
    )


@router.get("/reports/export")
async def export_assets_csv():
    """Generates downloadable CSV file of all network assets."""
    all_assets_res = await NetworkAssetRepository.list_assets(limit=5000)
    assets = all_assets_res["assets"]

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "ID", "Asset Tag", "Category", "Make", "Model", "Serial Number",
        "Location ID", "Status", "Installation Date", "Installed By", "IP Address", "MAC Address"
    ])

    for a in assets:
        writer.writerow([
            a.get("_id"),
            a.get("asset_tag"),
            a.get("category"),
            a.get("make"),
            a.get("model"),
            a.get("serial_number"),
            a.get("location_id"),
            a.get("status"),
            a.get("installation_date"),
            a.get("installed_by"),
            a.get("ip_address", ""),
            a.get("mac_address", "")
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=network_assets_export.csv"}
    )
