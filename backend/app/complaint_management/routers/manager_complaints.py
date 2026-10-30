# MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
# Manager and Admin complaint management router for monitoring, assigning, technician availability, and reports.

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from backend.app.db import get_database
from backend.app.auth.jwt_auth import require_roles
from backend.app.complaint_management.models import ComplaintStatus, TechnicianAvailability
from backend.app.complaint_management.schemas import (
    AssignComplaintPayload,
    TechnicianAvailabilityPayload,
    ComplaintDetailResponse,
    ComplaintListResponse,
    HistoryItemResponse
)
from backend.app.complaint_management.services.assignment_service import AssignmentService

router = APIRouter(prefix="/manager", tags=["manager-complaints"])


@router.get("/summary")
async def get_manager_summary(staff_user: dict = Depends(require_roles("MANAGER", "ADMIN"))):
    """Returns manager dashboard summary metrics cards including priority counts and unassigned counts."""
    db = get_database()

    open_unassigned = await db.complaints.count_documents({
        "status": ComplaintStatus.CLASSIFIED.value,
        "assigned_technician_id": None
    })

    all_open = await db.complaints.count_documents({
        "status": {"$nin": [ComplaintStatus.CLOSED.value, ComplaintStatus.JUNK.value]}
    })

    start_of_today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    closed_today = await db.complaints.count_documents({
        "status": ComplaintStatus.CLOSED.value,
        "closed_at": {"$gte": start_of_today}
    })

    total_closed = await db.complaints.count_documents({
        "status": ComplaintStatus.CLOSED.value
    })

    # Priority counts for open complaints
    open_query = {"status": {"$nin": [ComplaintStatus.CLOSED.value, ComplaintStatus.JUNK.value]}}
    p_critical = await db.complaints.count_documents({**open_query, "priority": "CRITICAL"})
    p_high = await db.complaints.count_documents({**open_query, "priority": "HIGH"})
    p_medium = await db.complaints.count_documents({**open_query, "priority": "MEDIUM"})
    p_low = await db.complaints.count_documents({**open_query, "priority": "LOW"})

    return {
        "open_unassigned": open_unassigned,
        "unassigned_count": open_unassigned,
        "all_open": all_open,
        "closed_today": closed_today,
        "total_closed": total_closed,
        "by_priority": {
            "CRITICAL": p_critical,
            "HIGH": p_high,
            "MEDIUM": p_medium,
            "LOW": p_low
        }
    }


async def _build_agent_analysis_data(c: Dict[str, Any], is_manager_or_admin: bool) -> Dict[str, Any]:
    """Helper constructing agent_analysis metadata dictionary for complaint detail API response."""
    db = get_database()
    notes = c.get("classification_notes") or {}

    # Equipment details
    eq_details = []
    eq_ids = c.get("affected_equipment_ids") or []
    if eq_ids:
        for eq_id in eq_ids:
            asset = await db.na_assets.find_one({"_id": eq_id})
            if asset:
                eq_details.append({
                    "id": str(asset["_id"]),
                    "category": asset.get("category"),
                    "make": asset.get("make"),
                    "model": asset.get("model"),
                    "location_id": asset.get("location_id"),
                    "status": asset.get("status")
                })

    # Candidates breakdown
    assign_details = c.get("assignment_details") or {}
    raw_candidates = assign_details.get("top_candidates") or []
    processed_candidates = []

    for cand in raw_candidates:
        cand_dict = cand.copy() if isinstance(cand, dict) else dict(cand)
        if not is_manager_or_admin:
            cand_dict.pop("score", None)
            cand_dict.pop("breakdown", None)
        processed_candidates.append(cand_dict)

    return {
        "student_category": c.get("problem_type"),
        "ai_category": c.get("ai_category"),
        "ai_confidence": c.get("ai_confidence"),
        "priority": c.get("priority", "MEDIUM"),
        "priority_reason": notes.get("priority_reason"),
        "affected_users_count": c.get("affected_users_count", 1),
        "affected_equipment_ids": eq_ids,
        "affected_equipment": eq_details,
        "similar_complaints": notes.get("similar", []),
        "assignment_reason": assign_details.get("reason"),
        "top_candidates": processed_candidates,
        "agent_suggestion": c.get("agent_suggestion"),
        "method": notes.get("method", "manual"),
        "provider": notes.get("provider"),
        "model": notes.get("model"),
        "analyzed_at": notes.get("analyzed_at")
    }


