"""Checks that a Gemini API key works and that a given model is available to it.

Usage:
    python test_gemini.py                      # lists models, tests the first "flash" model
    python test_gemini.py <model-name>         # tests the model you use in your project

The key is read from the GEMINI_API_KEY (or GOOGLE_API_KEY) environment
variable, or from a .env file in the current folder. Model can also be set
with GEMINI_MODEL.
"""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
import socket
import time

BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

# What the common HTTP error codes usually mean for the Gemini API.
HINTS = {
    400: "Bad request. Often 'API key not valid' (wrong or malformed key) or an invalid model/parameter.",
    403: "Permission denied. The key is wrong, restricted, or the Generative Language API is not enabled for it.",
    404: "Model not found. The model name is wrong, retired, or not available to this key/region.",
    429: "Quota or rate limit reached. Wait a minute, or check your plan/billing and quota in Google AI Studio.",
    500: "Google server error. Try again later.",
    503: "Model overloaded or unavailable. Try again later.",
}


def load_env_file(path: str = ".env") -> None:
    """Load KEY=VALUE lines from a .env file into os.environ (existing variables win)."""
    env_path = Path(path)
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        os.environ.setdefault(name.strip(), value.strip().strip('"').strip("'"))


def call_api(method: str, url: str, api_key: str, body: dict | None = None, timeout: int = 90):
    """Send one request. Returns (status_code, parsed_json). status is None if there was no reply."""
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8", errors="replace")
        try:
            return error.code, json.loads(raw)
        except ValueError:
            return error.code, {"raw": raw}
    except (TimeoutError, socket.timeout):
        # The connection worked but Google never answered in time.
        return None, {"error": f"No response within {timeout} seconds"}
    except urllib.error.URLError as error:
        return None, {"error": str(error.reason)}

def explain_failure(status, payload) -> None:
    """Print the exact error from Google plus a plain-language hint."""
    print(f"   FAILED (HTTP {status})")
    print("   Google says:", json.dumps(payload.get("error", payload), indent=2))
    if status in HINTS:
        print("   Hint:", HINTS[status])
    if status is None:
        print("   Hint: No reply at all. The model may be slow or overloaded, or the network is blocking the response.") 


def main() -> None:
    load_env_file()
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        sys.exit("No key found. Set GEMINI_API_KEY (environment variable or .env file).")
    print(f"Using key ending in ...{api_key[-4:]}")

    wanted_model = (sys.argv[1] if len(sys.argv) > 1 else os.getenv("GEMINI_MODEL", "")).replace("models/", "")

    # Step 1: ask Google which models this key can see. This also validates the key.
    print("\n1) Checking the key and listing models...")
    status, payload = call_api("GET", f"{BASE_URL}/models?pageSize=1000", api_key)
    if status != 200:
        explain_failure(status, payload)
        sys.exit(1)
    usable = sorted(
        m["name"].replace("models/", "")
        for m in payload.get("models", [])
        if "generateContent" in m.get("supportedGenerationMethods", [])
    )
    print(f"   Key is valid. {len(usable)} models support text generation:")
    for name in usable:
        print("    -", name)

    # Step 2: is the model you want in that list?
    if not wanted_model:
        flash = [m for m in usable if "flash" in m]
        if not flash:
            sys.exit("No model name given and no 'flash' model found. Pass one as an argument.")
        wanted_model = flash[0]
        print(f"\nNo model given, so testing: {wanted_model}")
    print(f"\n2) Is '{wanted_model}' available to this key?")
    if wanted_model in usable:
        print("   Yes, it is in the list.")
    else:
        print("   NO. It is not in the list above. Use one of the listed names in your project.")

    # Step 3: send a real prompt, because a model can be listed and still be rate limited.
    print(f"\n3) Sending a test prompt to '{wanted_model}'...")
    started = time.time()  # must be set BEFORE the request is sent
    status, payload = call_api(
        "POST",
        f"{BASE_URL}/models/{wanted_model}:generateContent",
        api_key,
        {"contents": [{"parts": [{"text": "Reply with exactly: OK"}]}]},
    )
    print(f"   Took {time.time() - started:.1f} seconds")
    if status != 200:
        explain_failure(status, payload)
        sys.exit(1)
    try:
        reply = payload["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError):
        # e.g. the response was blocked or empty; show it so you can see why
        print("   Request succeeded but returned no text:", json.dumps(payload, indent=2))
        sys.exit(1)
    print(f"   SUCCESS. Model replied: {reply!r}")


if __name__ == "__main__":
    main()