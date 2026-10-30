# MODULE: Agentic Classification and Assignment (Module 2) - this file belongs to the code for this module.
# Named constants, default scoring weights, and rule keywords for Module 2 agentic workflows.

# Scoring weights (Total = 100)
WEIGHT_ZONE_MATCH = 35.0
WEIGHT_WORKLOAD = 25.0
WEIGHT_EXPERIENCE = 15.0
WEIGHT_CLUSTER = 15.0
WEIGHT_PERFORMANCE = 10.0

# Keywords indicating high affected user impact in classification fallback rules
HIGH_IMPACT_KEYWORDS = [
    "whole floor",
    "all rooms",
    "everyone",
    "entire hostel",
    "no one",
    "whole hostel",
    "entire floor",
    "all students",
    "block wide",
    "wing wide"
]

# Classification Fallback Rule Constants
RULE_FALLBACK_CONFIDENCE = 0.5
RULE_FALLBACK_PRIORITY_HINT = "MEDIUM"
RULE_HIGH_IMPACT_PRIORITY_HINT = "HIGH"
RULE_HIGH_IMPACT_AFFECTED_USERS = 10

# Priority Numeric Scale Map
PRIORITY_VALUE_MAP = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "CRITICAL": 4
}

VALUE_TO_PRIORITY_MAP = {
    1: "LOW",
    2: "MEDIUM",
    3: "HIGH",
    4: "CRITICAL"
}

# Job Queue Stage Constants
STAGE_FULL = "FULL"
STAGE_ASSIGN = "ASSIGN"
STAGE_RAG_INDEX = "RAG_INDEX"

# Job Status Constants
JOB_PENDING = "PENDING"
JOB_RUNNING = "RUNNING"
JOB_DONE = "DONE"
JOB_FAILED = "FAILED"

# Agent Status Constants for Complaint
AGENT_STATUS_PENDING = "PENDING"
AGENT_STATUS_RUNNING = "RUNNING"
AGENT_STATUS_DONE = "DONE"
AGENT_STATUS_FAILED = "FAILED"
AGENT_STATUS_SKIPPED = "SKIPPED"
