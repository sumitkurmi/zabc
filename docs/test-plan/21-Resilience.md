# Area 21: Resilience

### TC-21-001 - LLM fallback
Priority: P2 | Role: system
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Configure primary LLM to timeout.
Expected result:
- Falls back to secondary provider automatically.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-21-002 - All LLM fail
Priority: P2 | Role: system
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Break all API keys.
Expected result:
- Falls back to mock or rules engine.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-21-003 - Slow LLM no block
Priority: P2 | Role: system
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Simulate 10s LLM response.
Expected result:
- OTP verify returns success immediately, LLM runs in background task.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.outbox.find().sort({created_at: -1}).limit(5)`

### TC-21-004 - MongoDB restart
Priority: P2 | Role: system
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Stop MongoDB. Start MongoDB. Make request.
Expected result:
- App reconnects and serves request (Motor driver handles reconnect).
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-21-005 - Double submit protection
Priority: P2 | Role: student
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Click submit button 5 times rapidly.
Expected result:
- Only one network request made.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `python3 scripts/testing/test_helper.py show-complaint 123456789012`

### TC-21-006 - Long list performance
Priority: P3 | Role: manager
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Use helper to make 200 complaints. Load manager list.
Expected result:
- Loads in < 2 seconds, pagination works.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`
### TC-21-007 - Redis/Rate limiter fail open
Priority: P3 | Role: system
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Stop Redis (if used for rate limiting).
Expected result:
- App falls back to in-memory or degrades gracefully, login works.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `python3 scripts/testing/test_helper.py show-complaint 123456789012`

### TC-21-008 - Large DB scan
Priority: P2 | Role: system
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Run get_all_complaints with empty filters on 100k rows.
Expected result:
- Pagination limits query, doesn't crash server.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `python3 scripts/testing/test_helper.py show-complaint 123456789012`

### TC-21-009 - Background worker restart
Priority: P2 | Role: system
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Restart main server while worker is running.
Expected result:
- Worker graceful shutdown and resumes correctly on start.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`
