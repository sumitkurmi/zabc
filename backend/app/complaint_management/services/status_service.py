# MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
# Single service handling all complaint lifecycle status transitions, history logging, and event emissions.

from datetime import datetime
from typing import Dict, Any, Optional
from backend.app.db import get_database
from backend.app.complaint_management.models import ComplaintStatus, HistoryEventType, HistoryActorType
from backend.app import events

# Transition rules matrix: maps (from_status, to_status) -> allowed actor roles/types
# Roles: "ADMIN", "MANAGER", "TECHNICIAN", "STUDENT", "SYSTEM", "AGENT", "SYSTEM_AUTO"
TRANSITION_RULES = {
    (ComplaintStatus.SUBMITTED, ComplaintStatus.CLASSIFIED): ["SYSTEM", "AGENT", "ADMIN"],
    (ComplaintStatus.CLASSIFIED, ComplaintStatus.ASSIGNED): ["MANAGER", "ADMIN", "AGENT", "SYSTEM"],
    (ComplaintStatus.ASSIGNED, ComplaintStatus.ASSIGNED): ["MANAGER", "ADMIN", "AGENT"],
    (ComplaintStatus.ASSIGNED, ComplaintStatus.DIAGNOSED): ["TECHNICIAN", "MANAGER", "ADMIN"],
    (ComplaintStatus.DIAGNOSED, ComplaintStatus.DIAGNOSED): ["TECHNICIAN", "MANAGER", "ADMIN"],
    (ComplaintStatus.DIAGNOSED, ComplaintStatus.ASSIGNED): ["MANAGER", "ADMIN"],
    (ComplaintStatus.DIAGNOSED, ComplaintStatus.ACTION_TAKEN): ["TECHNICIAN", "MANAGER", "ADMIN"],
    (ComplaintStatus.ACTION_TAKEN, ComplaintStatus.STUDENT_CONFIRMATION): ["SYSTEM", "ADMIN"],
    (ComplaintStatus.STUDENT_CONFIRMATION, ComplaintStatus.CLOSED): ["STUDENT", "SYSTEM_AUTO", "SYSTEM", "ADMIN"],
    (ComplaintStatus.STUDENT_CONFIRMATION, ComplaintStatus.ASSIGNED): ["STUDENT", "SYSTEM", "ADMIN"],
    (ComplaintStatus.STUDENT_CONFIRMATION, ComplaintStatus.CLASSIFIED): ["STUDENT", "SYSTEM", "ADMIN"],
}


class StatusService:
    """Central service managing complaint state transitions with concurrency protection and audit history."""

    @staticmethod
    async def change_status(
        ticket_id: str,
        to_status: str,
        actor: Dict[str, Any],
        note: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Transitions a complaint status enforcing matrix rules and atomic updates.

        Args:
            ticket_id: 12-digit ticket ID string.
            to_status: Target ComplaintStatus value string.
            actor: Dictionary containing 'type' (USER/SYSTEM/AGENT/STUDENT), 'id', 'role', 'name'.
            note: Optional audit log note.
            details: Optional metadata details dictionary.

        Returns:
            Updated complaint document.

        Raises:
            ValueError: If illegal status transition or unauthorized actor role.
        """
        db = get_database()
        complaint = await db.complaints.find_one({"ticket_id": ticket_id})
        if not complaint:
            raise ValueError(f"Complaint ticket '{ticket_id}' not found.")

        from_status = complaint.get("status")
        to_status_enum = ComplaintStatus(to_status) if isinstance(to_status, str) else to_status
        to_status_val = to_status_enum.value

        actor_role = actor.get("role") or actor.get("type", "SYSTEM")

        # Handle JUNK side-status rules
        if to_status_val == ComplaintStatus.JUNK.value:
            if actor_role != "ADMIN":
                raise ValueError("Only ADMIN can mark a complaint as JUNK.")
            if from_status == ComplaintStatus.CLOSED.value:
                raise ValueError("Closed complaints cannot be marked as JUNK.")
        elif from_status == ComplaintStatus.JUNK.value:
            if actor_role != "ADMIN":
                raise ValueError("Only ADMIN can restore a complaint from JUNK.")
            target_restore = complaint.get("previous_status", ComplaintStatus.CLASSIFIED.value)
            if to_status_val != target_restore:
                to_status_val = target_restore
        else:
            rule_key = (ComplaintStatus(from_status), ComplaintStatus(to_status_val))
            allowed_roles = TRANSITION_RULES.get(rule_key)

            if not allowed_roles or actor_role not in allowed_roles:
                raise ValueError(
                    f"Illegal status transition from {from_status} to {to_status_val} for actor role '{actor_role}'."
                )

        now_dt = datetime.utcnow()
        update_doc: Dict[str, Any] = {
            "status": to_status_val,
            "updated_at": now_dt
        }

        if to_status_val == ComplaintStatus.JUNK.value:
            update_doc["previous_status"] = from_status
        elif from_status == ComplaintStatus.JUNK.value:
            update_doc["previous_status"] = None

        result = await db.complaints.find_one_and_update(
            {"ticket_id": ticket_id, "status": from_status},
            {"$set": update_doc},
            return_document=True
        )

        if not result:
            raise ValueError("Status transition failed due to concurrent modification or invalid initial state.")

        history_entry = {
            "ticket_id": ticket_id,
            "event_type": HistoryEventType.JUNK.value if to_status_val in [ComplaintStatus.JUNK.value, "JUNK"] or from_status == "JUNK" else HistoryEventType.STATUS_CHANGE.value,
            "from_status": from_status,
            "to_status": to_status_val,
            "actor_type": actor.get("type", HistoryActorType.SYSTEM.value),
            "actor_id": actor.get("id"),
            "actor_role": actor.get("role"),
            "actor_name": actor.get("name", "System"),
            "note": note,
            "details": details or {},
            "at": now_dt
        }
        await db.complaint_history.insert_one(history_entry)

        event_payload = {
            "ticket_id": ticket_id,
            "from_status": from_status,
            "to_status": to_status_val,
            "actor": actor,
            "complaint": result
        }
        await events.emit("complaint_status_changed", event_payload)

        if to_status_val == ComplaintStatus.JUNK.value:
            await events.emit("complaint_marked_junk", event_payload)

        return result
