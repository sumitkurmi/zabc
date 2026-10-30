# MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
# Auto-close service closing inactive student confirmation complaints after AUTO_CLOSE_DAYS.

import asyncio
import logging
from datetime import datetime, timedelta
from backend.app.db import get_database
from backend.app.config import settings
from backend.app.complaint_management.models import ComplaintStatus, ClosedBy
from backend.app.complaint_management.services.status_service import StatusService

logger = logging.getLogger("auto_close")


async def run_auto_close_check() -> int:
    """Finds and automatically closes complaints in STUDENT_CONFIRMATION exceeding AUTO_CLOSE_DAYS limit.

    Returns:
        Number of complaints auto-closed.
    """
    db = get_database()
    auto_close_days = getattr(settings, "AUTO_CLOSE_DAYS", 3)
    cutoff_dt = datetime.utcnow() - timedelta(days=auto_close_days)

    # Query complaints in STUDENT_CONFIRMATION older than cutoff
    cursor = db.complaints.find({
        "status": ComplaintStatus.STUDENT_CONFIRMATION.value,
        "confirmation_requested_at": {"$lte": cutoff_dt}
    })

    auto_closed_count = 0
    async for complaint in cursor:
        ticket_id = complaint["ticket_id"]
        try:
            # Set closed_by SYSTEM_AUTO
            await db.complaints.update_one(
                {"ticket_id": ticket_id, "status": ComplaintStatus.STUDENT_CONFIRMATION.value},
                {"$set": {"closed_by": ClosedBy.SYSTEM_AUTO.value, "closed_at": datetime.utcnow()}}
            )

            # Change status to CLOSED
            actor = {
                "type": "SYSTEM",
                "id": "system_auto_close",
                "role": "SYSTEM_AUTO",
                "name": "System Auto-Close Worker"
            }
            await StatusService.change_status(
                ticket_id=ticket_id,
                to_status=ComplaintStatus.CLOSED.value,
                actor=actor,
                note=f"Auto-closed: no student response in {auto_close_days} days"
            )
            auto_closed_count += 1
            logger.info(f"[AutoClose] Successfully auto-closed ticket '{ticket_id}'.")
        except Exception as e:
            logger.error(f"[AutoClose] Failed to auto-close ticket '{ticket_id}': {e}", exc_info=True)

    return auto_closed_count


async def auto_close_worker_loop():
    """Background asyncio worker loop running auto-close checks every AUTO_CLOSE_CHECK_MINUTES."""
    interval_minutes = getattr(settings, "AUTO_CLOSE_CHECK_MINUTES", 30)
    logger.info(f"[AutoCloseWorker] Starting background loop (interval: {interval_minutes} minutes)...")

    while True:
        try:
            closed_cnt = await run_auto_close_check()
            if closed_cnt > 0:
                logger.info(f"[AutoCloseWorker] Closed {closed_cnt} inactive complaint(s).")
        except Exception as e:
            logger.error(f"[AutoCloseWorker] Exception in auto-close loop: {e}", exc_info=True)

        await asyncio.sleep(interval_minutes * 60)
