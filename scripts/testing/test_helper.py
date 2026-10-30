#!/usr/bin/env python3
"""
Test Helper Script for MNNIT Network Complaint Portal
Belongs to the test plan. Only touches records created for testing or specific names.
"""
import argparse
import os
import asyncio
from datetime import datetime, timedelta, timezone
from pymongo import MongoClient
from dotenv import load_dotenv

# Load .env
load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "network_portal")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

def show_complaint(ticket: str):
    c = db.complaints.find_one({"ticket_id": ticket})
    if not c:
        print(f"Complaint {ticket} not found.")
        return
    print("=== COMPLAINT ===")
    for k, v in c.items():
        if k not in ['history', 'items_used', 'agent_notes', 'ratings']:
            print(f"{k}: {v}")

    print("\n=== HISTORY ===")
    for h in c.get("history", []):
        print(f" - {h}")

    print("\n=== ITEMS USED ===")
    for i in c.get("items_used", []):
        print(f" - {i}")

    print("\n=== AGENT NOTES ===")
    print(c.get("agent_notes"))

    print("\n=== RATING ===")
    print(c.get("rating"))

def show_agent_runs(ticket: str = None):
    query = {}
    if ticket:
        query["ticket_id"] = ticket
    runs = db.agent_runs.find(query).sort("created_at", -1).limit(10)
    for r in runs:
        print(r)

def show_outbox(ticket: str = None):
    query = {}
    if ticket:
        query["ticket_id"] = ticket
    emails = db.outbox.find(query).sort("created_at", -1).limit(10)
    for e in emails:
        print(f"[{e.get('status')}] To: {e.get('to')} | Subject: {e.get('subject')}")

def show_pending(email: str = None):
    query = {}
    if email:
        query["email"] = email
    pending = db.pending_complaints.find(query)
    for p in pending:
        print(p)

def expire_otp(pending_id: str):
    res = db.pending_complaints.update_one(
        {"_id": pending_id},
        {"$set": {"otp_expires_at": datetime.now(timezone.utc) - timedelta(hours=1)}}
    )
    if res.modified_count:
        print("OTP expired successfully.")
    else:
        print("Not found.")

def age_complaint(ticket: str, days: int):
    # moves confirmation_requested_at back N days
    res = db.complaints.update_one(
        {"ticket_id": ticket},
        {"$set": {"confirmation_requested_at": datetime.now(timezone.utc) - timedelta(days=days)}}
    )
    if res.modified_count:
        print(f"Moved confirmation_requested_at back {days} days for {ticket}.")
    else:
        print("Not found.")

def make_complaints(count: int, location: str, problem_type: str):
    import random
    import string

    for i in range(count):
        ticket_id = "".join(random.choices(string.digits, k=12))
        email = f"test_{ticket_id}@mnnit.ac.in"
        doc = {
            "ticket_id": ticket_id,
            "status": "Submitted",
            "student": {
                "name": "Manual Test",
                "email": email,
                "mobile": "9999999999",
                "room_number": "A-1"
            },
            "location": location,
            "problem_type": problem_type,
            "priority": "P3",
            "seed_batch": "manual_test",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "history": [{"status": "Submitted", "timestamp": datetime.now(timezone.utc), "actor_type": "student", "actor_name": "Test", "notes": "created by helper"}]
        }
        db.complaints.insert_one(doc)
    print(f"Created {count} complaints.")

def cleanup(manual_test: bool):
    if manual_test:
        res = db.complaints.delete_many({"seed_batch": "manual_test"})
        print(f"Deleted {res.deleted_count} manual test complaints.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test helper for MNNIT Portal")
    subparsers = parser.add_subparsers(dest="command")

    sc_parser = subparsers.add_parser("show-complaint")
    sc_parser.add_argument("ticket")

    ar_parser = subparsers.add_parser("show-agent-runs")
    ar_parser.add_argument("--ticket")

    so_parser = subparsers.add_parser("show-outbox")
    so_parser.add_argument("--ticket")

    sp_parser = subparsers.add_parser("show-pending")
    sp_parser.add_argument("--email")

    eo_parser = subparsers.add_parser("expire-otp")
    eo_parser.add_argument("pending_id")

    ac_parser = subparsers.add_parser("age-complaint")
    ac_parser.add_argument("ticket")
    ac_parser.add_argument("--days", type=int, required=True)

    mc_parser = subparsers.add_parser("make-complaints")
    mc_parser.add_argument("--count", type=int, required=True)
    mc_parser.add_argument("--location", type=str, required=True)
    mc_parser.add_argument("--problem-type", dest="problem_type", type=str, required=True)

    cu_parser = subparsers.add_parser("cleanup")
    cu_parser.add_argument("--manual-test", action="store_true")

    args = parser.parse_args()

    if args.command == "show-complaint":
        show_complaint(args.ticket)
    elif args.command == "show-agent-runs":
        show_agent_runs(args.ticket)
    elif args.command == "show-outbox":
        show_outbox(args.ticket)
    elif args.command == "show-pending":
        show_pending(args.email)
    elif args.command == "expire-otp":
        expire_otp(args.pending_id)
    elif args.command == "age-complaint":
        age_complaint(args.ticket, args.days)
    elif args.command == "make-complaints":
        make_complaints(args.count, args.location, args.problem_type)
    elif args.command == "cleanup":
        cleanup(args.manual_test)
    else:
        parser.print_help()
