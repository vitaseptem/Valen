"""Testes dos agentes e orquestração (via MockProvider, sem rede)."""

import pytest

from valen.domains.agents.entities.agent import DEFAULT_AGENTS, AgentState
from valen.domains.agents.services.orchestration import (
    AgentNotFound,
    AgentOrchestrationService,
    ToolRegistry,
)
from valen.domains.memory.repositories.base import InMemoryRepository
from valen.domains.memory.services.search import MemorySearchService
from valen.domains.providers.registry import ProviderRegistry
from valen.domains.tools.acl import PermissionDenied
from valen.domains.tools.implementations.memory import MemoryTool


@pytest.fixture
def orch():
    providers = ProviderRegistry([])  # só mock
    service = MemorySearchService(InMemoryRepository())
    tools = ToolRegistry()
    tools.register(MemoryTool(service=service))
    return AgentOrchestrationService(providers, tools)


def test_exatamente_quatro_agentes():
    assert set(DEFAULT_AGENTS) == {"CEO", "Forge", "Nexus", "Analyst"}


def test_personas_e_simbolos():
    assert DEFAULT_AGENTS["CEO"].symbol == "♛"
    assert "meu rei" in DEFAULT_AGENTS["CEO"].persona
    assert "system" not in DEFAULT_AGENTS["Forge"].system_prompt().lower()[:6]


async def test_chat_ceo_via_mock(orch):
    res = await orch.chat("CEO", "olá")
    assert res["agent"] == "CEO" and res["model"] == "mock-1"
    assert "olá" in res["reply"]
    assert orch.get_agent("CEO").state == AgentState.DONE


async def test_agente_inexistente(orch):
    with pytest.raises(AgentNotFound):
        await orch.chat("Hacker", "x")


async def test_use_tool_respeita_acesso_do_agente(orch):
    # Analyst só tem MemoryTool; pedir FilesystemTool (não na lista) deve negar
    with pytest.raises(PermissionDenied):
        await orch.use_tool("Analyst", "FilesystemTool", "read", {"path": "x"})


async def test_use_tool_memory_ok(orch):
    res = await orch.use_tool("CEO", "MemoryTool", "remember",
                              {"title": "T", "content": "infra do nexus"})
    assert res.ok
    rec = await orch.use_tool("Analyst", "MemoryTool", "recall", {"query": "nexus"})
    assert rec.ok and rec.result[0]["title"] == "T"
