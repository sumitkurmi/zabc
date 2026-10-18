"""MongoDB index initialization script.

Creates required unique and compound indexes on MongoDB collections to ensure
data integrity and high-performance querying across complaint and admin workflows.

Indexes created:
- complaints: `ref_no` (unique), `created_at` (descending)
- chats: `status` + `created_at` (descending), text index on `messages.content`
- reference_categories: `slug` (unique)
- documents: `category_slug` + `uploaded_at` (descending), `chat_id`
"""

import asyncio
import sys
from pymongo import IndexModel, ASCENDING, DESCENDING, TEXT
from backend.app.db import get_database, close_db_client


async def create_indexes():
    """Asynchronously applies indexes across MongoDB collections."""
    db = get_database()
    print("Setting up MongoDB indexes...")

    # 1. Complaints collection indexes
    await db.complaints.create_index([("ref_no", ASCENDING)], unique=True)
    await db.complaints.create_index([("created_at", DESCENDING)])

    # 2. Chats collection indexes
    await db.chats.create_index([("status", ASCENDING), ("created_at", DESCENDING)])
    await db.chats.create_index([("messages.content", TEXT)])

    # 3. Reference Categories collection indexes
    await db.reference_categories.create_index([("slug", ASCENDING)], unique=True)

    # 4. Documents collection indexes
    await db.documents.create_index([("category_slug", ASCENDING), ("uploaded_at", DESCENDING)])
    await db.documents.create_index([("chat_id", ASCENDING)])

    print("MongoDB indexes created successfully.")


if __name__ == "__main__":
    asyncio.run(create_indexes())
    close_db_client()
