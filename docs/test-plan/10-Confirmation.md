# Area 10: Confirmation

### TC-10-001 - Confirm solved
Priority: P1 | Role: student
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Click 'Solved' on confirmation link.
Expected result:
- Complaint status moves to Closed.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-10-002 - Confirm not solved
Priority: P1 | Role: student
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Click 'Not Solved'.
Expected result:
- Complaint reopens, assigned to same tech if active.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-10-003 - Used link
Priority: P2 | Role: student
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Click link again after confirming.
Expected result:
- Message: 'Already confirmed' or similar.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-10-004 - Expired link
Priority: P2 | Role: student
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Age complaint using helper, click link.
Expected result:
- Link expired message.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-10-005 - Rating submission
Priority: P1 | Role: student
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Submit 5-star rating with feedback after closing.
Expected result:
- Rating saved to DB, linked to tech.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-10-006 - Rating only once
Priority: P2 | Role: student
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Try to submit rating again via API.
Expected result:
- Rejected.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`
### TC-10-007 - Wrong purpose link
Priority: P2 | Role: student
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Use token meant for confirmation on rating endpoint.
Expected result:
- Rejected (token audience mismatch).
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-10-008 - Same tech reassignment
Priority: P2 | Role: system
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Confirm 'Not Solved'. Tech1 is still active.
Expected result:
- Reassigned to tech1 immediately.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-10-009 - Inactive tech reassignment
Priority: P2 | Role: system
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Confirm 'Not Solved'. Tech1 is now inactive.
Expected result:
- Status moves to Classified/Unassigned.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`
