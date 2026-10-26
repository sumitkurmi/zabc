"""Admin chat management router.

Specification Section 9.2, 9.3, 10.
Allows admin to review chats, move unassigned chats to reference categories (triggering RAG indexing),
unassign reference chats, and perform bulk moves.
Excludes empty chats (message_count < 1) from admin listings and counts.
"""

from datetime import datetime
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from backend.app.db import get_database
from backend.app.deps import require_admin
from backend.app.models import ChatStatus, DocumentSourceType, DocumentStatus
from backend.app.schemas import (
    AdminStatsResponse,
    ChatListResponse,
    ChatSummaryResponse,
    ChatTranscriptResponse,
    ChatTurnSchema,
    MoveChatRequest,
    BulkMoveChatRequest
)
from backend.app.services.rag_service import process_and_index_document, delete_document_and_vectors

router = APIRouter(prefix="/admin", tags=["admin-chats"])


@router.get("/stats", response_model=AdminStatsResponse)
async def get_admin_stats(admin_username: str = Depends(require_admin)):
    """Returns aggregated stats for dashboard header cards (excluding empty chats with message_count < 1)."""
    db = get_database()
    # Safety net: Exclude empty chats with message_count < 1
    unassigned_count = await db.chats.count_documents({
        "status": "UNASSIGNED",
        "message_count": {"$gte": 1}
    })
    documents_count = await db.documents.count_documents({})
    total_chats_count = await db.chats.count_documents({"message_count": {"$gte": 1}})

    start_of_today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    complaints_today_count = await db.complaints.count_documents({"created_at": {"$gte": start_of_today}})

    return AdminStatsResponse(
        unassigned_chats_count=unassigned_count,
        reference_documents_count=documents_count,
        complaints_today_count=complaints_today_count,
        total_chats_count=total_chats_count
    )


@router.get("/chats", response_model=ChatListResponse)
async def list_unassigned_chats(
    status_filter: str = Query("UNASSIGNED", alias="status"),
    q: str = Query(None),
    category: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    admin_username: str = Depends(require_admin)
):
    """Lists student chats with optional filtering and pagination (excluding empty chats)."""
    db = get_database()
    # Safety net: Only include chats with at least 1 user message
    query = {"message_count": {"$gte": 1}}
    if status_filter:
        query["status"] = status_filter
    if category:
        query["detected_category"] = category
    if q:
        query["$text"] = {"$search": q}

    skip = (page - 1) * limit
    total = await db.chats.count_documents(query)
    cursor = db.chats.find(query).sort("created_at", -1).skip(skip).limit(limit)

    chats_list = []
    async for chat in cursor:
        msgs = chat.get("messages", [])
        preview = ""
        for m in msgs:
            if m.get("role") == "user":
                preview = m.get("content", "")[:100]
                break

        chats_list.append(
            ChatSummaryResponse(
                id=str(chat["_id"]),
                preview=preview or "Empty conversation",
                message_count=chat.get("message_count", 0),
                detected_category=chat.get("detected_category"),
                created_at=chat.get("created_at", datetime.utcnow()),
                status=chat.get("status", ChatStatus.UNASSIGNED),
                reference_category_slug=chat.get("reference_category_slug")
            )
        )

    pages = (total + limit - 1) // limit if total > 0 else 1

    return ChatListResponse(
        chats=chats_list,
        total=total,
        page=page,
        pages=pages
    )


@router.get("/chats/{chat_id}", response_model=ChatTranscriptResponse)
async def get_admin_chat_detail(
    chat_id: str,
    admin_username: str = Depends(require_admin)
):
    """Returns full transcript for admin view."""
    db = get_database()
    try:
        obj_id = ObjectId(chat_id)
        chat = await db.chats.find_one({"_id": obj_id}) or await db.chats.find_one({"_id": chat_id})
    except Exception:
        chat = await db.chats.find_one({"_id": chat_id})

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    messages = [
        ChatTurnSchema(
            role=m["role"],
            content=m["content"],
            created_at=m.get("created_at", datetime.utcnow()),
            is_off_topic=m.get("is_off_topic", False)
        )
        for m in chat.get("messages", [])
    ]

    return ChatTranscriptResponse(
        chat_id=str(chat["_id"]),
        message_count=chat.get("message_count", 0),
        messages_remaining=max(0, 10 - chat.get("message_count", 0)),
        detected_category=chat.get("detected_category"),
        messages=messages
    )


