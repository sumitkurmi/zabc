# Area 18: Assets

### TC-18-001 - Create asset
Priority: P1 | Role: admin
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Create router asset.
Expected result:
- Created successfully.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-18-002 - Duplicate serial rejected
Priority: P2 | Role: admin
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Create asset with existing serial number.
Expected result:
- Validation error.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-18-003 - Status rules (faulty to in-use)
Priority: P2 | Role: admin
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Try to move 'Faulty' directly to 'In-Use' via API without maintenance record.
Expected result:
- Rejected.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-18-004 - Maintenance record
Priority: P2 | Role: admin
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Add maintenance record to asset.
Expected result:
- History updated, status changes to In-Use.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-18-005 - Retire vs Delete
Priority: P2 | Role: admin
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Delete asset.
Expected result:
- Actually marks as 'Retired' in DB, soft delete.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-18-006 - Locations tree delete blocked
Priority: P2 | Role: admin
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Try to delete location containing assets.
Expected result:
- Deletion blocked.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-18-007 - Switch ports bulk create
Priority: P2 | Role: admin
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Bulk create 24 ports for a switch.
Expected result:
- 24 port records created.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-18-008 - Port mapping to room
Priority: P2 | Role: admin
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Map port 5 to Room A-1.
Expected result:
- Mapping saved.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-18-009 - Restock
Priority: P1 | Role: admin
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Add 10 RJ45 connectors to stock.
Expected result:
- Stock quantity increases.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-18-010 - Stock issue
Priority: P1 | Role: technician
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Tech issues 2 RJ45 for a complaint.
Expected result:
- Stock decreases by 2, transaction logged.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-18-011 - Stock never below zero
Priority: P2 | Role: admin
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Issue more than available.
Expected result:
- Rejected.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-18-012 - Low stock filter
Priority: P3 | Role: manager
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Filter stock by 'Low Stock'.
Expected result:
- Shows only items below threshold.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.network_assets.find().sort({created_at: -1}).limit(1)`

### TC-18-013 - CSV export
Priority: P3 | Role: admin
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Click export CSV.
Expected result:
- File downloads with correct headers.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.network_assets.find().sort({created_at: -1}).limit(1)`

### TC-18-014 - Read-only for manager
Priority: P2 | Role: manager
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Manager tries to edit stock via API.
Expected result:
- 403 Forbidden.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`
### TC-18-015 - Edit asset
Priority: P2 | Role: admin
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Edit asset name and location.
Expected result:
- Changes saved correctly.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-18-016 - Filter assets by status
Priority: P2 | Role: admin
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Filter list by 'Faulty'.
Expected result:
- Only faulty assets shown.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.network_assets.find().sort({created_at: -1}).limit(1)`

### TC-18-017 - Search by MAC address
Priority: P2 | Role: admin
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Search by partial MAC.
Expected result:
- Returns matching assets.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.network_assets.find().sort({created_at: -1}).limit(1)`

### TC-18-018 - Warranty expiring report
Priority: P2 | Role: admin
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. View warranty report.
Expected result:
- Shows assets with warranty expiring within 30 days.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.network_assets.find().sort({created_at: -1}).limit(1)`

### TC-18-019 - Stock transactions list
Priority: P2 | Role: admin
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. View history of stock item.
Expected result:
- Shows all issues and restocks with timestamps and actors.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.network_assets.find().sort({created_at: -1}).limit(1)`

### TC-18-020 - Stock issued shows on complaint
Priority: P2 | Role: admin
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. View complaint detail that used stock.
Expected result:
- Shows 'Items Used' with quantity and name.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.network_assets.find().sort({created_at: -1}).limit(1)`
