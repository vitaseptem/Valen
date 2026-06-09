"""ProviderRegistry — registro e fallback automático por prioridade.

Tenta os providers em ordem de prioridade. Cada um recebe retry com backoff
exponencial; esgotado, cai para o próximo. O MockProvider, registrado por
último, garante que sempre há uma resposta (VALEN nunca trava por falta de LLM).
"""

from __future__ import annotations

import asyncio

from valen.domains.observability.logging import get_logger
from valen.domains.providers.base import ProviderBase, ProviderResponse
from valen.domains.providers.mock import MockProvider

log = get_logger(__name__)


class ProviderRegistry:
    """Lista ordenada de providers com fallback e retry."""

    def __init__(
        self,
        providers: list[ProviderBase] | None = None,
        *,
        max_retries: int = 2,
        base_delay: float = 0.5,
        ensure_mock: bool = True,
    ) -> None:
        self._providers: list[ProviderBase] = list(providers or [])
        if ensure_mock and not any(p.name == "mock" for p in self._providers):
            self._providers.append(MockProvider())
        self.max_retries = max_retries
        self.base_delay = base_delay

    @property
    def names(self) -> list[str]:
        return [p.name for p in self._providers]

    def register(self, provider: ProviderBase, *, front: bool = False) -> None:
        if front:
            self._providers.insert(0, provider)
        else:
            self._providers.append(provider)

    async def complete(
        self, messages: list, tools: list | None = None
    ) -> ProviderResponse:
        """Tenta cada provider em ordem; retorna a 1ª resposta bem-sucedida."""
        last_error: Exception | None = None
        for provider in self._providers:
            for attempt in range(self.max_retries + 1):
                try:
                    resp = await provider.complete(messages, tools)
                    if attempt or provider is not self._providers[0]:
                        log.info("provider_fallback_ok", provider=provider.name)
                    return resp
                except Exception as exc:  # noqa: BLE001 — tenta o próximo
                    last_error = exc
                    log.warning(
                        "provider_attempt_failed",
                        provider=provider.name, attempt=attempt, error=str(exc),
                    )
                    if attempt < self.max_retries:
                        await asyncio.sleep(self.base_delay * (2 ** attempt))
        raise RuntimeError(f"todos os providers falharam: {last_error}")
