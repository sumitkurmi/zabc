# MNNIT Network Complaint Portal - Master Test Plan

## Purpose
This document and its linked area files form the complete manual test suite for the MNNIT Network Complaint Portal. The project owner will run these tests manually step-by-step to verify all functionality, including AI features, student form, staff roles, reports, and asset management.

## How to use this checklist
1. Follow the **Setup Instructions** carefully.
2. Read the **Execution Order** to plan your testing sessions.
3. Open the linked area markdown files in an editor that supports checklist ticking (like VS Code or Obsidian).
4. Run each test step exactly as described.
5. Tick the checkboxes: `[ ] PASS`, `[ ] FAIL`, or `[ ] BLOCKED`.
6. Add notes if a test fails or is blocked.
7. Report any discrepancies in the `DEFECT LOG` or `docs/test-plan/OBSERVED_ISSUES.md`.

## Setup Instructions (Copy-Paste Steps)

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- MongoDB running locally on port 27017

### Environment Setup
Create the `.env` file for testing:
`cp .env.example .env`

Ensure these critical values are set in `.env`:
- `AGENT_ENABLED=true`
- `AGENT_ASSIGNMENT_MODE=auto`
- `AGENT_USE_LLM=true`
- `GEMINI_API_KEY=your_real_gemini_key`
- `EMAIL_BACKEND=console`
- `ALLOWED_EMAIL_DOMAIN=mnnit.ac.in`
- `AUTO_CLOSE_DAYS=3`
- `PUBLIC_BASE_URL=http://localhost:8000`
- `RATE_LIMIT_LOGIN=5/minute`
- `OTP_EXPIRY_MINUTES=5`

### Checking Real Gemini Usage
Check the terminal running the backend. When an AI feature triggers, look for:
- A log line like `INFO: Using LLM Provider: gemini, Model: gemini-1.5-flash`
- In MongoDB, run `db.agent_runs.find().sort({created_at: -1}).limit(1)` and check the `provider` and `model` fields.
- Run the provider check script: `PYTHONPATH=. python3 backend/tests/test_gemini.py`

### Prepare Database and Test Data
Start MongoDB if not already running.
Run these commands in order from the repository root:

`export PYTHONPATH=.`
`python3 scripts_db/create_indexes.py`
`python3 scripts_db/create_network_assets_indexes.py`
`python3 scripts_db/seed_categories.py`
`python3 scripts_db/seed_demo_chats.py`
`python3 scripts_db/seed_network_assets_demo.py`
`python3 scripts/create_admin.py admin admin123`

#### Test Accounts Seeded
| Role | Username | Password | Zones |
|---|---|---|---|
| Admin | admin | admin123 | N/A |
| Manager | manager1 | mnnit123 | All |
| Technician | tech1 | mnnit123 | SVBH, Tagore |
| Technician | tech2 | mnnit123 | Tilak, Patel |

*(Note: Check the seed script output. If accounts differ, create them manually using the Admin panel).*

#### Extra Manual Data to Prepare
Create these files for testing the RAG upload feature:
1. `unique_fact.txt`: A text file containing: "The secret MNNIT networking switch is located in the basement of the library behind the old servers."
2. `valid_doc.pdf`: A small, valid PDF document.
3. `valid_doc.docx`: A small, valid DOCX document.
4. `oversized.pdf`: A file larger than 5MB.
5. `wrong_type.jpg`: An image file.

Create test student email addresses in your mind to use in the form:
- `valid1@mnnit.ac.in`
- `valid2@mnnit.ac.in`
- `wrong@gmail.com`

### Running the Application

**Backend:**
`export PYTHONPATH=.`
`uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload &`

**Frontend:**
`cd frontend`
`npm install --legacy-peer-deps`
`npm run dev &`
Access at `http://localhost:5173` (Vite default) or `http://localhost:8000` (if frontend is built and served via FastAPI). For testing API directly, go to `http://localhost:8000/docs`.

### Observing Emails & Logs
- **Console Emails:** Look at the terminal running the `uvicorn` backend. OTPs and notifications will print there.
- **SMTP Emails:** Set `EMAIL_BACKEND=smtp` and configure `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` in `.env`.
- **Logs:** Printed in the backend terminal.
- **FastAPI Docs:** Open `http://localhost:8000/docs`. Click "Authorize", paste a JWT token obtained from logging in, to test APIs directly.

### Resetting Test Data
To wipe the database and start over:
`mongosh localhost:27017/network_portal --eval "db.dropDatabase()"`
Then rerun the data preparation scripts.

---

