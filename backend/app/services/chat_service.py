"""Chat Service orchestrating guard checks, RAG retrieval, LLM response generation, and summarization.

Specification Sections 4, 5.4, 6, 8.3.
Uses LLMRouter multi-provider fallback orchestrator.
"""

import os
from datetime import datetime
from typing import Dict, Any, Tuple, Optional
from bson import ObjectId
from backend.app.config import settings
from backend.app.db import get_database
from backend.app.models import ProblemType, ChatMessage
from backend.app.services.rag_service import retrieve_context
from backend.app.services.llm_router import llm_router
from backend.app.services.category_map import map_symptom_to_category

FIXED_OFF_TOPIC_REFUSAL = (
    "I can only help with network-related issues such as Wi-Fi, LAN, login, IP, DNS, "
    "slow internet, cable faults, switch ports or access points. Please ask about a network problem."
)


def load_prompt_template(filename: str) -> str:
    """Reads prompt template file from app/prompts/ directory."""
    path = os.path.join(os.path.dirname(__file__), "..", "prompts", filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


async def find_chat_in_db(chat_id: str):
    """Queries chat document matching either string _id or ObjectId _id."""
    db = get_database()
    chat = await db.chats.find_one({"_id": chat_id})
    if not chat:
        try:
            chat = await db.chats.find_one({"_id": ObjectId(chat_id)})
        except Exception:
            pass
    return chat


async def process_chat_message(chat_id: str, user_content: str) -> Tuple[Dict[str, Any], int]:
    """Processes a student message turn using LLMRouter multi-provider fallback.

    1. Checks 10-message limit.
    2. Runs Guard step via LLMRouter. Refusal returned if off-topic.
    3. Performs RAG retrieval from ChromaDB.
    4. Calls LLMRouter with prompt + context + history.
    5. Updates MongoDB chat document.

    Returns:
        Tuple of (response_dict, http_status_code)
    """
    db = get_database()
    chat = await find_chat_in_db(chat_id)
    if not chat:
        return {"error": {"code": "NOT_FOUND", "message": "Chat session not found"}}, 404

    # Enforce 10 user message limit (Section 5.4 & 6.2)
    current_count = chat.get("message_count", 0)
    if current_count >= settings.MAX_CHAT_MESSAGES:
        return {
            "error": {
                "code": "LIMIT_REACHED",
                "message": f"You've reached the {settings.MAX_CHAT_MESSAGES}-message limit. Click 'Log request using AI' to submit your complaint, or start a new chat."
            }
        }, 429

    # Step 1: Guard & Classify via LLMRouter fallback orchestrator
    guard_result = await llm_router.guard_and_classify(user_content)
    is_on_topic = guard_result.get("on_topic", True)
    category_str = guard_result.get("category")

    detected_category: Optional[ProblemType] = None
    if category_str and category_str in [pt.value for pt in ProblemType]:
        detected_category = ProblemType(category_str)
    else:
        detected_category = map_symptom_to_category(user_content)

    new_count = current_count + 1

    # Record user message
    user_turn = {
        "role": "user",
        "content": user_content,
        "created_at": datetime.utcnow(),
        "is_off_topic": not is_on_topic,
        "source_doc_ids": []
    }

    if not is_on_topic:
        # Fixed refusal reply
        bot_turn = {
            "role": "assistant",
            "content": FIXED_OFF_TOPIC_REFUSAL,
            "created_at": datetime.utcnow(),
            "is_off_topic": True,
            "source_doc_ids": []
        }

        await db.chats.update_one(
            {"_id": chat["_id"]},
            {
                "$set": {
                    "message_count": new_count,
                    "updated_at": datetime.utcnow()
                },
                "$push": {"messages": {"$each": [user_turn, bot_turn]}}
            }
        )

        return {
            "reply": FIXED_OFF_TOPIC_REFUSAL,
            "detected_category": detected_category.value if detected_category else None,
            "on_topic": False,
            "messages_used": new_count,
            "messages_remaining": settings.MAX_CHAT_MESSAGES - new_count
        }, 200

    # Step 2: On-topic -> RAG Retrieval & Answering
    category_slug = chat.get("reference_category_slug")
    retrieved_chunks = retrieve_context(query=user_content, category_slug=category_slug, top_k=6)

    context_str = ""
    source_doc_ids = []
    if retrieved_chunks:
        context_parts = []
        for chunk in retrieved_chunks:
            meta = chunk["metadata"]
            filename = meta.get("filename", "knowledge base")
            doc_id = meta.get("document_id")
            if doc_id and doc_id not in source_doc_ids:
                source_doc_ids.append(doc_id)
            context_parts.append(f"[Source: {filename}]\n{chunk['text']}")
        context_str = "\n\n".join(context_parts)

    system_template = load_prompt_template("chat_system.txt")
    system_prompt = system_template.format(retrieved_chunks=context_str if context_str else "No context found.")

    # Build history turns
    history = []
    for msg in chat.get("messages", [])[-6:]:  # recent 3 turns
        history.append({"role": msg["role"], "content": msg["content"]})

    reply_text = await llm_router.generate_answer(
        system_prompt=system_prompt,
        user_message=user_content,
        history=history
    )

    bot_turn = {
        "role": "assistant",
        "content": reply_text,
        "created_at": datetime.utcnow(),
        "is_off_topic": False,
        "source_doc_ids": source_doc_ids
    }

    # Update chat document with detected category if available
    update_fields = {
        "message_count": new_count,
        "updated_at": datetime.utcnow()
    }
    if detected_category:
        update_fields["detected_category"] = detected_category.value

    await db.chats.update_one(
        {"_id": chat["_id"]},
        {
            "$set": update_fields,
            "$push": {"messages": {"$each": [user_turn, bot_turn]}}
        }
    )

    return {
        "reply": reply_text,
        "detected_category": detected_category.value if detected_category else None,
        "on_topic": True,
        "messages_used": new_count,
        "messages_remaining": settings.MAX_CHAT_MESSAGES - new_count
    }, 200


async def summarize_chat_transcript(chat_id: str) -> Tuple[Dict[str, Any], int]:
    """Generates problem type and comment summary from transcript via LLMRouter for auto-filling complaint form."""
    chat = await find_chat_in_db(chat_id)
    if not chat:
        return {"error": {"code": "NOT_FOUND", "message": "Chat session not found"}}, 404

    messages = chat.get("messages", [])
    user_messages = [m for m in messages if m.get("role") == "user"]
    if not user_messages:
        return {"error": {"code": "NO_MESSAGES", "message": "At least one user message is required to summarize."}}, 400

    transcript_lines = []
    for m in messages:
        role = "Student" if m.get("role") == "user" else "Assistant"
        transcript_lines.append(f"{role}: {m.get('content')}")
    full_transcript = "\n".join(transcript_lines)

    summary_data = await llm_router.summarize_transcript(full_transcript)

    # Validate problem type
    pt_val = summary_data.get("problem_type")
    if not pt_val or pt_val not in [pt.value for pt in ProblemType]:
        cat = map_symptom_to_category(full_transcript) or ProblemType.WIFI_PROBLEM
        pt_val = cat.value

    comment = summary_data.get("additional_comment", "").strip()
    if not comment:
        comment = " ".join([m.get("content", "") for m in user_messages])[:500]

    return {
        "problem_type": pt_val,
        "additional_comment": comment[:1000]
    }, 200