@router.get("/complaints")
async def list_manager_complaints(
    view: str = Query("open", regex="^(open_unassigned|open|closed|all)$"),
    status_filter: Optional[str] = Query(None, alias="status"),
    priority_filter: Optional[str] = Query(None, alias="priority"),
    problem_type: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    technician_id: Optional[str] = Query(None),
    sort: Optional[str] = Query("priority"),
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    staff_user: dict = Depends(require_roles("MANAGER", "ADMIN"))
):
    """Lists complaints with priority filtering, priority sorting, search, and pagination."""
    db = get_database()
    query: Dict[str, Any] = {}

    # Exclude JUNK from manager views
    if view == "open_unassigned":
        query["status"] = ComplaintStatus.CLASSIFIED.value
        query["assigned_technician_id"] = None
    elif view == "open":
        query["status"] = {"$nin": [ComplaintStatus.CLOSED.value, ComplaintStatus.JUNK.value]}
    elif view == "closed":
        query["status"] = ComplaintStatus.CLOSED.value
    else:  # 'all'
        query["status"] = {"$ne": ComplaintStatus.JUNK.value}

    if status_filter:
        query["status"] = status_filter
    if priority_filter:
        query["priority"] = priority_filter.upper()
    if problem_type:
        query["$or"] = [{"problem_type": problem_type}, {"ai_category": problem_type}]
    if location:
        query["location"] = location
    if technician_id:
        query["assigned_technician_id"] = technician_id
    if q:
        query["$or"] = [
            {"ticket_id": {"$regex": q.strip(), "$options": "i"}},
            {"name": {"$regex": q.strip(), "$options": "i"}},
            {"email": {"$regex": q.strip(), "$options": "i"}}
        ]

    total = await db.complaints.count_documents(query)
    cursor = db.complaints.find(query)
    all_matching = [doc async for doc in cursor]

    # Sort logic: priority then age (created_at ASC/DESC)
    priority_rank = {"CRITICAL": 1, "HIGH": 2, "MEDIUM": 3, "LOW": 4}

    if sort == "priority" or view == "open_unassigned":
        def p_sort_key(doc):
            p = doc.get("priority", "MEDIUM").upper()
            return (priority_rank.get(p, 3), doc.get("created_at") or datetime.max)
        all_matching.sort(key=p_sort_key)
    else:
        all_matching.sort(key=lambda d: d.get("created_at") or datetime.min, reverse=True)

    skip = (page - 1) * limit
    paged_docs = all_matching[skip:skip + limit]

    complaints_list = []
    for c in paged_docs:
        tech_name = None
        t_id = c.get("assigned_technician_id")
        if t_id:
            tech = await db.staff_users.find_one({"_id": t_id})
            if tech:
                tech_name = tech.get("full_name")

        hist_cursor = db.complaint_history.find({"ticket_id": c["ticket_id"]}).sort("at", 1)
        history_items = [
            HistoryItemResponse(
                event_type=h["event_type"],
                from_status=h.get("from_status"),
                to_status=h.get("to_status"),
                actor_type=h.get("actor_type", "SYSTEM"),
                actor_name=h.get("actor_name", "System"),
                note=h.get("note"),
                details=h.get("details"),
                at=h.get("at", datetime.utcnow())
            ) async for h in hist_cursor
        ]

        rating_info = await db.ratings.find_one({"ticket_id": c["ticket_id"]})
        agent_analysis = await _build_agent_analysis_data(c, is_manager_or_admin=True)

        complaints_list.append(
            ComplaintDetailResponse(
                _id=str(c["_id"]),
                ticket_id=c["ticket_id"],
                name=c["name"],
                email=c["email"],
                mobile=c["mobile"],
                location=c["location"],
                address_room=c["address_room"],
                preferred_from=c["preferred_from"],
                preferred_to=c["preferred_to"],
                problem_type=c["problem_type"],
                additional_comment=c.get("additional_comment", ""),
                chat_id=c.get("chat_id"),
                filled_by_ai=c.get("filled_by_ai", False),
                status=c["status"],
                assigned_technician_id=t_id,
                assigned_technician_name=tech_name,
                assigned_at=c.get("assigned_at"),
                assignment_count=c.get("assignment_count", 0),
                diagnosis=c.get("diagnosis"),
                solution=c.get("solution"),
                resolved_at=c.get("resolved_at"),
                items_used=c.get("items_used", []),
                asset_actions=c.get("asset_actions", []),
                previous_attempts=c.get("previous_attempts", []),
                reopen_count=c.get("reopen_count", 0),
                confirmation_requested_at=c.get("confirmation_requested_at"),
                closed_at=c.get("closed_at"),
                closed_by=c.get("closed_by"),
                priority=c.get("priority", "MEDIUM"),
                ai_category=c.get("ai_category"),
                ai_confidence=c.get("ai_confidence"),
                affected_users_count=c.get("affected_users_count", 1),
                agent_suggestion=c.get("agent_suggestion"),
                agent_analysis=agent_analysis,
                agent_status=c.get("agent_status"),
                created_at=c["created_at"],
                updated_at=c.get("updated_at", c["created_at"]),
                history=history_items,
                rating_info={"rating": rating_info["rating"], "feedback": rating_info.get("feedback")} if rating_info else None
            )
        )

    pages = (total + limit - 1) // limit if total > 0 else 1
    return {
        "complaints": complaints_list,
        "total": total,
        "page": page,
        "pages": pages
    }


