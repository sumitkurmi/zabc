# Area 22: Data checks

### TC-22-001 - Unique ticket index
Priority: P1 | Role: system
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Run `db.complaints.getIndexes()`.
Expected result:
- Unique index on `ticket_id` exists.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.complaints.getIndexes()`

### TC-22-002 - TTL index
Priority: P2 | Role: system
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Run `db.pending_complaints.getIndexes()`.
Expected result:
- TTL index on `otp_expires_at` exists.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.pending_complaints.getIndexes()`

### TC-22-003 - No empty chats
Priority: P2 | Role: system
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Run `db.chat_sessions.find({messages: {$size: 0}})`.
Expected result:
- Returns 0 documents.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.chat_sessions.find({messages: {$size: 0}})`

### TC-22-004 - History ordering
Priority: P3 | Role: system
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Check history array of a complaint.
Expected result:
- Timestamps are strictly increasing.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-22-005 - Test data cleanup
Priority: P2 | Role: admin
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Run `python test_helper.py cleanup --manual-test`.
Expected result:
- Returns exact count deleted, leaves real data intact.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`
### TC-22-006 - No orphan pending
Priority: P2 | Role: system
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Check pending collection after expiry.
Expected result:
- No documents older than expiry time.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.pending_complaints.find({otp_expires_at: {$lt: new Date()}})`

### TC-22-007 - Ticket ID format
Priority: P1 | Role: system
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Run regex check in mongosh.
Expected result:
- All ticket IDs are exactly 12 digits.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-22-008 - Staff zones format
Priority: P2 | Role: system
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Check DB staff.
Expected result:
- Zones are arrays of strings matching categories.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-22-009 - Orphan users
Priority: P3 | Role: system
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Check DB.
Expected result:
- No complaints assigned to non-existent technician IDs.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.pending_complaints.find({otp_expires_at: {$lt: new Date()}})`
