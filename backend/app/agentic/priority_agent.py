# MODULE: Agentic Classification and Assignment (Module 2) - this file belongs to the code for this module.
# Table-driven priority calculation rules engine combining LLM hint, user count, location, and recurrence.

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from backend.app.config import settings
from backend.app.db import get_database
from backend.app.agentic.constants import PRIORITY_VALUE_MAP, VALUE_TO_PRIORITY_MAP

logger = logging.getLogger("agentic.priority")


def compute_priority(
    priority_hint: str,
    affected_users_count: int,
    location: str,
    recurring: bool = False
) -> Dict[str, Any]:
    """Calculates complaint priority level (LOW, MEDIUM, HIGH, CRITICAL) using rule matrix.

    Rules Matrix Table:
    -----------------------------------------------------------------------------------------
    Base Input               Condition                           Impact             Cap
    -----------------------------------------------------------------------------------------
    priority_hint            LOW=1, MEDIUM=2, HIGH=3, CRITICAL=4 Base Level         CRITICAL (4)
    affected_users_count     >= AGENT_HIGH_IMPACT_USERS (5)      +1 level           CRITICAL (4)
    affected_users_count     >= AGENT_CRITICAL_IMPACT_USERS (20) Set CRITICAL (4)  CRITICAL (4)
    location                 In AGENT_PRIORITY_LOCATIONS         +1 level           CRITICAL (4)
    recurring                >= 2 complaints in last 7 days      +1 level           CRITICAL (4)
    -----------------------------------------------------------------------------------------

    Args:
        priority_hint: Base hint string ("LOW", "MEDIUM", "HIGH", "CRITICAL").
        affected_users_count: Total affected users count.
        location: Complaint location name string.
        recurring: Boolean indicating if 2+ complaints occurred in same location in last 7 days.

    Returns:
        Dict with 'priority' (str) and 'priority_reason' (str).
    """
    hint_upper = (priority_hint or "MEDIUM").upper()
    base_val = PRIORITY_VALUE_MAP.get(hint_upper, 2)
    current_val = base_val

    reasons: List[str] = [f"base {hint_upper}"]

    high_impact_thresh = int(getattr(settings, "AGENT_HIGH_IMPACT_USERS", 5))
    critical_impact_thresh = int(getattr(settings, "AGENT_CRITICAL_IMPACT_USERS", 20))

    # Critical user impact override
    if affected_users_count >= critical_impact_thresh:
        current_val = 4
        reasons.append(f"{affected_users_count} users affected (CRITICAL threshold >= {critical_impact_thresh})")
    elif affected_users_count >= high_impact_thresh:
        current_val += 1
        reasons.append(f"{affected_users_count} users affected (+1)")

    # Priority locations check
    priority_locs_raw = getattr(settings, "AGENT_PRIORITY_LOCATIONS", "")
    priority_locs = [p.strip().lower() for p in priority_locs_raw.split(",") if p.strip()] if priority_locs_raw else []

    if location and location.strip().lower() in priority_locs:
        current_val += 1
        reasons.append(f"priority location '{location}' (+1)")

    # Recurrence check
    if recurring:
        current_val += 1
        reasons.append("recurring fault in last 7 days (+1)")

    # Cap at 4 (CRITICAL)
    final_val = min(current_val, 4)
    final_val = max(final_val, 1)

    final_priority = VALUE_TO_PRIORITY_MAP.get(final_val, "MEDIUM")
    reason_str = f"{final_priority}: " + ", ".join(reasons)

    return {
        "priority": final_priority,
        "priority_reason": reason_str
    }


class PriorityAgent:
    """Agent evaluating complaint priority levels and logging reasoning."""

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Executes priority evaluation including recurrence database query.

        Args:
            context: Dict containing 'complaint', 'priority_hint', 'affected_users_count', 'routing_category'.

        Returns:
            Dict containing priority level string and priority_reason string.
        """
        complaint = context.get("complaint", {})
        priority_hint = context.get("priority_hint") or "MEDIUM"
        affected_users_count = int(context.get("affected_users_count", 1))
        location = complaint.get("location", "")
        routing_category = context.get("routing_category") or complaint.get("problem_type")
        ticket_id = complaint.get("ticket_id")

        # Check for recurrence in last 7 days (at least 2 other complaints with same location and category)
        db = get_database()
        seven_days_ago = datetime.utcnow() - timedelta(days=7)

        recurring_count = await db.complaints.count_documents({
            "ticket_id": {"$ne": ticket_id},
            "location": location,
            "$or": [
                {"ai_category": routing_category},
                {"problem_type": routing_category}
            ],
            "created_at": {"$gte": seven_days_ago}
        })

        is_recurring = recurring_count >= 2

        res = compute_priority(
            priority_hint=priority_hint,
            affected_users_count=affected_users_count,
            location=location,
            recurring=is_recurring
        )

        return res
