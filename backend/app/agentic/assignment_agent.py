# MODULE: Agentic Classification and Assignment (Module 2) - this file belongs to the code for this module.
# Assignment agent selecting and scoring best technician candidates using hard filters, multi-factor scoring, and execution modes.

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from backend.app.db import get_database
from backend.app.config import settings
from backend.app import events
from backend.app.services.llm_router import llm_router
from backend.app.complaint_management.models import (
    StaffRole,
    TechnicianAvailability,
    ComplaintStatus,
    HistoryEventType,
    HistoryActorType
)
from backend.app.complaint_management.services.assignment_service import AssignmentService
from backend.app.complaint_management.services.scoring_service import compute_technician_score
from backend.app.agentic.schemas import CandidateEvaluation, ScoreBreakdown, AgentSuggestion
from backend.app.agentic.constants import (
    WEIGHT_ZONE_MATCH,
    WEIGHT_WORKLOAD,
    WEIGHT_EXPERIENCE,
    WEIGHT_CLUSTER,
    WEIGHT_PERFORMANCE
)

logger = logging.getLogger("agentic.assignment")


class AssignmentAgent:
    """Agent that ranks technicians and executes automatic or suggested assignment."""

    def _get_weights(self) -> Dict[str, float]:
        """Parses weights from AGENT_ASSIGNMENT_WEIGHTS JSON setting or defaults."""
        defaults = {
            "ZONE_MATCH": WEIGHT_ZONE_MATCH,
            "WORKLOAD": WEIGHT_WORKLOAD,
            "EXPERIENCE": WEIGHT_EXPERIENCE,
            "CLUSTER": WEIGHT_CLUSTER,
            "PERFORMANCE": WEIGHT_PERFORMANCE
        }

        weights_raw = getattr(settings, "AGENT_ASSIGNMENT_WEIGHTS", "")
        if weights_raw:
            try:
                parsed = json.loads(weights_raw)
                for k, v in parsed.items():
                    if k.upper() in defaults and isinstance(v, (int, float)):
                        defaults[k.upper()] = float(v)
            except Exception as e:
                logger.warning(f"[AssignmentAgent] Failed to parse AGENT_ASSIGNMENT_WEIGHTS: {e}")

        return defaults

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluates technician candidates and performs assignment based on AGENT_ASSIGNMENT_MODE.

        Args:
            context: Context containing 'complaint', 'routing_category', 'similar_complaint_ids'.

        Returns:
            Dict containing assigned status, candidates list, suggestion, and action taken.
        """
        db = get_database()
        complaint = context.get("complaint", {})
        ticket_id = complaint.get("ticket_id")
        location = complaint.get("location", "")
        routing_category = context.get("routing_category") or complaint.get("problem_type")
        similar_ids = context.get("similar_complaint_ids", [])

        mode = getattr(settings, "AGENT_ASSIGNMENT_MODE", "auto").lower()
        if mode == "off":
            logger.info(f"[AssignmentAgent] Assignment mode is OFF for ticket {ticket_id}. Skipping.")
            return {"status": "SKIPPED", "reason": "Assignment mode is OFF"}

        # 1. Fetch all active technician staff users
        tech_cursor = db.staff_users.find({
            "role": StaffRole.TECHNICIAN.value,
            "is_active": True
        })
        all_techs = [doc async for doc in tech_cursor]

        # 2. Apply Hard Filters
        eligible_techs = []
        for tech in all_techs:
            t_profile = tech.get("technician_profile") or {}

            # Hard filter A: Availability
            if t_profile.get("availability") != TechnicianAvailability.AVAILABLE.value:
                continue

            # Hard filter B: Category coverage
            categories = t_profile.get("categories") or []
            if routing_category not in categories:
                continue

            # Hard filter C: Live open complaints limit (ASSIGNED or DIAGNOSED)
            t_id = str(tech["_id"])
            open_count = await db.complaints.count_documents({
                "assigned_technician_id": t_id,
                "status": {"$in": [ComplaintStatus.ASSIGNED.value, ComplaintStatus.DIAGNOSED.value]}
            })

            max_open = t_profile.get("max_open_complaints")
            if max_open is not None and open_count >= int(max_open):
                continue

            tech["_live_open_count"] = open_count
            eligible_techs.append(tech)

        if not eligible_techs:
            logger.warning(f"[AssignmentAgent] No eligible technician found for ticket {ticket_id} in category '{routing_category}'.")

            # Check if complaint_needs_attention should be emitted
            attention_notified_at = complaint.get("attention_notified_at")
            if not attention_notified_at:
                now_dt = datetime.utcnow()
                await db.complaints.update_one(
                    {"ticket_id": ticket_id},
                    {"$set": {"attention_notified_at": now_dt}}
                )

                # Emit needs attention event
                await events.emit("complaint_needs_attention", {
                    "ticket_id": ticket_id,
                    "complaint": complaint,
                    "reason": f"No available technician in category '{routing_category}'"
                })

            # Add history NOTE
            note_doc = {
                "ticket_id": ticket_id,
                "event_type": HistoryEventType.NOTE.value,
                "from_status": complaint.get("status"),
                "to_status": complaint.get("status"),
                "actor_type": HistoryActorType.AGENT.value,
                "actor_id": "assignment_agent",
                "actor_role": "AGENT",
                "actor_name": "Assignment Agent",
                "note": f"No available technician in category '{routing_category}'",
                "details": {"reason": "NO_ELIGIBLE_TECHNICIAN", "routing_category": routing_category},
                "at": datetime.utcnow()
            }
            await db.complaint_history.insert_one(note_doc)

            return {
                "status": "NO_ELIGIBLE_TECHNICIAN",
                "reason": f"No available technician in category '{routing_category}'"
            }

        # 3. Calculate Scores for Eligible Technicians
        weights = self._get_weights()
        highest_open = max([t["_live_open_count"] for t in eligible_techs]) if eligible_techs else 0
        ninety_days_ago = datetime.utcnow() - timedelta(days=90)

        evaluated_candidates: List[CandidateEvaluation] = []

        for tech in eligible_techs:
            t_id = str(tech["_id"])
            t_profile = tech.get("technician_profile") or {}
            open_count = tech["_live_open_count"]

            # Factor A: Zone Match
            zones = t_profile.get("zones") or []
            zone_score = weights["ZONE_MATCH"] if location in zones else 0.0

            # Factor B: Workload Score = WEIGHT_WORKLOAD * (1 - open_count / (highest_open + 1))
            workload_ratio = 1.0 - (open_count / (highest_open + 1))
            workload_score = round(weights["WORKLOAD"] * max(workload_ratio, 0.0), 2)

            # Factor C: Experience Score = WEIGHT_EXPERIENCE * min(n, 5) / 5
            closed_n = await db.complaints.count_documents({
                "assigned_technician_id": t_id,
                "status": ComplaintStatus.CLOSED.value,
                "updated_at": {"$gte": ninety_days_ago},
                "$or": [
                    {"location": location},
                    {"ai_category": routing_category},
                    {"problem_type": routing_category}
                ]
            })
            exp_score = round(weights["EXPERIENCE"] * (min(closed_n, 5) / 5.0), 2)

            # Factor D: Cluster Score = WEIGHT_CLUSTER if holds an open complaint in similar_ids
            cluster_match = False
            if similar_ids:
                cluster_count = await db.complaints.count_documents({
                    "assigned_technician_id": t_id,
                    "status": {"$in": [ComplaintStatus.ASSIGNED.value, ComplaintStatus.DIAGNOSED.value]},
                    "ticket_id": {"$in": similar_ids}
                })
                cluster_match = cluster_count > 0

            cluster_score = weights["CLUSTER"] if cluster_match else 0.0

            # Factor E: Performance Score = WEIGHT_PERFORMANCE * (rating / 5.0)
            avg_rating = tech.get("avg_rating")
            rating_count = tech.get("rating_count", 0)
            resolved_count = tech.get("resolved_count", 0)

            if avg_rating is not None and rating_count > 0:
                calc_rating = compute_technician_score(avg_rating, rating_count, resolved_count)
            else:
                calc_rating = 5.0  # Neutral 5 score when no ratings exist

            perf_score = round(weights["PERFORMANCE"] * (min(calc_rating, 5.0) / 5.0), 2)

            total_score = round(zone_score + workload_score + exp_score + cluster_score + perf_score, 2)

            # Build Deterministic Reason
            reason_parts = []
            if zone_score > 0:
                reason_parts.append(f"Zone match '{location}'")
            reason_parts.append(f"{open_count} open complaint(s)")
            if closed_n > 0:
                reason_parts.append(f"closed {closed_n} similar fault(s) in last 90d")
            if cluster_match:
                reason_parts.append("holds open complaint in same cluster")

            det_reason = ", ".join(reason_parts) if reason_parts else "Meets availability and category requirements"

            breakdown = ScoreBreakdown(
                zone_match=zone_score,
                workload=workload_score,
                experience=exp_score,
                cluster=cluster_score,
                performance=perf_score,
                total=total_score
            )

            candidate_eval = CandidateEvaluation(
                technician_id=t_id,
                full_name=tech.get("full_name", "Technician"),
                staff_id=str(tech.get("staff_id") or t_id),
                score=total_score,
                breakdown=breakdown,
                reason=det_reason
            )

            # Store auxiliary sorting properties
            tech["_eval"] = candidate_eval
            tech["_last_assigned_at"] = tech.get("last_assigned_at") or datetime.min

        # 4. Tie-breaking & Ranking:
        # Priority: higher total score, lower open_count, oldest last_assigned_at, staff_id string
        def sort_key(tech_doc):
            ev = tech_doc["_eval"]
            return (
                -ev.score,
                tech_doc["_live_open_count"],
                tech_doc["_last_assigned_at"],
                str(tech_doc.get("staff_id") or tech_doc["_id"])
            )

        ranked_techs = sorted(eligible_techs, key=sort_key)
        top_candidates = [t["_eval"] for t in ranked_techs[:3]]

        winning_tech_doc = ranked_techs[0]
        winning_eval = winning_tech_doc["_eval"]

        # 5. LLM Reason Rewrite (Optional)
        use_llm_reason = getattr(settings, "AGENT_LLM_REASON", True)
        final_reason = winning_eval.reason

        if use_llm_reason:
            try:
                llm_rewritten = await llm_router.rewrite_assignment_reason(winning_eval.reason)
                if llm_rewritten:
                    final_reason = llm_rewritten
            except Exception as e:
                logger.warning(f"[AssignmentAgent] LLM reason rewrite failed: {e}. Using deterministic text.")

        actor_agent = {
            "type": HistoryActorType.AGENT.value,
            "id": "assignment_agent",
            "role": "AGENT",
            "name": "Assignment Agent"
        }

        # 6. Mode Execution: auto vs suggest
        if mode == "auto":
            # Execute actual assignment via AssignmentService
            updated = await AssignmentService.assign(
                ticket_id=ticket_id,
                technician_id=winning_eval.technician_id,
                actor=actor_agent,
                method="AUTO",
                reason=final_reason
            )

            # Update winning technician's last_assigned_at timestamp
            await db.staff_users.update_one(
                {"_id": winning_tech_doc["_id"]},
                {"$set": {"last_assigned_at": datetime.utcnow()}}
            )

            # Store top candidates in assignment details metadata
            await db.complaints.update_one(
                {"ticket_id": ticket_id},
                {
                    "$set": {
                        "assignment_details": {
                            "top_candidates": [c.model_dump() for c in top_candidates],
                            "assigned_by": "Assignment Agent",
                            "method": "AUTO"
                        }
                    }
                }
            )

            return {
                "status": "ASSIGNED",
                "assigned_technician_id": winning_eval.technician_id,
                "technician_name": winning_eval.full_name,
                "reason": final_reason,
                "candidates": [c.model_dump() for c in top_candidates]
            }

        elif mode == "suggest":
            # Store suggestion on complaint document
            suggestion = AgentSuggestion(
                technician_id=winning_eval.technician_id,
                technician_name=winning_eval.full_name,
                score=winning_eval.score,
                reason=final_reason,
                breakdown=winning_eval.breakdown,
                at=datetime.utcnow()
            )

            await db.complaints.update_one(
                {"ticket_id": ticket_id},
                {
                    "$set": {
                        "agent_suggestion": suggestion.model_dump(),
                        "assignment_details": {
                            "top_candidates": [c.model_dump() for c in top_candidates],
                            "suggested_by": "Assignment Agent"
                        }
                    }
                }
            )

            # Add history NOTE
            note_doc = {
                "ticket_id": ticket_id,
                "event_type": HistoryEventType.NOTE.value,
                "from_status": complaint.get("status"),
                "to_status": complaint.get("status"),
                "actor_type": HistoryActorType.AGENT.value,
                "actor_id": "assignment_agent",
                "actor_role": "AGENT",
                "actor_name": "Assignment Agent",
                "note": f"Suggested technician {winning_eval.full_name}: {final_reason}",
                "details": suggestion.model_dump(),
                "at": datetime.utcnow()
            }
            await db.complaint_history.insert_one(note_doc)

            return {
                "status": "SUGGESTED",
                "suggestion": suggestion.model_dump(),
                "candidates": [c.model_dump() for c in top_candidates]
            }

        return {"status": "SKIPPED", "reason": f"Unknown mode '{mode}'"}
