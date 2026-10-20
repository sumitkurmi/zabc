"""Public chat API router.

Handles starting chat sessions, sending messages, fetching transcript history, and AI summarization.
Specification Section 5.4, Section 10.
"""

from datetime import datetime
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Request, status
from backend.app.config import settings
from backend.app.db import get_database
from backend.app.schemas import (
    ChatCreateResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    ChatTranscriptResponse,
    ChatTurnSchema,
    SummarizeResponse
)
from backend.app.services.chat_service import process_chat_message, summarize_chat_transcript

router = APIRouter(prefix="/chat", tags=["chat"])


async def find_chat_by_id(chat_id: str):
    """Helper to query chat document accepting both string _id and ObjectId _id."""
    db = get_database()
    chat = await db.chats.find_one({"_id": chat_id})
    if not chat:
        try:
            chat = await db.chats.find_one({"_id": ObjectId(chat_id)})
        except Exception:
            pass
    return chat


@router.post("", response_model=ChatCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(request: Request):
    """Generates a new chat session ID without storing a document in MongoDB yet.

    Lazy chat creation: To prevent storing empty chat documents when users open
    the chat panel or click 'New chat' without typing anything, no document is inserted
    at session start. The document is only created upon the first user message.
    """
    # Simply generate a new ObjectId and return it as chat_id
    new_chat_id = str(ObjectId())
    return ChatCreateResponse(chat_id=new_chat_id)


@router.get("/{chat_id}", response_model=ChatTranscriptResponse)
async def get_chat_transcript(chat_id: str):
    """Fetches full chat transcript for page refresh restore.

    If the chat ID is a valid ObjectId format but has no document stored in MongoDB yet
    (due to lazy chat creation), return an empty transcript instead of 404.
    """
    # Validate ObjectId format
    try:
        obj_id = ObjectId(chat_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid chat session ID format")

    chat = await find_chat_by_id(chat_id)

    # If no document is stored yet, return empty transcript response
    if not chat:
        return ChatTranscriptResponse(
            chat_id=chat_id,
            message_count=0,
            messages_remaining=settings.MAX_CHAT_MESSAGES,
            detected_category=None,
            messages=[]
        )

    messages = [
        ChatTurnSchema(
            role=m["role"],
            content=m["content"],
            created_at=m.get("created_at", datetime.utcnow()),
            is_off_topic=m.get("is_off_topic", False)
        )
        for m in chat.get("messages", [])
    ]

    msg_count = chat.get("message_count", 0)

    return ChatTranscriptResponse(
        chat_id=str(chat["_id"]),
        message_count=msg_count,
        messages_remaining=max(0, settings.MAX_CHAT_MESSAGES - msg_count),
        detected_category=chat.get("detected_category"),
        messages=messages
    )


@router.post("/{chat_id}/message", response_model=ChatMessageResponse)
async def send_chat_message(chat_id: str, data: ChatMessageRequest, request: Request):
    """Sends a user message turn in a student chat session."""
    result, status_code = await process_chat_message(chat_id=chat_id, user_content=data.content)
    if status_code != 200:
        err = result.get("error", {})
        raise HTTPException(status_code=status_code, detail=err.get("message", "Chat error"))

    return ChatMessageResponse(**result)


@router.post("/{chat_id}/summarize", response_model=SummarizeResponse)
async def summarize_chat(chat_id: str, request: Request):
    """Summarizes chat transcript into complaint form pre-fill fields."""
    result, status_code = await summarize_chat_transcript(chat_id=chat_id)
    if status_code != 200:
        err = result.get("error", {})
        raise HTTPException(status_code=status_code, detail=err.get("message", "Summarization error"))

    return SummarizeResponse(**result)
