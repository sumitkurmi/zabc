# MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
# Standalone execution script for auto-closing inactive student confirmation complaints.

import asyncio
from backend.app.complaint_management.services.auto_close_service import run_auto_close_check
from backend.app.db import close_db_client


async def main():
    print("Executing standalone auto-close check...")
    count = await run_auto_close_check()
    print(f"Auto-close execution completed. {count} complaint(s) closed.")
    close_db_client()


if __name__ == "__main__":
    asyncio.run(main())
