# MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
# Enums, Pydantic models, and MongoDB document representations for Complaint Management.

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class StaffRole(str, Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    TECHNICIAN = "TECHNICIAN"


class TechnicianAvailability(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


class ComplaintStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    CLASSIFIED = "CLASSIFIED"
    ASSIGNED = "ASSIGNED"
    DIAGNOSED = "DIAGNOSED"
    ACTION_TAKEN = "ACTION_TAKEN"
    STUDENT_CONFIRMATION = "STUDENT_CONFIRMATION"
    CLOSED = "CLOSED"
    JUNK = "JUNK"


class ClosedBy(str, Enum):
    STUDENT = "STUDENT"
    SYSTEM_AUTO = "SYSTEM_AUTO"


class HistoryEventType(str, Enum):
    STATUS_CHANGE = "STATUS_CHANGE"
    ASSIGNMENT = "ASSIGNMENT"
    JUNK = "JUNK"
    NOTE = "NOTE"


class HistoryActorType(str, Enum):
    USER = "USER"
    SYSTEM = "SYSTEM"
    AGENT = "AGENT"


class AssignmentMethod(str, Enum):
    MANUAL = "MANUAL"
    AUTO = "AUTO"


class ActionTokenPurpose(str, Enum):
    CONFIRM = "CONFIRM"
    RATE = "RATE"


class OutboxStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


# Stock usage item embedded in complaint
class UsedStockItem(BaseModel):
    stock_item_id: str
    name: str
    quantity: int
    location_id: Optional[str] = None
    used_by: str
    used_at: datetime = Field(default_factory=datetime.utcnow)


# Asset action embedded in complaint
class AssetActionItem(BaseModel):
    asset_id: str
    new_status: str  # REPLACED | FAULTY
    reason: str


# Reopened previous attempt record
class PreviousAttemptRecord(BaseModel):
    diagnosis: str
    solution: str
    items_used: List[UsedStockItem] = []
    asset_actions: List[AssetActionItem] = []
    resolved_at: datetime
    reopened_at: datetime = Field(default_factory=datetime.utcnow)
