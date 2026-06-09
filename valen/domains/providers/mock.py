"""MockProvider — provider sem rede, sempre disponível.

Garante que o VALEN roda 100% sem API keys nem Ollama. Gera respostas
determinísticas e cientes do contexto (último system + user). Fallback final
do ProviderRegistry.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from valen.domains.providers.base import ProviderBase, ProviderResponse


class MockProvider(ProviderBase):
    """Provider local determinístico (sem custo, sem rede)."""

    name = "mock"
    model = "mock-1"
    api_key_env = ""
    supports_streaming = True
    supports_vision = False
    supports_tools = False
    max_context_tokens = 8192

    def _compose(self, messages: list[dict]) -> str:
        system = next((m["content"] for m in messages if m.get("role") == "system"), "")
        user = next(
            (m["content"] for m in reversed(messages) if m.get("role") == "user"), ""
        )
        persona = system.split("\n", 1)[0] if system else "VALEN"
        return f"[{self.name}] {persona} recebeu: «{user.strip()}». (resposta simulada)"

    async def complete(
        self, messages: list, tools: list | None = None
    ) -> ProviderResponse:
        return ProviderResponse(
            content=self._compose(messages),
            model=self.model,
            usage={"provider": self.name},
        )

    async def stream(self, messages: list) -> AsyncGenerator[str, None]:
        for word in self._compose(messages).split(" "):
            yield word + " "
