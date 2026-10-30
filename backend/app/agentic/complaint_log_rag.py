# MODULE: Agentic Classification and Assignment (Module 2) - this file belongs to the code for this module.
# Anonymized complaint log generator and RAG knowledge base indexing pipeline.

import os
import re
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from backend.app.db import get_database
from backend.app.config import settings
from backend.app.models import DocumentModel, DocumentSourceType, DocumentStatus
from backend.app.services.sanitizer import sanitize_text
from backend.app.services.rag_service import process_and_index_document

logger = logging.getLogger("agentic.complaint_log_rag")


def anonymize_text(text: str, student_name: Optional[str] = None, room_number: Optional[str] = None) -> str:
    """Strips personal identifiers, student name parts (>=3 chars), and room numbers from text.

    Args:
        text: Free text string to sanitize.
        student_name: Student full name to redact.
        room_number: Room number string to redact.

    Returns:
        Redacted text string.
    """
    if not text:
        return ""

    sanitized = sanitize_text(text)

    # Redact student name parts (3 or more letters)
    if student_name:
        name_parts = [p.strip() for p in re.split(r"\s+", student_name) if len(p.strip()) >= 3]
        for part in name_parts:
            pattern = re.compile(re.escape(part), re.IGNORECASE)
            sanitized = pattern.sub("[removed]", sanitized)

    # Redact room number string
    if room_number and len(room_number.strip()) > 0:
        room_str = room_number.strip()
        pattern = re.compile(re.escape(room_str), re.IGNORECASE)
        sanitized = pattern.sub("[removed]", sanitized)

    return sanitized


async def ensure_complaint_logs_category() -> None:
    """Ensures reference_categories collection contains the 'complaint-logs' slug."""
    db = get_database()
    cat = await db.reference_categories.find_one({"slug": "complaint-logs"})
    if not cat:
        await db.reference_categories.insert_one({
            "slug": "complaint-logs",
            "name": "Previous complaint and fault logs",
            "description": "Historical resolved complaint records and fault diagnostic solutions"
        })


