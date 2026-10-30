# MODULE: Agentic Classification and Assignment (Module 2) - this file belongs to the code for this module.
# Classification agent categorizing complaint faults, extracting priority hints, equipment mentions, and summary.

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import ValidationError

from backend.app.config import settings
from backend.app.services.llm_router import llm_router
from backend.app.services.sanitizer import sanitize_text
from backend.app.agentic.schemas import ClassificationOutput, ClassificationNotes
from backend.app.agentic.constants import (
    RULE_FALLBACK_CONFIDENCE,
    RULE_FALLBACK_PRIORITY_HINT,
    HIGH_IMPACT_KEYWORDS,
    RULE_HIGH_IMPACT_PRIORITY_HINT,
    RULE_HIGH_IMPACT_AFFECTED_USERS
)

logger = logging.getLogger("agentic.classification")


def get_routing_category(complaint: Dict[str, Any]) -> str:
    """Helper returning ai_category if ai_confidence >= AGENT_CATEGORY_MIN_CONFIDENCE, otherwise problem_type.

    Args:
        complaint: Complaint document dictionary.

    Returns:
        Routing problem category string.
    """
    ai_cat = complaint.get("ai_category")
    ai_conf = complaint.get("ai_confidence", 0.0)
    student_cat = complaint.get("problem_type")

    min_conf = getattr(settings, "AGENT_CATEGORY_MIN_CONFIDENCE", 0.75)
    if ai_cat and ai_conf is not None and float(ai_conf) >= float(min_conf):
        return ai_cat
    return student_cat or "WIFI_PROBLEM"


class ClassificationAgent:
    """Agent that classifies student complaints using LLM router with keyword rules fallback."""

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Executes complaint classification.

        Args:
            context: Context dict containing 'complaint' and optional 'chat_summary'.

        Returns:
            Dict with ai_category, ai_confidence, zone, classification_notes.
        """
        complaint = context.get("complaint", {})
        student_problem_type = complaint.get("problem_type", "WIFI_PROBLEM")
        location_name = complaint.get("location", "Unknown Location")

        # PRIVACY RULE: Never send student name, email, mobile, or room number to LLM.
        raw_comment = complaint.get("additional_comment", "")
        raw_summary = context.get("chat_summary") or complaint.get("chat_summary", "")

        comment_sanitized = sanitize_text(raw_comment) if raw_comment else ""
        summary_sanitized = sanitize_text(raw_summary) if raw_summary else ""

        use_llm = getattr(settings, "AGENT_USE_LLM", True)
        result_data: Optional[Dict[str, Any]] = None
        method = "llm"
        provider_name = "mock"
        model_name = "mock-v1"

        if use_llm:
            try:
                # LLM Call 1
                raw_res = await llm_router.classify_complaint(
                    student_problem_type=student_problem_type,
                    location_name=location_name,
                    comment_text=comment_sanitized,
                    chat_summary=summary_sanitized
                )
                provider_name = raw_res.get("provider", "unknown")
                model_name = raw_res.get("model", "unknown")

                try:
                    parsed = ClassificationOutput(**raw_res)
                    result_data = parsed.model_dump()
                except ValidationError:
                    # Retry once stripping code fences or whitespace
                    logger.warning("[ClassificationAgent] First LLM response validation failed, retrying...")
                    raw_res_retry = await llm_router.classify_complaint(
                        student_problem_type=student_problem_type,
                        location_name=location_name,
                        comment_text=comment_sanitized,
                        chat_summary=summary_sanitized
                    )
                    parsed_retry = ClassificationOutput(**raw_res_retry)
                    result_data = parsed_retry.model_dump()

            except Exception as err:
                logger.warning(f"[ClassificationAgent] LLM classification failed: {err}. Falling back to rules.")
                result_data = None

        if not result_data:
            # Rules Fallback
            method = "rules"
            provider_name = None
            model_name = None

            combined = f"{comment_sanitized} {summary_sanitized}".lower()
            priority_hint = RULE_FALLBACK_PRIORITY_HINT
            affected_hint = None

            if any(kw in combined for kw in HIGH_IMPACT_KEYWORDS):
                priority_hint = RULE_HIGH_IMPACT_PRIORITY_HINT
                affected_hint = RULE_HIGH_IMPACT_AFFECTED_USERS

            eq_mentions = []
            if "switch" in combined:
                eq_mentions.append("Switch")
            if "ap" in combined or "access point" in combined:
                eq_mentions.append("Access Point")
            if "port" in combined or "socket" in combined:
                eq_mentions.append("Wall Socket")

            clean_summary = comment_sanitized[:157] + "..." if len(comment_sanitized) > 160 else comment_sanitized
            if not clean_summary:
                clean_summary = f"Network issue reported at {location_name}"

            result_data = {
                "problem_type": student_problem_type,
                "confidence": RULE_FALLBACK_CONFIDENCE,
                "priority_hint": priority_hint,
                "affected_users_hint": affected_hint,
                "equipment_mentions": eq_mentions,
                "summary": clean_summary
            }

        ai_category = result_data["problem_type"]
        if hasattr(ai_category, "value"):
            ai_category = ai_category.value

        ai_confidence = float(result_data["confidence"])
        priority_hint = result_data.get("priority_hint", "MEDIUM")
        affected_users_hint = result_data.get("affected_users_hint")
        equipment_mentions = result_data.get("equipment_mentions", [])
        summary = result_data.get("summary", "")

        notes = ClassificationNotes(
            method=method,
            provider=provider_name,
            model=model_name,
            summary=summary,
            priority_reason=f"Classification priority hint: {priority_hint}",
            equipment_mentions=equipment_mentions,
            agent_version="v2.0-agentic",
            analyzed_at=datetime.utcnow(),
            similar=[]
        )

        return {
            "ai_category": ai_category,
            "ai_confidence": ai_confidence,
            "zone": location_name,
            "priority_hint": priority_hint,
            "affected_users_hint": affected_users_hint,
            "classification_notes": notes.model_dump()
        }
