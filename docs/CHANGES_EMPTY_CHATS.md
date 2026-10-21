# Change Record: Lazy Chat Creation & Empty Chat Prevention

- **Reason**: Chat session records were stored in MongoDB when the chat panel opened or 'New chat' was clicked, causing empty chats with 0 user messages to accumulate.
- **New Behaviour**: Opening the chat panel or clicking 'New chat' returns a new ObjectId without creating a database document; chats are inserted into MongoDB atomically only when the student sends their first user message.

## File Changes
- `backend/app/routers/public_chat.py` -> `create_chat` -> Generates and returns new ObjectId string without inserting document to MongoDB.
- `backend/app/routers/public_chat.py` -> `get_chat_transcript` -> Returns empty transcript with message_count 0 for valid unsaved chat ObjectIds.
- `backend/app/services/chat_service.py` -> `process_chat_message` -> Atomically upserts chat document on first user message using $setOnInsert and $push.
- `backend/app/services/chat_service.py` -> `summarize_chat_transcript` -> Returns 400 NO_MESSAGES error when chat does not exist or has 0 user messages.
- `backend/app/routers/admin_chats.py` -> `list_unassigned_chats` / `get_admin_stats` -> Filters queries with `message_count: {"$gte": 1}` to exclude empty chats.
- `backend/app/routers/admin_reference.py` -> `list_categories` / `get_category_detail` -> Filters category queries with `message_count: {"$gte": 1}`.

## Database Cleanup
- To delete previously stored empty chats manually from MongoDB shell:
  `db.chats.deleteMany({message_count: {$lt: 1}})`

## Risk / Behaviour Changes
- Low risk: Opening the chat panel or clicking 'New chat' no longer creates a MongoDB document until a message is sent. API contract and frontend UI remain unchanged.