@router.get("/complaints/{ticket_id}", response_model=ComplaintDetailResponse)
async def get_manager_complaint_detail(ticket_id: str, staff_user: dict = Depends(require_roles("MANAGER", "ADMIN"))):
    """Returns full complaint detail including history timeline, resolution items, and linked chat transcript."""
    db = get_database()
    c = await db.complaints.find_one({"ticket_id": ticket_id})
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint ticket not found")

    tech_name = None
    t_id = c.get("assigned_technician_id")
    if t_id:
        tech = await db.staff_users.find_one({"_id": t_id})
        if tech:
            tech_name = tech.get("full_name")

    hist_cursor = db.complaint_history.find({"ticket_id": ticket_id}).sort("at", 1)
    history_items = [
        HistoryItemResponse(
            event_type=h["event_type"],
            from_status=h.get("from_status"),
            to_status=h.get("to_status"),
            actor_type=h.get("actor_type", "SYSTEM"),
            actor_name=h.get("actor_name", "System"),
            note=h.get("note"),
            details=h.get("details"),
            at=h.get("at", datetime.utcnow())
        ) async for h in hist_cursor
    ]

    rating_info = await db.ratings.find_one({"ticket_id": ticket_id})
    agent_analysis = await _build_agent_analysis_data(c, is_manager_or_admin=True)

    return ComplaintDetailResponse(
        _id=str(c["_id"]),
        ticket_id=c["ticket_id"],
        name=c["name"],
        email=c["email"],
        mobile=c["mobile"],
        location=c["location"],
        address_room=c["address_room"],
        preferred_from=c["preferred_from"],
        preferred_to=c["preferred_to"],
        problem_type=c["problem_type"],
        additional_comment=c.get("additional_comment", ""),
        chat_id=c.get("chat_id"),
        filled_by_ai=c.get("filled_by_ai", False),
        status=c["status"],
        assigned_technician_id=t_id,
        assigned_technician_name=tech_name,
        assigned_at=c.get("assigned_at"),
        assignment_count=c.get("assignment_count", 0),
        diagnosis=c.get("diagnosis"),
        solution=c.get("solution"),
        resolved_at=c.get("resolved_at"),
        items_used=c.get("items_used", []),
        asset_actions=c.get("asset_actions", []),
        previous_attempts=c.get("previous_attempts", []),
        reopen_count=c.get("reopen_count", 0),
        confirmation_requested_at=c.get("confirmation_requested_at"),
        closed_at=c.get("closed_at"),
        closed_by=c.get("closed_by"),
        priority=c.get("priority", "MEDIUM"),
        ai_category=c.get("ai_category"),
        ai_confidence=c.get("ai_confidence"),
        affected_users_count=c.get("affected_users_count", 1),
        agent_suggestion=c.get("agent_suggestion"),
        agent_analysis=agent_analysis,
        agent_status=c.get("agent_status"),
        created_at=c["created_at"],
        updated_at=c.get("updated_at", c["created_at"]),
        history=history_items,
        rating_info={"rating": rating_info["rating"], "feedback": rating_info.get("feedback")} if rating_info else None
    )


