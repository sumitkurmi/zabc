# Area 12: Emails

### TC-12-001 - Subject format
Priority: P2 | Role: admin
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Check outbox for any notification.
Expected result:
- Subject contains 12-digit ticket ID.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.outbox.find().sort({created_at: -1}).limit(5)`

### TC-12-002 - No tech mobile in student email
Priority: P2 | Role: admin
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Check 'assigned' email sent to student.
Expected result:
- Technician's mobile number is NOT present.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.outbox.find().sort({created_at: -1}).limit(5)`

### TC-12-003 - In-charge CC
Priority: P2 | Role: admin
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Check 'escalation' or 'delayed' email.
Expected result:
- Manager is CC'd correctly.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.outbox.find().sort({created_at: -1}).limit(5)`

### TC-12-004 - No CC on student emails
Priority: P2 | Role: admin
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Check 'received' email to student.
Expected result:
- No CC field present.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.outbox.find().sort({created_at: -1}).limit(5)`

### TC-12-005 - Retry and failure
Priority: P2 | Role: admin
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Break SMTP settings. Trigger email.
Expected result:
- Status goes to FAILED after retries.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.outbox.find().sort({created_at: -1}).limit(5)`

### TC-12-006 - OTP not in outbox
Priority: P3 | Role: admin
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Request OTP. Check outbox DB.
Expected result:
- OTP email is sent directly, not stored in outbox.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.outbox.find().sort({created_at: -1}).limit(5)`
### TC-12-007 - SMTP connection fail
Priority: P2 | Role: system
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Provide invalid SMTP port.
Expected result:
- Email fails, outbox marks FAILED.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.outbox.find().sort({created_at: -1}).limit(5)`

### TC-12-008 - All event triggers
Priority: P2 | Role: system
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Go through full lifecycle.
Expected result:
- Emails triggered at: Submitted, Assigned, Resolved, Closed, Rated.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.outbox.find().sort({created_at: -1}).limit(5)`

### TC-12-009 - Email layout
Priority: P3 | Role: student
Tags: [NEEDS REAL EMAIL]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. View email in client.
Expected result:
- Logo and MNNIT branding present and clear.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______


### TC-12-010 - Rating link present
Priority: P2 | Role: student
Tags: [NEEDS REAL EMAIL]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. View 'Closed' email.
Expected result:
- Contains link to rating page.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.outbox.find().sort({created_at: -1}).limit(5)`
