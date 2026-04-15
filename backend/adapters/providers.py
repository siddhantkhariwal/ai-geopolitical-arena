"""Concrete adapter implementations for each sovereign AI model provider."""

from __future__ import annotations

import asyncio
import logging

import httpx

from backend.adapters.base import ModelAdapter

logger = logging.getLogger(__name__)


class OpenAICompatibleAdapter(ModelAdapter):
    """Adapter for any OpenAI-compatible API (OpenAI, DeepSeek, Mistral, Qwen, local vLLM, etc.)."""

    DEFAULT_BASES = {
        "openai": "https://api.openai.com/v1",
        "deepseek": "https://api.deepseek.com",
        "mistral": "https://api.mistral.ai/v1",
        "qwen": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        "groq": "https://api.groq.com/openai/v1",
        "openrouter": "https://openrouter.ai/api/v1",
        "local": "http://localhost:8000/v1",
    }

    def __init__(
        self,
        model_id: str,
        api_key: str | None = None,
        api_base: str | None = None,
        provider_tag: str = "openai",
    ):
        resolved_base = api_base or self.DEFAULT_BASES.get(provider_tag, self.DEFAULT_BASES["openai"])
        super().__init__(model_id, api_key, resolved_base)
        self.provider_tag = provider_tag

    async def generate(self, messages: list[dict[str, str]], temperature: float = 0.3, max_tokens: int = 2048) -> str:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        for attempt in range(8):
            async with httpx.AsyncClient(timeout=45.0) as client:
                resp = await client.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                if resp.status_code == 429:
                    wait = min(2 ** attempt + 2, 60)
                    logger.warning(f"Rate limited ({self.model_id}), retrying in {wait}s...")
                    await asyncio.sleep(wait)
                    continue
                resp.raise_for_status()
                data = resp.json()
                msg = data["choices"][0]["message"]
                content = msg.get("content")
                if not content and msg.get("reasoning"):
                    content = msg["reasoning"]
                return content or ""
        raise Exception(f"Rate limited after 8 retries for {self.model_id}")


class AnthropicAdapter(ModelAdapter):
    """Adapter for Anthropic's Claude API."""

    API_BASE = "https://api.anthropic.com/v1"

    async def generate(self, messages: list[dict[str, str]], temperature: float = 0.3, max_tokens: int = 2048) -> str:
        # Separate system message from conversation messages
        system = ""
        conversation = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                conversation.append(msg)

        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key or "",
            "anthropic-version": "2023-06-01",
        }

        payload = {
            "model": self.model_id,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": conversation,
        }
        if system:
            payload["system"] = system

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self.API_BASE}/messages",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"]


class CohereAdapter(ModelAdapter):
    """Adapter for Cohere's Command API (Canada)."""

    API_BASE = "https://api.cohere.com/v2"

    async def generate(self, messages: list[dict[str, str]], temperature: float = 0.3, max_tokens: int = 2048) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        payload = {
            "model": self.model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self.API_BASE}/chat",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["message"]["content"][0]["text"]


class GoogleAdapter(ModelAdapter):
    """Adapter for Google Gemini API."""

    API_BASE = "https://generativelanguage.googleapis.com/v1beta"

    async def generate(self, messages: list[dict[str, str]], temperature: float = 0.3, max_tokens: int = 2048) -> str:
        # Convert to Gemini format
        system_instruction = None
        contents = []
        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
            else:
                role = "user" if msg["role"] == "user" else "model"
                contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        payload: dict = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        url = f"{self.API_BASE}/models/{self.model_id}:generateContent?key={self.api_key}"

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_adapter(provider: str, model_id: str, api_key: str | None = None, api_base: str | None = None) -> ModelAdapter:
    """Create the right adapter for a given provider."""
    provider = provider.lower()

    if provider == "anthropic":
        return AnthropicAdapter(model_id, api_key, api_base)
    elif provider == "google":
        return GoogleAdapter(model_id, api_key, api_base)
    elif provider == "cohere":
        return CohereAdapter(model_id, api_key, api_base)
    elif provider in ("openai", "deepseek", "mistral", "qwen", "falcon", "local", "gigachat", "hyperclova", "sarvam", "groq", "openrouter"):
        return OpenAICompatibleAdapter(model_id, api_key, api_base, provider_tag=provider)
    else:
        # Default to OpenAI-compatible
        return OpenAICompatibleAdapter(model_id, api_key, api_base, provider_tag="openai")
