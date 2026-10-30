# MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
# Technician workbench router for assigned complaints, stock issue resolution flow, and rating feedback.

from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from backend.app.db import get_database
from backend.app.auth.jwt_auth import require_roles
from backend.app.complaint_management.models import ComplaintStatus, ActionTokenPurpose
from backend.app.complaint_management.schemas import (
    ResolveComplaintPayload,
    ComplaintDetailResponse,
    HistoryItemResponse
)
from backend.app.complaint_management.services.status_service import StatusService
from backend.app.complaint_management.routers.student_actions import create_action_token
from backend.app.network_assets.services import StockService, AssetService
from backend.app import events

router = APIRouter(prefix="/technician", tags=["technician-complaints"])


@router.get("/complaints")
async def list_technician_complaints(
    tab: str = Query("open", regex="^(open|closed)$"),
    priority_filter: Optional[str] = Query(None, alias="priority"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    staff_user: dict = Depends(require_roles("TECHNICIAN"))
):
    """Lists complaints assigned strictly to the logged-in technician, sorted by priority then age."""
    db = get_database()
    tech_id = str(staff_user["_id"])

    query: Dict[str, Any] = {"assigned_technician_id": tech_id}
    if tab == "open":
        query["status"] = {"$in": [ComplaintStatus.ASSIGNED.value, ComplaintStatus.DIAGNOSED.value, ComplaintStatus.ACTION_TAKEN.value, ComplaintStatus.STUDENT_CONFIRMATION.value]}
    else:  # 'closed'
        query["status"] = ComplaintStatus.CLOSED.value

    if priority_filter:
        query["priority"] = priority_filter.upper()

    total = await db.complaints.count_documents(query)
    cursor = db.complaints.find(query)
    all_docs = [doc async for doc in cursor]

    # Sort open complaints by priority (CRITICAL first) then created_at ascending (oldest first)
    priority_rank = {"CRITICAL": 1, "HIGH": 2, "MEDIUM": 3, "LOW": 4}

    if tab == "open":
        all_docs.sort(key=lambda d: (priority_rank.get(d.get("priority", "MEDIUM").upper(), 3), d.get("created_at") or datetime.max))
    else:
        all_docs.sort(key=lambda d: d.get("created_at") or datetime.min, reverse=True)

    skip = (page - 1) * limit
    paged_docs = all_docs[skip:skip + limit]

    from backend.app.complaint_management.routers.manager_complaints import _build_agent_analysis_data

    complaints_list = []
    for c in paged_docs:
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
        agent_analysis = await _build_agent_analysis_data(c, is_manager_or_admin=False)

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
                assigned_technician_id=tech_id,
                assigned_technician_name=staff_user["full_name"],
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
async def get_technician_complaint_detail(ticket_id: str, staff_user: dict = Depends(require_roles("TECHNICIAN"))):
    """Returns assigned complaint detail including linked chat transcript and resolution fields."""
    db = get_database()
    tech_id = str(staff_user["_id"])

    c = await db.complaints.find_one({"ticket_id": ticket_id, "assigned_technician_id": tech_id})
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assigned complaint ticket not found")

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
    from backend.app.complaint_management.routers.manager_complaints import _build_agent_analysis_data
    agent_analysis = await _build_agent_analysis_data(c, is_manager_or_admin=False)

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
        assigned_technician_id=tech_id,
        assigned_technician_name=staff_user["full_name"],
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


@router.post("/complaints/{ticket_id}/resolve")
async def resolve_complaint(
    ticket_id: str,
    payload: ResolveComplaintPayload,
    staff_user: dict = Depends(require_roles("TECHNICIAN"))
):
    """Submits technician diagnosis, solution, and stock usage. Executes compensating transaction rollback if stock issue fails."""
    db = get_database()
    tech_id = str(staff_user["_id"])
    tech_name = staff_user["full_name"]

    c = await db.complaints.find_one({"ticket_id": ticket_id, "assigned_technician_id": tech_id})
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assigned complaint ticket not found")

    current_status = c.get("status")
    if current_status not in [ComplaintStatus.ASSIGNED.value, ComplaintStatus.DIAGNOSED.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot resolve complaint in status '{current_status}'."
        )

    # 1. Apply stock issues with rollback tracker
    issued_stock_log = []
    items_used_recorded = []

    try:
        for item in payload.items_used:
            stock_id = item["stock_item_id"]
            qty = int(item.get("quantity", 1))

            stock_res = await StockService.issue_stock(
                item_id=stock_id,
                qty=qty,
                reason=f"Used for Ticket #{ticket_id}",
                by=tech_name,
                complaint_id=ticket_id,
                used_by=tech_name,
                location_id=item.get("location_id") or c.get("location")
            )
            issued_stock_log.append((stock_id, qty))

            # Fetch stock name
            stock_doc = await db.na_stock_items.find_one({"_id": stock_id})
            stock_name = stock_doc.get("item_type", "Stock Item") if stock_doc else "Stock Item"

            items_used_recorded.append({
                "stock_item_id": stock_id,
                "name": stock_name,
                "quantity": qty,
                "location_id": item.get("location_id") or c.get("location"),
                "used_by": tech_name,
                "used_at": datetime.utcnow()
            })

    except Exception as stock_err:
        # Rollback compensating restock transactions
        for rolled_id, rolled_qty in issued_stock_log:
            try:
                await StockService.restock_stock(rolled_id, rolled_qty, f"Rollback for Ticket #{ticket_id}")
            except Exception:
                pass
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stock issue failed: {stock_err}. Rollback completed."
        )

    # 2. Apply asset actions
    asset_actions_recorded = []
    for action in payload.asset_actions:
        asset_id = action["asset_id"]
        new_stat = action["new_status"]
        reason = action.get("reason", f"Resolution for Ticket #{ticket_id}")

        await AssetService.update_asset_status(asset_id, new_stat, reason, tech_name)
        await AssetService.add_maintenance_record(
            asset_id=asset_id,
            date=datetime.utcnow().strftime("%Y-%m-%d"),
            type="REPAIR" if new_stat == "FAULTY" else "REPLACEMENT",
            description=reason,
            performed_by=tech_name,
            cost=0.0,
            complaint_id=ticket_id
        )
        asset_actions_recorded.append({
            "asset_id": asset_id,
            "new_status": new_stat,
            "reason": reason
        })

    # 3. Save diagnosis, solution, items_used, asset_actions, resolved_at
    now_dt = datetime.utcnow()
    tech_actor = {
        "type": "USER",
        "id": tech_id,
        "role": "TECHNICIAN",
        "name": tech_name
    }

    await db.complaints.update_one(
        {"ticket_id": ticket_id},
        {
            "$set": {
                "diagnosis": payload.diagnosis,
                "solution": payload.solution,
                "items_used": items_used_recorded,
                "asset_actions": asset_actions_recorded,
                "resolved_at": now_dt,
                "confirmation_requested_at": now_dt
            }
        }
    )

    # 4. Status transitions: DIAGNOSED -> ACTION_TAKEN -> STUDENT_CONFIRMATION
    await StatusService.change_status(ticket_id, ComplaintStatus.DIAGNOSED.value, tech_actor, note="Diagnosis saved")
    await StatusService.change_status(ticket_id, ComplaintStatus.ACTION_TAKEN.value, tech_actor, note="Action taken saved")

    sys_actor = {"type": "SYSTEM", "id": "system", "role": "SYSTEM", "name": "System Engine"}
    updated_complaint = await StatusService.change_status(
        ticket_id,
        ComplaintStatus.STUDENT_CONFIRMATION.value,
        sys_actor,
        note="Confirmation link sent to student"
    )

    # 5. Generate CONFIRM token and dispatch email
    confirm_token = await create_action_token(ticket_id, ActionTokenPurpose.CONFIRM)

    await events.emit("complaint_solved", {
        "ticket_id": ticket_id,
        "complaint": updated_complaint,
        "confirm_token": confirm_token,
        "technician_name": tech_name,
        "actor": tech_actor
    })

    return {"message": "Complaint resolution submitted and confirmation email queued.", "ticket_id": ticket_id}


