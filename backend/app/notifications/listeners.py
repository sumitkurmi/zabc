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


async def _build_tech_assignment_context(complaint: Dict[str, Any], tech: Dict[str, Any]) -> Dict[str, Any]:
    """Helper formatting rich assignment context for technician notification emails."""
    db = get_database()
    ticket_id = complaint.get("ticket_id")

    priority = complaint.get("priority", "MEDIUM")
    student_cat = complaint.get("problem_type")
    ai_cat = complaint.get("ai_category") or student_cat
    confidence = complaint.get("ai_confidence", 1.0)
    affected_users = complaint.get("affected_users_count", 1)

    notes = complaint.get("classification_notes") or {}
    summary = notes.get("summary") or complaint.get("additional_comment") or "No description provided."

    # Equipment details
    eq_details_list = []
    eq_ids = complaint.get("affected_equipment_ids") or []
    if eq_ids:
        for eq_id in eq_ids:
            asset = await db.na_assets.find_one({"_id": eq_id})
            if asset:
                eq_details_list.append(f"{asset.get('category')} ({asset.get('make')} {asset.get('model')} at {asset.get('location_id')})")
    eq_str = ", ".join(eq_details_list) if eq_details_list else "None specified"

    # Similar solution snippets
    similar_list = notes.get("similar") or []
    sim_snippets = []
    for s in similar_list:
        tid = s.get("ticket_id")
        snip = s.get("solution_snippet")
        sim_snippets.append(f"Ticket #{tid}: {snip}")
    sim_str = "\n".join(sim_snippets) if sim_snippets else "No similar faults logged."

    # Assignment reason
    assign_details = complaint.get("assignment_details") or {}
    reason = assign_details.get("reason") or "Matched active technician profile, workload, and availability."

    return {
        "name": tech.get("full_name"),
        "technician_name": tech.get("full_name"),
        "priority": priority,
        "student_category": student_cat,
        "agent_category": ai_cat,
        "confidence": f"{float(confidence):.2f}",
        "location": complaint.get("location"),
        "address_room": complaint.get("address_room"),
        "affected_users": affected_users,
        "affected_equipment": eq_str,
        "summary": summary,
        "similar_solutions": sim_str,
        "assignment_reason": reason,
        "to_role": "TECHNICIAN"
    }


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

    # Notify student (NEVER include technician mobile or CC)
    if student_email:
        context = {
            "name": complaint.get("name"),
            "technician_name": tech.get("full_name", "Technician"),
            "to_role": "STUDENT"
        }
        await notify("complaint_assigned", ticket_id, [student_email], context)

    # Notify technician (Include CC list to Computer Centre In-charge)
    if tech_email:
        tech_context = await _build_tech_assignment_context(complaint, tech)
        await notify("complaint_assigned", ticket_id, [tech_email] + cc_emails, tech_context)


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
    """Dispatches ticket closed notice, rating request, and enqueues RAG_INDEX job."""
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

    # Enqueue RAG_INDEX job asynchronously for closed complaint knowledge base
    try:
        from backend.app.agentic.job_queue import JobQueue
        from backend.app.agentic.constants import STAGE_RAG_INDEX
        await JobQueue.enqueue_job(ticket_id, STAGE_RAG_INDEX)
    except Exception as e:
        logger.error(f"[Listeners] Failed enqueuing RAG_INDEX job for ticket '{ticket_id}': {e}")


async def on_complaint_needs_attention(payload: Dict[str, Any]):
    """Dispatches alert to managers and In-charge CC list when complaint cannot be auto-assigned."""
    ticket_id = payload.get("ticket_id")
    reason = payload.get("reason", "No eligible technician found")

    if not ticket_id:
        return

    db = get_database()
    cursor = db.staff_users.find({"role": {"$in": ["MANAGER", "ADMIN"]}, "is_active": True})
    manager_emails = [m["email"] async for m in cursor if m.get("email")]

    cc_emails = get_incharge_cc_emails()
    recipients = list(set(manager_emails + cc_emails))

    if recipients:
        context = {
            "reason": reason,
            "to_role": "MANAGER"
        }
        await notify("complaint_needs_attention", ticket_id, recipients, context)


async def on_technician_availability_changed(payload: Dict[str, Any]):
    """Triggers immediate unassigned complaints sweep when technician becomes AVAILABLE."""
    try:
        from backend.app.agentic.worker import trigger_assignment_sweep
        trigger_assignment_sweep()
    except Exception as e:
        logger.error(f"[Listeners] Error triggering assignment sweep: {e}")


def register_notification_listeners():
    """Registers all notification subscribers with the global event bus."""
    events.subscribe("complaint_registered", on_complaint_registered)
    events.subscribe("complaint_assigned", on_complaint_assigned)
    events.subscribe("complaint_reassigned", on_complaint_reassigned)
    events.subscribe("complaint_solved", on_complaint_solved)
    events.subscribe("complaint_closed", on_complaint_closed)
    events.subscribe("complaint_reopened", on_complaint_reopened)
    events.subscribe("rating_received", on_rating_received)
    events.subscribe("complaint_needs_attention", on_complaint_needs_attention)
    events.subscribe("technician_availability_changed", on_technician_availability_changed)
    logger.info("[Listeners] Registered all complaint notification subscribers.")


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
