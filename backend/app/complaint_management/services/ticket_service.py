# MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
# Ticket ID generator providing 12-digit IST timestamp formatting with duplicate retry loop.

import zoneinfo
from datetime import datetime, timedelta
from typing import Optional
from backend.app.db import get_database
from backend.app.config import settings


def get_ist_now(dt_utc: Optional[datetime] = None) -> datetime:
    """Converts UTC datetime or current time to target timezone (Asia/Kolkata IST)."""
    tz_str = getattr(settings, "APP_TIMEZONE", "Asia/Kolkata")
    try:
        tz = zoneinfo.ZoneInfo(tz_str)
    except Exception:
        tz = zoneinfo.ZoneInfo("Asia/Kolkata")

    base = dt_utc or datetime.utcnow()
    base_utc = base.replace(tzinfo=zoneinfo.ZoneInfo("UTC"))
    return base_utc.astimezone(tz)


async def generate_ticket_id(base_utc: Optional[datetime] = None) -> str:
    """Generates a 12-digit ticket ID formatted as YYMMDDHHMMSS in IST.

    If a ticket ID collision occurs in MongoDB, retries up to 10 times adding 1 second each.

    Returns:
        12-digit ticket ID string.

    Raises:
        RuntimeError: If unable to allocate unique ticket ID after 10 retries.
    """
    db = get_database()
    curr_dt = base_utc or datetime.utcnow()

    for attempt in range(10):
        ist_dt = get_ist_now(curr_dt)
        ticket_id = ist_dt.strftime("%y%m%d%H%M%S")

        existing = await db.complaints.find_one({"ticket_id": ticket_id})
        if not existing:
            return ticket_id

        curr_dt = curr_dt + timedelta(seconds=1)

    raise RuntimeError("Failed to generate a unique 12-digit ticket ID after 10 attempts.")
