# MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
# One-time script to create the initial ADMIN staff account.

import sys
import getpass
import asyncio
import bcrypt
from datetime import datetime
from backend.app.db import get_database, close_db_client


async def create_admin_user(
    username: str,
    full_name: str,
    email: str,
    password: str,
    force: bool = False
):
    """Creates the initial ADMIN staff user account in MongoDB."""
    db = get_database()
    clean_username = username.strip().lower()

    # Check if any ADMIN already exists
    existing_admin = await db.staff_users.find_one({"role": "ADMIN"})
    if existing_admin and not force:
        print(f"Error: An ADMIN account ('{existing_admin['username']}') already exists. Pass --force to override.")
        close_db_client()
        return

    # Check duplicate username
    existing_user = await db.staff_users.find_one({"username": clean_username})
    if existing_user and not force:
        print(f"Error: Username '{clean_username}' already exists.")
        close_db_client()
        return

    if len(password) < 8:
        print("Error: Password must be at least 8 characters long.")
        close_db_client()
        return

    hashed_pwd = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    now_dt = datetime.utcnow()

    doc = {
        "username": clean_username,
        "password_hash": hashed_pwd,
        "full_name": full_name.strip(),
        "role": "ADMIN",
        "email": email.strip().lower(),
        "mobile": "0000000000",
        "is_active": True,
        "failed_login_count": 0,
        "locked_until": None,
        "notify_on_new_complaint": False,
        "created_by": "initial_setup",
        "created_at": now_dt,
        "deactivated_at": None,
        "technician_profile": None
    }

    if existing_user and force:
        await db.staff_users.replace_one({"username": clean_username}, doc)
        print(f"ADMIN account '{clean_username}' updated with --force.")
    else:
        res = await db.staff_users.insert_one(doc)
        print(f"Successfully created initial ADMIN account '{clean_username}' (ID: {res.inserted_id}).")

    close_db_client()


if __name__ == "__main__":
    force_flag = "--force" in sys.argv

    # Read args or prompt
    if len(sys.argv) >= 5 and not sys.argv[1].startswith("--"):
        usr = sys.argv[1]
        name = sys.argv[2]
        em = sys.argv[3]
        pwd = sys.argv[4]
    else:
        print("--- Initial Admin Creation ---")
        usr = input("Username: ").strip() or "admin"
        name = input("Full Name: ").strip() or "MNNIT Admin"
        em = input("Email Address: ").strip() or "admin@mnnit.ac.in"
        pwd = getpass.getpass("Password (min 8 chars): ").strip()

    asyncio.run(create_admin_user(usr, name, em, pwd, force=force_flag))
