# MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
# Event subscribers mapping domain events to targeted email notifications.

import logging
from typing import Dict, Any, List
from backend.app.db import get_database
from backend.app.config import settings
from backend.app import events
from backend.app.notifications.service import notify

logger = logging.getLogger("listeners")


def get_incharge_cc_emails() -> List[str]:
    """Parses comma-separated Computer Centre In-charge CC email settings."""
    raw = getattr(settings, "INCHARGE_CC_EMAILS", "")
    if not raw:
        return []
    return [e.strip() for e in raw.split(",") if e.strip()]


async def on_complaint_registered(payload: Dict[str, Any]):
    """Dispatches registration email to student and subscribed admins."""
    complaint = payload.get("complaint", {})
    ticket_id = payload.get("ticket_id")
    student_email = complaint.get("email")

    if not student_email or not ticket_id:
        return

    # Notify student
    context = {
        "name": complaint.get("name"),
        "problem_type": complaint.get("problem_type"),
        "location": complaint.get("location"),
        "address_room": complaint.get("address_room"),
        "created_at": str(complaint.get("created_at")),
        "to_role": "STUDENT"
    }
    await notify("complaint_registered", ticket_id, [student_email], context)

    # Notify subscribed admins
    db = get_database()
    cursor = db.staff_users.find({"role": "ADMIN", "notify_on_new_complaint": True, "is_active": True})
    admin_emails = [a["email"] async for a in cursor if a.get("email")]

    if admin_emails:
        admin_context = context.copy()
        admin_context["to_role"] = "ADMIN"
        await notify("complaint_registered", ticket_id, admin_emails, admin_context)


async def on_complaint_assigned(payload: Dict[str, Any]):
    """Dispatches assignment notification to student and assigned technician."""
    complaint = payload.get("complaint", {})
    ticket_id = payload.get("ticket_id")
    tech = payload.get("technician", {})

    student_email = complaint.get("email")
    tech_email = tech.get("email")

    if not ticket_id:
        return

    cc_emails = get_incharge_cc_emails()

    # Notify student
    if student_email:
        context = {
            "name": complaint.get("name"),
            "technician_name": tech.get("full_name", "Technician"),
            "to_role": "STUDENT"
        }
        await notify("complaint_assigned", ticket_id, [student_email] + cc_emails, context)

    # Notify technician
    if tech_email:
        tech_context = {
            "name": tech.get("full_name"),
            "technician_name": tech.get("full_name"),
            "to_role": "TECHNICIAN"
        }
        await notify("complaint_assigned", ticket_id, [tech_email], tech_context)


async def on_complaint_reassigned(payload: Dict[str, Any]):
    """Dispatches reassignment notification to student, new technician, and old technician."""
    complaint = payload.get("complaint", {})
    ticket_id = payload.get("ticket_id")
    new_tech = payload.get("technician", {})
    old_tech_id = payload.get("old_technician_id")

    student_email = complaint.get("email")
    new_tech_email = new_tech.get("email")

    if not ticket_id:
        return

    # Notify student
    if student_email:
        context = {
            "name": complaint.get("name"),
            "technician_name": new_tech.get("full_name", "Technician"),
            "to_role": "STUDENT"
        }
        await notify("complaint_reassigned", ticket_id, [student_email], context)

    # Notify new technician
    if new_tech_email:
        new_context = {
            "name": new_tech.get("full_name"),
            "technician_name": new_tech.get("full_name"),
            "to_role": "TECHNICIAN"
        }
        await notify("complaint_assigned", ticket_id, [new_tech_email], new_context)

    # Notify old technician
    if old_tech_id:
        db = get_database()
        old_tech = await db.staff_users.find_one({"_id": old_tech_id})
        if old_tech and old_tech.get("email"):
            old_context = {
                "name": old_tech.get("full_name"),
                "technician_name": old_tech.get("full_name"),
                "to_role": "TECHNICIAN"
            }
            await notify("complaint_reassigned", ticket_id, [old_tech["email"]], old_context)


