# Chatbot Flow Tracing Guide

## Overview
The Flow Trace utility prints an end-to-end timing trace to the server terminal for every student chat request, summarization, and document ingestion event.

```
[trace a3f9c1] chat.message  chat=6ad7cdcb  total 5.84 s
  request.validate                     3 ms  OK
  db.load_chat                        14 ms  OK
  guard.classify                    1.92 s  OK
     llm.attempt provider=gemini model=gemini-1.5-flash   1.90 s  OK
  rag.retrieve                       310 ms  OK
     rag.build_query                   1 ms
     rag.embed_query                 120 ms
     rag.vector_search                85 ms  hits=6 kept=4
     rag.format_context                2 ms  chunks=4 chars=3120
  prompt.build                         2 ms  chars=4210
  llm.generate                      3.41 s  OK  SLOW
     llm.attempt provider=gemini model=gemini-1.5-flash  4.20 s  FAILED (TimeoutError)
     llm.attempt provider=openai model=gpt-4o-mini       1.10 s  OK
  db.save_messages                    22 ms  OK
  --------------------------------------------------
  llm time 5.33 s | rag time 310 ms | db time 36 ms | other 160 ms
```

## Step Dictionary
- `request.validate`: Input length and 10-message session limit checks.
- `db.load_chat` / `db.save_messages`: MongoDB query and update operations.
- `guard.classify` / `llm.generate` / `llm.summarize`: Outer LLM pipeline steps.
- `llm.attempt`: Per-provider API call duration, model ID, and status (`OK` / `FAILED (Type)`).
- `rag.retrieve`: Outer RAG context retrieval step.
- `rag.build_query` / `rag.embed_query` / `rag.vector_search` / `rag.format_context`: Query prep, embedding generation, vector search filtering (`hits`, `kept`), and context string formatting (`chunks`, `chars`).
- `json.parse`: Summarization payload JSON validation.
- `parse.extract` / `sanitize` / `chunk` / `embed` / `vector.store_write`: Document ingestion steps (`rag.ingest`).

## Environment Configuration
- `FLOW_TRACE=true` -> Enables terminal trace block printing (set `false` to disable).
- `FLOW_TRACE_SLOW_MS=3000` -> Flags steps exceeding threshold (in ms) with a `SLOW` tag.

## File Changes
- `backend/app/utils/flow_trace.py` -> `FlowTrace` -> Reusable contextvars timing trace class and terminal formatter.
- `backend/app/config.py` -> `Settings` -> Added `FLOW_TRACE` and `FLOW_TRACE_SLOW_MS` environment settings.
- `backend/app/services/llm_router.py` -> `guard_and_classify` / `generate_answer` / `summarize_transcript` -> Wrapped per-provider LLM attempts with `llm.attempt` trace steps.
- `backend/app/services/rag_service.py` -> `retrieve_context` / `process_and_index_document` -> Added `rag.retrieve` sub-steps and `rag.ingest` trace flow.
- `backend/app/services/chat_service.py` -> `process_chat_message` / `summarize_chat_transcript` -> Wrapped message pipeline and summarization steps.
- `backend/app/routers/public_chat.py` -> `send_chat_message` / `summarize_chat` -> Initialized `FlowTrace` and invoked `finish()` in `finally` blocks.

## Reading the Output
- **High `llm.attempt` FAILED duration**: Provider API timeout or rate-limit retry.
- **High `rag.embed_query` duration**: Local sentence-transformer embedding model computation delay.
- **High `db.load_chat` / `db.save_messages`**: MongoDB database latency or network roundtrip delay.
