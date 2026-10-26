# LLM Router & Gemini Diagnostic Guide

## Gemini Failure Analysis

| Reason | How to Check | Status |
| :--- | :--- | :--- |
| 1. Empty Exception Text | `str(e)` on timeouts/HTTP errors was empty | FIXED in this change |
| 2. Timeout Too Short | Hardcoded 15s timeout in `httpx.AsyncClient` | FIXED in this change |
| 3. Model Name Formatting | Model strings with `models/` prefix | FIXED in this change |
| 4. API Key Configuration | Checked `GEMINI_API_KEY` vs `GOOGLE_API_KEY` | FIXED in this change |
| 5. Request Format & Roles | Roles payload matching REST API schema | FIXED in this change |
| 6. Empty / Blocked Candidates | Checking `candidates` & `finishReason` | FIXED in this change |
| 7. Library Version Mismatch | Direct REST endpoint via `httpx` | FIXED in this change |
| 8. Network / Proxy Settings | `httpx.AsyncClient(trust_env=True)` | FIXED in this change |
| 9. JSON Parsing Failure | Stripping code fences before `json.loads` | FIXED in this change |

## Changes Made
- `backend/app/config.py` -> `Settings` -> Added `GEMINI_TIMEOUT: float = 60.0` configurable timeout option.
- `backend/app/services/llm_client.py` -> `GeminiLLMClient.__init__` -> Added `GOOGLE_API_KEY` fallback and cleaned `models/` prefix.
- `backend/app/services/llm_client.py` -> `GeminiLLMClient._call_gemini` -> Added 60s timeout, `trust_env=True`, HTTP body preview, and `finishReason` safety checks.
- `backend/app/services/llm_client.py` -> `GeminiLLMClient._parse_json_response` -> Added tolerant regex markdown fence stripping for JSON outputs.
- `backend/app/services/llm_router.py` -> `_init_providers` -> Added masked key logging (`...XXXX`) and provider model registration logs at startup.
- `backend/app/services/llm_router.py` -> `_format_exception` -> Added exception type, `repr(e)`, status code, and HTTP body preview logging.
- `backend/app/services/llm_router.py` -> `guard_and_classify` / `generate_answer` / `summarize_transcript` -> Added timer logging and `ALL REAL PROVIDERS FAILED - using mock answer` warning.
- `scripts/check_llm_providers.py` -> `main` -> Added CLI diagnostic script for testing provider API connectivity.

## Diagnostic Utility Usage
Run the diagnostic script from the repository root:
```bash
PYTHONPATH=. python3 scripts/check_llm_providers.py
```

### Interpreting Output
- `[+] Provider Name : SUCCESS` -> Provider is configured, active, and returned a valid guard classification response.
- `[-] Provider Name : SKIPPED` -> API key is missing in `.env`.
- `[!] Provider Name : FAILED | Error (Type): Details` -> Connection or API error occurred; inspect exception type, HTTP status, and response body preview.
