"""Unified LLM Router and multi-provider fallback orchestrator.

Iterates through LLM_PROVIDER_ORDER (e.g., gemini -> openai -> grok -> anthropic -> mock),
catching errors/rate-limits/connection issues, logging detailed diagnostic failover events,
and returning responses from the first available provider.
Integrates trace logging for individual LLM attempts.
"""

import time
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
from backend.app.utils.flow_trace import get_current_trace, DummyStepContext

logger = logging.getLogger("llm_router")
logging.basicConfig(level=logging.INFO)


class LLMRouter:
    """Orchestrates multi-provider LLM calls with automatic failover."""

    def __init__(self):
        self.providers: Dict[str, LLMClient] = {}
        self._init_providers()

    def _mask_key(self, key: str) -> str:
        """Returns masked API key showing only last 4 characters."""
        if not key:
            return "NOT_SET"
        return f"...{key[-4:]}" if len(key) >= 4 else "***"

    def _init_providers(self):
        """Initializes client instances if API keys are configured and logs diagnostic setup."""
        gemini_key = settings.GEMINI_API_KEY
        if gemini_key:
            self.providers["gemini"] = GeminiLLMClient(
                api_key=gemini_key,
                model=settings.GEMINI_MODEL
            )
            logger.info(f"[LLMRouter] Registered provider 'gemini' (model={settings.GEMINI_MODEL}, key={self._mask_key(gemini_key)})")

        openai_key = settings.OPENAI_API_KEY
        if openai_key:
            self.providers["openai"] = OpenAILLMClient(
                api_key=openai_key,
                model=settings.OPENAI_MODEL
            )
            logger.info(f"[LLMRouter] Registered provider 'openai' (model={settings.OPENAI_MODEL}, key={self._mask_key(openai_key)})")

        grok_key = settings.GROK_API_KEY
        if grok_key:
            self.providers["grok"] = GrokLLMClient(
                api_key=grok_key,
                model=settings.GROK_MODEL
            )
            logger.info(f"[LLMRouter] Registered provider 'grok' (model={settings.GROK_MODEL}, key={self._mask_key(grok_key)})")

        anthropic_key = settings.LLM_API_KEY
        if anthropic_key:
            self.providers["anthropic"] = AnthropicLLMClient(
                api_key=anthropic_key,
                model=settings.LLM_MODEL_CHAT
            )
            logger.info(f"[LLMRouter] Registered provider 'anthropic' (model={settings.LLM_MODEL_CHAT}, key={self._mask_key(anthropic_key)})")

        # Mock fallback is always registered
        self.providers["mock"] = MockLLMClient()
        logger.info("[LLMRouter] Registered fallback provider 'mock'")

    def get_configured_providers(self) -> List[LLMClient]:
        """Returns ordered list of active LLM clients per LLM_PROVIDER_ORDER."""
        ordered = []
        for name in settings.provider_list:
            if name in self.providers:
                ordered.append(self.providers[name])

        if not any(isinstance(p, MockLLMClient) for p in ordered):
            ordered.append(self.providers["mock"])

        return ordered

    def _format_exception(self, e: Exception) -> str:
        """Formats detailed exception description including type, repr, status code, and body preview."""
        e_type = type(e).__name__
        e_str = str(e) or repr(e)
        msg = f"{e_type}: {e_str}"

        if hasattr(e, "response") and getattr(e, "response", None) is not None:
            resp = getattr(e, "response")
            status = getattr(resp, "status_code", "N/A")
            body = getattr(resp, "text", "")
            body_preview = body[:500] if body else "No response body"
            msg += f" | HTTP {status}: {body_preview}"

        return msg

    async def guard_and_classify(self, user_message: str) -> Dict[str, Any]:
        """Runs guard and classification with multi-provider fallback."""
        clients = self.get_configured_providers()
        real_failed = False
        trace = get_current_trace()

        for client in clients:
            start_t = time.perf_counter()
            model_name = getattr(client, "model", "n/a")
            step_ctx = trace.step("llm.attempt", provider=client.provider_name, model=model_name) if trace else DummyStepContext()

            try:
                with step_ctx:
                    res = await client.guard_and_classify(user_message)
                elapsed = time.perf_counter() - start_t
                logger.info(f"[LLMRouter] guard_and_classify served by provider '{client.provider_name}' (model={model_name}) in {elapsed:.2f}s")
                return res
            except Exception as e:
                elapsed = time.perf_counter() - start_t
                err_detail = self._format_exception(e)
                logger.warning(
                    f"[LLMRouter] Provider '{client.provider_name}' (model={model_name}) failed guard_and_classify "
                    f"in {elapsed:.2f}s: {err_detail}. Falling back..."
                )
                logger.debug(f"[LLMRouter] Traceback for {client.provider_name} guard_and_classify failure:", exc_info=True)
                if client.provider_name != "mock":
                    real_failed = True

        if real_failed:
            logger.warning("ALL REAL PROVIDERS FAILED - using mock answer")

        return await self.providers["mock"].guard_and_classify(user_message)

    async def generate_answer(
        self,
        system_prompt: str,
        user_message: str,
        history: List[Dict[str, str]]
    ) -> str:
        """Generates answer with multi-provider fallback."""
        clients = self.get_configured_providers()
        real_failed = False
        trace = get_current_trace()

        for client in clients:
            start_t = time.perf_counter()
            model_name = getattr(client, "model", "n/a")
            step_ctx = trace.step("llm.attempt", provider=client.provider_name, model=model_name) if trace else DummyStepContext()

            try:
                with step_ctx:
                    res = await client.generate_answer(system_prompt, user_message, history)
                elapsed = time.perf_counter() - start_t
                logger.info(f"[LLMRouter] generate_answer served by provider '{client.provider_name}' (model={model_name}) in {elapsed:.2f}s")
                return res
            except Exception as e:
                elapsed = time.perf_counter() - start_t
                err_detail = self._format_exception(e)
                logger.warning(
                    f"[LLMRouter] Provider '{client.provider_name}' (model={model_name}) failed generate_answer "
                    f"in {elapsed:.2f}s: {err_detail}. Falling back..."
                )
                logger.debug(f"[LLMRouter] Traceback for {client.provider_name} generate_answer failure:", exc_info=True)
                if client.provider_name != "mock":
                    real_failed = True

        if real_failed:
            logger.warning("ALL REAL PROVIDERS FAILED - using mock answer")

        return await self.providers["mock"].generate_answer(system_prompt, user_message, history)

    async def summarize_transcript(self, transcript_text: str) -> Dict[str, Any]:
        """Summarizes transcript with multi-provider fallback."""
        clients = self.get_configured_providers()
        real_failed = False
        trace = get_current_trace()

        for client in clients:
            start_t = time.perf_counter()
            model_name = getattr(client, "model", "n/a")
            step_ctx = trace.step("llm.attempt", provider=client.provider_name, model=model_name) if trace else DummyStepContext()

            try:
                with step_ctx:
                    res = await client.summarize_transcript(transcript_text)
                elapsed = time.perf_counter() - start_t
                logger.info(f"[LLMRouter] summarize_transcript served by provider '{client.provider_name}' (model={model_name}) in {elapsed:.2f}s")
                return res
            except Exception as e:
                elapsed = time.perf_counter() - start_t
                err_detail = self._format_exception(e)
                logger.warning(
                    f"[LLMRouter] Provider '{client.provider_name}' (model={model_name}) failed summarize_transcript "
                    f"in {elapsed:.2f}s: {err_detail}. Falling back..."
                )
                logger.debug(f"[LLMRouter] Traceback for {client.provider_name} summarize_transcript failure:", exc_info=True)
                if client.provider_name != "mock":
                    real_failed = True

        if real_failed:
            logger.warning("ALL REAL PROVIDERS FAILED - using mock answer")

        return await self.providers["mock"].summarize_transcript(transcript_text)


# Global singleton instance
llm_router = LLMRouter()
