# Area 19: Security

### TC-19-001 - NoSQL injection login
Priority: P1 | Role: system
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Login with username `{"$gt": ""}`.
Expected result:
- Rejected, validation error (Pydantic protects).
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-19-002 - Script in comment
Priority: P1 | Role: student
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Submit `<script>alert(1)</script>` in form.
Expected result:
- Sanitized or strictly rendered as text (React protects).
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-19-003 - Malicious file name
Priority: P2 | Role: admin
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Upload `../../../etc/passwd.pdf`.
Expected result:
- Filename sanitized, saved safely.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-19-004 - JWT tampering
Priority: P1 | Role: system
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Change payload `role` to `admin` and sign with random key.
Expected result:
- 401 Unauthorized (signature invalid).
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-19-005 - Reuse student link
Priority: P2 | Role: student
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Use token from one complaint to access another.
Expected result:
- 403 Forbidden or 404 (token bound to ticket ID).
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-19-006 - Rate limit check
Priority: P2 | Role: system
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Hit /login 20 times quickly.
Expected result:
- 429 Too Many Requests.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-19-007 - Secrets in API
Priority: P1 | Role: system
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Check /api/config or user endpoints.
Expected result:
- Password hashes, tokens, API keys NEVER returned.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-19-008 - CORS check
Priority: P2 | Role: system
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Make request from `evil.com` origin.
Expected result:
- Rejected by CORS policy.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `python3 scripts/testing/test_helper.py show-complaint 123456789012`

### TC-19-009 - HTTP error shapes
Priority: P3 | Role: system
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Trigger 500 error intentionally.
Expected result:
- Response is generic JSON, no stack trace leaked.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`
### TC-19-010 - File upload path traversal
Priority: P1 | Role: admin
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Upload file with name '../../test.txt'.
Expected result:
- Rejected or sanitized to safe name.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-19-011 - File upload MIME sniffing
Priority: P2 | Role: admin
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Upload .txt file containing executable binary.
Expected result:
- Rejected based on strict content type validation.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-19-012 - Excessive payload size
Priority: P2 | Role: system
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Send 10MB JSON to /login.
Expected result:
- 413 Payload Too Large or closed connection.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-19-013 - XSS in chat Markdown
Priority: P2 | Role: student
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Chat bot outputs `[Link](javascript:alert(1))`.
Expected result:
- Sanitized by ReactMarkdown, doesn't execute.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-19-014 - Missing auth header
Priority: P1 | Role: system
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Access protected API route without Authorization header.
Expected result:
- 401 Unauthorized.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-19-015 - Invalid auth scheme
Priority: P2 | Role: system
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Send header `Authorization: Basic ...`.
Expected result:
- 401 Unauthorized.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`