## Execution Order and Time Estimates
Run the tests in this order to ensure prerequisites are met for later stages.
1. Area 01: Setup and health (~5 mins)
2. Area 06: Authentication and roles (~15 mins)
3. Area 07: Admin (~20 mins)
4. Area 18: Network assets and stock (~30 mins)
5. Area 02 & 03: Complaint form & Email OTP (~30 mins)
6. Area 04 & 05: Chatbot & RAG behaviour (~45 mins)
7. Area 14: AI agents (~60 mins)
8. Area 08 & 09: Manager & Technician (~40 mins)
9. Area 10 & 13: Student confirmation & Lifecycle (~20 mins)
10. Area 11 & 12: Auto-close & Emails (~25 mins)
11. Area 15 & 16: Closed complaints to RAG & Junk (~15 mins)
12. Area 17: Ratings, leaderboard, reports (~15 mins)
13. Area 19 & 20: Security & Responsive (~30 mins)
14. Area 21 & 22: Resilience & Data checks (~20 mins)
**Total Estimated Time:** ~6 hours

---

## 20-Minute Smoke Test
Run these critical test cases before any demo.
1. `TC-01-001`: System starts without errors.
2. `TC-06-001`: Admin login works.
3. `TC-02-001`: Student form happy path.
4. `TC-03-001`: Email OTP verify happy path.
5. `TC-04-001`: Chatbot basic troubleshooting.
6. `TC-14-001`: AI Classification works correctly.
7. `TC-14-007`: AI Assignment auto-assigns.
8. `TC-09-001`: Technician sees assigned complaint.
9. `TC-09-002`: Technician resolves complaint.
10. `TC-10-001`: Student confirms and closes.
11. `TC-18-001`: Create network asset.
12. `TC-18-010`: Issue stock.
13. `TC-08-001`: Manager dashboard counts are correct.
14. `TC-07-001`: Admin create staff.
15. `TC-05-001`: RAG ingestion works.

---

## Results Summary
| Area | Total | Passed | Failed | Blocked |
|---|---|---|---|---|
| 01 Setup | 5 | | | |
| 02 Form | 10 | | | |
| 03 OTP | 15 | | | |
| 04 Chatbot | 15 | | | |
| 05 RAG | 10 | | | |
| 06 Auth | 10 | | | |
| 07 Admin | 15 | | | |
| 08 Manager | 15 | | | |
| 09 Technician | 10 | | | |
| 10 Confirmation | 10 | | | |
| 11 Auto-close | 5 | | | |
| 12 Emails | 10 | | | |
| 13 Lifecycle | 10 | | | |
| 14 AI Agents | 20 | | | |
| 15 RAG Logs | 5 | | | |
| 16 Junk | 5 | | | |
| 17 Reports | 10 | | | |
| 18 Assets | 20 | | | |
| 19 Security | 15 | | | |
| 20 Responsive | 10 | | | |
| 21 Resilience | 5 | | | |
| 22 Data Checks | 5 | | | |
| **TOTAL** | **~235** | | | |

---

## Defect Log Template
Copy this template into `OBSERVED_ISSUES.md` when you find bugs.
```markdown
### Bug: [Short Description]
- **Area:**
- **Steps to reproduce:**
- **Expected:**
- **Observed:**
- **Suggested Fix / Notes:**
```

---
## Area Files
- [01-Setup.md](test-plan/01-Setup.md)
- [02-Form.md](test-plan/02-Form.md)
- [03-OTP.md](test-plan/03-OTP.md)
- [04-Chatbot.md](test-plan/04-Chatbot.md)
- [05-RAG.md](test-plan/05-RAG.md)
- [06-Auth.md](test-plan/06-Auth.md)
- [07-Admin.md](test-plan/07-Admin.md)
- [08-Manager.md](test-plan/08-Manager.md)
- [09-Technician.md](test-plan/09-Technician.md)
- [10-Confirmation.md](test-plan/10-Confirmation.md)
- [11-Auto-close.md](test-plan/11-Auto-close.md)
- [12-Emails.md](test-plan/12-Emails.md)
- [13-Lifecycle.md](test-plan/13-Lifecycle.md)
- [14-AIAgents.md](test-plan/14-AIAgents.md)
- [15-RAGLogs.md](test-plan/15-RAGLogs.md)
- [16-Junk.md](test-plan/16-Junk.md)
- [17-Reports.md](test-plan/17-Reports.md)
- [18-Assets.md](test-plan/18-Assets.md)
- [19-Security.md](test-plan/19-Security.md)
- [20-Responsive.md](test-plan/20-Responsive.md)
- [21-Resilience.md](test-plan/21-Resilience.md)
- [22-DataChecks.md](test-plan/22-DataChecks.md)