@router.post("/complaints/{ticket_id}/agent/run")
async def run_agent_on_complaint(ticket_id: str, staff_user: dict = Depends(require_roles("MANAGER", "ADMIN"))):
    """Manually triggers the FULL agentic pipeline for an unassigned complaint."""
    db = get_database()
    c = await db.complaints.find_one({"ticket_id": ticket_id})
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint ticket not found")

    if c.get("assigned_technician_id"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Complaint is already assigned to a technician.")

    from backend.app.agentic.job_queue import JobQueue
    from backend.app.agentic.constants import STAGE_FULL, AGENT_STATUS_PENDING

    await db.complaints.update_one(
        {"ticket_id": ticket_id},
        {"$set": {"agent_status": AGENT_STATUS_PENDING}}
    )

    job_id = await JobQueue.enqueue_job(ticket_id, STAGE_FULL)
    return {"message": "Agent pipeline enqueued successfully.", "ticket_id": ticket_id, "job_id": job_id}


@router.post("/complaints/{ticket_id}/agent/accept-suggestion")
async def accept_agent_suggestion(ticket_id: str, staff_user: dict = Depends(require_roles("MANAGER", "ADMIN"))):
    """Accepts the agent suggestion and assigns the suggested technician with method AUTO_CONFIRMED."""
    db = get_database()
    c = await db.complaints.find_one({"ticket_id": ticket_id})
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint ticket not found")

    suggestion = c.get("agent_suggestion")
    if not suggestion or not suggestion.get("technician_id"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No agent suggestion found for this complaint.")

    tech_id = suggestion["technician_id"]
    actor = {
        "type": "USER",
        "id": str(staff_user["_id"]),
        "role": staff_user["role"],
        "name": staff_user["full_name"]
    }

    try:
        updated = await AssignmentService.assign(
            ticket_id=ticket_id,
            technician_id=tech_id,
            actor=actor,
            method="AUTO_CONFIRMED",
            reason=f"Accepted agent suggestion: {suggestion.get('reason', '')}"
        )
        return {"message": "Agent suggestion accepted and technician assigned successfully.", "ticket_id": ticket_id}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/complaints/{ticket_id}/assign")
async def assign_complaint(
    ticket_id: str,
    payload: AssignComplaintPayload,
    staff_user: dict = Depends(require_roles("MANAGER", "ADMIN"))
):
    """Assigns or re-assigns complaint to a technician."""
    actor = {
        "type": "USER",
        "id": str(staff_user["_id"]),
        "role": staff_user["role"],
        "name": staff_user["full_name"]
    }

    try:
        updated = await AssignmentService.assign(
            ticket_id=ticket_id,
            technician_id=payload.technician_id,
            actor=actor,
            method="MANUAL",
            reason=payload.reason
        )
        return {"message": "Complaint assigned successfully", "ticket_id": ticket_id}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/technicians")
async def list_manager_technicians(staff_user: dict = Depends(require_roles("MANAGER", "ADMIN"))):
    """Lists active technicians with availability, zones, categories, and calculated open complaint counts."""
    db = get_database()
    cursor = db.staff_users.find({"role": "TECHNICIAN", "is_active": True})

    techs = []
    async for t in cursor:
        t_id = str(t["_id"])
        open_count = await db.complaints.count_documents({
            "assigned_technician_id": t_id,
            "status": {"$in": [ComplaintStatus.ASSIGNED.value, ComplaintStatus.DIAGNOSED.value]}
        })

        profile = t.get("technician_profile") or {}
        techs.append({
            "_id": t_id,
            "username": t["username"],
            "full_name": t["full_name"],
            "email": t["email"],
            "mobile": t["mobile"],
            "availability": profile.get("availability", TechnicianAvailability.UNAVAILABLE.value),
            "zones": profile.get("zones", []),
            "categories": profile.get("categories", []),
            "open_complaints_count": open_count
        })

    return techs


@router.patch("/technicians/{id}/availability")
async def toggle_technician_availability(
    id: str,
    payload: TechnicianAvailabilityPayload,
    staff_user: dict = Depends(require_roles("MANAGER", "ADMIN"))
):
    """Toggles technician availability (AVAILABLE / UNAVAILABLE). Warning 409 returned if open complaints exist."""
    db = get_database()
    tech = await db.staff_users.find_one({"_id": id, "role": "TECHNICIAN"})
    if not tech:
        try:
            tech = await db.staff_users.find_one({"_id": ObjectId(id), "role": "TECHNICIAN"})
        except Exception:
            pass

    if not tech:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Technician not found")

    tech_id = str(tech["_id"])
    target_avail = payload.availability.value if hasattr(payload.availability, "value") else str(payload.availability)

    if target_avail == TechnicianAvailability.UNAVAILABLE.value:
        open_count = await db.complaints.count_documents({
            "assigned_technician_id": tech_id,
            "status": {"$in": [ComplaintStatus.ASSIGNED.value, ComplaintStatus.DIAGNOSED.value]}
        })

        if open_count > 0 and not payload.confirm:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Technician currently has {open_count} open assigned complaint(s). Re-submit with confirm=true to mark unavailable anyway."
            )

    await db.staff_users.update_one(
        {"_id": tech["_id"]},
        {"$set": {"technician_profile.availability": target_avail}}
    )

    from backend.app import events
    if target_avail == TechnicianAvailability.AVAILABLE.value:
        await events.emit("technician_availability_changed", {
            "technician_id": tech_id,
            "availability": target_avail
        })

    return {"message": f"Technician availability updated to {target_avail}", "technician_id": tech_id}


@router.get("/reports")
async def get_manager_reports(
    range_filter: str = Query("today", alias="range", regex="^(today|weekly|all)$"),
    staff_user: dict = Depends(require_roles("MANAGER", "ADMIN"))
):
    """Generates analytics report by date range (excluding JUNK complaints)."""
    db = get_database()
    query: Dict[str, Any] = {"status": {"$ne": ComplaintStatus.JUNK.value}}

    now_dt = datetime.utcnow()
    if range_filter == "today":
        start_of_today = now_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        query["created_at"] = {"$gte": start_of_today}
    elif range_filter == "weekly":
        seven_days_ago = now_dt - timedelta(days=7)
        query["created_at"] = {"$gte": seven_days_ago}

    cursor = db.complaints.find(query)
    complaints = await cursor.to_list(length=5000)

    by_status: Dict[str, int] = {}
    by_problem_type: Dict[str, int] = {}
    by_location: Dict[str, int] = {}

    total_resolved = 0
    total_resolution_hours = 0.0

    for c in complaints:
        st = c.get("status", "SUBMITTED")
        pt = c.get("problem_type", "OTHER")
        loc = c.get("location", "OTHER")

        by_status[st] = by_status.get(st, 0) + 1
        by_problem_type[pt] = by_problem_type.get(pt, 0) + 1
        by_location[loc] = by_location.get(loc, 0) + 1

        if st == ComplaintStatus.CLOSED.value and c.get("closed_at") and c.get("created_at"):
            total_resolved += 1
            hrs = (c["closed_at"] - c["created_at"]).total_seconds() / 3600.0
            total_resolution_hours += hrs

    avg_resolution_hours = round(total_resolution_hours / total_resolved, 2) if total_resolved > 0 else 0.0

    return {
        "range": range_filter,
        "total_complaints": len(complaints),
        "by_status": by_status,
        "by_problem_type": by_problem_type,
        "by_location": by_location,
        "total_resolved": total_resolved,
        "avg_resolution_hours": avg_resolution_hours
    }
