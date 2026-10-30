# Area 03: Email OTP

### TC-03-001 - OTP happy path
Priority: P1 | Role: student
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Submit form, enter correct OTP from console.
Expected result:
- Complaint created, success page shown.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.outbox.find().sort({created_at: -1}).limit(5)`

### TC-03-002 - Wrong domain email
Priority: P2 | Role: student
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Enter wrong@gmail.com.
Expected result:
- Validation error: 'Email must end with @mnnit.ac.in'
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.outbox.find().sort({created_at: -1}).limit(5)`

### TC-03-003 - Uppercase email
Priority: P3 | Role: student
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Enter VALID@MNNIT.AC.IN.
Expected result:
- Accepted, converts to lowercase or verifies normally.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.outbox.find().sort({created_at: -1}).limit(5)`

### TC-03-004 - Subdomain email
Priority: P3 | Role: student
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Enter valid@cs.mnnit.ac.in.
Expected result:
- Rejected or accepted based on exact domain matching rules.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.outbox.find().sort({created_at: -1}).limit(5)`

### TC-03-005 - Two @ signs
Priority: P2 | Role: student
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Enter a@@mnnit.ac.in.
Expected result:
- Validation error.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.pending_complaints.find({email: 'valid1@mnnit.ac.in'})`

### TC-03-006 - Wrong OTP
Priority: P1 | Role: student
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Enter 000000.
Expected result:
- Error message: 'Invalid OTP'.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.outbox.find().sort({created_at: -1}).limit(5)`

### TC-03-007 - Five wrong attempts
Priority: P2 | Role: student
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Enter wrong OTP 5 times.
Expected result:
- Request cancelled, return to form.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.outbox.find().sort({created_at: -1}).limit(5)`

### TC-03-008 - OTP expiry
Priority: P2 | Role: student
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Wait 5 minutes or use helper to expire OTP, then enter correct OTP.
Expected result:
- Error message: 'OTP expired'.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.outbox.find().sort({created_at: -1}).limit(5)`

### TC-03-009 - Resend cooldown
Priority: P2 | Role: student
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Click resend immediately after request.
Expected result:
- Button disabled or shows countdown.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.pending_complaints.find({email: 'valid1@mnnit.ac.in'})`

### TC-03-010 - Resend limit
Priority: P3 | Role: student
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Click resend multiple times.
Expected result:
- Blocked after limit reached.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.pending_complaints.find({email: 'valid1@mnnit.ac.in'})`

### TC-03-011 - Old OTP stops working
Priority: P2 | Role: student
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Request OTP, click resend. Enter first OTP.
Expected result:
- Error message: 'Invalid OTP' (first is invalidated).
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.outbox.find().sort({created_at: -1}).limit(5)`

### TC-03-012 - Rate limits
Priority: P2 | Role: student
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Submit form rapidly 6 times from same IP.
Expected result:
- Rate limit error shown (429).
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-03-013 - Change email keeps data
Priority: P3 | Role: student
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. At OTP step, click 'change email'.
Expected result:
- Returns to form with previous data populated.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.outbox.find().sort({created_at: -1}).limit(5)`

### TC-03-014 - Double click verification
Priority: P2 | Role: student
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Double click 'Verify' button quickly.
Expected result:
- Only one complaint created (check DB).
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.pending_complaints.find({email: 'valid1@mnnit.ac.in'})`

### TC-03-015 - Pending record cleanup
Priority: P3 | Role: student
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Let OTP expire. Check DB.
Expected result:
- Pending record is deleted or marked expired.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.outbox.find().sort({created_at: -1}).limit(5)`
### TC-03-016 - OTP sent via SMTP
Priority: P1 | Role: student
Tags: [NEEDS REAL EMAIL]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Set EMAIL_BACKEND=smtp. Submit form.
Expected result:
- OTP arrives in real inbox.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.outbox.find().sort({created_at: -1}).limit(5)`

### TC-03-017 - SMTP retry logic
Priority: P3 | Role: system
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. SMTP server drops connection mid-send.
Expected result:
- App retries silently or logs error.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.pending_complaints.find({email: 'valid1@mnnit.ac.in'})`