@router.post("/chats/{chat_id}/move")
async def move_chat_to_reference(
    chat_id: str,
    data: MoveChatRequest,
    background_tasks: BackgroundTasks,
    admin_username: str = Depends(require_admin)
):
    """Moves a chat transcript to a reference category and triggers background vector indexing."""
    db = get_database()
    try:
        obj_id = ObjectId(chat_id)
        chat = await db.chats.find_one({"_id": obj_id}) or await db.chats.find_one({"_id": chat_id})
    except Exception:
        chat = await db.chats.find_one({"_id": chat_id})

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    cid = str(chat["_id"])

    # Update chat record
    await db.chats.update_one(
        {"_id": chat["_id"]},
        {
            "$set": {
                "status": ChatStatus.REFERENCE,
                "reference_category_slug": data.category_slug,
                "moved_at": datetime.utcnow()
            }
        }
    )

    # Check if document record already exists for this chat
    doc = await db.documents.find_one({"chat_id": cid})
    if doc:
        # Update category and set PROCESSING
        doc_id = str(doc["_id"])
        await db.documents.update_one(
            {"_id": doc["_id"]},
            {
                "$set": {
                    "category_slug": data.category_slug,
                    "status": DocumentStatus.PROCESSING,
                    "uploaded_at": datetime.utcnow()
                }
            }
        )
    else:
        # Create new document entry
        new_doc = {
            "category_slug": data.category_slug,
            "source_type": DocumentSourceType.CHAT,
            "chat_id": cid,
            "original_filename": f"Chat Transcript ({cid[:8]})",
            "mime_type": "text/plain",
            "storage_path": "",
            "size_bytes": sum(len(m.get("content", "")) for m in chat.get("messages", [])),
            "status": DocumentStatus.PROCESSING,
            "error_message": None,
            "chunk_count": 0,
            "uploaded_at": datetime.utcnow()
        }
        res = await db.documents.insert_one(new_doc)
        doc_id = str(res.inserted_id)

    # Trigger background RAG vector indexing
    background_tasks.add_task(process_and_index_document, doc_id)

    return {"message": "Chat moved to reference category and queued for indexing", "document_id": doc_id}


@router.post("/chats/{chat_id}/unassign")
async def unassign_chat_from_reference(
    chat_id: str,
    admin_username: str = Depends(require_admin)
):
    """Removes chat from reference categories and purges vector embeddings."""
    db = get_database()
    try:
        obj_id = ObjectId(chat_id)
        chat = await db.chats.find_one({"_id": obj_id}) or await db.chats.find_one({"_id": chat_id})
    except Exception:
        chat = await db.chats.find_one({"_id": chat_id})

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    cid = str(chat["_id"])

    # Update chat status
    await db.chats.update_one(
        {"_id": chat["_id"]},
        {
            "$set": {
                "status": ChatStatus.UNASSIGNED,
                "reference_category_slug": None,
                "moved_at": None
            }
        }
    )

    # Purge document and vector embeddings
    doc = await db.documents.find_one({"chat_id": cid})
    if doc:
        await delete_document_and_vectors(str(doc["_id"]))

    return {"message": "Chat returned to unassigned list and vectors removed"}


@router.post("/chats/bulk-move")
async def bulk_move_chats(
    data: BulkMoveChatRequest,
    background_tasks: BackgroundTasks,
    admin_username: str = Depends(require_admin)
):
    """Moves multiple chats to a reference category in bulk."""
    for cid in data.chat_ids:
        try:
            req = MoveChatRequest(category_slug=data.category_slug)
            await move_chat_to_reference(
                chat_id=cid,
                data=req,
                background_tasks=background_tasks,
                admin_username=admin_username
            )
        except Exception:
            pass
    return {"message": f"Successfully moved {len(data.chat_ids)} chats"}


@router.delete("/chats/{chat_id}")
async def delete_chat(
    chat_id: str,
    admin_username: str = Depends(require_admin)
):
    """Deletes spam or test chat transcript and associated vectors."""
    db = get_database()
    try:
        obj_id = ObjectId(chat_id)
        chat = await db.chats.find_one({"_id": obj_id}) or await db.chats.find_one({"_id": chat_id})
    except Exception:
        chat = await db.chats.find_one({"_id": chat_id})

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    cid = str(chat["_id"])

    # Delete document & vectors if exists
    doc = await db.documents.find_one({"chat_id": cid})
    if doc:
        await delete_document_and_vectors(str(doc["_id"]))

    await db.chats.delete_one({"_id": chat["_id"]})
    return {"message": "Chat deleted successfully"}