@router.get("/my-ratings")
async def get_my_ratings(staff_user: dict = Depends(require_roles("TECHNICIAN"))):
    """Returns technician's ratings list (anonymous without student PII), average rating, and position rank."""
    db = get_database()
    tech_id = str(staff_user["_id"])

    cursor = db.ratings.find({"technician_id": tech_id}).sort("created_at", -1)
    ratings_list = []
    async for r in cursor:
        ratings_list.append({
            "ticket_id": r["ticket_id"],
            "rating": r["rating"],
            "feedback": r.get("feedback", ""),
            "created_at": r["created_at"]
        })

    count = len(ratings_list)
    avg_rating = round(sum(r["rating"] for r in ratings_list) / count, 2) if count > 0 else None

    # Calculate position rank on leaderboard
    all_techs_cursor = db.staff_users.find({"role": "TECHNICIAN", "is_active": True})
    scores = []
    async for t in all_techs_cursor:
        t_id = str(t["_id"])
        t_ratings_cursor = db.ratings.find({"technician_id": t_id})
        t_ratings = [r["rating"] async for r in t_ratings_cursor]
        t_cnt = len(t_ratings)
        t_avg = sum(t_ratings) / t_cnt if t_cnt > 0 else 0.0
        scores.append((t_id, t_avg, t_cnt))

    scores.sort(key=lambda x: (x[1], x[2]), reverse=True)
    rank = 1
    for idx, s in enumerate(scores, start=1):
        if s[0] == tech_id:
            rank = idx
            break

    total_active_techs = len(scores)

    return {
        "average_rating": avg_rating,
        "rating_count": count,
        "rank_position": f"#{rank} of {total_active_techs}",
        "ratings": ratings_list
    }
