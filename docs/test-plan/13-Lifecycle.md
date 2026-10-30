# Area 13: Lifecycle

### TC-13-001 - Full path
Priority: P1 | Role: admin
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Track from Submitted -> Classified -> Assigned -> In Progress -> Student Confirmation -> Closed.
Expected result:
- History in DB records all transitions accurately.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-13-002 - Illegal transition
Priority: P2 | Role: admin
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Send API request to move Submitted -> Closed.
Expected result:
- Rejected by backend validation.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-13-003 - History append-only
Priority: P2 | Role: admin
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Try to PUT/edit a history entry via API.
Expected result:
- No route exists or request rejected.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-13-004 - Lifecycle stepper UI
Priority: P3 | Role: student
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. View tracking page.
Expected result:
- Stepper highlights correct stage.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `python3 scripts/testing/test_helper.py show-complaint 123456789012`
### TC-13-005 - Simultaneous actions
Priority: P2 | Role: system
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Two managers try to reassign at the exact same moment.
Expected result:
- One succeeds, the other gets 409 Conflict (Optimistic locking if implemented).
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.users.find()`

### TC-13-006 - Submitted to closed illegal
Priority: P1 | Role: admin
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Try to bypass workflow to Closed via API.
Expected result:
- Rejected by state machine validation.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-13-007 - Student info in history
Priority: P3 | Role: admin
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Check DB history.
Expected result:
- Actor type 'student' recorded for creation and rating.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-13-008 - System info in history
Priority: P3 | Role: admin
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Check DB history.
Expected result:
- Actor type 'system' recorded for AI classification/assignment.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-13-009 - Manager info in history
Priority: P3 | Role: admin
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Check DB history.
Expected result:
- Actor type 'manager' recorded for reassignment.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-13-010 - Technician info in history
Priority: P3 | Role: admin
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Check DB history.
Expected result:
- Actor type 'technician' recorded for resolution.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`
