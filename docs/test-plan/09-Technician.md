# Area 09: Technician

### TC-09-001 - Own complaints only
Priority: P1 | Role: technician
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. View dashboard as tech1.
Expected result:
- Only tech1's complaints are shown.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-09-002 - Resolve happy path
Priority: P1 | Role: technician
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Resolve with diagnosis and solution.
Expected result:
- Status moves to Student Confirmation.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-09-003 - Resolve with stock
Priority: P2 | Role: technician
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Resolve and select a stock item.
Expected result:
- Stock quantity decreases in DB.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-09-004 - Over-quantity stock rejected
Priority: P2 | Role: technician
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Resolve with stock quantity > available.
Expected result:
- Rejected, rollback occurs (complaint status unchanged).
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-09-005 - Cannot resolve others
Priority: P2 | Role: technician
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Try to resolve tech2's complaint via API.
Expected result:
- 403 Forbidden or not found.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-09-006 - My ratings page
Priority: P3 | Role: technician
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. View My Ratings.
Expected result:
- Shows personal score and position.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `python3 scripts/testing/test_helper.py show-complaint 123456789012`

### TC-09-007 - Read-only network assets
Priority: P2 | Role: technician
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. View assets. Try to create asset via API.
Expected result:
- View works. Create rejected (403).
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`
### TC-09-008 - View history timeline
Priority: P2 | Role: technician
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Open complaint detail.
Expected result:
- Timeline view renders correct stages.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `python3 scripts/testing/test_helper.py show-complaint 123456789012`

### TC-09-009 - Chat transcript viewable
Priority: P2 | Role: technician
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Open complaint with linked chat.
Expected result:
- Full AI chat transcript visible to help tech.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-09-010 - Resolve without mandatory fields
Priority: P2 | Role: technician
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Submit resolution without diagnosis.
Expected result:
- Form validation blocks submission.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`
