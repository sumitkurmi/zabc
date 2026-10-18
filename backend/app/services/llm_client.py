"""Provider-specific LLM implementations and unified interface.

Supports:
- GeminiLLMClient (Google Gemini via REST API with GEMINI_API_KEY)
- OpenAILLMClient (OpenAI gpt-4o-mini via REST API with OPENAI_API_KEY)
- GrokLLMClient (xAI Grok via REST API with GROK_API_KEY)
- AnthropicLLMClient (Anthropic Claude via SDK/REST with LLM_API_KEY)
- MockLLMClient (Offline local fallback)
"""

import json
import re
from typing import Dict, Any, List, Optional
import httpx
import anthropic
from backend.app.config import settings
from backend.app.models import ProblemType
from backend.app.services.category_map import map_symptom_to_category


class LLMClient:
    """Interface for individual LLM client providers."""

    provider_name: str = "base"

    async def guard_and_classify(self, user_message: str) -> Dict[str, Any]:
        """Classifies message on-topic status and problem category."""
        raise NotImplementedError

    async def generate_answer(
        self,
        system_prompt: str,
        user_message: str,
        history: List[Dict[str, str]]
    ) -> str:
        """Generates chatbot answer given system rules, RAG context, and history."""
        raise NotImplementedError

    async def summarize_transcript(self, transcript_text: str) -> Dict[str, Any]:
        """Summarizes student chat transcript into JSON for complaint pre-fill."""
        raise NotImplementedError


class MockLLMClient(LLMClient):
    """Fallback LLM client for local testing without requiring external API keys."""

    provider_name: str = "mock"

    async def guard_and_classify(self, user_message: str) -> Dict[str, Any]:
        text_lower = user_message.lower()

        # Prompt injection & jailbreak phrases
        injection_phrases = [
            "system override", "developer mode", "ignore all previous",
            "forget college guidelines", "bypass guard", "ignore network scope",
            "print out", "secret api", "credentials", "build a bomb"
        ]
        if any(phrase in text_lower for phrase in injection_phrases):
            return {"on_topic": False, "category": None, "confidence": 0.0}

        # Off-topic general topics
        off_topic_keywords = [
            "essay", "weather", "match", "movie", "recipe", "joke", "capital of",
            "president", "algebra", "quadratic", "distance between earth", "moon"
        ]
        if any(kw in text_lower for kw in off_topic_keywords) and not any(net in text_lower for net in ["wifi", "lan", "net", "internet"]):
            return {"on_topic": False, "category": None, "confidence": 0.0}

        detected_cat = map_symptom_to_category(user_message)
        if not detected_cat and not any(net in text_lower for net in ["wifi", "wi-fi", "lan", "network", "internet", "ip", "dns", "proxy", "port", "socket"]):
            return {"on_topic": False, "category": None, "confidence": 0.0}

        return {
            "on_topic": True,
            "category": detected_cat.value if detected_cat else ProblemType.WIFI_PROBLEM.value,
            "confidence": 0.85
        }

    async def generate_answer(
        self,
        system_prompt: str,
        user_message: str,
        history: List[Dict[str, str]]
    ) -> str:
        cat = map_symptom_to_category(user_message)
        if "wifi" in user_message.lower():
            return "I understand you are facing Wi-Fi connection issues. Please try the following steps:\n1. Forget the 'MNNIT-WiFi' network on your device.\n2. Turn your Wi-Fi off and on again.\n3. Re-enter your credentials.\nAre you connecting from a hostel block or academic block?"
        elif "ip" in user_message.lower() or "dhcp" in user_message.lower():
            return "For IP address allocation issues:\n1. Ensure your network card is set to 'Obtain an IP address automatically (DHCP)'.\n2. Open command prompt and run `ipconfig /renew`.\n3. Restart your laptop.\nHas your device received a valid campus IP (10.x.x.x)?"
        elif "proxy" in user_message.lower():
            return "For proxy configuration errors:\n1. Open browser network settings.\n2. Set proxy host to `proxy.mnnit.ac.in` and port `8080`.\n3. Check 'Bypass proxy for local addresses'.\nWhich browser are you currently using?"
        elif "port" in user_message.lower() or "cable" in user_message.lower():
            return "For dead LAN port or damaged cable issues:\n1. Check if the green/orange link LED lights up on your wall socket.\n2. Try testing with another CAT6 Ethernet cable.\n3. Inspect the RJ45 jack for physical bent pins.\nDoes the port show any activity lights when plugged in?"
        else:
            return "Thank you for reaching out to the Network Assistant. Could you please specify your device type and exact location so I can guide you through troubleshooting?"

    async def summarize_transcript(self, transcript_text: str) -> Dict[str, Any]:
        cat = map_symptom_to_category(transcript_text) or ProblemType.WIFI_PROBLEM
        summary_comment = f"Student experiencing network issues. Transcript summary: {transcript_text[:250]}..."
        return {
            "problem_type": cat.value,
            "additional_comment": summary_comment
        }


