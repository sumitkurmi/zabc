# MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
# Pydantic schemas for API request and response payload validation.

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from backend.app.complaint_management.models import (
    StaffRole,
    TechnicianAvailability,
    ComplaintStatus,
    ClosedBy,
    HistoryEventType,
    HistoryActorType,
    AssignmentMethod,
    ActionTokenPurpose,
    UsedStockItem,
    AssetActionItem,
    PreviousAttemptRecord
)


# OTP Registration Schemas
class OTPRequestPayload(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    email: str
    mobile: str
    location: str
    address_room: str = Field(..., min_length=1, max_length=100)
    preferred_from: str
    preferred_to: str
    problem_type: str
    additional_comment: Optional[str] = ""
    chat_id: Optional[str] = None
    filled_by_ai: bool = False
    honeypot: Optional[str] = None


class OTPRequestResponse(BaseModel):
    pending_id: str
    message: str
    expires_in_seconds: int
    resend_cooldown_seconds: int


class OTPVerifyPayload(BaseModel):
    pending_id: str
    otp: str = Field(..., min_length=6, max_length=6)


class OTPVerifyResponse(BaseModel):
    ticket_id: str
    message: str


class OTPResendPayload(BaseModel):
    pending_id: str


# Student Confirmation and Rating Schemas
class StudentConfirmPayload(BaseModel):
    solved: bool
    comment: Optional[str] = None


class StudentRatePayload(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    feedback: Optional[str] = Field(None, max_length=1000)


class StudentTokenInfoResponse(BaseModel):
    ticket_id: str
    purpose: ActionTokenPurpose
    solution: Optional[str] = None
    technician_name: Optional[str] = None
    status: str
    is_valid: bool
    is_expired: bool
    is_used: bool


# Auth Schemas
class StaffLoginPayload(BaseModel):
    username: str
    password: str


class StaffLoginResponse(BaseModel):
    token: str
    role: StaffRole
    full_name: str
    expires_at: datetime


class StaffUserResponse(BaseModel):
    id: str = Field(alias="_id")
    username: str
    full_name: str
    role: StaffRole
    email: str
    mobile: str
    is_active: bool
    notify_on_new_complaint: bool = False
    technician_profile: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        populate_by_name = True


# Staff Management Schemas
class StaffCreatePayload(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=80)
    email: str
    mobile: str
    role: StaffRole  # MANAGER or TECHNICIAN
    zones: Optional[List[str]] = []
    categories: Optional[List[str]] = []
    max_open_complaints: Optional[int] = None


class StaffUpdatePayload(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None
    zones: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    max_open_complaints: Optional[int] = None


class PasswordResetPayload(BaseModel):
    new_password: str = Field(..., min_length=8)


class TechnicianAvailabilityPayload(BaseModel):
    availability: TechnicianAvailability
    confirm: Optional[bool] = False


# Assignment Payload
class AssignComplaintPayload(BaseModel):
    technician_id: str
    reason: Optional[str] = None


# Technician Resolution Payload
class ResolveComplaintPayload(BaseModel):
    diagnosis: str = Field(..., min_length=5)
    solution: str = Field(..., min_length=5)
    items_used: List[Dict[str, Any]] = []
    asset_actions: List[Dict[str, Any]] = []


# Mark Junk Payload
class MarkJunkPayload(BaseModel):
    reason: Optional[str] = None


# Complaint Detail & Summary Response
class HistoryItemResponse(BaseModel):
    event_type: str
    from_status: Optional[str] = None
    to_status: Optional[str] = None
    actor_type: str
    actor_name: str
    note: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    at: datetime


class ComplaintDetailResponse(BaseModel):
    id: str = Field(alias="_id")
    ticket_id: str
    name: str
    email: str
    mobile: str
    location: str
    address_room: str
    preferred_from: str
    preferred_to: str
    problem_type: str
    additional_comment: Optional[str] = ""
    chat_id: Optional[str] = None
    filled_by_ai: bool = False
    status: ComplaintStatus
    assigned_technician_id: Optional[str] = None
    assigned_technician_name: Optional[str] = None
    assigned_at: Optional[datetime] = None
    assignment_count: int = 0
    diagnosis: Optional[str] = None
    solution: Optional[str] = None
    resolved_at: Optional[datetime] = None
    items_used: List[Dict[str, Any]] = []
    asset_actions: List[Dict[str, Any]] = []
    previous_attempts: List[Dict[str, Any]] = []
    reopen_count: int = 0
    confirmation_requested_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    closed_by: Optional[str] = None
    priority: Optional[str] = "MEDIUM"
    ai_category: Optional[str] = None
    ai_confidence: Optional[float] = None
    affected_users_count: Optional[int] = 1
    agent_suggestion: Optional[Dict[str, Any]] = None
    agent_analysis: Optional[Dict[str, Any]] = None
    agent_status: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    history: List[HistoryItemResponse] = []
    rating_info: Optional[Dict[str, Any]] = None

    class Config:
        populate_by_name = True


class ComplaintListResponse(BaseModel):
    complaints: List[ComplaintDetailResponse]
    total: int
    page: int
    pages: int


# Leaderboard Response
class LeaderboardItemResponse(BaseModel):
    technician_id: str
    name: str
    availability: str
    average_rating: Optional[float] = None
    rating_count: int = 0
    resolved_count: int = 0
    open_complaints_count: int = 0
    score: float = 0.0
    rank: int = 0
