# MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
# Classification service hook managing immediate or asynchronous agentic complaint classification.

import logging
from typing import Dict, Any
from datetime import datetime
from backend.app.db import get_database
from backend.app.config import settings
from backend.app.complaint_management.models import ComplaintStatus, HistoryActorType
from backend.app.complaint_management.services.status_service import StatusService
from backend.app.agentic.job_queue import JobQueue
from backend.app.agentic.constants import STAGE_FULL, AGENT_STATUS_PENDING

logger = logging.getLogger("classification_service")


async def classify_and_advance(ticket_id: str) -> Dict[str, Any]:
    """Advances a newly SUBMITTED complaint.

    If AGENT_ENABLED=true: enqueues a background FULL job for agent processing.
    If AGENT_ENABLED=false: performs immediate Part 2 classification and advances to CLASSIFIED.

    Args:
        ticket_id: 12-digit complaint ticket ID string.

    Returns:
        Updated complaint document or job summary dictionary.
    """
    db = get_database()
    complaint = await db.complaints.find_one({"ticket_id": ticket_id})
    if not complaint:
        raise ValueError(f"Complaint ticket '{ticket_id}' not found.")

    agent_enabled = getattr(settings, "AGENT_ENABLED", True)

    if agent_enabled:
        # Enqueue FULL stage job for async agent processing
        await db.complaints.update_one(
            {"ticket_id": ticket_id},
            {"$set": {"agent_status": AGENT_STATUS_PENDING}}
        )
        job_id = await JobQueue.enqueue_job(ticket_id, STAGE_FULL)
        logger.info(f"[ClassificationService] AGENT_ENABLED=true. Enqueued FULL job {job_id} for ticket '{ticket_id}'.")
        return {"ticket_id": ticket_id, "agent_status": AGENT_STATUS_PENDING, "job_id": job_id}

    # Fallback when AGENT_ENABLED=false: Immediate transition SUBMITTED -> CLASSIFIED
    problem_type = complaint.get("problem_type")
    location = complaint.get("location")

    update_payload = {
        "ai_category": problem_type,
        "ai_confidence": 1.0,
        "zone": location,
        "priority": "MEDIUM",
        "affected_users_count": 1,
        "classification_notes": {
            "method": "manual",
            "summary": complaint.get("additional_comment") or f"Issue at {location}",
            "confidence": 1.0,
            "agent_version": "v1.0-manual",
            "analyzed_at": datetime.utcnow()
        }
    }

    await db.complaints.update_one(
        {"ticket_id": ticket_id},
        {"$set": update_payload}
    )

    actor_system = {
        "type": HistoryActorType.SYSTEM.value,
        "id": "system",
        "role": "SYSTEM",
        "name": "System"
    }

    updated_complaint = await StatusService.change_status(
        ticket_id=ticket_id,
        to_status=ComplaintStatus.CLASSIFIED.value,
        actor=actor_system,
        note="Classified immediately (Agent disabled)",
        details=update_payload
    )

    return updated_complaint


async def classify(complaint: Dict[str, Any]) -> Dict[str, Any]:
    """Legacy classification hook compatibility function."""
    problem_type = complaint.get("problem_type")
    return {
        "ai_category": problem_type,
        "priority": "MEDIUM",
        "zone": complaint.get("location"),
        "classification_notes": {
            "confidence": 1.0,
            "reasoning": "Student selected problem type retained in Part 2",
            "agent_version": "v1.0-manual"
        }
    }
