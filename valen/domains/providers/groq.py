"""GroqProvider — API compatível com OpenAI, alta velocidade.

Modelos: llama3-70b-8192, mixtral-8x7b-32768. Requer GROQ_API_KEY.
Disponível apenas quando há chave configurada (ver `available`).
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator

import httpx

from valen.domains.providers.base import ProviderBase, ProviderResponse

_BASE_URL = "https://api.groq.com/openai/v1/chat/completions"


class GroqProvider(ProviderBase):
    """Provider Groq (chat completions compatível com OpenAI)."""

    name = "groq"
    api_key_env = "GROQ_API_KEY"
    supports_streaming = True
    supports_vision = False
    supports_tools = True
    max_context_tokens = 8192

    def __init__(self, model: str = "llama3-70b-8192", timeout: float = 30.0) -> None:
        self.model = model
        self._timeout = timeout
        self._api_key = os.getenv(self.api_key_env, "")

    @property
    def available(self) -> bool:
        return bool(self._api_key)

    async def complete(
        self, messages: list, tools: list | None = None
    ) -> ProviderResponse:
        if not self.available:
            raise RuntimeError("GROQ_API_KEY ausente")
        payload: dict = {"model": self.model, "messages": messages}
        if tools:
            payload["tools"] = tools
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(
                _BASE_URL,
                headers={"Authorization": f"Bearer {self._api_key}"},
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
        choice = data["choices"][0]["message"]
        return ProviderResponse(
            content=choice.get("content") or "",
            model=self.model,
            tool_calls=choice.get("tool_calls", []) or [],
            usage=data.get("usage", {}),
        )

    async def stream(self, messages: list) -> AsyncGenerator[str, None]:
        # Streaming real entra depois; por ora emite a resposta completa.
        resp = await self.complete(messages)
        yield resp.content
