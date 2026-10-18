"""LLM Provider API Connection Test Suite.

Tests connectivity and responses across configured LLM providers:
- Anthropic Claude
- Google Gemini
- OpenAI
- xAI Grok
- Mock Fallback

Usage:
    PYTHONPATH=. pytest backend/tests/test_llm_providers.py -v -s
    PYTHONPATH=. python3 backend/tests/test_llm_providers.py
"""

import asyncio
import os
import pytest
from backend.app.config import settings
from backend.app.services.llm_client import (
    AnthropicLLMClient,
    GeminiLLMClient,
    OpenAILLMClient,
    GrokLLMClient,
    MockLLMClient
)
from backend.app.services.llm_router import llm_router


@pytest.mark.asyncio
async def test_anthropic_api_connection():
    """Tests Anthropic Claude API connection if LLM_API_KEY is configured."""
    api_key = settings.LLM_API_KEY
    if not api_key:
        pytest.skip("LLM_API_KEY (Anthropic) not configured in environment")

    client = AnthropicLLMClient(api_key=api_key)
    res = await client.guard_and_classify("My hostel Wi-Fi connection keeps dropping.")
    assert "on_topic" in res
    assert res["on_topic"] is True

    answer = await client.generate_answer(
        system_prompt="You are a network assistant.",
        user_message="How do I reset my Wi-Fi?",
        history=[]
    )
    assert len(answer) > 0


@pytest.mark.asyncio
async def test_gemini_api_connection():
    """Tests Google Gemini API connection if GEMINI_API_KEY is configured."""
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        pytest.skip("GEMINI_API_KEY not configured in environment")

    client = GeminiLLMClient(api_key=api_key, model=settings.GEMINI_MODEL)
    res = await client.guard_and_classify("Cannot get an IP address from DHCP.")
    assert "on_topic" in res
    assert res["on_topic"] is True


@pytest.mark.asyncio
async def test_openai_api_connection():
    """Tests OpenAI API connection if OPENAI_API_KEY is configured."""
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        pytest.skip("OPENAI_API_KEY not configured in environment")

    client = OpenAILLMClient(api_key=api_key, model=settings.OPENAI_MODEL)
    res = await client.guard_and_classify("Browser shows proxy error port 8080.")
    assert "on_topic" in res


@pytest.mark.asyncio
async def test_grok_api_connection():
    """Tests xAI Grok API connection if GROK_API_KEY is configured."""
    api_key = settings.GROK_API_KEY
    if not api_key:
        pytest.skip("GROK_API_KEY not configured in environment")

    client = GrokLLMClient(api_key=api_key, model=settings.GROK_MODEL)
    res = await client.guard_and_classify("Wall LAN port is broken.")
    assert "on_topic" in res


@pytest.mark.asyncio
async def test_mock_llm_client():
    """Tests Mock fallback LLM client (always passes offline)."""
    client = MockLLMClient()
    res = await client.guard_and_classify("Wi-Fi is slow")
    assert res["on_topic"] is True


@pytest.mark.asyncio
async def test_orchestrated_llm_router():
    """Tests orchestrated LLMRouter fallback logic."""
    res = await llm_router.guard_and_classify("Hostel Wi-Fi issue")
    assert "on_topic" in res


if __name__ == "__main__":
    async def run_standalone():
        print("=" * 60)
        print("TESTING CONFIGURABLE LLM PROVIDER CONNECTIONS")
        print("=" * 60)

        providers_to_test = [
            ("Anthropic Claude", settings.LLM_API_KEY, lambda: AnthropicLLMClient(settings.LLM_API_KEY)),
            ("Google Gemini", settings.GEMINI_API_KEY, lambda: GeminiLLMClient(settings.GEMINI_API_KEY, settings.GEMINI_MODEL)),
            ("OpenAI", settings.OPENAI_API_KEY, lambda: OpenAILLMClient(settings.OPENAI_API_KEY, settings.OPENAI_MODEL)),
            ("xAI Grok", settings.GROK_API_KEY, lambda: GrokLLMClient(settings.GROK_API_KEY, settings.GROK_MODEL)),
            ("Mock Fallback", "ALWAYS_ACTIVE", lambda: MockLLMClient()),
        ]

        for name, key, factory in providers_to_test:
            if not key:
                print(f"[-] {name:16s} : SKIPPED (API Key missing in .env)")
                continue

            try:
                client = factory()
                res = await client.guard_and_classify("Hostel Wi-Fi is disconnecting")
                print(f"[+] {name:16s} : SUCCESS | Guard result: {res}")
            except Exception as e:
                print(f"[!] {name:16s} : FAILED  | Error: {e}")

        print("=" * 60)

    asyncio.run(run_standalone())
