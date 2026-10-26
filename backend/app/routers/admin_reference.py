"""Admin reference category and file upload management router.

Specification Section 9.4 & Section 10.
Handles listing reference categories, uploading PDF/DOCX/TXT files, file size & type validation,
document status polling, file downloading, and deletion.
Excludes empty chats (message_count < 1) from category chat lists and counts.
"""

import os
import uuid
from datetime import datetime
from bson import ObjectId
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    BackgroundTasks,
    status
)
from fastapi.responses import FileResponse, PlainTextResponse, Response
from docx import Document
from io import BytesIO
from backend.app.config import settings
from backend.app.db import get_database
from backend.app.deps import require_admin
from backend.app.models import DocumentSourceType, DocumentStatus
from backend.app.schemas import (
    CategoryDetailResponse,
    CategorySummaryResponse,
    ChatSummaryResponse,
    DocumentResponse
)

from backend.app.services.rag_service import process_and_index_document, delete_document_and_vectors

router = APIRouter(prefix="/admin", tags=["admin-reference"])

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


@router.get("/categories", response_model=list[CategorySummaryResponse])
async def list_categories(admin_username: str = Depends(require_admin)):
    """Lists six reference categories with chat and document counts (excluding empty chats)."""
    db = get_database()
    categories_cursor = db.reference_categories.find({})

    categories = []
    async for cat in categories_cursor:
        slug = cat["slug"]
        # Safety net: Exclude empty chats with message_count < 1
        chats_count = await db.chats.count_documents({
            "status": "REFERENCE",
            "reference_category_slug": slug,
            "message_count": {"$gte": 1}
        })
        documents_count = await db.documents.count_documents({
            "category_slug": slug,
            "source_type": DocumentSourceType.UPLOAD
        })

        categories.append(
            CategorySummaryResponse(
                slug=slug,
                name=cat["name"],
                description=cat["description"],
                chats_count=chats_count,
                documents_count=documents_count
            )
        )

    return categories


@router.get("/categories/{slug}", response_model=CategoryDetailResponse)
async def get_category_detail(
    slug: str,
    admin_username: str = Depends(require_admin)
):
    """Returns detailed category view including assigned chats and uploaded documents (excluding empty chats)."""
    db = get_database()
    cat = await db.reference_categories.find_one({"slug": slug})
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")

    # Safety net: Exclude empty chats with message_count < 1
    chats_count = await db.chats.count_documents({
        "status": "REFERENCE",
        "reference_category_slug": slug,
        "message_count": {"$gte": 1}
    })
    documents_count = await db.documents.count_documents({
        "category_slug": slug,
        "source_type": DocumentSourceType.UPLOAD
    })

    category_summary = CategorySummaryResponse(
        slug=slug,
        name=cat["name"],
        description=cat["description"],
        chats_count=chats_count,
        documents_count=documents_count
    )

    # Fetch assigned reference chats (excluding empty chats)
    chats_cursor = db.chats.find({
        "status": "REFERENCE",
        "reference_category_slug": slug,
        "message_count": {"$gte": 1}
    }).sort("moved_at", -1)

    chats_list = []
    async for chat in chats_cursor:
        msgs = chat.get("messages", [])
        preview = ""
        for m in msgs:
            if m.get("role") == "user":
                preview = m.get("content", "")[:100]
                break

        chats_list.append(
            ChatSummaryResponse(
                id=str(chat["_id"]),
                preview=preview or "Empty transcript",
                message_count=chat.get("message_count", 0),
                detected_category=chat.get("detected_category"),
                created_at=chat.get("created_at", datetime.utcnow()),
                status=chat.get("status"),
                reference_category_slug=chat.get("reference_category_slug")
            )
        )

    # Fetch category documents
    docs_cursor = db.documents.find({"category_slug": slug,"source_type": DocumentSourceType.UPLOAD}).sort("uploaded_at", -1)
    docs_list = []
    async for doc in docs_cursor:
        docs_list.append(
            DocumentResponse(
                id=str(doc["_id"]),
                category_slug=doc["category_slug"],
                source_type=doc.get("source_type", DocumentSourceType.UPLOAD),
                chat_id=doc.get("chat_id"),
                original_filename=doc.get("original_filename", "file"),
                mime_type=doc.get("mime_type", "application/octet-stream"),
                size_bytes=doc.get("size_bytes", 0),
                status=doc.get("status", DocumentStatus.PROCESSING),
                error_message=doc.get("error_message"),
                chunk_count=doc.get("chunk_count", 0),
                uploaded_at=doc.get("uploaded_at", datetime.utcnow())
            )
        )

    return CategoryDetailResponse(
        category=category_summary,
        chats=chats_list,
        documents=docs_list
    )


