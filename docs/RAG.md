# Knowledge Base Ingestion & RAG Pipeline Architecture

This document details how student chats and uploaded documents (PDF, DOCX, TXT) flow through the RAG pipeline into ChromaDB, and how context is retrieved during student troubleshooting sessions.

---

## 1. Document & Chat Ingestion Pipeline

```
[Uploaded File / Promoted Chat]
        │
        ▼
[Text Extraction Parser]  ──►  PDF (pypdf), DOCX (python-docx), TXT / Chat turns
        │
        ▼
[PII Sanitizer]           ──►  Strips emails, phone numbers, and plain passwords
        │
        ▼
[Text Chunker]            ──►  Splits into ~800 char chunks with ~100 char overlap
        │
        ▼
[Vector Store Embedding]  ──►  Generates vectors and stores in ChromaDB collection 'network_kb'
        │
        ▼
[Database Status Update]  ──►  Updates documents.status to 'INDEXED' with chunk_count
```

---

## 2. RAG Retrieval during Student Chat Turns

1. **User Query Input**: Student sends a troubleshooting query via `POST /api/chat/{id}/message`.
2. **Guard Step**: `guard_and_classify` determines if the query is on-topic. If off-topic, returns fixed refusal.
3. **Similarity Search**: `retrieve_context` queries ChromaDB for the top 6 relevant text chunks.
4. **Similarity Threshold Filtering**: Chunks with similarity score below `0.3` are discarded.
5. **Prompt Injection**: Relevant chunks are injected into `chat_system.txt` under `CONTEXT:` block.
6. **LLM Generation**: LLM generates friendly, beginner-level troubleshooting steps grounded in retrieved context.
