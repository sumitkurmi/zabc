# MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
# Seed script populating demo staff accounts, complaints across all statuses, history, and ratings.

import os
import sys
import asyncio
import bcrypt
from datetime import datetime, timedelta
from backend.app.db import get_database, close_db_client
from backend.app.complaint_management.models import ComplaintStatus, TechnicianAvailability, StaffRole


async def seed_complaint_management_demo(remove_only: bool = False):
    """Seeds or removes Part 2 demo dataset in MongoDB."""
    db = get_database()

    print("Cleaning up existing Part 2 demo seed records (seed_batch='part2_demo')...")

    # Delete marked records
    demo_staff = await db.staff_users.find({"seed_batch": "part2_demo"}).to_list(length=100)
    demo_staff_ids = [str(s["_id"]) for s in demo_staff]

    demo_complaints = await db.complaints.find({"seed_batch": "part2_demo"}).to_list(length=500)
    demo_tickets = [c["ticket_id"] for c in demo_complaints]

    if demo_tickets:
        await db.complaint_history.delete_many({"ticket_id": {"$in": demo_tickets}})
        await db.ratings.delete_many({"ticket_id": {"$in": demo_tickets}})
        await db.action_tokens.delete_many({"ticket_id": {"$in": demo_tickets}})

    await db.complaints.delete_many({"seed_batch": "part2_demo"})
    await db.staff_users.delete_many({"seed_batch": "part2_demo"})

    print("Part 2 demo seed cleanup complete.")

    if remove_only:
        print("Removal flag '--remove' specified. Exiting.")
        close_db_client()
        return

    # Create Staff Accounts
    demo_pwd = os.environ.get("SEED_PASSWORD", "demo_pass123")
    hashed_pwd = bcrypt.hashpw(demo_pwd.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    now_dt = datetime.now()

    # 1 Admin, 2 Managers, 4 Technicians
    staff_docs = [
        {
            "username": "demo_admin",
            "password_hash": hashed_pwd,
            "full_name": "Demo Admin User",
            "role": StaffRole.ADMIN.value,
            "email": "demo_admin@mnnit.ac.in",
            "mobile": "+919876543210",
            "is_active": True,
            "notify_on_new_complaint": True,
            "seed_batch": "part2_demo",
            "created_at": now_dt
        },
        {
            "username": "demo_manager1",
            "password_hash": hashed_pwd,
            "full_name": "Demo Manager One",
            "role": StaffRole.MANAGER.value,
            "email": "demo_mgr1@mnnit.ac.in",
            "mobile": "+919876543211",
            "is_active": True,
            "seed_batch": "part2_demo",
            "created_at": now_dt
        },
        {
            "username": "demo_manager2",
            "password_hash": hashed_pwd,
            "full_name": "Demo Manager Two",
            "role": StaffRole.MANAGER.value,
            "email": "demo_mgr2@mnnit.ac.in",
            "mobile": "+919876543212",
            "is_active": True,
            "seed_batch": "part2_demo",
            "created_at": now_dt
        }
    ]

    # Technicians
    techs_spec = [
        ("demo_tech1", "Ramesh Kumar (Hostels)", TechnicianAvailability.AVAILABLE.value, ["SVBH Hostel", "PG Hostel"], ["WIFI_PROBLEM", "LAN_PROBLEM"]),
        ("demo_tech2", "Suresh Verma (Academic)", TechnicianAvailability.AVAILABLE.value, ["Academic Campus", "Guest House"], ["IP_ADDRESS_ISSUE", "PROXY_ISSUE"]),
        ("demo_tech3", "Anita Singh (Girls Hostels)", TechnicianAvailability.AVAILABLE.value, ["SN Girls Hostel", "KN Girls Hostel"], ["WIFI_PROBLEM", "LAN_PORT_BROKEN"]),
        ("demo_tech4", "Vikram Patel (Colony & Labs)", TechnicianAvailability.UNAVAILABLE.value, ["Residential Colony"], ["LAN_PROBLEM", "LAN_PORT_BROKEN"])
    ]

    tech_ids = {}
    for un, fn, avail, zones, cats in techs_spec:
        doc = {
            "username": un,
            "password_hash": hashed_pwd,
            "full_name": fn,
            "role": StaffRole.TECHNICIAN.value,
            "email": f"{un}@mnnit.ac.in",
            "mobile": "+919876543215",
            "is_active": True,
            "technician_profile": {
                "availability": avail,
                "zones": zones,
                "categories": cats,
                "max_open_complaints": 5
            },
            "seed_batch": "part2_demo",
            "created_at": now_dt
        }
        res = await db.staff_users.insert_one(doc)
        tech_ids[un] = str(res.inserted_id)

    await db.staff_users.insert_many(staff_docs)
    print("Seeded demo staff users (password: 'demo_pass123').")

    # Seed ~30 Complaints across all statuses
    statuses = [
        ComplaintStatus.CLASSIFIED.value,
        ComplaintStatus.ASSIGNED.value,
        ComplaintStatus.DIAGNOSED.value,
        ComplaintStatus.ACTION_TAKEN.value,
        ComplaintStatus.STUDENT_CONFIRMATION.value,
        ComplaintStatus.CLOSED.value,
        ComplaintStatus.JUNK.value
    ]

    locations = ["SVBH Hostel", "Academic Campus", "SN Girls Hostel", "Residential Colony", "Guest House"]
    problem_types = ["WIFI_PROBLEM", "LAN_PROBLEM", "IP_ADDRESS_ISSUE", "PROXY_ISSUE", "LAN_PORT_BROKEN"]

    t_id_base = 261021100000

    priorities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    for idx in range(1, 31):
        st = statuses[idx % len(statuses)]
        loc = locations[idx % len(locations)]
        pt = problem_types[idx % len(problem_types)]
        t_id = str(t_id_base + idx)

        created_days = idx * 2
        created_at = now_dt - timedelta(days=created_days)
        ref_no = f"NET-{created_at.year}-{100000 + idx:06d}"

        # Special seed cases
        priority_val = priorities[idx % len(priorities)]
        agent_sug = None

        if idx == 1:
            # Unassigned CRITICAL complaint
            st = ComplaintStatus.CLASSIFIED.value
            priority_val = "CRITICAL"
            assigned_tech_id = None
        elif idx == 2:
            # CLASSIFIED complaint with agent_suggestion
            st = ComplaintStatus.CLASSIFIED.value
            priority_val = "HIGH"
            assigned_tech_id = None
            agent_sug = {
                "technician_id": tech_ids["demo_tech1"],
                "technician_name": "Ramesh Kumar (Hostels)",
                "score": 88.5,
                "reason": "Zone match SVBH Hostel, 0 open complaints, closed 3 similar faults",
                "breakdown": {"zone_match": 35, "workload": 25, "experience": 15, "cluster": 0, "performance": 13.5},
                "at": created_at + timedelta(minutes=5)
            }
        else:
            assigned_tech_id = tech_ids[f"demo_tech{(idx % 3) + 1}"] if st not in [ComplaintStatus.SUBMITTED.value, ComplaintStatus.CLASSIFIED.value] else None

        c_doc = {
            "ticket_id": t_id,
            "ref_no": ref_no,
            "name": f"Student {idx}",
            "email": f"student{idx}@mnnit.ac.in",
            "mobile": f"+9198000{idx:05d}",
            "location": loc,
            "address_room": f"Room {100 + idx}",
            "preferred_from": "09:00",
            "preferred_to": "17:00",
            "problem_type": pt,
            "additional_comment": f"Demo problem description #{idx} regarding {pt}.",
            "status": st,
            "priority": priority_val,
            "ai_category": pt,
            "ai_confidence": 0.88,
            "affected_users_count": (idx % 6) + 1,
            "similar_complaint_ids": [str(t_id_base + max(1, idx - 1))],
            "agent_suggestion": agent_sug,
            "classification_notes": {
                "method": "llm",
                "provider": "mock",
                "model": "mock-v1",
                "summary": f"Demo summary for ticket #{t_id}",
                "priority_reason": f"{priority_val}: base MEDIUM, {idx % 6 + 1} users affected",
                "analyzed_at": created_at + timedelta(minutes=2)
            },
            "assigned_technician_id": assigned_tech_id,
            "assigned_at": created_at + timedelta(hours=2) if assigned_tech_id else None,
            "assignment_count": 1 if assigned_tech_id else 0,
            "diagnosis": f"Diagnosed issue #{idx}" if st in ["DIAGNOSED", "ACTION_TAKEN", "STUDENT_CONFIRMATION", "CLOSED"] else None,
            "solution": f"Resolved issue #{idx} by adjusting network parameters." if st in ["ACTION_TAKEN", "STUDENT_CONFIRMATION", "CLOSED"] else None,
            "resolved_at": created_at + timedelta(hours=5) if st in ["ACTION_TAKEN", "STUDENT_CONFIRMATION", "CLOSED"] else None,
            "items_used": [],
            "asset_actions": [],
            "previous_attempts": [],
            "reopen_count": 0,
            "confirmation_requested_at": created_at + timedelta(hours=5) if st in ["STUDENT_CONFIRMATION", "CLOSED"] else None,
            "closed_at": created_at + timedelta(hours=24) if st == "CLOSED" else None,
            "closed_by": "STUDENT" if st == "CLOSED" else None,
            "previous_status": "CLASSIFIED" if st == "JUNK" else None,
            "seed_batch": "part2_demo",
            "created_at": created_at,
            "updated_at": created_at
        }

        await db.complaints.insert_one(c_doc)

        # History entries (with AGENT actor for AUTO assigned)
        hist_actor_type = "AGENT" if (assigned_tech_id and idx % 2 == 0) else "SYSTEM"
        hist_actor_name = "Assignment Agent" if hist_actor_type == "AGENT" else "Demo Seeder"

        hist_entry = {
            "ticket_id": t_id,
            "event_type": "ASSIGNMENT" if assigned_tech_id else "STATUS_CHANGE",
            "from_status": "SUBMITTED",
            "to_status": st,
            "actor_type": hist_actor_type,
            "actor_name": hist_actor_name,
            "note": "Automatically assigned by Assignment Agent" if hist_actor_type == "AGENT" else "Initial demo seed state",
            "at": created_at
        }
        await db.complaint_history.insert_one(hist_entry)

        # Seed Rating for closed complaints
        if st == "CLOSED" and assigned_tech_id:
            rating_val = (idx % 5) + 1
            await db.ratings.insert_one({
                "ticket_id": t_id,
                "technician_id": assigned_tech_id,
                "rating": rating_val,
                "feedback": f"Great service for ticket {t_id}!",
                "created_at": created_at + timedelta(hours=25)
            })

    print(f"Seeded 30 demo complaints across all statuses with history and ratings.")
    close_db_client()


if __name__ == "__main__":
    remove_flag = "--remove" in sys.argv
    asyncio.run(seed_complaint_management_demo(remove_only=remove_flag))
