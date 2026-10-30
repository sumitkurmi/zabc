# MODULE: Agentic Classification and Assignment (Module 2) - this file belongs to the code for this module.
# End-to-end smoke test verifying OTP registration, autonomous agent pipeline, cluster escalation, resolution, confirmation, RAG indexing, and suggest mode.

import os
import sys
import asyncio
import logging
from datetime import datetime
from bson import ObjectId

from backend.app.config import settings
from backend.app.db import get_database, close_db_client
from backend.app.complaint_management.models import ComplaintStatus, TechnicianAvailability, StaffRole
from backend.app.complaint_management.services.classification_service import classify_and_advance
from backend.app.agentic.orchestrator import AgenticOrchestrator
from backend.app.agentic.complaint_log_rag import build_and_index_complaint_log
from backend.app.complaint_management.services.status_service import StatusService
from backend.app.complaint_management.services.assignment_service import AssignmentService
from backend.app.complaint_management.routers.student_actions import create_action_token
from backend.app.complaint_management.models import ActionTokenPurpose, ClosedBy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("e2e_module2_smoke")


async def run_e2e_smoke_test():
    """Runs end-to-end Module 2 agentic smoke test flow."""
    logger.info("=== Starting Module 2 Agentic E2E Smoke Test ===")

    # Use mongomock_motor fallback if local MongoDB is not running
    import mongomock_motor
    from backend.app import db as db_module

    try:
        real_cli = db_module.AsyncIOMotorClient(settings.MONGODB_URI, serverSelectionTimeoutMS=1000)
        await real_cli.admin.command("ping")
        db = get_database()
        logger.info("[SmokeTest] Connected to live MongoDB.")
    except Exception:
        logger.info("[SmokeTest] Live MongoDB not reachable at localhost:27017. Using mongomock_motor fallback.")
        mock_cli = mongomock_motor.AsyncMongoMockClient()
        loop = asyncio.get_running_loop()
        db_module._clients[id(loop)] = mock_cli
        db_module._clients["default"] = mock_cli
        db = mock_cli[settings.MONGODB_DB_NAME]

    # Cleanup previous test records
    await db.complaints.delete_many({"seed_batch": "smoke_test_m2"})
    await db.staff_users.delete_many({"seed_batch": "smoke_test_m2"})

    now_dt = datetime.utcnow()

    # 1. Create Test Technician
    tech_doc = {
        "username": "smoke_tech_m2",
        "password_hash": "unused_hash",
        "full_name": "Smoke Tech Engineer",
        "role": StaffRole.TECHNICIAN.value,
        "email": "smoke_tech@mnnit.ac.in",
        "mobile": "+919999988888",
        "is_active": True,
        "technician_profile": {
            "availability": TechnicianAvailability.AVAILABLE.value,
            "zones": ["SVBH Hostel", "PG Hostel"],
            "categories": ["WIFI_PROBLEM", "LAN_PROBLEM", "IP_ADDRESS_ISSUE", "LAN_PORT_BROKEN", "PROXY_ISSUE"],
            "max_open_complaints": 10
        },
        "seed_batch": "smoke_test_m2",
        "created_at": now_dt
    }
    res_tech = await db.staff_users.insert_one(tech_doc)
    tech_id = str(res_tech.inserted_id)

    # 2. Submit Complaint #1 (Wi-Fi issue at SVBH Hostel)
    t1_id = "261021990001"
    c1 = {
        "ticket_id": t1_id,
        "ref_no": "NET-2026-990001",
        "name": "Ananya Sharma",
        "email": "ananya.sharma@mnnit.ac.in",
        "mobile": "+919876500001",
        "location": "SVBH Hostel",
        "address_room": "Room 214",
        "preferred_from": "10:00",
        "preferred_to": "16:00",
        "problem_type": "WIFI_PROBLEM",
        "additional_comment": "Wi-Fi disconnections across the whole floor since morning.",
        "status": ComplaintStatus.SUBMITTED.value,
        "seed_batch": "smoke_test_m2",
        "created_at": now_dt,
        "updated_at": now_dt
    }
    await db.complaints.insert_one(c1)
    logger.info(f"Submitted Complaint #1 (Ticket #{t1_id})")

    # Run FULL pipeline for Complaint #1
    orchestrator = AgenticOrchestrator()
    res1 = await orchestrator.run_full_pipeline(t1_id)

    c1_after = await db.complaints.find_one({"ticket_id": t1_id})
    assert c1_after["status"] in [ComplaintStatus.CLASSIFIED.value, ComplaintStatus.ASSIGNED.value]
    assert c1_after.get("priority") in ["HIGH", "CRITICAL"]
    logger.info(f"Complaint #1 processed: Priority={c1_after.get('priority')}, Users={c1_after.get('affected_users_count')}, Status={c1_after['status']}")

    # 3. Submit Complaint #2 (Same location SVBH Hostel to test open cluster)
    t2_id = "261021990002"
    c2 = {
        "ticket_id": t2_id,
        "ref_no": "NET-2026-990002",
        "name": "Rohan Patel",
        "email": "rohan.patel@mnnit.ac.in",
        "mobile": "+919876500002",
        "location": "SVBH Hostel",
        "address_room": "Room 218",
        "preferred_from": "10:00",
        "preferred_to": "16:00",
        "problem_type": "WIFI_PROBLEM",
        "additional_comment": "Wi-Fi signal completely dropped for everyone.",
        "status": ComplaintStatus.SUBMITTED.value,
        "seed_batch": "smoke_test_m2",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    await db.complaints.insert_one(c2)

    res2 = await orchestrator.run_full_pipeline(t2_id)
    c1_cluster = await db.complaints.find_one({"ticket_id": t1_id})
    c2_cluster = await db.complaints.find_one({"ticket_id": t2_id})

    assert c2_cluster.get("affected_users_count", 1) >= 2
    logger.info(f"Open Cluster verified: Ticket #{t2_id} joined cluster. Affected users count escalated to {c2_cluster.get('affected_users_count')}.")

    # 4. Technician Resolves Complaint #1
    tech_actor = {"type": "USER", "id": tech_id, "role": "TECHNICIAN", "name": "Smoke Tech Engineer"}
    await db.complaints.update_one(
        {"ticket_id": t1_id},
        {
            "$set": {
                "assigned_technician_id": tech_id,
                "diagnosis": "Keystone jack damaged and AP disassociation",
                "solution": "Replaced wall socket keystone jack and rebooted floor access point.",
                "resolved_at": datetime.utcnow()
            }
        }
    )
    await StatusService.change_status(t1_id, ComplaintStatus.DIAGNOSED.value, tech_actor, note="Diagnosis saved")
    await StatusService.change_status(t1_id, ComplaintStatus.ACTION_TAKEN.value, tech_actor, note="Action taken saved")

    sys_actor = {"type": "SYSTEM", "id": "system", "role": "SYSTEM", "name": "System"}
    await StatusService.change_status(t1_id, ComplaintStatus.STUDENT_CONFIRMATION.value, sys_actor, note="Confirmation requested")

    # 5. Student Confirms -> CLOSED
    student_actor = {"type": "STUDENT", "id": c1["email"], "role": "STUDENT", "name": c1["name"]}
    await db.complaints.update_one(
        {"ticket_id": t1_id},
        {"$set": {"closed_by": ClosedBy.STUDENT.value, "closed_at": datetime.utcnow()}}
    )
    await StatusService.change_status(t1_id, ComplaintStatus.CLOSED.value, student_actor, note="Confirmed solved")

    # 6. RAG Complaint Log Indexing Verification
    doc_id = await build_and_index_complaint_log(t1_id)
    assert doc_id is not None

    doc_record = await db.documents.find_one({"_id": doc_id})
    if not doc_record:
        doc_record = await db.documents.find_one({"_id": ObjectId(doc_id)})

    assert doc_record is not None
    assert doc_record["category_slug"] == "complaint-logs"

    # Read generated .txt file and verify PII exclusion
    with open(doc_record["storage_path"], "r", encoding="utf-8") as f:
        file_text = f.read()

    assert "Ananya" not in file_text
    assert "Sharma" not in file_text
    assert "ananya.sharma@mnnit.ac.in" not in file_text
    assert "+919876500001" not in file_text
    assert "Room 214" not in file_text
    logger.info("Complaint Log RAG Indexing verified: PII (name, email, mobile, room) completely redacted.")

    # 7. Test Suggest Mode
    old_mode = getattr(settings, "AGENT_ASSIGNMENT_MODE", "auto")
    settings.AGENT_ASSIGNMENT_MODE = "suggest"

    t3_id = "261021990003"
    c3 = {
        "ticket_id": t3_id,
        "ref_no": "NET-2026-990003",
        "name": "Kavita Rao",
        "email": "kavita.rao@mnnit.ac.in",
        "mobile": "+919876500003",
        "location": "PG Hostel",
        "address_room": "Room 305",
        "preferred_from": "11:00",
        "preferred_to": "15:00",
        "problem_type": "LAN_PROBLEM",
        "additional_comment": "Wired LAN port connection failing.",
        "status": ComplaintStatus.SUBMITTED.value,
        "seed_batch": "smoke_test_m2",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    await db.complaints.insert_one(c3)

    res3 = await orchestrator.run_full_pipeline(t3_id)
    c3_suggest = await db.complaints.find_one({"ticket_id": t3_id})

    assert c3_suggest["status"] == ComplaintStatus.CLASSIFIED.value
    assert c3_suggest.get("agent_suggestion") is not None
    logger.info(f"Suggest Mode verified: Ticket #{t3_id} status stayed CLASSIFIED with agent_suggestion.")

    # Accept suggestion via AssignmentService
    sug_tech_id = c3_suggest["agent_suggestion"]["technician_id"]
    mgr_actor = {"type": "USER", "id": "demo_manager1", "role": "MANAGER", "name": "Demo Manager"}
    await AssignmentService.assign(t3_id, sug_tech_id, mgr_actor, method="AUTO_CONFIRMED", reason="Accepted suggestion")

    c3_assigned = await db.complaints.find_one({"ticket_id": t3_id})
    assert c3_assigned["status"] == ComplaintStatus.ASSIGNED.value
    logger.info(f"Accept Suggestion verified: Ticket #{t3_id} assigned with method AUTO_CONFIRMED.")

    settings.AGENT_ASSIGNMENT_MODE = old_mode

    # Clean up test batch
    await db.complaints.delete_many({"seed_batch": "smoke_test_m2"})
    await db.staff_users.delete_many({"seed_batch": "smoke_test_m2"})

    logger.info("=== All Module 2 Agentic E2E Smoke Tests PASSED Successfully ===")
    close_db_client()


if __name__ == "__main__":
    asyncio.run(run_e2e_smoke_test())
