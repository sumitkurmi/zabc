# MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
# Technician assignment service enforcing availability rules, re-assignment history, and event notification triggers.

from datetime import datetime
from typing import Dict, Any, Optional
from bson import ObjectId
from backend.app.db import get_database
from backend.app.complaint_management.models import ComplaintStatus, HistoryEventType, HistoryActorType, TechnicianAvailability
from backend.app.complaint_management.services.status_service import StatusService
from backend.app import events


class AssignmentService:
    """Service handling technician complaint assignment and re-assignment."""

    @staticmethod
    async def assign(
        ticket_id: str,
        technician_id: str,
        actor: Dict[str, Any],
        method: str = "MANUAL",
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Assigns or re-assigns a complaint to an active, available technician.

        Args:
            ticket_id: 12-digit ticket ID.
            technician_id: Mongo ID string of technician staff user.
            actor: Dict containing 'type', 'id', 'role', 'name'.
            method: 'MANUAL' or 'AUTO'.
            reason: Optional assignment explanation.

        Returns:
            Updated complaint document.

        Raises:
            ValueError: If technician invalid/unavailable or complaint in invalid status.
        """
        db = get_database()

        # 1. Retrieve complaint
        complaint = await db.complaints.find_one({"ticket_id": ticket_id})
        if not complaint:
            raise ValueError(f"Complaint ticket '{ticket_id}' not found.")

        current_status = complaint.get("status")
        if current_status not in [ComplaintStatus.CLASSIFIED.value, ComplaintStatus.ASSIGNED.value, ComplaintStatus.DIAGNOSED.value]:
            raise ValueError(f"Cannot assign complaint in status '{current_status}'. Must be CLASSIFIED, ASSIGNED, or DIAGNOSED.")

        # 2. Retrieve and validate technician
        tech_doc = await db.staff_users.find_one({"_id": technician_id})
        if not tech_doc:
            try:
                tech_doc = await db.staff_users.find_one({"_id": ObjectId(technician_id)})
            except Exception:
                pass

        if not tech_doc:
            raise ValueError(f"Technician ID '{technician_id}' not found.")

        if not tech_doc.get("is_active", True):
            raise ValueError(f"Technician '{tech_doc.get('full_name')}' is deactivated.")

        tech_profile = tech_doc.get("technician_profile") or {}
        if tech_profile.get("availability") != TechnicianAvailability.AVAILABLE.value:
            raise ValueError(f"Technician '{tech_doc.get('full_name')}' is currently UNAVAILABLE.")

        old_tech_id = complaint.get("assigned_technician_id")
        is_reassignment = bool(old_tech_id and old_tech_id != str(tech_doc["_id"]))

        # Retrieve old technician name if reassigning
        old_tech_name = None
        if old_tech_id:
            old_tech = await db.staff_users.find_one({"_id": old_tech_id})
            if not old_tech:
                try:
                    old_tech = await db.staff_users.find_one({"_id": ObjectId(old_tech_id)})
                except Exception:
                    pass
            if old_tech:
                old_tech_name = old_tech.get("full_name")

        now_dt = datetime.utcnow()
        assign_count = complaint.get("assignment_count", 0) + 1

        # 3. Update complaint document (Conditional update for AUTO assignment so manual always wins)
        update_filter: Dict[str, Any] = {"ticket_id": ticket_id}
        if method == "AUTO":
            update_filter["$or"] = [{"assigned_technician_id": None}, {"assigned_technician_id": ""}]

        res = await db.complaints.update_one(
            update_filter,
            {
                "$set": {
                    "assigned_technician_id": str(tech_doc["_id"]),
                    "assigned_at": now_dt,
                    "assignment_count": assign_count
                }
            }
        )

        if method == "AUTO" and res.matched_count == 0:
            # Manual assignment already performed by a manager
            return await db.complaints.find_one({"ticket_id": ticket_id})

        # 4. Transition status to ASSIGNED via StatusService
        updated_complaint = await StatusService.change_status(
            ticket_id=ticket_id,
            to_status=ComplaintStatus.ASSIGNED.value,
            actor=actor,
            note=f"Assigned to {tech_doc.get('full_name')}" if not is_reassignment else f"Reassigned from {old_tech_name or 'Previous Tech'} to {tech_doc.get('full_name')}",
            details={
                "from_technician_id": old_tech_id,
                "from_technician_name": old_tech_name,
                "to_technician_id": str(tech_doc["_id"]),
                "to_technician_name": tech_doc.get("full_name"),
                "method": method,
                "reason": reason
            }
        )

        # 5. Log ASSIGNMENT history entry
        assign_history = {
            "ticket_id": ticket_id,
            "event_type": HistoryEventType.ASSIGNMENT.value,
            "from_status": current_status,
            "to_status": ComplaintStatus.ASSIGNED.value,
            "actor_type": actor.get("type", HistoryActorType.USER.value),
            "actor_id": actor.get("id"),
            "actor_role": actor.get("role"),
            "actor_name": actor.get("name", "Manager"),
            "note": reason or f"Assigned to {tech_doc.get('full_name')}",
            "details": {
                "from_technician_id": old_tech_id,
                "from_technician_name": old_tech_name,
                "to_technician_id": str(tech_doc["_id"]),
                "to_technician_name": tech_doc.get("full_name"),
                "method": method,
                "reason": reason
            },
            "at": now_dt
        }
        await db.complaint_history.insert_one(assign_history)

        # 6. Emit event
        event_name = "complaint_reassigned" if is_reassignment else "complaint_assigned"
        await events.emit(event_name, {
            "ticket_id": ticket_id,
            "technician": tech_doc,
            "old_technician_id": old_tech_id,
            "old_technician_name": old_tech_name,
            "complaint": updated_complaint,
            "actor": actor
        })

        return updated_complaint
