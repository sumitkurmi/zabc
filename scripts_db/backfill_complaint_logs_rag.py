# MODULE: Agentic Classification and Assignment (Module 2) - this file belongs to the code for this module.
# CLI script backfilling eligible closed complaints into RAG knowledge base.

import argparse
import asyncio
import logging
from backend.app.db import get_database
from backend.app.complaint_management.models import ComplaintStatus
from backend.app.agentic.complaint_log_rag import build_and_index_complaint_log

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backfill_complaint_logs_rag")


async def run_backfill(dry_run: bool = False, limit: int = 0):
    """Queries closed complaints without rag_indexed_at and processes them into RAG."""
    db = get_database()

    query = {
        "status": ComplaintStatus.CLOSED.value,
        "rag_indexed_at": None,
        "diagnosis": {"$exists": True, "$ne": ""},
        "solution": {"$exists": True, "$ne": ""}
    }

    cursor = db.complaints.find(query).sort("created_at", 1)
    if limit > 0:
        cursor = cursor.limit(limit)

    eligible_complaints = [doc async for doc in cursor]
    logger.info(f"Found {len(eligible_complaints)} eligible closed complaint(s) for RAG backfilling.")

    if dry_run:
        logger.info("DRY RUN MODE: No files will be generated or indexed.")
        for c in eligible_complaints:
            logger.info(f"  [Dry Run] Would index Ticket #{c['ticket_id']} ({c.get('problem_type')}, {c.get('location')})")
        return

    count = 0
    for c in eligible_complaints:
        ticket_id = c["ticket_id"]
        logger.info(f"Processing Ticket #{ticket_id}...")
        doc_id = await build_and_index_complaint_log(ticket_id)
        if doc_id:
            count += 1
            logger.info(f"  Successfully indexed Ticket #{ticket_id} (doc_id={doc_id}).")

    logger.info(f"Backfill completed. Indexed {count} complaint log(s).")


def main():
    parser = argparse.ArgumentParser(description="Backfill closed complaints into RAG complaint-logs category.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate backfill without creating files or vectors.")
    parser.add_argument("--limit", type=int, default=0, help="Maximum number of complaints to backfill (0 for unlimited).")
    args = parser.parse_args()

    asyncio.run(run_backfill(dry_run=args.dry_run, limit=args.limit))


if __name__ == "__main__":
    main()
