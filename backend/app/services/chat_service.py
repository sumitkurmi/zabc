"""Chat Service orchestrating guard checks, RAG retrieval, LLM response generation, and summarization.

Specification Sections 4, 5.4, 6, 8.3.
Uses LLMRouter multi-provider fallback orchestrator.
Lazy chat creation logic ensures chat documents are only created in MongoDB upon the first message.
Integrates per-request FlowTrace timing steps.
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
from backend.app.utils.flow_trace import get_current_trace, DummyStepContext

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
    """Processes a student message turn using LLMRouter multi-provider fallback with step timing trace.

    Lazy Creation Logic:
    - Validate chat_id format (must be valid ObjectId).
    - If the message is rejected before being accepted (empty text, too long), store nothing.
    - Check message limit (MAX_CHAT_MESSAGES).
    - Perform guard/classification & RAG generation.
    - Upsert chat document atomically using $setOnInsert for creation fields and $push for turns.
    """
    trace = get_current_trace()

    # Step 1: request.validate
    validate_step = trace.step("request.validate") if trace else DummyStepContext()
    with validate_step:
        try:
            obj_id = ObjectId(chat_id)
        except Exception:
            return {"error": {"code": "INVALID_ID", "message": "Invalid chat session ID format"}}, 400

        user_content_clean = user_content.strip()
        if not user_content_clean:
            return {"error": {"code": "EMPTY_MESSAGE", "message": "Message content cannot be empty"}}, 400
        if len(user_content_clean) > 500:
            return {"error": {"code": "MESSAGE_TOO_LONG", "message": "Message exceeds 500 character limit"}}, 400

    db = get_database()

    # Step 2: db.load_chat
    load_step = trace.step("db.load_chat") if trace else DummyStepContext()
    with load_step:
        chat = await find_chat_in_db(chat_id)

    # Check 10 user message limit
    current_count = chat.get("message_count", 0) if chat else 0
    if current_count >= settings.MAX_CHAT_MESSAGES:
        return {
            "error": {
                "code": "LIMIT_REACHED",
                "message": f"You've reached the {settings.MAX_CHAT_MESSAGES}-message limit. Click 'Log request using AI' to submit your complaint, or start a new chat."
            }
        }, 429

    # Step 3: guard.classify
    guard_step = trace.step("guard.classify") if trace else DummyStepContext()
    with guard_step:
        guard_result = await llm_router.guard_and_classify(user_content_clean)

    is_on_topic = guard_result.get("on_topic", True)
    category_str = guard_result.get("category")

    detected_category: Optional[ProblemType] = None
    if category_str and category_str in [pt.value for pt in ProblemType]:
        detected_category = ProblemType(category_str)
    else:
        detected_category = map_symptom_to_category(user_content_clean)

    new_count = current_count + 1
    now_dt = datetime.utcnow()

    user_turn = {
        "role": "user",
        "content": user_content_clean,
        "created_at": now_dt,
        "is_off_topic": not is_on_topic,
        "source_doc_ids": []
    }

    mongo_id = chat["_id"] if chat else obj_id

    if not is_on_topic:
        bot_turn = {
            "role": "assistant",
            "content": FIXED_OFF_TOPIC_REFUSAL,
            "created_at": datetime.utcnow(),
            "is_off_topic": True,
            "source_doc_ids": []
        }

        save_step = trace.step("db.save_messages") if trace else DummyStepContext()
        with save_step:
            await db.chats.update_one(
                {"_id": mongo_id},
                {
                    "$setOnInsert": {
                        "created_at": now_dt,
                        "status": "UNASSIGNED",
                        "reference_category_slug": None,
                        "moved_at": None,
                    },
                    "$set": {
                        "message_count": new_count,
                        "updated_at": datetime.utcnow(),
                        "detected_category": detected_category.value if detected_category else None
                    },
                    "$push": {"messages": {"$each": [user_turn, bot_turn]}}
                },
                upsert=True
            )

        return {
            "reply": FIXED_OFF_TOPIC_REFUSAL,
            "detected_category": detected_category.value if detected_category else None,
            "on_topic": False,
            "messages_used": new_count,
            "messages_remaining": settings.MAX_CHAT_MESSAGES - new_count
        }, 200

    # Step 4: rag.retrieve (handled in retrieve_context)
    category_slug = chat.get("reference_category_slug") if chat else None
    retrieved_chunks = retrieve_context(query=user_content_clean, category_slug=category_slug, top_k=6)

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

    # Step 5: prompt.build
    prompt_step = trace.step("prompt.build") if trace else DummyStepContext()
    with prompt_step:
        system_template = load_prompt_template("chat_system.txt")
        system_prompt = system_template.format(retrieved_chunks=context_str if context_str else "No context found.")
        if hasattr(prompt_step, "add"):
            prompt_step.add(chars=len(system_prompt))

    history = []
    if chat:
        for msg in chat.get("messages", [])[-6:]:
            history.append({"role": msg["role"], "content": msg["content"]})

    # Step 6: llm.generate
    gen_step = trace.step("llm.generate") if trace else DummyStepContext()
    with gen_step:
        reply_text = await llm_router.generate_answer(
            system_prompt=system_prompt,
            user_message=user_content_clean,
            history=history
        )

    bot_turn = {
        "role": "assistant",
        "content": reply_text,
        "created_at": datetime.utcnow(),
        "is_off_topic": False,
        "source_doc_ids": source_doc_ids
    }

    update_fields = {
        "message_count": new_count,
        "updated_at": datetime.utcnow()
    }
    if detected_category:
        update_fields["detected_category"] = detected_category.value

    # Step 7: db.save_messages
    save_step = trace.step("db.save_messages") if trace else DummyStepContext()
    with save_step:
        await db.chats.update_one(
            {"_id": mongo_id},
            {
                "$setOnInsert": {
                    "created_at": now_dt,
                    "status": "UNASSIGNED",
                    "reference_category_slug": None,
                    "moved_at": None,
                },
                "$set": update_fields,
                "$push": {"messages": {"$each": [user_turn, bot_turn]}}
            },
            upsert=True
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
    trace = get_current_trace()

    try:
        ObjectId(chat_id)
    except Exception:
        return {"error": {"code": "INVALID_ID", "message": "Invalid chat session ID format"}}, 400

    # Step 1: db.load_chat
    load_step = trace.step("db.load_chat") if trace else DummyStepContext()
    with load_step:
        chat = await find_chat_in_db(chat_id)

    if not chat:
        return {"error": {"code": "NO_MESSAGES", "message": "At least one user message is required to summarize."}}, 400

    messages = chat.get("messages", [])
    user_messages = [m for m in messages if m.get("role") == "user"]
    if not user_messages:
        return {"error": {"code": "NO_MESSAGES", "message": "At least one user message is required to summarize."}}, 400

    transcript_lines = []
    for m in messages:
        role = "Student" if m.get("role") == "user" else "Assistant"
        transcript_lines.append(f"{role}: {m.get('content')}")
    full_transcript = "\n".join(transcript_lines)

    # Step 2: llm.summarize
    sum_step = trace.step("llm.summarize") if trace else DummyStepContext()
    with sum_step:
        summary_data = await llm_router.summarize_transcript(full_transcript)

    # Step 3: json.parse
    parse_step = trace.step("json.parse") if trace else DummyStepContext()
    with parse_step:
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
