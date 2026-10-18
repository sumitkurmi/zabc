"""Database seeding script for fixed reference categories.

Populates the MongoDB `reference_categories` collection with the six required
curated reference categories from Section 7 of the design specification.

Categories seeded:
1. `complaint-logs`: Previous complaint and fault logs
2. `admin-observations`: Network administrator observations
3. `corrective-measures`: Approved corrective measures
4. `frequent-problems`: Frequently encountered network problems
5. `student-guidelines`: Student troubleshooting guidelines
6. `manuals-sops`: Device manuals and standard operating procedures
"""

import asyncio
from backend.app.db import get_database, close_db_client

# Fixed list of reference categories per specification Section 7
SEED_CATEGORIES = [
    {
        "slug": "complaint-logs",
        "name": "Previous complaint and fault logs",
        "description": "Historical fault reports, complaint records, and resolved outage tickets."
    },
    {
        "slug": "admin-observations",
        "name": "Network administrator observations",
        "description": "Admin inspection logs, infrastructure status notes, and campus network topology observations."
    },
    {
        "slug": "corrective-measures",
        "name": "Approved corrective measures",
        "description": "Official step-by-step resolution actions approved by IT administration."
    },
    {
        "slug": "frequent-problems",
        "name": "Frequently encountered network problems",
        "description": "Common student issues with hostel Wi-Fi, DHCP lease timeouts, and browser proxy setups."
    },
    {
        "slug": "student-guidelines",
        "name": "Student troubleshooting guidelines",
        "description": "First-line self-service guidance and step-by-step device connection instructions."
    },
    {
        "slug": "manuals-sops",
        "name": "Device manuals and standard operating procedures",
        "description": "Hardware manuals for campus access points, switches, routers, and standard network SOPs."
    }
]


async def seed_categories():
    """Seeds or updates the reference categories collection in MongoDB."""
    db = get_database()
    print("Seeding reference categories...")

    for cat in SEED_CATEGORIES:
        await db.reference_categories.update_one(
            {"slug": cat["slug"]},
            {"$set": cat},
            upsert=True
        )

    print("Reference categories seeded successfully.")


if __name__ == "__main__":
    asyncio.run(seed_categories())
    close_db_client()