@router.post("/categories/{slug}/documents", response_model=DocumentResponse)
async def upload_document(
    slug: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    admin_username: str = Depends(require_admin)
):
    """Uploads document file (.pdf, .docx, .txt), stores on disk, and triggers RAG indexing."""
    db = get_database()
    cat = await db.reference_categories.find_one({"slug": slug})
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file extension {ext}. Allowed formats: .pdf, .docx, .txt"
        )

    # Check file size limit (10MB)
    contents = await file.read()
    size_bytes = len(contents)
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024

    if size_bytes > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_MB} MB"
        )

    # Save to disk with randomized filename
    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)
    unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
    storage_path = os.path.join(upload_dir, unique_filename)

    with open(storage_path, "wb") as f:
        f.write(contents)

    # Create document record
    doc_data = {
        "category_slug": slug,
        "source_type": DocumentSourceType.UPLOAD,
        "chat_id": None,
        "original_filename": file.filename,
        "mime_type": file.content_type or "application/octet-stream",
        "storage_path": storage_path,
        "size_bytes": size_bytes,
        "status": DocumentStatus.PROCESSING,
        "error_message": None,
        "chunk_count": 0,
        "uploaded_at": datetime.utcnow()
    }

    result = await db.documents.insert_one(doc_data)
    doc_id = str(result.inserted_id)

    # Trigger background indexing
    background_tasks.add_task(process_and_index_document, doc_id)

    return DocumentResponse(
        id=doc_id,
        category_slug=slug,
        source_type=DocumentSourceType.UPLOAD,
        chat_id=None,
        original_filename=file.filename,
        mime_type=file.content_type or "application/octet-stream",
        size_bytes=size_bytes,
        status=DocumentStatus.PROCESSING,
        error_message=None,
        chunk_count=0,
        uploaded_at=doc_data["uploaded_at"]
    )


@router.get("/documents/{doc_id}", response_model=DocumentResponse)
async def get_document_status(
    doc_id: str,
    admin_username: str = Depends(require_admin)
):
    """Polls indexing status of a document."""
    db = get_database()
    try:
        obj_id = ObjectId(doc_id)
        doc = await db.documents.find_one({"_id": obj_id}) or await db.documents.find_one({"_id": doc_id})
    except Exception:
        doc = await db.documents.find_one({"_id": doc_id})

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return DocumentResponse(
        id=str(doc["_id"]),
        category_slug=doc["category_slug"],
        source_type=doc.get("source_type", DocumentSourceType.UPLOAD),
        chat_id=doc.get("chat_id"),
        original_filename=doc.get("original_filename", "file"),
        mime_type=doc.get("mime_type", "application/octet-stream"),
        size_bytes=doc.get("size_bytes", 0),
        status=doc.get("status", DocumentStatus.PROCESSING),
        error_message=doc.get("error_message"),
        chunk_count=doc.get("chunk_count", 0),
        uploaded_at=doc.get("uploaded_at", datetime.utcnow())
    )


@router.get("/documents/{doc_id}/download")
async def download_document(
    doc_id: str,
    admin_username: str = Depends(require_admin)
):
    """Downloads original uploaded file."""
    db = get_database()
    try:
        obj_id = ObjectId(doc_id)
        doc = await db.documents.find_one({"_id": obj_id}) or await db.documents.find_one({"_id": doc_id})
    except Exception:
        doc = await db.documents.find_one({"_id": doc_id})

    if not doc or not doc.get("storage_path"):
        raise HTTPException(status_code=404, detail="File not found")

    path = doc["storage_path"]
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File content missing from disk")

    return FileResponse(
        path=path,
        filename=doc.get("original_filename", "download"),
        media_type=doc.get("mime_type", "application/octet-stream")
    )




@router.get("/documents/{doc_id}/preview")
async def preview_document(
    doc_id: str,
    admin_username: str = Depends(require_admin)
):
    """Previews an uploaded PDF, TXT, or DOCX document."""
    db = get_database()

    try:
        obj_id = ObjectId(doc_id)
        doc = await db.documents.find_one({"_id": obj_id})
        if not doc:
            doc = await db.documents.find_one({"_id": doc_id})
    except Exception:
        doc = await db.documents.find_one({"_id": doc_id})

    if not doc or doc.get("source_type") != DocumentSourceType.UPLOAD:
        raise HTTPException(status_code=404, detail="Document not found")

    filename = doc.get("original_filename", "")
    extension = os.path.splitext(filename)[1].lower()

    if extension not in {".pdf", ".txt", ".docx"}:
        raise HTTPException(
            status_code=400,
            detail="Preview is only available for PDF, TXT, and DOCX files"
        )

    path = doc.get("storage_path")
    if not path or not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="File content missing from disk")

    if extension == ".pdf":
        return FileResponse(
            path=path,
            media_type="application/pdf",
            content_disposition_type="inline"
        )

    if extension == ".txt":
        try:
            with open(path, "r", encoding="utf-8-sig") as file:
                content = file.read()
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=422,
                detail="TXT file encoding is not supported for preview"
            )

        return PlainTextResponse(content=content)

    if extension == ".docx":
        return FileResponse(
            path=path,
            media_type=(
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
            filename=filename
        )



@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    admin_username: str = Depends(require_admin)
):
    """Deletes uploaded document file and purges associated vector embeddings."""
    await delete_document_and_vectors(doc_id)
    return {"message": "Document deleted successfully"}


@router.get("/complaints")
async def list_submitted_complaints(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    admin_username: str = Depends(require_admin)
):
    """Lists submitted complaints for admin review / demo verification."""
    db = get_database()
    skip = (page - 1) * limit
    total = await db.complaints.count_documents({})
    cursor = db.complaints.find({}).sort("created_at", -1).skip(skip).limit(limit)

    complaints = []
    async for c in cursor:
        complaints.append({
            "id": str(c["_id"]),
            "ref_no": c.get("ref_no"),
            "name": c.get("name"),
            "email": c.get("email"),
            "mobile": c.get("mobile"),
            "location": c.get("location"),
            "address_room": c.get("address_room"),
            "preferred_from": c.get("preferred_from"),
            "preferred_to": c.get("preferred_to"),
            "problem_type": c.get("problem_type"),
            "additional_comment": c.get("additional_comment"),
            "filled_by_ai": c.get("filled_by_ai", False),
            "status": c.get("status", "NEW"),
            "created_at": c.get("created_at")
        })

    return {
        "complaints": complaints,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit if total > 0 else 1
    }
