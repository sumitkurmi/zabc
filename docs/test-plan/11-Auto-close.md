# Area 11: Auto-close

### TC-11-001 - Auto-close executes
Priority: P1 | Role: admin
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Use helper to age complaint 4 days. Run auto-close script.
Expected result:
- Complaint status moves to Closed.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-11-002 - System note
Priority: P2 | Role: admin
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Check DB history of auto-closed complaint.
Expected result:
- History shows 'System' auto-closed it.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-11-003 - Emails queued
Priority: P2 | Role: admin
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Check outbox after auto-close.
Expected result:
- Closed and rating emails are queued.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.outbox.find().sort({created_at: -1}).limit(5)`

### TC-11-004 - Not closed before time
Priority: P2 | Role: admin
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Age complaint 1 day. Run auto-close.
Expected result:
- Complaint remains in Student Confirmation.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-11-005 - Running twice safe
Priority: P3 | Role: admin
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Run auto-close script twice.
Expected result:
- No duplicates or errors.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`
