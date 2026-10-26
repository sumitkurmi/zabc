# MODULE: Network Asset and Stock Management - this file belongs to the code for this module.
# Pytest suite for network_assets module models, factory, rules, and services.

import pytest
from backend.app.network_assets.models import (
    AssetCategory,
    AssetStatus,
    LocationType,
    Switch,
    AccessPoint,
    StockItem
)
from backend.app.network_assets.factory import AssetFactory
from backend.app.network_assets.services import (
    AssetService,
    StockService,
    LocationService,
    PortMappingService
)


def test_asset_factory_creates_correct_subclass():
    data = {
        "asset_tag": "TEST-SW-01",
        "category": "SWITCH",
        "make": "Cisco",
        "model": "Catalyst 2960",
        "serial_number": "SN-SW-001",
        "location_id": "loc_1",
        "total_ports": 48
    }
    asset = AssetFactory.create("SWITCH", data)
    assert isinstance(asset, Switch)
    assert asset.total_ports == 48
    assert asset.category == AssetCategory.SWITCH

    ap_data = {
        "asset_tag": "TEST-AP-01",
        "category": "ACCESS_POINT",
        "make": "Aruba",
        "model": "AP-505",
        "serial_number": "SN-AP-001",
        "location_id": "loc_1",
        "ssid_list": ["MNNIT-WiFi"],
        "coverage_area": "Block A"
    }
    ap = AssetFactory.create("ACCESS_POINT", ap_data)
    assert isinstance(ap, AccessPoint)
    assert ap.ssid_list == ["MNNIT-WiFi"]


def test_status_change_rules_enforced():
    data = {
        "asset_tag": "TEST-SW-02",
        "category": "SWITCH",
        "make": "Cisco",
        "model": "2960",
        "serial_number": "SN-SW-002",
        "location_id": "loc_1",
        "status": "FAULTY"
    }
    asset = AssetFactory.create("SWITCH", data)

    # Attempting to move directly from FAULTY to IN_USE raises ValueError
    with pytest.raises(ValueError, match="Cannot set status IN_USE directly from FAULTY"):
        asset.change_status(AssetStatus.IN_USE, by="admin", reason="Direct repair attempt")

    # Moving to UNDER_REPAIR first is valid
    asset.change_status(AssetStatus.UNDER_REPAIR, by="admin", reason="Sent to shop")
    assert asset.status == AssetStatus.UNDER_REPAIR

    # Moving from UNDER_REPAIR to IN_USE is valid
    asset.change_status(AssetStatus.IN_USE, by="admin", reason="Repaired successfully")
    assert asset.status == AssetStatus.IN_USE


def test_stock_item_issue_non_negative_rule():
    stock = StockItem(
        id="stock_1",
        item_type="Cat6 Cable Box",
        make="D-Link",
        model="NCB",
        quantity_available=5,
        minimum_level=2,
        store_location_id="store_1"
    )

    # Issue valid quantity
    new_qty = stock.issue(3, by="admin", reason="Testing deployment")
    assert new_qty == 2
    assert stock.is_low()  # 2 <= 2 minimum level

    # Attempt to issue more than available raises ValueError
    with pytest.raises(ValueError, match="Insufficient stock"):
        stock.issue(5, by="admin", reason="Excess issue")
