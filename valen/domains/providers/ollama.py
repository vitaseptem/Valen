"""OllamaProvider — LLM local, custo zero, privacidade máxima.

Fala com o endpoint /api/chat do Ollama. Disponível quando o servidor responde.
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator

import httpx

from valen.domains.providers.base import ProviderBase, ProviderResponse


class OllamaProvider(ProviderBase):
    """Provider Ollama local."""

    name = "ollama"
    api_key_env = ""
    supports_streaming = True
    supports_vision = False
    supports_tools = False
    max_context_tokens = 8192

    def __init__(self, model: str = "llama3", url: str | None = None,
                 timeout: float = 60.0) -> None:
        self.model = model
        self._url = (url or os.getenv("OLLAMA_URL", "http://localhost:11434")).rstrip("/")
        self._timeout = timeout

    async def available(self) -> bool:
        """True se o servidor Ollama responde."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(f"{self._url}/api/tags")
                return resp.status_code == 200
        except httpx.HTTPError:
            return False

    async def complete(
        self, messages: list, tools: list | None = None
    ) -> ProviderResponse:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(
                f"{self._url}/api/chat",
                json={"model": self.model, "messages": messages, "stream": False},
            )
            resp.raise_for_status()
            data = resp.json()
        return ProviderResponse(
            content=data.get("message", {}).get("content", ""),
            model=self.model,
            usage={"provider": self.name},
        )

    async def stream(self, messages: list) -> AsyncGenerator[str, None]:
        resp = await self.complete(messages)
        yield resp.content
