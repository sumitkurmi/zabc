# Observed Issues

### Bug: Missing API test file `test_gemini.py`
- **Area:** Testing / Setup
- **Steps to reproduce:** Run `PYTHONPATH=. python3 backend/tests/test_gemini.py` as stated in README.
- **Expected:** Script should run and evaluate Gemini setup.
- **Observed:** File does not exist in `backend/tests/`.
- **Suggested Fix / Notes:** Update README to correct test name (`eval_chatbot.py`?) or add the missing script.

### Bug: `npm run dev` long running execution
- **Area:** Setup instructions
- **Steps to reproduce:** Instructions say `npm run dev`, which is blocking.
- **Expected:** Setup instructions should mention running it in background or in a separate terminal.
- **Observed:** Might block execution if user doesn't know to background it.
- **Suggested Fix / Notes:** Update instructions in `TEST_PLAN.md` to note running in a separate terminal.
