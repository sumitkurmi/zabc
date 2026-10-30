# MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
# Admin router for marking junk complaints, restoring from junk, and permanently clearing junk records.

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from backend.app.db import get_database
from backend.app.auth.jwt_auth import require_roles
from backend.app.complaint_management.models import ComplaintStatus
from backend.app.complaint_management.schemas import MarkJunkPayload, ComplaintDetailResponse
from backend.app.complaint_management.services.status_service import StatusService
from backend.app.complaint_management.routers.admin_staff import log_admin_audit

router = APIRouter(prefix="/admin", tags=["admin-junk"])


@router.post("/complaints/{ticket_id}/mark-junk")
async def mark_complaint_junk(
    ticket_id: str,
    payload: MarkJunkPayload,
    admin_user: dict = Depends(require_roles("ADMIN"))
):
    """Marks a complaint as JUNK (admin only). Stores previous_status and writes history without sending emails."""
    actor = {
        "type": "USER",
        "id": str(admin_user["_id"]),
        "role": "ADMIN",
        "name": admin_user["full_name"]
    }

    try:
        updated = await StatusService.change_status(
            ticket_id=ticket_id,
            to_status=ComplaintStatus.JUNK.value,
            actor=actor,
            note=payload.reason or "Marked as JUNK by admin"
        )
        await log_admin_audit("MARK_JUNK", str(admin_user["_id"]), {"ticket_id": ticket_id, "reason": payload.reason})
        return {"message": "Complaint marked as JUNK", "ticket_id": ticket_id}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/complaints/{ticket_id}/restore")
async def restore_junk_complaint(
    ticket_id: str,
    admin_user: dict = Depends(require_roles("ADMIN"))
):
    """Restores a JUNK complaint back to its previous lifecycle status."""
    actor = {
        "type": "USER",
        "id": str(admin_user["_id"]),
        "role": "ADMIN",
        "name": admin_user["full_name"]
    }

    try:
        updated = await StatusService.change_status(
            ticket_id=ticket_id,
            to_status="RESTORE_PREVIOUS",
            actor=actor,
            note="Restored from JUNK by admin"
        )
        await log_admin_audit("RESTORE_JUNK", str(admin_user["_id"]), {"ticket_id": ticket_id})
        return {"message": f"Complaint restored to status {updated['status']}", "ticket_id": ticket_id}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/junk")
async def list_junk_complaints(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    admin_user: dict = Depends(require_roles("ADMIN"))
):
    """Lists all complaints currently marked as JUNK."""
    db = get_database()
    query = {"status": ComplaintStatus.JUNK.value}

    skip = (page - 1) * limit
    total = await db.complaints.count_documents(query)
    cursor = db.complaints.find(query).sort("updated_at", -1).skip(skip).limit(limit)

    complaints_list = []
    async for c in cursor:
        complaints_list.append({
            "ticket_id": c["ticket_id"],
            "name": c["name"],
            "email": c["email"],
            "location": c["location"],
            "problem_type": c["problem_type"],
            "previous_status": c.get("previous_status"),
            "created_at": c["created_at"],
            "updated_at": c.get("updated_at")
        })

    pages = (total + limit - 1) // limit if total > 0 else 1
    return {"complaints": complaints_list, "total": total, "page": page, "pages": pages}


@router.delete("/junk")
async def clear_all_junk_complaints(
    confirm: bool = Query(False),
    admin_user: dict = Depends(require_roles("ADMIN"))
):
    """Permanently deletes ALL JUNK complaints, their history, and action tokens."""
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmation required. Pass query parameter confirm=true to permanently purge junk."
        )

    db = get_database()
    junk_cursor = db.complaints.find({"status": ComplaintStatus.JUNK.value})
    junk_tickets = [c["ticket_id"] async for c in junk_cursor]

    if not junk_tickets:
        return {"message": "No junk complaints to clear.", "deleted_count": 0}

    # Purge history, tokens, ratings, and complaints
    await db.complaint_history.delete_many({"ticket_id": {"$in": junk_tickets}})
    await db.action_tokens.delete_many({"ticket_id": {"$in": junk_tickets}})
    await db.ratings.delete_many({"ticket_id": {"$in": junk_tickets}})

    res = await db.complaints.delete_many({"status": ComplaintStatus.JUNK.value})
    deleted_cnt = res.deleted_count

    admin_id = str(admin_user["_id"])
    await log_admin_audit("CLEAR_JUNK", admin_id, {"deleted_count": deleted_cnt, "ticket_ids": junk_tickets})

    return {"message": f"Permanently deleted {deleted_cnt} junk complaint(s).", "deleted_count": deleted_cnt}
