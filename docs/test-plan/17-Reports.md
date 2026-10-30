# Area 17: Reports

### TC-17-001 - Score computation
Priority: P2 | Role: system
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Calculate expected score manually based on 2 resolved, 1 rated 5-star.
Expected result:
- Matches leaderboard exactly.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.users.find({}, {rating: 1, resolved_count: 1})`

### TC-17-002 - Unrated technicians
Priority: P3 | Role: manager
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. View leaderboard.
Expected result:
- Unrated techs show N/A or 0 correctly.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.users.find()`

### TC-17-003 - Report totals by status
Priority: P2 | Role: manager
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. View report totals.
Expected result:
- Matches DB exactly (e.g. 5 open, 2 closed).
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.users.find()`

### TC-17-004 - IST day boundaries
Priority: P3 | Role: system
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Create complaint at 23:59 IST and 00:01 IST.
Expected result:
- They appear in different 'Today' report days.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.users.find({}, {rating: 1, resolved_count: 1})`
### TC-17-005 - Leaderboard weighting
Priority: P2 | Role: manager
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Check weighted score for 5 resolved (4.0 avg) vs 50 resolved (4.0 avg).
Expected result:
- 50 resolved has higher final score (using formula in logic).
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.users.find()`

### TC-17-006 - Problem type breakdown
Priority: P2 | Role: manager
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Check report 'By Problem Type'.
Expected result:
- Counts exactly match DB grouped by problem type.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.users.find()`

### TC-17-007 - Location breakdown
Priority: P2 | Role: manager
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Check report 'By Location'.
Expected result:
- Counts exactly match DB grouped by location.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.users.find()`

### TC-17-008 - Report pagination/scrolling
Priority: P3 | Role: manager
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. View report with many locations.
Expected result:
- Scrolls correctly within the widget.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______


### TC-17-009 - Ratings optional feedback
Priority: P3 | Role: manager
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Check if feedback text from student is visible to manager/admin.
Expected result:
- Visible in the correct UI view.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.users.find()`

### TC-17-010 - Unrated hidden from formula errors
Priority: P3 | Role: system
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Ensure unrated techs don't break leaderboard with division by zero.
Expected result:
- Leaderboard renders cleanly.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.users.find({}, {rating: 1, resolved_count: 1})`

### TC-17-011 - Weekly report exact boundaries
Priority: P2 | Role: manager
Tags: [MANUAL ONLY]
Requirement: Generic
Preconditions: System is running.
Test data: None
Steps:
1. Run weekly report on Monday 00:05.
Expected result:
- Covers exact correct 7-day previous window.
Result: - [ ] PASS  - [ ] FAIL  - [ ] BLOCKED   Notes: ______

Verify in database: `db.users.find()`
