"""Seed database script for populating demo chats containing rich Markdown content.

Run with: PYTHONPATH=. python3 scripts_db/seed_demo_chats.py
"""

import asyncio
from datetime import datetime
from backend.app.db import get_database, close_db_client


async def seed_demo_chats():
    """Inserts two demo chats with Markdown formatting (bold, code, tables, lists) into MongoDB."""
    db = get_database()

    demo_chats = [
        {
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "message_count": 2,
            "detected_category": "WIFI_PROBLEM",
            "status": "UNASSIGNED",
            "reference_category_slug": None,
            "moved_at": None,
            "messages": [
                {
                    "role": "user",
                    "content": "My laptop connects to MNNIT-WiFi but I cannot load any website. How do I fix this?",
                    "created_at": datetime.utcnow(),
                    "is_off_topic": False,
                    "source_doc_ids": []
                },
                {
                    "role": "assistant",
                    "content": (
                        "Follow these **step-by-step instructions** to restore your internet connection:\n\n"
                        "1. Flush your DNS cache and renew your IP address.\n"
                        "2. Ensure your proxy server settings are set to **Auto-detect**.\n\n"
                        "### Recommended Command\n"
                        "Open Terminal or Command Prompt and run:\n\n"
                        "```bash\n"
                        "ipconfig /flushdns\n"
                        "ipconfig /renew\n"
                        "```\n\n"
                        "Here is a summary of typical Wi-Fi statuses:\n\n"
                        "| Status | Primary Cause | Action Required |\n"
                        "| :--- | :--- | :--- |\n"
                        "| No Internet | Stale IP / DNS | Run `ipconfig /renew` |\n"
                        "| Auth Failed | Expired Credentials | Update portal login |\n\n"
                        "For detailed guide, visit [MNNIT Network SOPs](https://mnnit.ac.in)."
                    ),
                    "created_at": datetime.utcnow(),
                    "is_off_topic": False,
                    "source_doc_ids": []
                }
            ]
        },
        {
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "message_count": 2,
            "detected_category": "IP_ADDRESS_ISSUE",
            "status": "UNASSIGNED",
            "reference_category_slug": None,
            "moved_at": None,
            "messages": [
                {
                    "role": "user",
                    "content": "I am getting an IP conflict error in Hostel Block A.",
                    "created_at": datetime.utcnow(),
                    "is_off_topic": False,
                    "source_doc_ids": []
                },
                {
                    "role": "assistant",
                    "content": (
                        "Hostel Block A IP conflicts are usually caused by static IP misconfigurations.\n\n"
                        "**Quick Troubleshooting Steps:**\n"
                        "- Switch your network adapter to **DHCP (Obtain an IP address automatically)**.\n"
                        "- Restart your network interface.\n\n"
                        "```python\n"
                        "# Sample script to verify IP assignment status\n"
                        "import socket\n"
                        "print('Host IP:', socket.gethostbyname(socket.gethostname()))\n"
                        "```\n\n"
                        "Please verify your settings with your block administrator if problem persists."
                    ),
                    "created_at": datetime.utcnow(),
                    "is_off_topic": False,
                    "source_doc_ids": []
                }
            ]
        }
    ]

    result = await db.chats.insert_many(demo_chats)
    print(f"Successfully seeded {len(result.inserted_ids)} demo chats into 'chats' collection.")
    close_db_client()


if __name__ == "__main__":
    asyncio.run(seed_demo_chats())
