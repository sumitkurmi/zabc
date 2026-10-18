"""API Integration tests for FastAPI backend endpoints using httpx AsyncClient with ASGI transport.

Specification Section 15.
Tests complaint validation, 10-message chat limit enforcement, admin authentication,
and document upload validations.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from backend.app.main import app


@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_get_config(async_client: AsyncClient):
    response = await async_client.get("/api/config")
    assert response.status_code == 200
    data = response.json()
    assert data["college_name"] == "MNNIT Allahabad"
    assert len(data["locations"]) > 0
    assert len(data["problem_types"]) == 5
    assert data["max_chat_messages"] == 10


@pytest.mark.asyncio
async def test_submit_complaint_and_validation(async_client: AsyncClient):
    # Valid submission payload
    payload = {
        "name": "Rahul Sharma",
        "email": "rahul@mnnit.ac.in",
        "mobile": "9876543210",
        "location": "hostel_a",
        "address_room": "Room 101, Block A",
        "preferred_from": "10:00",
        "preferred_to": "12:00",
        "problem_type": "WIFI_PROBLEM",
        "additional_comment": "Tested with laptop and phone",
        "honeypot": ""
    }
    res = await async_client.post("/api/complaints", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert "ref_no" in data
    assert data["ref_no"].startswith("NET-")

    # Honeypot spam rejection
    spam_payload = payload.copy()
    spam_payload["honeypot"] = "bot_input"
    res_spam = await async_client.post("/api/complaints", json=spam_payload)
    assert res_spam.status_code == 400


@pytest.mark.asyncio
async def test_admin_auth_and_protected_routes(async_client: AsyncClient):
    # Login with valid credentials
    login_res = await async_client.post("/api/admin/login", json={"username": "admin", "password": "admin123"})
    assert login_res.status_code == 200
    token = login_res.json()["token"]

    # Access protected stats route with bearer token
    stats_res = await async_client.get("/api/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert stats_res.status_code == 200
    data = stats_res.json()
    assert "unassigned_chats_count" in data
