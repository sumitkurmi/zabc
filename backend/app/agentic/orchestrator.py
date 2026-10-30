# MODULE: Agentic Classification and Assignment (Module 2) - this file belongs to the code for this module.
# Orchestrator sequencing agent workflows, updating complaint metadata, and writing audit run logs.

import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from backend.app.db import get_database
from backend.app.config import settings
from backend.app.complaint_management.models import ComplaintStatus, HistoryActorType
from backend.app.complaint_management.services.status_service import StatusService
from backend.app.agentic.classification_agent import ClassificationAgent, get_routing_category
from backend.app.agentic.equipment_matcher import find_affected_equipment
from backend.app.agentic.similar_fault_agent import SimilarFaultAgent
from backend.app.agentic.priority_agent import PriorityAgent
from backend.app.agentic.assignment_agent import AssignmentAgent
from backend.app.agentic.schemas import AgentRunModel, ClassificationNotes
from backend.app.agentic.constants import (
    AGENT_STATUS_RUNNING,
    AGENT_STATUS_DONE,
    AGENT_STATUS_FAILED
)

logger = logging.getLogger("agentic.orchestrator")


class AgenticOrchestrator:
    """Main pipeline orchestrator sequencing classification, fault analysis, priority estimation, and assignment."""

    async def _record_agent_run(
        self,
        ticket_id: str,
        agent_name: str,
        started_at: datetime,
        duration_ms: float,
        method: str,
        provider: Optional[str],
        model: Optional[str],
        success: bool,
        error: Optional[str],
        output: Dict[str, Any]
    ) -> None:
        """Inserts an auditable agent execution log into agent_runs collection."""
        try:
            db = get_database()
            # PRIVACY FILTER: Remove any potential personal data from logged output
            safe_output = output.copy() if output else {}
            for sensitive_key in ["name", "email", "mobile", "address_room", "student_name"]:
                safe_output.pop(sensitive_key, None)

            run_doc = AgentRunModel(
                ticket_id=ticket_id,
                agent=agent_name,
                started_at=started_at,
                duration_ms=duration_ms,
                method=method or "rules",
                provider=provider,
                model=model,
                success=success,
                error=error,
                output=safe_output
            )
            await db.agent_runs.insert_one(run_doc.model_dump())
        except Exception as e:
            logger.error(f"[Orchestrator] Failed writing agent_runs log: {e}")

    async def run_full_pipeline(self, ticket_id: str) -> Dict[str, Any]:
        """Runs stage FULL pipeline for a new or unassigned complaint ticket.

        Args:
            ticket_id: 12-digit ticket ID.

        Returns:
            Dict summary of orchestrator execution results.
        """
        db = get_database()

        # 1. Re-read complaint
        complaint = await db.complaints.find_one({"ticket_id": ticket_id})
        if not complaint:
            raise ValueError(f"Complaint ticket '{ticket_id}' not found.")

        # Respect manual actions: If already JUNK or closed or assigned manually, check state
        if complaint.get("status") == ComplaintStatus.JUNK.value:
            logger.info(f"[Orchestrator] Complaint '{ticket_id}' is JUNK. Skipping pipeline.")
            return {"status": "SKIPPED", "reason": "Complaint is JUNK"}

        # Set agent_status to RUNNING
        await db.complaints.update_one(
            {"ticket_id": ticket_id},
            {"$set": {"agent_status": AGENT_STATUS_RUNNING}}
        )

        try:
            # Step 1: Classification Agent
            t0 = time.perf_counter()
            start_dt = datetime.utcnow()
            class_agent = ClassificationAgent()
            class_res = await class_agent.run({"complaint": complaint})
            dur_ms = (time.perf_counter() - t0) * 1000

            notes_dict = class_res.get("classification_notes", {})
            await self._record_agent_run(
                ticket_id=ticket_id,
                agent_name="ClassificationAgent",
                started_at=start_dt,
                duration_ms=dur_ms,
                method=notes_dict.get("method", "rules"),
                provider=notes_dict.get("provider"),
                model=notes_dict.get("model"),
                success=True,
                error=None,
                output=class_res
            )

            # Extract routing category
            ai_category = class_res["ai_category"]
            ai_confidence = class_res["ai_confidence"]
            routing_cat = get_routing_category({
                "ai_category": ai_category,
                "ai_confidence": ai_confidence,
                "problem_type": complaint.get("problem_type")
            })

            # Step 2: Equipment Matcher (Best Effort)
            affected_equipment = await find_affected_equipment(
                location_name=complaint.get("location", ""),
                problem_category=routing_cat,
                address_room=complaint.get("address_room")
            )

            # Step 3: Similar Fault Agent
            t0 = time.perf_counter()
            start_dt = datetime.utcnow()
            similar_agent = SimilarFaultAgent()
            similar_res = await similar_agent.run({
                "complaint": complaint,
                "routing_category": routing_cat,
                "priority_hint": class_res.get("priority_hint"),
                "affected_users_hint": class_res.get("affected_users_hint")
            })
            dur_ms = (time.perf_counter() - t0) * 1000

            await self._record_agent_run(
                ticket_id=ticket_id,
                agent_name="SimilarFaultAgent",
                started_at=start_dt,
                duration_ms=dur_ms,
                method="rules",
                provider=None,
                model=None,
                success=True,
                error=None,
                output=similar_res
            )

            # Step 4: Priority Agent
            t0 = time.perf_counter()
            start_dt = datetime.utcnow()
            priority_agent = PriorityAgent()
            priority_res = await priority_agent.run({
                "complaint": complaint,
                "priority_hint": class_res.get("priority_hint"),
                "affected_users_count": similar_res.get("affected_users_count", 1),
                "routing_category": routing_cat
            })
            dur_ms = (time.perf_counter() - t0) * 1000

            await self._record_agent_run(
                ticket_id=ticket_id,
                agent_name="PriorityAgent",
                started_at=start_dt,
                duration_ms=dur_ms,
                method="rules",
                provider=None,
                model=None,
                success=True,
                error=None,
                output=priority_res
            )

            # Combine classification_notes with similar snippets and priority reason
            notes_dict["similar"] = similar_res.get("similar_snippets", [])
            notes_dict["priority_reason"] = priority_res.get("priority_reason")
            notes_dict["priority_hint"] = class_res.get("priority_hint")

            # Save Analysis Results on Complaint Document
            update_payload = {
                "ai_category": ai_category,
                "ai_confidence": ai_confidence,
                "zone": class_res.get("zone", complaint.get("location")),
                "priority": priority_res.get("priority", "MEDIUM"),
                "affected_users_count": similar_res.get("affected_users_count", 1),
                "affected_equipment_ids": affected_equipment,
                "similar_complaint_ids": similar_res.get("similar_complaint_ids", []),
                "classification_notes": notes_dict,
                "agent_status": AGENT_STATUS_DONE,
                "analyzed_at": datetime.utcnow()
            }

            await db.complaints.update_one(
                {"ticket_id": ticket_id},
                {"$set": update_payload}
            )

            # Step 5: Advance Complaint Status SUBMITTED -> CLASSIFIED (if currently SUBMITTED)
            fresh_complaint = await db.complaints.find_one({"ticket_id": ticket_id})
            if fresh_complaint and fresh_complaint.get("status") == ComplaintStatus.SUBMITTED.value:
                actor_agent = {
                    "type": HistoryActorType.AGENT.value,
                    "id": "classification_agent",
                    "role": "AGENT",
                    "name": "Classification Agent"
                }
                note_msg = (
                    f"Classified as {ai_category} (conf: {ai_confidence:.2f}). "
                    f"Priority {priority_res.get('priority')}. "
                    f"Affected users: {similar_res.get('affected_users_count', 1)}. "
                    f"Similar faults: {len(similar_res.get('similar_complaint_ids', []))}."
                )
                await StatusService.change_status(
                    ticket_id=ticket_id,
                    to_status=ComplaintStatus.CLASSIFIED.value,
                    actor=actor_agent,
                    note=note_msg,
                    details=update_payload
                )

            # Step 6: Assignment Agent (Only if AGENT_ASSIGNMENT_MODE is auto or suggest)
            assignment_mode = getattr(settings, "AGENT_ASSIGNMENT_MODE", "auto").lower()
            assignment_res = {}

            if assignment_mode in ["auto", "suggest"]:
                # Re-verify manual action before running assignment
                latest_complaint = await db.complaints.find_one({"ticket_id": ticket_id})
                if latest_complaint and latest_complaint.get("assigned_technician_id"):
                    logger.info(f"[Orchestrator] Complaint {ticket_id} already assigned manually. Skipping auto assignment.")
                elif latest_complaint and latest_complaint.get("status") in [ComplaintStatus.CLOSED.value, ComplaintStatus.JUNK.value]:
                    logger.info(f"[Orchestrator] Complaint {ticket_id} is in status {latest_complaint.get('status')}. Skipping assignment.")
                else:
                    t0 = time.perf_counter()
                    start_dt = datetime.utcnow()
                    assign_agent = AssignmentAgent()
                    assignment_res = await assign_agent.run({
                        "complaint": latest_complaint,
                        "routing_category": routing_cat,
                        "similar_complaint_ids": similar_res.get("similar_complaint_ids", [])
                    })
                    dur_ms = (time.perf_counter() - t0) * 1000

                    await self._record_agent_run(
                        ticket_id=ticket_id,
                        agent_name="AssignmentAgent",
                        started_at=start_dt,
                        duration_ms=dur_ms,
                        method="rules",
                        provider=None,
                        model=None,
                        success=assignment_res.get("status") in ["ASSIGNED", "SUGGESTED"],
                        error=assignment_res.get("reason") if assignment_res.get("status") not in ["ASSIGNED", "SUGGESTED"] else None,
                        output=assignment_res
                    )

            return {
                "ticket_id": ticket_id,
                "status": "SUCCESS",
                "classification": class_res,
                "priority": priority_res,
                "assignment": assignment_res
            }

        except Exception as pipeline_err:
            logger.error(f"[Orchestrator] Agentic pipeline failed on ticket {ticket_id}: {pipeline_err}", exc_info=True)
            await db.complaints.update_one(
                {"ticket_id": ticket_id},
                {"$set": {"agent_status": AGENT_STATUS_FAILED, "agent_error": str(pipeline_err)}}
            )
            raise pipeline_err

    async def run_assignment_only(self, ticket_id: str) -> Dict[str, Any]:
        """Runs stage ASSIGN only (used by sweep or re-assignment retries).

        Args:
            ticket_id: 12-digit ticket ID.

        Returns:
            Dict assignment result.
        """
        db = get_database()
        complaint = await db.complaints.find_one({"ticket_id": ticket_id})
        if not complaint:
            return {"status": "FAILED", "reason": "Complaint not found"}

        # Skip if already assigned or JUNK or CLOSED
        if complaint.get("assigned_technician_id") or complaint.get("status") in [ComplaintStatus.CLOSED.value, ComplaintStatus.JUNK.value]:
            return {"status": "SKIPPED", "reason": "Complaint already assigned or closed"}

        routing_cat = get_routing_category(complaint)
        similar_ids = complaint.get("similar_complaint_ids", [])

        t0 = time.perf_counter()
        start_dt = datetime.utcnow()
        assign_agent = AssignmentAgent()
        assign_res = await assign_agent.run({
            "complaint": complaint,
            "routing_category": routing_cat,
            "similar_complaint_ids": similar_ids
        })
        dur_ms = (time.perf_counter() - t0) * 1000

        await self._record_agent_run(
            ticket_id=ticket_id,
            agent_name="AssignmentAgent",
            started_at=start_dt,
            duration_ms=dur_ms,
            method="rules",
            provider=None,
            model=None,
            success=assign_res.get("status") in ["ASSIGNED", "SUGGESTED"],
            error=assign_res.get("reason") if assign_res.get("status") not in ["ASSIGNED", "SUGGESTED"] else None,
            output=assign_res
        )

        return assign_res
