# MODULE: Agentic Classification and Assignment (Module 2) - this file belongs to the code for this module.
# Persistent job queue operations on agent_jobs MongoDB collection with atomic locking.

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from backend.app.db import get_database
from backend.app.config import settings
from backend.app.agentic.constants import (
    STAGE_FULL,
    STAGE_ASSIGN,
    STAGE_RAG_INDEX,
    JOB_PENDING,
    JOB_RUNNING,
    JOB_DONE,
    JOB_FAILED
)

logger = logging.getLogger("agentic.job_queue")


class JobQueue:
    """Manager for enqueueing, claiming, and updating persistent background agent jobs."""

    @staticmethod
    async def enqueue_job(ticket_id: str, stage: str, delay_seconds: int = 0) -> str:
        """Enqueues or updates an agent job in agent_jobs collection.

        Args:
            ticket_id: 12-digit ticket ID string.
            stage: Stage string ('FULL', 'ASSIGN', 'RAG_INDEX').
            delay_seconds: Optional initial delay before job is runnable.

        Returns:
            Job document ID string.
        """
        db = get_database()
        now_dt = datetime.utcnow()
        run_at = now_dt + timedelta(seconds=delay_seconds)

        # Check if pending or running job exists for this ticket and stage
        existing = await db.agent_jobs.find_one({
            "ticket_id": ticket_id,
            "stage": stage,
            "status": {"$in": [JOB_PENDING, JOB_RUNNING]}
        })

        if existing:
            # Update next_run_at and reset status to PENDING
            await db.agent_jobs.update_one(
                {"_id": existing["_id"]},
                {
                    "$set": {
                        "status": JOB_PENDING,
                        "next_run_at": run_at,
                        "locked_until": None
                    }
                }
            )
            return str(existing["_id"])

        job_doc = {
            "ticket_id": ticket_id,
            "stage": stage,
            "status": JOB_PENDING,
            "attempts": 0,
            "next_run_at": run_at,
            "locked_until": None,
            "last_error": None,
            "created_at": now_dt
        }
        res = await db.agent_jobs.insert_one(job_doc)
        logger.info(f"[JobQueue] Enqueued stage '{stage}' job for ticket '{ticket_id}'.")
        return str(res.inserted_id)

    @staticmethod
    async def claim_next_job() -> Optional[Dict[str, Any]]:
        """Atomically claims next runnable job using find_one_and_update.

        Returns:
            Claimed job document dictionary or None.
        """
        db = get_database()
        now_dt = datetime.utcnow()
        lock_until = now_dt + timedelta(seconds=60)

        # Query: status PENDING, next_run_at <= now, locked_until is None or <= now
        filter_doc = {
            "status": JOB_PENDING,
            "next_run_at": {"$lte": now_dt},
            "$or": [
                {"locked_until": None},
                {"locked_until": {"$lte": now_dt}}
            ]
        }

        update_doc = {
            "$set": {
                "status": JOB_RUNNING,
                "locked_until": lock_until
            },
            "$inc": {"attempts": 1}
        }

        claimed = await db.agent_jobs.find_one_and_update(
            filter_doc,
            update_doc,
            return_document=True
        )

        if claimed and "_id" in claimed:
            claimed["_id"] = str(claimed["_id"])
        return claimed

    @staticmethod
    async def mark_job_done(job_id: str) -> None:
        """Marks job status as DONE and unlocks it."""
        db = get_database()
        from bson import ObjectId
        oid = ObjectId(job_id) if ObjectId.is_valid(job_id) else job_id
        await db.agent_jobs.update_one(
            {"_id": oid},
            {"$set": {"status": JOB_DONE, "locked_until": None}}
        )

    @staticmethod
    async def mark_job_failed(job_id: str, error_msg: str, attempts: int) -> None:
        """Marks job as FAILED or schedules retry with exponential backoff."""
        db = get_database()
        from bson import ObjectId
        oid = ObjectId(job_id) if ObjectId.is_valid(job_id) else job_id

        max_attempts = int(getattr(settings, "AGENT_MAX_ATTEMPTS", 3))

        if attempts >= max_attempts:
            await db.agent_jobs.update_one(
                {"_id": oid},
                {
                    "$set": {
                        "status": JOB_FAILED,
                        "locked_until": None,
                        "last_error": error_msg
                    }
                }
            )
            logger.error(f"[JobQueue] Job {job_id} failed permanently after {attempts} attempts: {error_msg}")
        else:
            # Exponential backoff: 5s, 20s, 80s...
            backoff_seconds = (2 ** attempts) * 5
            next_run = datetime.utcnow() + timedelta(seconds=backoff_seconds)
            await db.agent_jobs.update_one(
                {"_id": oid},
                {
                    "$set": {
                        "status": JOB_PENDING,
                        "next_run_at": next_run,
                        "locked_until": None,
                        "last_error": error_msg
                    }
                }
            )
            logger.warning(f"[JobQueue] Job {job_id} attempt {attempts} failed. Rescheduled in {backoff_seconds}s.")
