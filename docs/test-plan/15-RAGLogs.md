# Area 15: Closed complaints into RAG

### TC-15-001 - Student confirmed generates log
Priority: P1 | Role: system
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Student confirms 'Solved'.
Expected result:
- New document in RAG collection created.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-15-002 - PII sanitized in RAG
Priority: P1 | Role: system
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Check generated RAG document text.
Expected result:
- No names, emails, phones, or ticket IDs present.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.outbox.find().sort({created_at: -1}).limit(5)`

### TC-15-003 - Auto-closed not indexed
Priority: P2 | Role: system
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Auto-close a complaint.
Expected result:
- No RAG document created (default behavior).
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-15-004 - No duplicate indexing
Priority: P2 | Role: system
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Trigger indexing twice via API.
Expected result:
- Only one RAG doc exists per complaint.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-15-005 - Backfill script
Priority: P3 | Role: admin
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Run backfill script with dry run.
Expected result:
- Identifies correct number of unindexed closed complaints.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`