async def build_and_index_complaint_log(ticket_id: str) -> Optional[str]:
    """Generates an anonymized .txt document for a closed complaint and indexes it into ChromaDB RAG.

    Args:
        ticket_id: 12-digit ticket ID of closed complaint.

    Returns:
        Document ID string if successfully indexed, else None.
    """
    db = get_database()

    # 1. Fetch complaint record
    complaint = await db.complaints.find_one({"ticket_id": ticket_id})
    if not complaint:
        logger.warning(f"[ComplaintLogRAG] Complaint '{ticket_id}' not found.")
        return None

    # Idempotency check: Skip if already indexed
    if complaint.get("rag_indexed_at"):
        logger.info(f"[ComplaintLogRAG] Complaint '{ticket_id}' already indexed at {complaint.get('rag_indexed_at')}.")
        return None

    # Check eligibility rules
    auto_index_enabled = getattr(settings, "RAG_AUTO_INDEX_CLOSED", True)
    if not auto_index_enabled:
        logger.info("[ComplaintLogRAG] RAG_AUTO_INDEX_CLOSED is false. Skipping.")
        return None

    diagnosis = complaint.get("diagnosis")
    solution = complaint.get("solution")
    if not diagnosis or not solution:
        logger.info(f"[ComplaintLogRAG] Complaint '{ticket_id}' lacks diagnosis/solution. Skipping RAG indexing.")
        return None

    closed_by = complaint.get("closed_by", "STUDENT")
    include_auto_closed = getattr(settings, "RAG_INCLUDE_AUTO_CLOSED", False)

    if closed_by == "SYSTEM_AUTO" and not include_auto_closed:
        logger.info(f"[ComplaintLogRAG] Complaint '{ticket_id}' was auto-closed. Skipping RAG indexing.")
        return None

    # 2. Extract anonymized metadata fields
    student_name = complaint.get("name")
    room_number = complaint.get("address_room")

    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    prob_type = complaint.get("ai_category") or complaint.get("problem_type") or "WIFI_PROBLEM"
    location = complaint.get("zone") or complaint.get("location") or "Campus Location"
    priority = complaint.get("priority", "MEDIUM")
    affected_users = complaint.get("affected_users_count", 1)

    # Resolution hours calculation
    created_at = complaint.get("created_at") or datetime.utcnow()
    updated_at = complaint.get("updated_at") or datetime.utcnow()
    res_hours = round((updated_at - created_at).total_seconds() / 3600.0, 1)

    # Affected equipment make/model details
    equipment_details = []
    eq_ids = complaint.get("affected_equipment_ids") or []
    if eq_ids:
        for eq_id in eq_ids:
            asset = await db.na_assets.find_one({"_id": eq_id})
            if asset:
                eq_details = f"{asset.get('category')} ({asset.get('make')} {asset.get('model')})"
                equipment_details.append(eq_details)

    eq_str = ", ".join(equipment_details) if equipment_details else "Standard Network Hardware"

    # Items used from stock
    items_used = complaint.get("items_used") or []
    items_str = ", ".join([f"{item.get('name')} (qty: {item.get('quantity')})" for item in items_used]) if items_used else "None"

    # Problem description
    comment_anon = anonymize_text(complaint.get("additional_comment", ""), student_name, room_number)
    notes = complaint.get("classification_notes") or {}
    summary_anon = anonymize_text(notes.get("summary", ""), student_name, room_number)

    diag_anon = anonymize_text(diagnosis, student_name, room_number)
    sol_anon = anonymize_text(solution, student_name, room_number)

    # 3. Format Anonymized Log Document
    log_content = f"""ANONYMIZED COMPLAINT AND FAULT RESOLUTION LOG
==================================================
Date: {date_str}
Problem Category: {prob_type}
Location Zone: {location}
Priority Level: {priority}
Affected Users Count: {affected_users}
Affected Network Equipment: {eq_str}
Resolution Time: {res_hours} hours

PROBLEM SUMMARY:
{summary_anon if summary_anon else "Fault reported by student."}

DETAILED COMMENT:
{comment_anon if comment_anon else "No additional commentary."}

DIAGNOSIS:
{diag_anon}

SOLUTION APPLIED:
{sol_anon}

SPARES AND ITEMS USED:
{items_str}
==================================================
"""

    # Ensure upload directory and reference category exist
    upload_dir = getattr(settings, "UPLOAD_DIR", "./data/uploads")
    os.makedirs(upload_dir, exist_ok=True)
    await ensure_complaint_logs_category()

    # Save to .txt file on disk
    filename = f"complaint_log_{ticket_id}_{date_str}.txt"
    filepath = os.path.join(upload_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(log_content)

    file_size = os.path.getsize(filepath)
    display_name = f"Complaint log - {date_str} - {prob_type} - {location}"

    # 4. Check for existing document by complaint_ticket_id (sparse unique index)
    existing_doc = await db.documents.find_one({"complaint_ticket_id": ticket_id})
    if existing_doc:
        doc_id = str(existing_doc["_id"])
    else:
        doc_record = {
            "category_slug": "complaint-logs",
            "source_type": DocumentSourceType.COMPLAINT.value,
            "complaint_ticket_id": ticket_id,
            "original_filename": display_name,
            "mime_type": "text/plain",
            "storage_path": filepath,
            "size_bytes": file_size,
            "status": DocumentStatus.PROCESSING.value,
            "error_message": None,
            "chunk_count": 0,
            "uploaded_at": datetime.utcnow()
        }
        res = await db.documents.insert_one(doc_record)
        doc_id = str(res.inserted_id)

    # 5. Process document through RAG pipeline (extract, chunk, embed into ChromaDB)
    await process_and_index_document(doc_id)

    # Mark complaints.rag_indexed_at timestamp
    now_dt = datetime.utcnow()
    await db.complaints.update_one(
        {"ticket_id": ticket_id},
        {"$set": {"rag_indexed_at": now_dt}}
    )

    logger.info(f"[ComplaintLogRAG] Successfully indexed complaint log for ticket '{ticket_id}' into RAG.")
    return doc_id
