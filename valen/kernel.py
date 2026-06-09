"""Kernel — montagem central do VALEN.

Conecta Audit Trail, NeuroValen, Tools, Providers e os 4 Agentes num único
objeto usado pela API e pela CLI. Roda 100% sem infraestrutura externa
(in-memory + MockProvider); quando há GROQ_API_KEY/Ollama/Postgres, usa-os.
"""

from __future__ import annotations

import os

from valen.config import Settings, get_settings
from valen.domains.agents.services.orchestration import (
    AgentOrchestrationService,
    ToolRegistry,
)
from valen.domains.memory.repositories.base import InMemoryRepository
from valen.domains.memory.services.search import MemorySearchService
from valen.domains.observability.logging import configure_logging, get_logger
from valen.domains.providers.groq import GroqProvider
from valen.domains.providers.registry import ProviderRegistry
from valen.domains.tools.audit import AuditTrail
from valen.domains.tools.base import ToolBase
from valen.domains.tools.implementations.filesystem import FilesystemTool
from valen.domains.tools.implementations.memory import MemoryTool
from valen.domains.tools.implementations.network import NetworkTool
from valen.domains.tools.implementations.provider import ProviderTool
from valen.domains.tools.implementations.terminal import TerminalTool

log = get_logger(__name__)


class Kernel:
    """Container de dependências do VALEN."""

    def __init__(self, settings: Settings | None = None,
                 workspace: str | None = None) -> None:
        self.settings = settings or get_settings()
        configure_logging(self.settings.valen_log_level)

        self.workspace = workspace or os.getenv("VALEN_WORKSPACE", "./data/workspace")
        os.makedirs(self.workspace, exist_ok=True)

        # Auditoria (sink in-memory por padrão; Postgres pode ser adicionado depois)
        self.audit = AuditTrail()

        # NeuroValen
        self.memory_repo = InMemoryRepository()
        self.memory_service = MemorySearchService(self.memory_repo)

        # Providers (prioridade: groq → mock; mock garantido pelo registry)
        providers = []
        groq = GroqProvider(model="llama3-70b-8192")
        if groq.available:
            providers.append(groq)
            log.info("provider_enabled", provider="groq")
        self.providers = ProviderRegistry(providers)

        # Tools
        self.tools = ToolRegistry()
        for tool in self._build_tools():
            self.tools.register(tool)

        # Agentes
        self.orchestrator = AgentOrchestrationService(self.providers, self.tools)

    def _build_tools(self) -> list[ToolBase]:
        return [
            FilesystemTool(root=self.workspace, audit=self.audit),
            TerminalTool(root=self.workspace, audit=self.audit),
            MemoryTool(service=self.memory_service, audit=self.audit),
            NetworkTool(audit=self.audit),
            ProviderTool(providers=self.providers, audit=self.audit),
        ]


_kernel: Kernel | None = None


def get_kernel() -> Kernel:
    """Singleton do Kernel (lazy)."""
    global _kernel
    if _kernel is None:
        _kernel = Kernel()
    return _kernel
