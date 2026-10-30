# Area 02: Complaint form

### TC-02-001 - Form happy path
Priority: P1 | Role: student
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Fill all required fields with valid data. Submit.
Expected result:
- Moves to OTP verification step.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.outbox.find().sort({created_at: -1}).limit(5)`

### TC-02-002 - Location list check
Priority: P2 | Role: student
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Open location dropdown.
Expected result:
- Dropdown contains the exact locations defined in seed_categories.py.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______


### TC-02-003 - Time-from before Time-to
Priority: P2 | Role: student
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Set availability 'From' later than 'To'.
Expected result:
- Validation error prevents submission.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `python3 scripts/testing/test_helper.py show-complaint 123456789012`

### TC-02-004 - Mobile format validation
Priority: P2 | Role: student
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Enter '123' in mobile field.
Expected result:
- Validation error for invalid mobile format.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______


### TC-02-005 - Honeypot field
Priority: P3 | Role: student
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Inspect element, fill honeypot field, submit.
Expected result:
- Form rejected or silently ignored as bot.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `python3 scripts/testing/test_helper.py show-complaint 123456789012`

### TC-02-006 - Character limits
Priority: P2 | Role: student
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Paste 2000 chars into description.
Expected result:
- Input truncated or validation error shown.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `python3 scripts/testing/test_helper.py show-complaint 123456789012`

### TC-02-007 - Form keeps values while chat panel opens
Priority: P2 | Role: student
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Fill form, open chatbot panel.
Expected result:
- Form values are retained.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `python3 scripts/testing/test_helper.py show-complaint 123456789012`

### TC-02-008 - Success page
Priority: P1 | Role: student
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Complete OTP verification.
Expected result:
- Redirected to success page showing 12-digit ticket ID.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.outbox.find().sort({created_at: -1}).limit(5)`

### TC-02-009 - Required fields validation
Priority: P2 | Role: student
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Submit empty form.
Expected result:
- All required fields show validation errors.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `python3 scripts/testing/test_helper.py show-complaint 123456789012`

### TC-02-010 - Problem type list
Priority: P2 | Role: student
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Check problem type dropdown.
Expected result:
- Contains exactly the 5 problem types.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

### TC-02-011 - Hostel room exact match
Priority: P3 | Role: student
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Type 'SVBH 101' in room.
Expected result:
- Matches location 'SVBH' properly if autocomplete used.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `python3 scripts/testing/test_helper.py show-complaint 123456789012`

### TC-02-012 - Empty description fallback
Priority: P3 | Role: student
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Try to bypass frontend required check for description.
Expected result:
- Backend validator catches it (422 error).
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `python3 scripts/testing/test_helper.py show-complaint 123456789012`
