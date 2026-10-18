"""Unified LLM Router and multi-provider fallback orchestrator.

Iterates through LLM_PROVIDER_ORDER (e.g., gemini -> openai -> grok -> anthropic -> mock),
catching errors/rate-limits/connection issues, logging fallback events, and returning
responses from the first available provider.
"""

import logging
from typing import Dict, Any, List
from backend.app.config import settings
from backend.app.services.llm_client import (
    LLMClient,
    GeminiLLMClient,
    OpenAILLMClient,
    GrokLLMClient,
    AnthropicLLMClient,
    MockLLMClient
)

logger = logging.getLogger("llm_router")
logging.basicConfig(level=logging.INFO)


class LLMRouter:
    """Orchestrates multi-provider LLM calls with automatic failover."""

    def __init__(self):
        self.providers: Dict[str, LLMClient] = {}
        self._init_providers()

    def _init_providers(self):
        """Initializes client instances if API keys are configured."""
        if settings.GEMINI_API_KEY:
            self.providers["gemini"] = GeminiLLMClient(
                api_key=settings.GEMINI_API_KEY,
                model=settings.GEMINI_MODEL
            )
        if settings.OPENAI_API_KEY:
            self.providers["openai"] = OpenAILLMClient(
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_MODEL
            )
        if settings.GROK_API_KEY:
            self.providers["grok"] = GrokLLMClient(
                api_key=settings.GROK_API_KEY,
                model=settings.GROK_MODEL
            )
        if settings.LLM_API_KEY:
            self.providers["anthropic"] = AnthropicLLMClient(
                api_key=settings.LLM_API_KEY
            )

        # Mock fallback is always available
        self.providers["mock"] = MockLLMClient()

    def get_configured_providers(self) -> List[LLMClient]:
        """Returns ordered list of active LLM clients per LLM_PROVIDER_ORDER."""
        ordered = []
        for name in settings.provider_list:
            if name in self.providers:
                ordered.append(self.providers[name])

        if not any(isinstance(p, MockLLMClient) for p in ordered):
            ordered.append(self.providers["mock"])

        return ordered

    async def guard_and_classify(self, user_message: str) -> Dict[str, Any]:
        """Runs guard and classification with multi-provider fallback."""
        clients = self.get_configured_providers()
        for client in clients:
            try:
                res = await client.guard_and_classify(user_message)
                logger.info(f"[LLMRouter] guard_and_classify served by provider: {client.provider_name}")
                return res
            except Exception as e:
                logger.warning(f"[LLMRouter] Provider {client.provider_name} failed guard_and_classify: {str(e)}. Falling back...")

        # Ultimate fallback to mock
        return await self.providers["mock"].guard_and_classify(user_message)

    async def generate_answer(
        self,
        system_prompt: str,
        user_message: str,
        history: List[Dict[str, str]]
    ) -> str:
        """Generates answer with multi-provider fallback."""
        clients = self.get_configured_providers()
        for client in clients:
            try:
                res = await client.generate_answer(system_prompt, user_message, history)
                logger.info(f"[LLMRouter] generate_answer served by provider: {client.provider_name}")
                return res
            except Exception as e:
                logger.warning(f"[LLMRouter] Provider {client.provider_name} failed generate_answer: {str(e)}. Falling back...")

        return await self.providers["mock"].generate_answer(system_prompt, user_message, history)

    async def summarize_transcript(self, transcript_text: str) -> Dict[str, Any]:
        """Summarizes transcript with multi-provider fallback."""
        clients = self.get_configured_providers()
        for client in clients:
            try:
                res = await client.summarize_transcript(transcript_text)
                logger.info(f"[LLMRouter] summarize_transcript served by provider: {client.provider_name}")
                return res
            except Exception as e:
                logger.warning(f"[LLMRouter] Provider {client.provider_name} failed summarize_transcript: {str(e)}. Falling back...")

        return await self.providers["mock"].summarize_transcript(transcript_text)


# Global singleton instance
llm_router = LLMRouter()
