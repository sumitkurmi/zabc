# MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
# Classification service hook reserved for Agentic AI Classification in Module 2.

from typing import Dict, Any


async def classify(complaint: Dict[str, Any]) -> Dict[str, Any]:
    """Classifies complaint problem category, priority, and zone.

    Module 2 Hook: In Part 2, this function preserves the student's selected problem_type.
    Module 2 will extend this function to run agentic LLM classification and auto-tagging.

    Args:
        complaint: Raw complaint document dictionary.

    Returns:
        Classification result metadata dictionary.
    """
    problem_type = complaint.get("problem_type")
    return {
        "ai_category": problem_type,
        "priority": "MEDIUM",
        "zone": complaint.get("location"),
        "classification_notes": {
            "confidence": 1.0,
            "reasoning": "Student selected problem type retained in Part 2",
            "agent_version": "v1.0-manual"
        }
    }
