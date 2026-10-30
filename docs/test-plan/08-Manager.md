# Area 08: Manager

### TC-08-001 - Dashboard counts
Priority: P1 | Role: manager
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. View manager dashboard.
Expected result:
- Counts match DB exactly.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-08-002 - Lists and filters
Priority: P1 | Role: manager
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. View Open unassigned list. Filter by Priority.
Expected result:
- List filters correctly.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.users.find()`

### TC-08-003 - Search by ticket
Priority: P2 | Role: manager
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Search specific 12-digit ticket ID.
Expected result:
- Exact match returned.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.users.find()`

### TC-08-004 - Assign dialog hints
Priority: P2 | Role: manager
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Click assign on a complaint.
Expected result:
- Dialog shows available techs, their open counts, and zone hints.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______


### TC-08-005 - Reassign allowed status
Priority: P2 | Role: manager
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Reassign 'In Progress' complaint.
Expected result:
- Reassigned successfully.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-08-006 - Reassign refused status
Priority: P2 | Role: manager
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Try to reassign 'Closed' complaint via API.
Expected result:
- Reassign rejected.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-08-007 - Availability toggle
Priority: P2 | Role: manager
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Toggle availability of a tech with open complaints.
Expected result:
- Warning shown to manager.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.users.find()`

### TC-08-008 - Reports accuracy
Priority: P2 | Role: manager
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. View today/weekly reports.
Expected result:
- Numbers match DB aggregate queries exactly.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.users.find()`

### TC-08-009 - Leaderboard sorting
Priority: P3 | Role: manager
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. View leaderboard.
Expected result:
- Sorted by rating/resolved count correctly.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.users.find()`

### TC-08-010 - Manager role isolation
Priority: P2 | Role: manager
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Manager tries to view junk or staff settings.
Expected result:
- Access denied.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`
### TC-08-011 - Sort lists by priority
Priority: P2 | Role: manager
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Click priority column header.
Expected result:
- List sorts High to Low.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.users.find()`

### TC-08-012 - Filter by specific location
Priority: P2 | Role: manager
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Select 'SVBH' in location filter.
Expected result:
- Only SVBH complaints shown.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.users.find()`

### TC-08-013 - View closed detail
Priority: P3 | Role: manager
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Click a closed complaint.
Expected result:
- Detail page loads, all actions disabled except view.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.users.find()`

### TC-08-014 - Manager unassign
Priority: P2 | Role: manager
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Click unassign on Assigned complaint.
Expected result:
- Moves back to Classified, tech unlinked.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`
