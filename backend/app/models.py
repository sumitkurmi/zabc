"""Pydantic database document models and domain enums.

This module defines the database models representing MongoDB collections,
enforcing domain types, validation rules, and structural consistency.

Collections modeled:
- Complaints (`complaints`)
- Chats (`chats`)
- Reference Categories (`reference_categories`)
- Documents (`documents`)
- Counters (`counters`)
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr


class ProblemType(str, Enum):
    """Fixed list of 5 network problem types recognized by the system."""
    LAN_PROBLEM = "LAN_PROBLEM"
    IP_ADDRESS_ISSUE = "IP_ADDRESS_ISSUE"
    PROXY_ISSUE = "PROXY_ISSUE"
    LAN_PORT_BROKEN = "LAN_PORT_BROKEN"
    WIFI_PROBLEM = "WIFI_PROBLEM"


class ComplaintStatus(str, Enum):
    """Workflow status for submitted student complaints."""
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"


class ChatStatus(str, Enum):
    """Status indicating whether a chat transcript is unassigned or curated into reference."""
    UNASSIGNED = "UNASSIGNED"
    REFERENCE = "REFERENCE"


class DocumentSourceType(str, Enum):
    """Source of a curated knowledge document."""
    UPLOAD = "UPLOAD"
    CHAT = "CHAT"


class DocumentStatus(str, Enum):
    """Processing and vector indexing status for uploaded or converted documents."""
    PROCESSING = "PROCESSING"
    INDEXED = "INDEXED"
    FAILED = "FAILED"


class ChatMessage(BaseModel):
    """Individual turn in a student chat conversation."""
    role: str  # "user" or "assistant"
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_off_topic: bool = False
    source_doc_ids: List[str] = Field(default_factory=list)


class ComplaintModel(BaseModel):
    """MongoDB document model for student network complaints."""
    id: Optional[str] = Field(default=None, alias="_id")
    ref_no: str  # e.g., "NET-2026-000123"
    name: str
    email: str
    mobile: str
    location: str
    address_room: str
    preferred_from: str  # "HH:MM" format
    preferred_to: str    # "HH:MM" format
    problem_type: ProblemType
    additional_comment: Optional[str] = None
    chat_id: Optional[str] = None
    filled_by_ai: bool = False
    status: ComplaintStatus = ComplaintStatus.NEW
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True


class ChatModel(BaseModel):
    """MongoDB document model for student chat sessions."""
    id: Optional[str] = Field(default=None, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    message_count: int = 0  # User messages count only
    detected_category: Optional[ProblemType] = None
    status: ChatStatus = ChatStatus.UNASSIGNED
    reference_category_slug: Optional[str] = None
    moved_at: Optional[datetime] = None
    messages: List[ChatMessage] = Field(default_factory=list)

    class Config:
        populate_by_name = True


class ReferenceCategoryModel(BaseModel):
    """MongoDB document model for admin curated reference categories."""
    id: Optional[str] = Field(default=None, alias="_id")
    slug: str
    name: str
    description: str

    class Config:
        populate_by_name = True


class DocumentModel(BaseModel):
    """MongoDB document model for uploaded or chat-derived knowledge base documents."""
    id: Optional[str] = Field(default=None, alias="_id")
    category_slug: str
    source_type: DocumentSourceType
    chat_id: Optional[str] = None
    original_filename: str
    mime_type: str
    storage_path: str
    size_bytes: int
    status: DocumentStatus = DocumentStatus.PROCESSING
    error_message: Optional[str] = None
    chunk_count: int = 0
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True


class CounterModel(BaseModel):
    """Sequence counter for generating complaint reference numbers atomically."""
    id: str  # e.g., "complaint_ref_2026"
    seq: int = 0

    class Config:
        populate_by_name = True
