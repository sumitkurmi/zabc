# MODULE: Agentic Classification and Assignment (Module 2) - this file belongs to the code for this module.
# Database index creation script for Module 2 collections and complaint priority queries.

import asyncio
import logging
from pymongo import ASCENDING, DESCENDING
from backend.app.db import get_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("create_module2_indexes")


async def create_module2_indexes():
    """Creates MongoDB indexes required for Module 2 agentic jobs, runs, and priority queries."""
    db = get_database()

    logger.info("Creating indexes for collection 'agent_jobs'...")
    await db.agent_jobs.create_index([("status", ASCENDING), ("next_run_at", ASCENDING)], name="idx_jobs_status_next_run")
    await db.agent_jobs.create_index([("ticket_id", ASCENDING), ("stage", ASCENDING)], name="idx_jobs_ticket_stage")

    logger.info("Creating indexes for collection 'agent_runs'...")
    await db.agent_runs.create_index([("ticket_id", ASCENDING), ("started_at", DESCENDING)], name="idx_runs_ticket_started")

    logger.info("Creating indexes for collection 'complaints'...")
    await db.complaints.create_index([("priority", ASCENDING), ("status", ASCENDING)], name="idx_complaints_priority_status")
    await db.complaints.create_index(
        [("location", ASCENDING), ("problem_type", ASCENDING), ("created_at", DESCENDING)],
        name="idx_complaints_loc_prob_created"
    )

    logger.info("Creating sparse unique index on 'documents' for complaint_ticket_id...")
    await db.documents.create_index(
        [("complaint_ticket_id", ASCENDING)],
        unique=True,
        sparse=True,
        name="idx_documents_complaint_ticket_unique"
    )

    logger.info("Module 2 database indexes created successfully.")


if __name__ == "__main__":
    asyncio.run(create_module2_indexes())
