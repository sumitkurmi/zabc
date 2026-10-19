# Anonymous Chat Sessions Guide

This document explains how student chat sessions operate without student login in the MNNIT Allahabad Network Complaint Portal.

```
[Browser Client]                                  [FastAPI Backend]                [MongoDB]
  |                                                     |                             |
  |-- (No session key in sessionStorage) -------------->| POST /api/chat ------------>| Insert chat doc
  |                                                     |                             | (_id, count:0)
  |<- Returns {chat_id} <-------------------------------|                             |
  | Stores key 'student_chat_id' in sessionStorage      |                             |
  |                                                     |                             |
  |-- POST /api/chat/{chat_id}/message ---------------->| Process turn & update ----->| Inc count +2
  |<- Returns {reply, messages_used, ...} --------------|                             | turns
```

---

## 1. Chat Identification
- **Creation**: The backend creates an anonymous chat document in MongoDB (`_id`, `message_count: 0`, `status: UNASSIGNED`) inside `create_chat()` in `backend/app/routers/public_chat.py`.
- **Client Storage**: The frontend `useChat` hook (`frontend/src/hooks/useChat.ts`) stores the returned string ID in `sessionStorage` under the key name **`student_chat_id`**.
- **Message Transmission**: For each turn, `sendChatMessage(chatId, content)` in `frontend/src/api/chat.ts` sends `POST /api/chat/{chat_id}/message`.

---

## 2. Starting a New Chat
A new chat is initialized (calling `POST /api/chat`) under the following conditions:
1. **First Visit**: No `student_chat_id` exists in `sessionStorage`.
2. **User Clicks "New Chat"**: Calling `startNewChat()` / `initChat()` in `useChat.ts` creates a fresh ID and overwrites `student_chat_id`.
3. **Session Reached Limit**: Once `message_count >= 10`, the user is prompted to start a new chat.
4. **Missing or Deleted Session**: If `GET /api/chat/{chat_id}` returns `404 Not Found`, the frontend automatically calls `initChat()`.
5. **Session Expiry Rule**: Chat sessions do **not** expire automatically in MongoDB v1. Session persistence is tied to browser tab life via `sessionStorage` (closing the tab clears the key).

---

## 3. Continuing an Existing Chat
- **Page Refresh**: On refresh within the same browser tab, `useChat.ts` reads `student_chat_id` from `sessionStorage` and calls `getChatTranscript(chatId)` (`GET /api/chat/{chat_id}`).
- **Panel Toggle**: Closing/reopening the widget retains in-memory state; reloading restores the full message transcript, current count, and category from MongoDB.

---

## 4. 10-Message Limit & Storage Clearing
- **Backend Enforcement**: `process_chat_message()` in `backend/app/services/chat_service.py` checks `chat.get("message_count", 0) >= 10` and returns `429 Too Many Requests` with code `LIMIT_REACHED` if exceeded.
- **Device Switch / Clearing Storage**: Clearing browser storage or opening the portal on a new device/browser loses `student_chat_id`. A new anonymous chat is created, while the old chat document remains preserved in MongoDB for admin review.

---

## 5. Known Limitations & Security Safeguards
- **Limitation**: A user can clear `sessionStorage` or open incognito tabs to initiate multiple fresh 10-message chats.
- **Protections**:
  - **IP Rate Limiting**: `slowapi` limits chat message endpoints to 30 requests per hour per IP.
  - **Off-Topic Guard**: Guard step intercepts non-network queries early without spending heavy RAG tokens.
- **Gaps**: IP rate limits affect shared campus Wi-Fi/NAT blocks; v1 does not restrict multi-chat creation per IP.

---

## File and Function Summary
- **Backend**: `backend/app/routers/public_chat.py` (`create_chat`, `get_chat_transcript`), `backend/app/services/chat_service.py` (`process_chat_message`).
- **Frontend**: `frontend/src/hooks/useChat.ts` (`useChat`, `initChat`), `frontend/src/api/chat.ts` (`createChat`, `sendChatMessage`, `getChatTranscript`).
