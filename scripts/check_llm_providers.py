#!/usr/bin/env python3
"""LLM Provider Diagnostic Checker.

Tests connectivity and logging for configured LLM providers.

Usage:
    PYTHONPATH=. python3 scripts/check_llm_providers.py
"""

import asyncio
from backend.app.config import settings
from backend.app.services.llm_client import (
    AnthropicLLMClient,
    GeminiLLMClient,
    OpenAILLMClient,
    GrokLLMClient,
    MockLLMClient
)
from backend.app.services.llm_router import llm_router


async def main():
    print("=" * 70)
    print("MNNIT Network Portal - LLM Provider Connection Diagnostic Tool")
    print("=" * 70)

    providers_to_test = [
        ("Google Gemini", settings.GEMINI_API_KEY, lambda: GeminiLLMClient(settings.GEMINI_API_KEY, settings.GEMINI_MODEL)),
        ("OpenAI", settings.OPENAI_API_KEY, lambda: OpenAILLMClient(settings.OPENAI_API_KEY, settings.OPENAI_MODEL)),
        ("xAI Grok", settings.GROK_API_KEY, lambda: GrokLLMClient(settings.GROK_API_KEY, settings.GROK_MODEL)),
        ("Anthropic Claude", settings.LLM_API_KEY, lambda: AnthropicLLMClient(settings.LLM_API_KEY, settings.LLM_MODEL_CHAT)),
        ("Mock Fallback", "ALWAYS_ACTIVE", lambda: MockLLMClient()),
    ]

    for name, key, factory in providers_to_test:
        if not key:
            print(f"[-] {name:16s} : SKIPPED (API key missing in .env)")
            continue

        try:
            client = factory()
            res = await client.guard_and_classify("My hostel Wi-Fi keeps disconnecting.")
            print(f"[+] {name:16s} : SUCCESS  | Guard result: {res}")
        except Exception as e:
            e_type = type(e).__name__
            print(f"[!] {name:16s} : FAILED   | Error ({e_type}): {e or repr(e)}")

    print("\n", sustained_bar := "=" * 70)
    print("TESTING MULTI-PROVIDER ROUTER FALLBACK EXECUTION:")
    print("=" * 70)
    router_res = await llm_router.guard_and_classify("Hostel Wi-Fi issue")
    print(f"Router Guard Result: {router_res}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
