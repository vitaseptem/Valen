"""Contrato base dos providers de IA — arquitetura modular.

Stub da Fase 0: define `ProviderBase` (ABC) e `ProviderResponse`. As
implementações (Groq, Ollama, …) entram na Fase 4.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProviderResponse:
    """Resposta normalizada de qualquer provider."""

    content: str
    model: str
    tool_calls: list[dict] = field(default_factory=list)
    usage: dict[str, Any] = field(default_factory=dict)


class ProviderBase(ABC):
    """Interface comum a todos os providers de LLM."""

    name: str
    model: str
    api_key_env: str
    supports_streaming: bool
    supports_vision: bool
    supports_tools: bool
    max_context_tokens: int

    @abstractmethod
    async def complete(
        self, messages: list, tools: list | None = None
    ) -> ProviderResponse:
        """Gera uma resposta completa (não-streaming)."""
        ...

    @abstractmethod
    async def stream(self, messages: list) -> AsyncGenerator[str, None]:
        """Gera a resposta em streaming, token a token."""
        ...
