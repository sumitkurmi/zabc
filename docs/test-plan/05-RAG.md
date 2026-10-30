# Area 05: RAG behaviour

### TC-05-001 - Upload TXT
Priority: P1 | Role: admin
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Upload unique_fact.txt. Ask chatbot for fact.
Expected result:
- Chatbot uses the unique fact.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-05-002 - Promote chat to RAG
Priority: P2 | Role: admin
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Admin promotes a chat session.
Expected result:
- Chat becomes part of RAG context.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.users.find()`

### TC-05-003 - Delete document
Priority: P1 | Role: admin
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Delete unique_fact.txt. Ask chatbot again.
Expected result:
- Chatbot no longer knows the fact.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-05-004 - Move document category
Priority: P2 | Role: admin
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Move document to another category.
Expected result:
- Reflected in UI and search filter.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.users.find()`

### TC-05-005 - Wrong file type
Priority: P2 | Role: admin
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Upload wrong_type.jpg.
Expected result:
- Upload rejected, error message shown.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-05-006 - Oversize file
Priority: P2 | Role: admin
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Upload oversized.pdf.
Expected result:
- Upload rejected, size limit error shown.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-05-007 - Scanned PDF failure
Priority: P3 | Role: admin
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Upload scanned (image-only) PDF.
Expected result:
- Warning or failure about lack of extractable text.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.users.find()`

### TC-05-008 - Indexing status
Priority: P2 | Role: admin
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Upload valid_doc.docx.
Expected result:
- Status changes from Pending to Indexed.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.users.find()`

### TC-05-009 - From complaint badge
Priority: P3 | Role: admin
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Check RAG documents list.
Expected result:
- Documents extracted from complaints have 'From complaint' badge.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.users.find()`
### TC-05-010 - Delete document RAG sync
Priority: P2 | Role: admin
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Delete a document from ChromaDB collection.
Expected result:
- Vector store and DB are synced successfully.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`
