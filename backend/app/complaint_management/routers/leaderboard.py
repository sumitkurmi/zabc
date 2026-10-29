# MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
# Shared leaderboard router computing technician performance metrics and ranks on the fly.

from typing import List
from fastapi import APIRouter, Depends, Query
from backend.app.db import get_database
from backend.app.auth.jwt_auth import require_roles
from backend.app.complaint_management.schemas import LeaderboardItemResponse
from backend.app.complaint_management.services.scoring_service import compute_technician_score
from backend.app.complaint_management.models import ComplaintStatus, TechnicianAvailability

router = APIRouter(tags=["leaderboard"])


@router.get("/leaderboard", response_model=List[LeaderboardItemResponse])
async def get_leaderboard(
    sort_by: str = Query("score", alias="sort", regex="^(score|rating|resolved)$"),
    staff_user: dict = Depends(require_roles("ADMIN", "MANAGER", "TECHNICIAN"))
):
    """Calculates active technician performance leaderboard on the fly using scoring_service."""
    db = get_database()
    cursor = db.staff_users.find({"role": "TECHNICIAN", "is_active": True})

    items = []
    async for tech in cursor:
        tech_id = str(tech["_id"])
        tech_name = tech.get("full_name", tech["username"])
        profile = tech.get("technician_profile") or {}
        avail = profile.get("availability", TechnicianAvailability.UNAVAILABLE.value)

        # Count resolved CLOSED complaints where this technician was assigned at closing
        resolved_cnt = await db.complaints.count_documents({
            "assigned_technician_id": tech_id,
            "status": ComplaintStatus.CLOSED.value
        })

        # Count current open complaints
        open_cnt = await db.complaints.count_documents({
            "assigned_technician_id": tech_id,
            "status": {"$in": [ComplaintStatus.ASSIGNED.value, ComplaintStatus.DIAGNOSED.value]}
        })

        # Compute rating aggregate
        ratings_cursor = db.ratings.find({"technician_id": tech_id})
        ratings_list = [r["rating"] async for r in ratings_cursor]

        rating_cnt = len(ratings_list)
        avg_rating = round(sum(ratings_list) / rating_cnt, 2) if rating_cnt > 0 else None

        score = compute_technician_score(
            avg_rating=avg_rating,
            rating_count=rating_cnt,
            resolved_count=resolved_cnt
        )

        items.append({
            "technician_id": tech_id,
            "name": tech_name,
            "availability": avail,
            "average_rating": avg_rating,
            "rating_count": rating_cnt,
            "resolved_count": resolved_cnt,
            "open_complaints_count": open_cnt,
            "score": score,
            "rank": 0
        })

    # Sort
    if sort_by == "rating":
        items.sort(key=lambda x: (x["average_rating"] or 0.0, x["resolved_count"]), reverse=True)
    elif sort_by == "resolved":
        items.sort(key=lambda x: (x["resolved_count"], x["score"]), reverse=True)
    else:  # 'score'
        items.sort(key=lambda x: (x["score"], x["resolved_count"]), reverse=True)

    # Assign ranks
    response_list = []
    for idx, item in enumerate(items, start=1):
        item["rank"] = idx
        response_list.append(LeaderboardItemResponse(**item))

    return response_list
