"""RAG Service for orchestrating ingestion, deletion, and context retrieval.

Specification Section 8.
Coordinates document text parsing, chunking, PII sanitization, vector store updates,
and retrieval filtering with similarity threshold.
Incorporates flow tracing for retrieval and document ingestion.
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId
from backend.app.db import get_database
from backend.app.models import DocumentModel, DocumentSourceType, DocumentStatus
from backend.app.services.parsers import parse_pdf, parse_docx, parse_txt, format_chat_transcript
from backend.app.services.chunker import chunk_text
from backend.app.services.sanitizer import sanitize_text
from backend.app.services.vector_store import get_vector_store
from backend.app.utils.flow_trace import FlowTrace, get_current_trace, DummyStepContext

MIN_SIMILARITY_THRESHOLD = 0.3  # Chunks below score 0.3 are discarded as irrelevant


async def find_document_by_id(document_id: str):
    """Queries document record matching either string _id or ObjectId _id."""
    db = get_database()
    doc = await db.documents.find_one({"_id": document_id})
    if not doc:
        try:
            doc = await db.documents.find_one({"_id": ObjectId(document_id)})
        except Exception:
            pass
    return doc


async def process_and_index_document(document_id: str) -> None:
    """Background task to extract, chunk, and index an uploaded document or moved chat into ChromaDB.

    Args:
        document_id: MongoDB string or ObjectId of the document record.
    """
    trace = FlowTrace("rag.ingest", chat_id=document_id)
    db = get_database()

    with trace:
        try:
            doc_dict = await find_document_by_id(document_id)
            if not doc_dict:
                return

            doc_obj_id = doc_dict["_id"]
            source_type = doc_dict.get("source_type")
            storage_path = doc_dict.get("storage_path")
            category_slug = doc_dict.get("category_slug")
            filename = doc_dict.get("original_filename", "document")

            raw_text = ""

            with trace.step("parse.extract"):
                if source_type == DocumentSourceType.CHAT:
                    # Fetch chat turns and format
                    chat_id = doc_dict.get("chat_id")
                    chat = await db.chats.find_one({"_id": chat_id})
                    if not chat:
                        try:
                            chat = await db.chats.find_one({"_id": ObjectId(chat_id)})
                        except Exception:
                            pass

                    if chat and "messages" in chat:
                        chat_date = str(chat.get("created_at", datetime.utcnow()))
                        raw_text = format_chat_transcript(chat["messages"], chat_date)
                    else:
                        raise ValueError("Chat transcript not found or empty")
                else:
                    # File Upload (PDF, DOCX, TXT)
                    mime_type = doc_dict.get("mime_type", "")
                    ext = os.path.splitext(storage_path)[1].lower() if storage_path else ""

                    if ext == ".pdf" or "pdf" in mime_type:
                        raw_text = parse_pdf(storage_path)
                    elif ext == ".docx" or "word" in mime_type:
                        raw_text = parse_docx(storage_path)
                    elif ext == ".txt" or "plain" in mime_type:
                        raw_text = parse_txt(storage_path)
                    else:
                        raise ValueError(f"Unsupported file format extension: {ext}")

            with trace.step("sanitize"):
                if source_type == DocumentSourceType.CHAT:
                    raw_text = sanitize_text(raw_text)

            # Chunk text (~800 chars, ~100 overlap)
            with trace.step("chunk") as chunk_step:
                chunks = chunk_text(raw_text, chunk_size=800, overlap=100)
                if hasattr(chunk_step, "add"):
                    chunk_step.add(chunks=len(chunks))

            # Embed and Index in ChromaDB
            v_store = get_vector_store()
            with trace.step("embed") as embed_step:
                if hasattr(embed_step, "add"):
                    embed_step.add(chunks=len(chunks))

            with trace.step("vector.store_write"):
                chunk_count = v_store.add_chunks(
                    document_id=str(doc_obj_id),
                    category_slug=category_slug,
                    source_type=source_type,
                    filename=filename,
                    chunks=chunks
                )

            # Update document status to INDEXED
            await db.documents.update_one(
                {"_id": doc_obj_id},
                {
                    "$set": {
                        "status": DocumentStatus.INDEXED,
                        "chunk_count": chunk_count,
                        "error_message": None
                    }
                }
            )

        except Exception as e:
            # Mark status FAILED with error message
            if 'doc_obj_id' in locals():
                await db.documents.update_one(
                    {"_id": doc_obj_id},
                    {
                        "$set": {
                            "status": DocumentStatus.FAILED,
                            "error_message": str(e)
                        }
                    }
                )
            raise e
        finally:
            trace.finish()


async def delete_document_and_vectors(document_id: str) -> None:
    """Deletes document record from MongoDB and purges vectors from ChromaDB.

    Args:
        document_id: MongoDB ID of document to purge.
    """
    db = get_database()
    doc = await find_document_by_id(document_id)
    if doc:
        doc_obj_id = doc["_id"]
        # Delete file from disk if it was an uploaded file
        storage_path = doc.get("storage_path")
        if storage_path and os.path.exists(storage_path) and doc.get("source_type") == DocumentSourceType.UPLOAD:
            try:
                os.remove(storage_path)
            except Exception:
                pass

        # Purge vector embeddings from ChromaDB
        v_store = get_vector_store()
        v_store.delete_document(str(doc_obj_id))

        # Delete MongoDB record
        await db.documents.delete_one({"_id": doc_obj_id})


def retrieve_context(query: str, category_slug: Optional[str] = None, top_k: int = 6) -> List[Dict[str, Any]]:
    """Retrieves context chunks relevant to the user's message above minimum score threshold.

    Args:
        query: User query text.
        category_slug: Optional category filter.
        top_k: Max chunks to return (default 6).

    Returns:
        Filtered list of top chunks with source filenames.
    """
    trace = get_current_trace()
    outer_step = trace.step("rag.retrieve") if trace else DummyStepContext()

    with outer_step:
        # 1. rag.build_query
        build_step = trace.step("rag.build_query") if trace else DummyStepContext()
        with build_step:
            search_query = query.strip()

        # 2. rag.embed_query & 3. rag.vector_search
        embed_step = trace.step("rag.embed_query") if trace else DummyStepContext()
        with embed_step:
            # Query embedding step
            pass

        v_store = get_vector_store()
        search_step = trace.step("rag.vector_search") if trace else DummyStepContext()
        with search_step:
            raw_hits = v_store.search(query=search_query, top_k=top_k * 2, category_slug=category_slug)
            filtered_hits = [hit for hit in raw_hits if hit["score"] >= MIN_SIMILARITY_THRESHOLD]
            final_hits = filtered_hits[:top_k]
            if hasattr(search_step, "add"):
                search_step.add(hits=len(raw_hits), kept=len(final_hits))

        # 4. rag.format_context
        fmt_step = trace.step("rag.format_context") if trace else DummyStepContext()
        with fmt_step:
            total_chars = sum(len(hit.get("text", "")) for hit in final_hits)
            if hasattr(fmt_step, "add"):
                fmt_step.add(chunks=len(final_hits), chars=total_chars)

    return final_hits
