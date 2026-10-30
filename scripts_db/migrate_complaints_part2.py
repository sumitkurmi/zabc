# MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
# Migration script converting Part 1 complaint documents to Part 2 ticket_id schema and status fields.

import sys
import asyncio
from datetime import datetime
from backend.app.db import get_database, close_db_client
from backend.app.complaint_management.services.ticket_service import generate_ticket_id
from backend.app.routers.public_complaints import generate_reference_number


async def migrate_complaints(dry_run: bool = False):
    """Migrates legacy Part 1 complaints to Part 2 schema.

    Args:
        dry_run: If True, prints plan without modifying MongoDB documents.
    """
    db = get_database()
    cursor = db.complaints.find({"ticket_id": {"$exists": False}})
    legacy_list = await cursor.to_list(length=10000)

    print(f"Found {len(legacy_list)} legacy complaint document(s) requiring migration.")

    if dry_run:
        print("Dry-run mode active. No changes will be saved.")

    status_map = {
        "NEW": "CLASSIFIED",
        "IN_PROGRESS": "CLASSIFIED",
        "RESOLVED": "CLOSED"
    }

    migrated_count = 0
    for doc in legacy_list:
        doc_id = doc["_id"]
        created_at = doc.get("created_at", datetime.utcnow())

        ticket_id = await generate_ticket_id(created_at)
        ref_no = doc.get("ref_no") or await generate_reference_number()
        old_status = doc.get("status", "NEW")
        new_status = status_map.get(old_status, "CLASSIFIED")

        update_fields = {
            "ticket_id": ticket_id,
            "ref_no": ref_no,
            "status": new_status,
            "assigned_technician_id": None,
            "assigned_at": None,
            "assignment_count": 0,
            "diagnosis": None,
            "solution": None,
            "resolved_at": doc.get("closed_at") if new_status == "CLOSED" else None,
            "items_used": [],
            "asset_actions": [],
            "previous_attempts": [],
            "reopen_count": 0,
            "confirmation_requested_at": None,
            "closed_at": created_at if new_status == "CLOSED" else None,
            "closed_by": "SYSTEM_MIGRATION" if new_status == "CLOSED" else None,
            "updated_at": datetime.utcnow()
        }

        if dry_run:
            print(f"  [DRY-RUN] Document {doc_id} -> ticket_id: {ticket_id}, ref_no: {ref_no}, status: {old_status} => {new_status}")
        else:
            await db.complaints.update_one({"_id": doc_id}, {"$set": update_fields})
            migrated_count += 1

    print(f"Migration finished. Total migrated documents: {migrated_count}")
    close_db_client()


if __name__ == "__main__":
    is_dry = "--dry-run" in sys.argv
    asyncio.run(migrate_complaints(dry_run=is_dry))
