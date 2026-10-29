# MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
# Database index initialization script for Part 2 collections and TTL expiration rules.

import asyncio
from pymongo import ASCENDING, DESCENDING
from backend.app.db import get_database, close_db_client


async def create_part2_indexes():
    """Creates required unique, lookup, and TTL indexes for Part 2 collections."""
    db = get_database()

    print("Creating Part 2 database collection indexes...")

    # staff_users: unique username
    await db.staff_users.create_index([("username", ASCENDING)], unique=True)
    await db.staff_users.create_index([("role", ASCENDING), ("is_active", ASCENDING)])

    # pending_complaints: TTL index on expires_at
    await db.pending_complaints.create_index([("expires_at", ASCENDING)], expireAfterSeconds=0)

    # otp_request_log: TTL index 1 hour (3600s) on at
    await db.otp_request_log.create_index([("at", ASCENDING)], expireAfterSeconds=3600)
    await db.otp_request_log.create_index([("email", ASCENDING), ("at", DESCENDING)])

    # complaints: unique ticket_id, query indexes
    await db.complaints.create_index([("ticket_id", ASCENDING)], unique=True)
    await db.complaints.create_index([("status", ASCENDING), ("created_at", DESCENDING)])
    await db.complaints.create_index([("assigned_technician_id", ASCENDING), ("status", ASCENDING)])
    await db.complaints.create_index([("location", ASCENDING), ("problem_type", ASCENDING)])

    # complaint_history: query by ticket_id and at
    await db.complaint_history.create_index([("ticket_id", ASCENDING), ("at", ASCENDING)])

    # ratings: unique ticket_id
    await db.ratings.create_index([("ticket_id", ASCENDING)], unique=True)
    await db.ratings.create_index([("technician_id", ASCENDING)])

    # action_tokens: unique token_hash, TTL index on expires_at
    await db.action_tokens.create_index([("token_hash", ASCENDING)], unique=True)
    await db.action_tokens.create_index([("expires_at", ASCENDING)], expireAfterSeconds=0)

    # email_outbox: lookup by status and next_attempt_at
    await db.email_outbox.create_index([("status", ASCENDING), ("next_attempt_at", ASCENDING)])

    print("Part 2 database indexes created successfully.")
    close_db_client()


if __name__ == "__main__":
    asyncio.run(create_part2_indexes())
