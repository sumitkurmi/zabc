"""Public complaints API router.

Handles complaint submissions and ref_no reference number generation.
Specification Section 5.2, Section 7, Section 10.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, status
from backend.app.db import get_database
from backend.app.schemas import ComplaintCreateRequest, ComplaintCreateResponse

router = APIRouter(prefix="/complaints", tags=["complaints"])


async def generate_reference_number() -> str:
    """Generates unique reference number format like NET-2026-000123 using atomic counter.

    Returns:
        Formatted reference string.
    """
    db = get_database()
    current_year = datetime.utcnow().year
    counter_id = f"complaint_ref_{current_year}"

    result = await db.counters.find_one_and_update(
        {"_id": counter_id},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    seq = result.get("seq", 1)
    return f"NET-{current_year}-{seq:06d}"


@router.post("", response_model=ComplaintCreateResponse, status_code=status.HTTP_201_CREATED)
async def submit_complaint(data: ComplaintCreateRequest, request: Request):
    """Submits a student network complaint report.

    Validates honeypot, generates ref_no, and saves complaint to MongoDB.
    """
    # Anti-spam honeypot check
    if data.honeypot:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Spam submission detected"
        )

    db = get_database()
    ref_no = await generate_reference_number()

    complaint_doc = {
        "ref_no": ref_no,
        "name": data.name,
        "email": data.email,
        "mobile": data.mobile,
        "location": data.location,
        "address_room": data.address_room,
        "preferred_from": data.preferred_from,
        "preferred_to": data.preferred_to,
        "problem_type": data.problem_type.value,
        "additional_comment": data.additional_comment,
        "chat_id": data.chat_id,
        "filled_by_ai": data.filled_by_ai,
        "status": "NEW",
        "created_at": datetime.utcnow()
    }

    result = await db.complaints.insert_one(complaint_doc)

    return ComplaintCreateResponse(
        id=str(result.inserted_id),
        ref_no=ref_no,
        message="Complaint submitted successfully"
    )
