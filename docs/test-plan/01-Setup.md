# Area 01: Setup and health

### TC-01-001 - Backend starts successfully
Priority: P1 | Role: admin
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Start backend, check no errors in logs. Open /docs and see Swagger UI.
Expected result:
- Swagger UI loads successfully, no startup errors.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-01-002 - Frontend starts successfully
Priority: P1 | Role: student
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Run npm run dev, open localhost:5173
Expected result:
- Homepage loads without console errors.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `python3 scripts/testing/test_helper.py show-complaint 123456789012`

### TC-01-003 - Agent status chip
Priority: P2 | Role: admin
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Look at the footer or header for the AI agent status chip.
Expected result:
- Chip shows 'Agent: Online' or similar, depending on settings.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-01-004 - Settings validation (Invalid Mode)
Priority: P2 | Role: admin
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Set AGENT_ASSIGNMENT_MODE=invalid in .env, start backend.
Expected result:
- Startup fails with a clear validation error about invalid assignment mode.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`

### TC-01-005 - Settings validation (Missing Key)
Priority: P2 | Role: admin
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Remove GEMINI_API_KEY from .env, set AGENT_USE_LLM=true, start backend.
Expected result:
- Startup behavior matches expected failure or warning for missing key.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`
### TC-01-006 - Database ping
Priority: P1 | Role: system
Tags: [VERIFIED BY AGENT]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Start application with wrong MongoDB URI.
Expected result:
- Application crashes on startup with connection error.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.agent_runs.find().sort({created_at: -1}).limit(1)`
