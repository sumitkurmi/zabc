# MODULE: Agentic Classification and Assignment (Module 2) - this file belongs to the code for this module.
# Background worker loop processing agent jobs and periodic sweeps.

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from backend.app.db import get_database
from backend.app.config import settings
from backend.app.complaint_management.models import ComplaintStatus, HistoryEventType, HistoryActorType
from backend.app.complaint_management.services.status_service import StatusService
from backend.app.agentic.constants import (
    STAGE_FULL,
    STAGE_ASSIGN,
    STAGE_RAG_INDEX,
    JOB_RUNNING,
    JOB_PENDING,
    AGENT_STATUS_FAILED
)
from backend.app.agentic.job_queue import JobQueue
from backend.app.agentic.orchestrator import AgenticOrchestrator
from backend.app.agentic.complaint_log_rag import build_and_index_complaint_log

logger = logging.getLogger("agentic.worker")

# Global flag to control worker loop task lifecycle
_worker_running = False
_sweep_trigger_event = asyncio.Event()


async def sweep_stuck_complaints() -> None:
    """Sweep stuck SUBMITTED complaints older than AGENT_STUCK_MINUTES."""
    try:
        enabled = getattr(settings, "AGENT_ENABLED", True)
        if not enabled:
            return

        db = get_database()
        stuck_minutes = int(getattr(settings, "AGENT_STUCK_MINUTES", 10))
        cutoff = datetime.utcnow() - timedelta(minutes=stuck_minutes)

        cursor = db.complaints.find({
            "status": ComplaintStatus.SUBMITTED.value,
            "created_at": {"$lte": cutoff}
        })

        async for complaint in cursor:
            ticket_id = complaint["ticket_id"]

            # Check if there is an active running job for this ticket
            running_job = await db.agent_jobs.find_one({
                "ticket_id": ticket_id,
                "status": JOB_RUNNING
            })

            if not running_job:
                logger.warning(f"[WorkerSweep] Complaint '{ticket_id}' stuck in SUBMITTED > {stuck_minutes}m. Applying rules fallback.")

                update_payload = {
                    "ai_category": complaint.get("problem_type"),
                    "ai_confidence": 0.5,
                    "zone": complaint.get("location"),
                    "priority": "MEDIUM",
                    "agent_status": AGENT_STATUS_FAILED,
                    "classification_notes": {
                        "method": "rules",
                        "summary": "Agent processing timed out or failed. Default rules applied.",
                        "agent_version": "v2.0-fallback",
                        "analyzed_at": datetime.utcnow()
                    }
                }

                await db.complaints.update_one(
                    {"ticket_id": ticket_id},
                    {"$set": update_payload}
                )

                actor_agent = {
                    "type": HistoryActorType.AGENT.value,
                    "id": "classification_agent",
                    "role": "AGENT",
                    "name": "Classification Agent"
                }

                await StatusService.change_status(
                    ticket_id=ticket_id,
                    to_status=ComplaintStatus.CLASSIFIED.value,
                    actor=actor_agent,
                    note="Agent failed, manual assignment needed",
                    details=update_payload
                )

    except Exception as e:
        logger.error(f"[WorkerSweep] Error in sweep_stuck_complaints: {e}", exc_info=True)


async def sweep_unassigned_complaints() -> None:
    """Sweep CLASSIFIED unassigned complaints ordered by priority then age (CRITICAL first)."""
    try:
        enabled = getattr(settings, "AGENT_ENABLED", True)
        mode = getattr(settings, "AGENT_ASSIGNMENT_MODE", "auto").lower()

        if not enabled or mode != "auto":
            return

        db = get_database()

        # Priority order custom mapping for sorting in MongoDB
        priority_order_map = {"CRITICAL": 1, "HIGH": 2, "MEDIUM": 3, "LOW": 4}

        cursor = db.complaints.find({
            "status": ComplaintStatus.CLASSIFIED.value,
            "assigned_technician_id": None
        })

        unassigned_docs = [doc async for doc in cursor]

        if not unassigned_docs:
            return

        # Sort in memory: priority (CRITICAL first) then created_at ascending (oldest first)
        def unassigned_sort_key(doc):
            p = doc.get("priority", "MEDIUM").upper()
            p_val = priority_order_map.get(p, 3)
            return (p_val, doc.get("created_at") or datetime.max)

        unassigned_docs.sort(key=unassigned_sort_key)

        orchestrator = AgenticOrchestrator()
        for complaint in unassigned_docs:
            ticket_id = complaint["ticket_id"]
            logger.info(f"[WorkerSweep] Retrying auto-assignment for unassigned complaint '{ticket_id}' ({complaint.get('priority')}).")
            await orchestrator.run_assignment_only(ticket_id)

    except Exception as e:
        logger.error(f"[WorkerSweep] Error in sweep_unassigned_complaints: {e}", exc_info=True)


def trigger_assignment_sweep() -> None:
    """Triggers an immediate unassigned complaint sweep (e.g. on technician availability change)."""
    _sweep_trigger_event.set()


async def agent_worker_loop():
    """Background loop claiming and processing persistent agent jobs."""
    global _worker_running
    _worker_running = True
    logger.info("[AgentWorker] Starting background agent worker loop...")

    orchestrator = AgenticOrchestrator()
    sweep_minutes = int(getattr(settings, "AGENT_SWEEP_MINUTES", 5))
    last_sweep_at = datetime.utcnow()

    while _worker_running:
        try:
            now_dt = datetime.utcnow()

            # 1. Process Runnable Jobs
            claimed_job = await JobQueue.claim_next_job()
            if claimed_job:
                job_id = claimed_job["_id"]
                ticket_id = claimed_job["ticket_id"]
                stage = claimed_job["stage"]
                attempts = claimed_job["attempts"]

                logger.info(f"[AgentWorker] Processing job {job_id} for ticket '{ticket_id}' (stage={stage}, attempt={attempts}).")

                try:
                    if stage == STAGE_FULL:
                        await orchestrator.run_full_pipeline(ticket_id)
                    elif stage == STAGE_ASSIGN:
                        await orchestrator.run_assignment_only(ticket_id)
                    elif stage == STAGE_RAG_INDEX:
                        await build_and_index_complaint_log(ticket_id)
                    else:
                        logger.warning(f"[AgentWorker] Unknown job stage '{stage}' for job {job_id}.")

                    await JobQueue.mark_job_done(job_id)
                    logger.info(f"[AgentWorker] Successfully finished job {job_id} for ticket '{ticket_id}'.")

                except Exception as err:
                    logger.error(f"[AgentWorker] Job {job_id} failed: {err}")
                    await JobQueue.mark_job_failed(job_id, str(err), attempts)

            # 2. Check periodic sweeps or triggered sweeps
            if (now_dt - last_sweep_at) >= timedelta(minutes=sweep_minutes) or _sweep_trigger_event.is_set():
                _sweep_trigger_event.clear()
                last_sweep_at = datetime.utcnow()

                await sweep_stuck_complaints()
                await sweep_unassigned_complaints()

        except Exception as loop_err:
            logger.error(f"[AgentWorker] Exception in worker loop: {loop_err}", exc_info=True)

        await asyncio.sleep(3)


def stop_agent_worker():
    """Stops the background agent worker loop."""
    global _worker_running
    _worker_running = False
