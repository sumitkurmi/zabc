# MODULE: Agentic Classification and Assignment (Module 2) - this file belongs to the code for this module.
# Unit tests for Module 2 agentic classification, equipment matcher, similar fault cluster analysis, priority computation, and job queue.

import pytest
from backend.app.agentic.priority_agent import compute_priority
from backend.app.agentic.schemas import ClassificationOutput, ScoreBreakdown, CandidateEvaluation
from backend.app.agentic.classification_agent import get_routing_category


def test_priority_matrix_computation():
    """Tests deterministic compute_priority formula calculation."""
    # Base LOW hint, 1 user -> LOW (1)
    res1 = compute_priority(priority_hint="LOW", affected_users_count=1, location="Hostel 1")
    assert res1["priority"] == "LOW"

    # Base MEDIUM hint, 6 users (high impact >= 5) -> HIGH (3)
    res2 = compute_priority(priority_hint="MEDIUM", affected_users_count=6, location="Hostel 1")
    assert res2["priority"] == "HIGH"

    # Base LOW hint, 25 users (critical impact >= 20) -> CRITICAL (4)
    res3 = compute_priority(priority_hint="LOW", affected_users_count=25, location="Hostel 1")
    assert res3["priority"] == "CRITICAL"

    # Base HIGH hint, 1 user, recurring fault -> CRITICAL (4)
    res4 = compute_priority(priority_hint="HIGH", affected_users_count=1, location="Hostel 1", recurring=True)
    assert res4["priority"] == "CRITICAL"


def test_routing_category_confidence_threshold():
    """Tests get_routing_category confidence threshold behavior."""
    # High confidence (0.85 >= 0.75) -> returns ai_category
    complaint_high = {
        "problem_type": "WIFI_PROBLEM",
        "ai_category": "LAN_PORT_BROKEN",
        "ai_confidence": 0.85
    }
    assert get_routing_category(complaint_high) == "LAN_PORT_BROKEN"

    # Low confidence (0.50 < 0.75) -> falls back to student's problem_type
    complaint_low = {
        "problem_type": "WIFI_PROBLEM",
        "ai_category": "LAN_PORT_BROKEN",
        "ai_confidence": 0.50
    }
    assert get_routing_category(complaint_low) == "WIFI_PROBLEM"


def test_classification_schema_validation():
    """Tests Pydantic validation and clamping of classification outputs."""
    out = ClassificationOutput(
        problem_type="WIFI_PROBLEM",
        confidence=0.9,
        priority_hint="high",
        summary="Wi-Fi AP disconnections in block A"
    )
    assert out.priority_hint == "HIGH"
    assert out.confidence == 0.9
