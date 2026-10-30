# MODULE: Agentic Classification and Assignment (Module 2) - this file belongs to the code for this module.
# Agent detecting open complaint clusters, calculating affected user counts, and searching historical fault solutions.

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from backend.app.db import get_database
from backend.app.config import settings
from backend.app.services.sanitizer import sanitize_text
from backend.app.complaint_management.models import ComplaintStatus, HistoryEventType, HistoryActorType
from backend.app.agentic.priority_agent import compute_priority

logger = logging.getLogger("agentic.similar_fault")


class SimilarFaultAgent:
    """Agent identifying cluster faults and previous resolution history."""

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Executes similar fault analysis and cluster propagation.

        Args:
            context: Context containing 'complaint', 'routing_category', 'priority_hint', 'affected_users_hint'.

        Returns:
            Dict containing affected_users_count, similar_complaint_ids, and similar_snippets list.
        """
        db = get_database()
        complaint = context.get("complaint", {})
        ticket_id = complaint.get("ticket_id")
        location = complaint.get("location", "")
        routing_category = context.get("routing_category") or complaint.get("problem_type")
        student_email = complaint.get("email")
        affected_users_hint = context.get("affected_users_hint")

        window_hours = int(getattr(settings, "AGENT_SIMILAR_WINDOW_HOURS", 6))
        previous_days = int(getattr(settings, "AGENT_PREVIOUS_FAULT_DAYS", 90))

        now_dt = datetime.utcnow()
        cluster_cutoff = now_dt - timedelta(hours=window_hours)
        previous_cutoff = now_dt - timedelta(days=previous_days)

        # 1. Find Open Cluster members
        # Open cluster: status not in [CLOSED, JUNK], location == location, routing category == routing_category, created >= cluster_cutoff
        open_cluster_cursor = db.complaints.find({
            "ticket_id": {"$ne": ticket_id},
            "status": {"$nin": [ComplaintStatus.CLOSED.value, ComplaintStatus.JUNK.value]},
            "location": location,
            "$or": [
                {"ai_category": routing_category},
                {"problem_type": routing_category}
            ],
            "created_at": {"$gte": cluster_cutoff}
        }).sort("created_at", -1)

        open_cluster_docs = [doc async for doc in open_cluster_cursor]

        # Calculate distinct student emails in cluster
        cluster_emails = set()
        if student_email:
            cluster_emails.add(student_email.strip().lower())

        open_cluster_ticket_ids = []
        for doc in open_cluster_docs:
            open_cluster_ticket_ids.append(doc["ticket_id"])
            if doc.get("email"):
                cluster_emails.add(doc["email"].strip().lower())

        calculated_count = len(cluster_emails)
        if affected_users_hint is not None:
            affected_users_count = max(calculated_count, int(affected_users_hint))
        else:
            affected_users_count = max(calculated_count, 1)

        # Cap at 500 max
        affected_users_count = min(affected_users_count, 500)

        # 2. Find Previous CLOSED Faults with Solutions
        prev_faults_cursor = db.complaints.find({
            "ticket_id": {"$ne": ticket_id},
            "status": ComplaintStatus.CLOSED.value,
            "location": location,
            "$or": [
                {"ai_category": routing_category},
                {"problem_type": routing_category}
            ],
            "created_at": {"$gte": previous_cutoff},
            "solution": {"$exists": True, "$ne": "", "$ne": None}
        }).sort("created_at", -1).limit(10)

        prev_faults_docs = [doc async for doc in prev_faults_cursor]

        # Build similar list (max 5 ticket IDs, open cluster first then previous faults)
        similar_snippets: List[Dict[str, Any]] = []
        similar_ticket_ids: List[str] = []

        for doc in open_cluster_docs:
            if len(similar_ticket_ids) >= 5:
                break
            tid = doc["ticket_id"]
            similar_ticket_ids.append(tid)
            comment_text = sanitize_text(doc.get("additional_comment", ""))[:200]
            similar_snippets.append({
                "ticket_id": tid,
                "relation": "OPEN_CLUSTER",
                "solution_snippet": comment_text or "Open complaint in same cluster"
            })

        for doc in prev_faults_docs:
            if len(similar_ticket_ids) >= 5:
                break
            tid = doc["ticket_id"]
            if tid not in similar_ticket_ids:
                similar_ticket_ids.append(tid)
                solution_text = sanitize_text(doc.get("solution", ""))[:200]
                similar_snippets.append({
                    "ticket_id": tid,
                    "relation": "PREVIOUS_FAULT",
                    "solution_snippet": solution_text or "Resolved fault"
                })

        # 3. Cluster Propagation: Update other open cluster members
        if open_cluster_docs:
            for member in open_cluster_docs:
                m_tid = member["ticket_id"]
                old_users_count = member.get("affected_users_count", 1)
                new_users_count = max(old_users_count, affected_users_count)

                # Re-evaluate priority for cluster member (priority can only go UP)
                m_priority_hint = member.get("classification_notes", {}).get("priority_hint", "MEDIUM")
                m_computed = compute_priority(
                    priority_hint=m_priority_hint,
                    affected_users_count=new_users_count,
                    location=location,
                    recurring=True  # Has cluster members
                )

                old_priority = member.get("priority", "MEDIUM")
                p_order = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
                final_priority = old_priority
                if p_order.get(m_computed["priority"], 1) > p_order.get(old_priority, 1):
                    final_priority = m_computed["priority"]

                # Update member complaint
                await db.complaints.update_one(
                    {"ticket_id": m_tid},
                    {
                        "$set": {
                            "affected_users_count": new_users_count,
                            "priority": final_priority
                        }
                    }
                )

                # Add history NOTE entry for cluster update
                note_entry = {
                    "ticket_id": m_tid,
                    "event_type": HistoryEventType.NOTE.value,
                    "from_status": member.get("status"),
                    "to_status": member.get("status"),
                    "actor_type": HistoryActorType.AGENT.value,
                    "actor_id": "similar_fault_agent",
                    "actor_role": "AGENT",
                    "actor_name": "Similar Fault Agent",
                    "note": f"Cluster expanded: affected users updated to {new_users_count}, priority updated to {final_priority}",
                    "details": {
                        "cluster_trigger_ticket_id": ticket_id,
                        "affected_users_count": new_users_count,
                        "priority": final_priority
                    },
                    "at": now_dt
                }
                await db.complaint_history.insert_one(note_entry)

        return {
            "affected_users_count": affected_users_count,
            "similar_complaint_ids": similar_ticket_ids,
            "similar_snippets": similar_snippets
        }