class GeminiLLMClient(LLMClient):
    """Google Gemini LLM client implementation."""

    provider_name: str = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model = model
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

    async def _call_gemini(self, prompt: str) -> str:
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(self.url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()

    async def guard_and_classify(self, user_message: str) -> Dict[str, Any]:
        prompt = f"""You are a guard classifier for MNNIT Allahabad Network Assistant.
Determine if the user message is about campus network issues (Wi-Fi, LAN, IP, DHCP, DNS, Proxy, dead LAN ports, switch, access points, slow internet, network cable fault).

User message: "{user_message}"

Respond strictly with a JSON object:
{{
  "on_topic": true or false,
  "category": "LAN_PROBLEM" | "IP_ADDRESS_ISSUE" | "PROXY_ISSUE" | "LAN_PORT_BROKEN" | "WIFI_PROBLEM" | null,
  "confidence": 0.0 to 1.0
}}
"""
        text = await self._call_gemini(prompt)
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return json.loads(text)

    async def generate_answer(
        self,
        system_prompt: str,
        user_message: str,
        history: List[Dict[str, str]]
    ) -> str:
        hist_str = "\n".join([f"{h['role']}: {h['content']}" for h in history])
        full_prompt = f"{system_prompt}\n\nChat History:\n{hist_str}\n\nStudent: {user_message}\nAssistant:"
        return await self._call_gemini(full_prompt)

    async def summarize_transcript(self, transcript_text: str) -> Dict[str, Any]:
        prompt = f"""Summarize this student chat transcript into strict JSON for a complaint form.

TRANSCRIPT:
{transcript_text}

JSON Format:
{{
  "problem_type": "WIFI_PROBLEM" | "LAN_PROBLEM" | "IP_ADDRESS_ISSUE" | "PROXY_ISSUE" | "LAN_PORT_BROKEN",
  "additional_comment": "First-person summary max 600 chars."
}}
"""
        text = await self._call_gemini(prompt)
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return json.loads(text)


class OpenAILLMClient(LLMClient):
    """OpenAI / OpenAI-compatible API LLM client implementation."""

    provider_name: str = "openai"

    def __init__(self, api_key: str, model: str = "gpt-4o-mini", base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    async def _call_openai(self, messages: List[Dict[str, str]], response_json: bool = False) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2
        }
        if response_json:
            payload["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()

    async def guard_and_classify(self, user_message: str) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": "You are a guard classifier for MNNIT Network Assistant. Output strictly JSON with keys on_topic (bool), category (string or null), and confidence (float)."},
            {"role": "user", "content": f"User message: '{user_message}'"}
        ]
        text = await self._call_openai(messages, response_json=True)
        return json.loads(text)

    async def generate_answer(
        self,
        system_prompt: str,
        user_message: str,
        history: List[Dict[str, str]]
    ) -> str:
        messages = [{"role": "system", "content": system_prompt}]
        for turn in history:
            messages.append({"role": turn["role"], "content": turn["content"]})
        messages.append({"role": "user", "content": user_message})

        return await self._call_openai(messages)

    async def summarize_transcript(self, transcript_text: str) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": "Summarize transcript into JSON with keys problem_type (one of WIFI_PROBLEM, LAN_PROBLEM, IP_ADDRESS_ISSUE, PROXY_ISSUE, LAN_PORT_BROKEN) and additional_comment (max 600 chars)."},
            {"role": "user", "content": transcript_text}
        ]
        text = await self._call_openai(messages, response_json=True)
        return json.loads(text)


class GrokLLMClient(OpenAILLMClient):
    """xAI Grok API client (OpenAI compatible endpoint)."""

    provider_name: str = "grok"

    def __init__(self, api_key: str, model: str = "grok-beta"):
        super().__init__(api_key=api_key, model=model, base_url="https://api.x.ai/v1")


class AnthropicLLMClient(LLMClient):
    """Anthropic Claude API client implementation."""

    provider_name: str = "anthropic"

    def __init__(self, api_key: str):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)

    async def guard_and_classify(self, user_message: str) -> Dict[str, Any]:
        prompt = f"""You are a guard classifier for MNNIT Allahabad Network Assistant.
Determine if the user message is about campus network issues (Wi-Fi, LAN, IP, DHCP, DNS, Proxy, dead LAN ports, switch, access points, slow internet, network cable fault).

User message: "{user_message}"

Respond strictly with a JSON object:
{{
  "on_topic": true or false,
  "category": "LAN_PROBLEM" | "IP_ADDRESS_ISSUE" | "PROXY_ISSUE" | "LAN_PORT_BROKEN" | "WIFI_PROBLEM" | null,
  "confidence": 0.0 to 1.0
}}
"""
        response = await self.client.messages.create(
            model=settings.LLM_MODEL_GUARD,
            max_tokens=150,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.content[0].text.strip()
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return json.loads(content)

    async def generate_answer(
        self,
        system_prompt: str,
        user_message: str,
        history: List[Dict[str, str]]
    ) -> str:
        messages = []
        for turn in history:
            messages.append({"role": turn["role"], "content": turn["content"]})
        messages.append({"role": "user", "content": user_message})

        response = await self.client.messages.create(
            model=settings.LLM_MODEL_CHAT,
            max_tokens=600,
            temperature=0.3,
            system=system_prompt,
            messages=messages
        )
        return response.content[0].text.strip()

    async def summarize_transcript(self, transcript_text: str) -> Dict[str, Any]:
        prompt = f"""Summarize chat transcript into concise complaint report JSON.

TRANSCRIPT:
{transcript_text}

OUTPUT INSTRUCTIONS:
{{
  "problem_type": "WIFI_PROBLEM" | "LAN_PROBLEM" | "IP_ADDRESS_ISSUE" | "PROXY_ISSUE" | "LAN_PORT_BROKEN",
  "additional_comment": "First-person summary max 600 chars."
}}
"""
        response = await self.client.messages.create(
            model=settings.LLM_MODEL_CHAT,
            max_tokens=400,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.content[0].text.strip()
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return json.loads(content)
