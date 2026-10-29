"""Request and response Pydantic schemas for API validation and documentation.

This module defines data contracts for HTTP endpoints across student-facing
and admin-facing APIs.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
from backend.app.models import ProblemType, ComplaintStatus, ChatStatus, DocumentSourceType, DocumentStatus


# --- Configuration Schemas ---

class LocationOption(BaseModel):
    """Location item for select dropdowns."""
    id: str
    name: str


class ProblemTypeOption(BaseModel):
    """Problem type item with enum value and display label."""
    value: ProblemType
    label: str


class ConfigResponse(BaseModel):
    """Response schema for public /api/config endpoint."""
    college_name: str
    locations: List[LocationOption]
    problem_types: List[ProblemTypeOption]
    max_chat_messages: int
    max_upload_mb: int
    allowed_email_domain: str = "mnnit.ac.in"


# --- Student Complaint Schemas ---

class ComplaintCreateRequest(BaseModel):
    """Request payload for submitting a new student complaint."""
    name: str = Field(..., min_length=2, max_length=80)
    email: str
    mobile: str = Field(..., pattern=r"^(\+91)?\d{10}$")
    location: str
    address_room: str = Field(..., min_length=1, max_length=100)
    preferred_from: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    preferred_to: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    problem_type: ProblemType
    additional_comment: Optional[str] = Field(None, max_length=1000)
    chat_id: Optional[str] = None
    filled_by_ai: bool = False
    honeypot: Optional[str] = None  # Hidden anti-spam field, must remain empty

    @field_validator("preferred_to")
    def validate_time_range(cls, v, values):
        """Ensures preferred_to is logically later than preferred_from."""
        preferred_from = values.data.get("preferred_from")
        if preferred_from and v <= preferred_from:
            raise ValueError("Preferred end time must be later than start time")
        return v


class ComplaintCreateResponse(BaseModel):
    """Response payload returned upon successful complaint creation."""
    id: str
    ref_no: str
    message: str = "Complaint registered successfully"


# --- Student Chat Schemas ---

class ChatCreateResponse(BaseModel):
    """Response payload for starting a new chat session."""
    chat_id: str


class ChatMessageRequest(BaseModel):
    """Request payload for sending a user message to the chatbot."""
    content: str = Field(..., min_length=1, max_length=500)


class ChatMessageResponse(BaseModel):
    """Response payload returned by the AI assistant."""
    reply: str
    detected_category: Optional[ProblemType]
    on_topic: bool
    messages_used: int
    messages_remaining: int


class ChatTurnSchema(BaseModel):
    """Single turn representation for full transcript response."""
    role: str
    content: str
    created_at: datetime
    is_off_topic: bool = False


class ChatTranscriptResponse(BaseModel):
    """Full chat transcript payload for page state restoration."""
    chat_id: str
    message_count: int
    messages_remaining: int
    detected_category: Optional[ProblemType]
    messages: List[ChatTurnSchema]


class SummarizeResponse(BaseModel):
    """AI pre-fill response payload for 'Log request using AI' button."""
    problem_type: ProblemType
    additional_comment: str


# --- Admin Auth Schemas ---

class AdminLoginRequest(BaseModel):
    """Payload for admin login."""
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    """Token payload returned on successful admin login."""
    token: str
    expires_at: str


# --- Admin Dashboard & Chat Management Schemas ---

class AdminStatsResponse(BaseModel):
    """Dashboard summary metrics for admin header cards."""
    unassigned_chats_count: int
    reference_documents_count: int
    complaints_today_count: int
    total_chats_count: int


class ChatSummaryResponse(BaseModel):
    """Compact chat representation for admin list table."""
    id: str
    preview: str
    message_count: int
    detected_category: Optional[ProblemType]
    created_at: datetime
    status: ChatStatus
    reference_category_slug: Optional[str] = None


class ChatListResponse(BaseModel):
    """Paginated list of chat transcripts."""
    chats: List[ChatSummaryResponse]
    total: int
    page: int
    pages: int


class MoveChatRequest(BaseModel):
    """Payload for moving a chat to a reference category."""
    category_slug: str


class BulkMoveChatRequest(BaseModel):
    """Payload for bulk moving chats to a reference category."""
    chat_ids: List[str]
    category_slug: str


# --- Admin Reference & Document Schemas ---

class CategorySummaryResponse(BaseModel):
    """Category detail with document and chat counts."""
    slug: str
    name: str
    description: str
    chats_count: int
    documents_count: int


class DocumentResponse(BaseModel):
    """Document metadata representation for admin lists."""
    id: str
    category_slug: str
    source_type: DocumentSourceType
    chat_id: Optional[str]
    original_filename: str
    mime_type: str
    size_bytes: int
    status: DocumentStatus
    error_message: Optional[str]
    chunk_count: int
    uploaded_at: datetime


class CategoryDetailResponse(BaseModel):
    """Full category view containing details, assigned chats, and uploaded documents."""
    category: CategorySummaryResponse
    chats: List[ChatSummaryResponse]
    documents: List[DocumentResponse]
