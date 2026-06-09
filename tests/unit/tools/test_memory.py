"""Testes do NeuroValen: MemorySearchService e MemoryTool."""

import pytest

from valen.domains.memory.entities.note import Note
from valen.domains.memory.repositories.base import InMemoryRepository
from valen.domains.memory.services.search import MemorySearchService
from valen.domains.tools.base import ToolContext
from valen.domains.tools.implementations.memory import MemoryTool


@pytest.fixture
def service():
    return MemorySearchService(InMemoryRepository())


@pytest.fixture
def tool(service):
    return MemoryTool(service=service)


def ctx(agent="CEO", **kw):
    return ToolContext(agent_id=agent, **kw)


def test_note_links_e_markdown():
    n = Note(title="A", content="liga em [[B]] e [[C]]", tags=["x"])
    assert n.links() == ["B", "C"]
    md = n.to_markdown()
    assert md.startswith("---") and "# A" in md and "priority: medium" in md


async def test_search_ranking(service):
    await service.create("Docker no Nexus", "infra e containers", note_type="architecture",
                         tags=["docker"], priority="high")
    await service.create("Receita de bolo", "farinha e ovos")
    res = await service.search("docker")
    assert res and res[0].title == "Docker no Nexus"


async def test_search_sem_query_retorna_recentes(service):
    await service.create("um", "a")
    await service.create("dois", "b")
    res = await service.search("")
    assert {n.title for n in res} == {"um", "dois"}


async def test_memorytool_remember_recall(tool):
    r = await tool.execute("remember", {"title": "T", "content": "alpha beta"}, ctx())
    assert r.ok and r.result["id"]
    rec = await tool.execute("recall", {"query": "alpha"}, ctx())
    assert rec.ok and rec.result[0]["title"] == "T"


async def test_memorytool_forget_requer_aprovacao(tool):
    r = await tool.execute("remember", {"title": "T", "content": "x"}, ctx())
    nid = r.result["id"]
    deny = await tool.execute("forget", {"id": nid}, ctx())
    assert deny.ok is False and "aprovação" in deny.error
    ok = await tool.execute("forget", {"id": nid}, ctx(approved=True))
    assert ok.ok and ok.result["forgotten"] == nid


async def test_memorytool_acl(tool):
    # Forge tem 'memory'; agente sem memory negado
    res = await tool.execute("recall", {"query": "x"}, ctx(agent="Ghost"))
    assert res.ok is False and "permissão" in res.error
