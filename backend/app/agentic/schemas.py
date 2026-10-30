# MODULE: Agentic Classification and Assignment (Module 2) - this file belongs to the code for this module.
# Pydantic schemas for agentic pipeline execution, input validation, structured LLM outputs, and job tracking.

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from backend.app.models import ProblemType


class ClassificationOutput(BaseModel):
    """Structured response from Classification Agent."""
    problem_type: ProblemType
    confidence: float = Field(ge=0.0, le=1.0)
    priority_hint: str = Field(default="MEDIUM")
    affected_users_hint: Optional[int] = Field(default=None)
    equipment_mentions: List[str] = Field(default_factory=list)
    summary: str = Field(max_length=160)

    @field_validator("priority_hint")
    @classmethod
    def validate_priority_hint(cls, v: str) -> str:
        upper = v.upper() if v else "MEDIUM"
        if upper not in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
            return "MEDIUM"
        return upper


class SimilarSnippet(BaseModel):
    """Snippet summary of a previous or related complaint fault."""
    ticket_id: str
    relation: str  # OPEN_CLUSTER | PREVIOUS_FAULT
    solution_snippet: Optional[str] = None


class ClassificationNotes(BaseModel):
    """Agent classification notes stored on complaint document."""
    method: str  # llm | rules
    provider: Optional[str] = None
    model: Optional[str] = None
    summary: str
    priority_reason: Optional[str] = None
    equipment_mentions: List[str] = Field(default_factory=list)
    agent_version: str = "v2.0-agentic"
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    similar: List[SimilarSnippet] = Field(default_factory=list)


class ScoreBreakdown(BaseModel):
    """Technician evaluation score components (0 to 100 max total)."""
    zone_match: float
    workload: float
    experience: float
    cluster: float
    performance: float
    total: float


class CandidateEvaluation(BaseModel):
    """Technician candidate evaluated by Assignment Agent."""
    technician_id: str
    full_name: str
    staff_id: str
    score: float
    breakdown: ScoreBreakdown
    reason: str


class AgentSuggestion(BaseModel):
    """Suggested technician assignment generated in 'suggest' mode."""
    technician_id: str
    technician_name: str
    score: float
    reason: str
    breakdown: ScoreBreakdown
    at: datetime = Field(default_factory=datetime.utcnow)


class AgentJobModel(BaseModel):
    """MongoDB document schema for background agent jobs."""
    id: Optional[str] = Field(default=None, alias="_id")
    ticket_id: str
    stage: str  # FULL | ASSIGN | RAG_INDEX
    status: str  # PENDING | RUNNING | DONE | FAILED
    attempts: int = 0
    next_run_at: datetime = Field(default_factory=datetime.utcnow)
    locked_until: Optional[datetime] = None
    last_error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AgentRunModel(BaseModel):
    """MongoDB document schema for agent execution audit logs."""
    id: Optional[str] = Field(default=None, alias="_id")
    ticket_id: str
    agent: str  # ClassificationAgent | SimilarFaultAgent | PriorityAgent | AssignmentAgent
    started_at: datetime
    duration_ms: float
    method: str  # llm | rules
    provider: Optional[str] = None
    model: Optional[str] = None
    success: bool
    error: Optional[str] = None
    output: Dict[str, Any] = Field(default_factory=dict)
