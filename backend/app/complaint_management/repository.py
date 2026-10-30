# MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
# Database repository methods for MongoDB complaint management collections.

from datetime import datetime
from typing import List, Dict, Any, Optional
from bson import ObjectId
from backend.app.db import get_database


class ComplaintRepository:
    """Repository handling database queries for complaints, staff, history, and notifications."""

    @staticmethod
    async def find_complaint_by_ticket_id(ticket_id: str) -> Optional[Dict[str, Any]]:
        db = get_database()
        return await db.complaints.find_one({"ticket_id": ticket_id})

    @staticmethod
    async def find_complaint_by_id(cid: str) -> Optional[Dict[str, Any]]:
        db = get_database()
        doc = await db.complaints.find_one({"_id": cid})
        if not doc:
            try:
                doc = await db.complaints.find_one({"_id": ObjectId(cid)})
            except Exception:
                pass
        return doc

    @staticmethod
    async def find_staff_by_username(username: str) -> Optional[Dict[str, Any]]:
        db = get_database()
        return await db.staff_users.find_one({"username": username.lower().strip()})

    @staticmethod
    async def find_staff_by_id(staff_id: str) -> Optional[Dict[str, Any]]:
        db = get_database()
        doc = await db.staff_users.find_one({"_id": staff_id})
        if not doc:
            try:
                doc = await db.staff_users.find_one({"_id": ObjectId(staff_id)})
            except Exception:
                pass
        return doc

    @staticmethod
    async def get_history_by_ticket_id(ticket_id: str) -> List[Dict[str, Any]]:
        db = get_database()
        cursor = db.complaint_history.find({"ticket_id": ticket_id}).sort("at", 1)
        return await cursor.to_list(length=1000)

    @staticmethod
    async def add_history_entry(entry: Dict[str, Any]) -> str:
        db = get_database()
        if "at" not in entry:
            entry["at"] = datetime.utcnow()
        res = await db.complaint_history.insert_one(entry)
        return str(res.inserted_id)

    @staticmethod
    async def count_open_complaints_for_technician(tech_id: str) -> int:
        db = get_database()
        return await db.complaints.count_documents({
            "assigned_technician_id": tech_id,
            "status": {"$in": ["ASSIGNED", "DIAGNOSED"]}
        })

    @staticmethod
    async def get_rating_for_ticket(ticket_id: str) -> Optional[Dict[str, Any]]:
        db = get_database()
        return await db.ratings.find_one({"ticket_id": ticket_id})