async def on_complaint_solved(payload: Dict[str, Any]):
    """Dispatches solution notification with confirmation token link to student and copy to technician."""
    complaint = payload.get("complaint", {})
    ticket_id = payload.get("ticket_id")
    confirm_token = payload.get("confirm_token")
    tech_name = payload.get("technician_name", "Technician")

    student_email = complaint.get("email")
    if not student_email or not ticket_id:
        return

    context = {
        "name": complaint.get("name"),
        "technician_name": tech_name,
        "diagnosis": complaint.get("diagnosis", "N/A"),
        "solution": complaint.get("solution", "N/A"),
        "confirm_token": confirm_token,
        "to_role": "STUDENT"
    }
    await notify("complaint_solved", ticket_id, [student_email], context)


async def on_complaint_closed(payload: Dict[str, Any]):
    """Dispatches ticket closed notice and rating request token link to student."""
    complaint = payload.get("complaint", {})
    ticket_id = payload.get("ticket_id")
    rate_token = payload.get("rate_token")

    student_email = complaint.get("email")
    if not student_email or not ticket_id:
        return

    cc_emails = get_incharge_cc_emails()

    context = {
        "name": complaint.get("name"),
        "closed_by_text": f"Closed by {complaint.get('closed_by', 'Student')}",
        "to_role": "STUDENT"
    }
    await notify("complaint_closed", ticket_id, [student_email] + cc_emails, context)

    # Dispatch rating request email to student
    if rate_token:
        tech_name = "Technician"
        tech_id = complaint.get("assigned_technician_id")
        if tech_id:
            db = get_database()
            tech = await db.staff_users.find_one({"_id": tech_id})
            if tech:
                tech_name = tech.get("full_name", "Technician")

        rate_context = {
            "name": complaint.get("name"),
            "technician_name": tech_name,
            "rate_token": rate_token,
            "to_role": "STUDENT"
        }
        await notify("rating_request", ticket_id, [student_email], rate_context)


async def on_complaint_reopened(payload: Dict[str, Any]):
    """Dispatches reopened notification to student and assigned technician."""
    complaint = payload.get("complaint", {})
    ticket_id = payload.get("ticket_id")
    student_email = complaint.get("email")

    if not student_email or not ticket_id:
        return

    context = {
        "name": complaint.get("name"),
        "to_role": "STUDENT"
    }
    await notify("complaint_reopened", ticket_id, [student_email], context)

    # Notify technician
    tech_id = complaint.get("assigned_technician_id")
    if tech_id:
        db = get_database()
        tech = await db.staff_users.find_one({"_id": tech_id})
        if tech and tech.get("email"):
            tech_context = {
                "name": tech.get("full_name"),
                "to_role": "TECHNICIAN"
            }
            await notify("complaint_reopened", ticket_id, [tech["email"]], tech_context)


async def on_rating_received(payload: Dict[str, Any]):
    """Dispatches rating received notification to the assigned technician."""
    ticket_id = payload.get("ticket_id")
    tech_id = payload.get("technician_id")
    rating = payload.get("rating")
    feedback = payload.get("feedback")

    if not tech_id or not ticket_id:
        return

    db = get_database()
    tech = await db.staff_users.find_one({"_id": tech_id})
    if tech and tech.get("email"):
        context = {
            "rating": rating,
            "feedback": feedback,
            "to_role": "TECHNICIAN"
        }
        await notify("rating_received", ticket_id, [tech["email"]], context)


def register_notification_listeners():
    """Registers all notification subscribers with the global event bus."""
    events.subscribe("complaint_registered", on_complaint_registered)
    events.subscribe("complaint_assigned", on_complaint_assigned)
    events.subscribe("complaint_reassigned", on_complaint_reassigned)
    events.subscribe("complaint_solved", on_complaint_solved)
    events.subscribe("complaint_closed", on_complaint_closed)
    events.subscribe("complaint_reopened", on_complaint_reopened)
    events.subscribe("rating_received", on_rating_received)
    logger.info("[Listeners] Registered all complaint notification subscribers.")
