"""Testes de orquestração (ToolBase.execute), FilesystemTool e TerminalTool."""

import pytest

from valen.domains.tools.audit import AuditTrail, InMemoryAuditSink
from valen.domains.tools.base import ToolContext
from valen.domains.tools.implementations.filesystem import FilesystemTool
from valen.domains.tools.implementations.terminal import TerminalTool


@pytest.fixture
def audit():
    return AuditTrail(sinks=[InMemoryAuditSink()])


def ctx(agent="Forge", **kw):
    return ToolContext(agent_id=agent, **kw)


# --- ACL na orquestração ---------------------------------------------------
async def test_acl_bloqueia_agente_sem_permissao(tmp_path, audit):
    tool = FilesystemTool(root=tmp_path, audit=audit)
    # Analyst não tem 'read'? tem. Mas FilesystemTool exige 'read'; Analyst tem read.
    # Usar agente desconhecido para negar.
    res = await tool.execute("read", {"path": "x"}, ctx(agent="Ghost"))
    assert res.ok is False
    assert "permissão" in res.error


# --- Filesystem ------------------------------------------------------------
async def test_filesystem_write_read(tmp_path, audit):
    tool = FilesystemTool(root=tmp_path, audit=audit)
    w = await tool.execute("write", {"path": "a.txt", "content": "ola"}, ctx())
    assert w.ok and w.result["written"] == 3
    r = await tool.execute("read", {"path": "a.txt"}, ctx())
    assert r.ok and r.result == "ola"


async def test_filesystem_path_traversal_bloqueado(tmp_path, audit):
    tool = FilesystemTool(root=tmp_path, audit=audit)
    res = await tool.execute("read", {"path": "../../etc/passwd"}, ctx())
    assert res.ok is False
    assert "fora da raiz" in res.error


async def test_filesystem_delete_requer_aprovacao(tmp_path, audit):
    tool = FilesystemTool(root=tmp_path, audit=audit)
    await tool.execute("write", {"path": "d.txt", "content": "x"}, ctx())
    # delete é DESTRUCTIVE → sem approved deve falhar
    res = await tool.execute("delete", {"path": "d.txt"}, ctx())
    assert res.ok is False and "aprovação" in res.error
    # com approved=True executa
    ok = await tool.execute("delete", {"path": "d.txt"}, ctx(approved=True))
    assert ok.ok and ok.result["deleted"]


async def test_dry_run_nao_executa(tmp_path, audit):
    tool = FilesystemTool(root=tmp_path, audit=audit)
    res = await tool.execute("write", {"path": "z.txt", "content": "x"}, ctx(dry_run=True))
    assert res.ok and res.result["dry_run"] is True
    assert not (tmp_path / "z.txt").exists()


# --- Terminal --------------------------------------------------------------
async def test_terminal_echo(tmp_path, audit):
    tool = TerminalTool(root=tmp_path, audit=audit)
    res = await tool.execute("run", {"command": "echo ola"}, ctx())
    assert res.ok and res.result["stdout"].strip() == "ola"


async def test_terminal_comando_bloqueado(tmp_path, audit):
    tool = TerminalTool(root=tmp_path, audit=audit)
    # rm -rf / é ALWAYS_BLOCKED; é DESTRUCTIVE/SYSTEM → precisa approved p/ chegar no _run
    res = await tool.execute("run", {"command": "rm -rf /"}, ctx(agent="Nexus", approved=True))
    assert res.ok is False
    assert "sandbox" in res.error


async def test_terminal_systemlevel_requer_aprovacao(tmp_path, audit):
    tool = TerminalTool(root=tmp_path, audit=audit)
    res = await tool.execute("run", {"command": "docker ps"}, ctx(agent="Nexus"))
    assert res.ok is False and "aprovação" in res.error


# --- Audit ----------------------------------------------------------------
async def test_audit_registra_execucao(tmp_path):
    sink = InMemoryAuditSink()
    tool = FilesystemTool(root=tmp_path, audit=AuditTrail(sinks=[sink]))
    await tool.execute("write", {"path": "a.txt", "content": "x"}, ctx())
    assert len(sink.entries) == 1
    e = sink.entries[0]
    assert e.tool_name == "FilesystemTool" and e.result_ok is True
    assert e.audit_hash.startswith("sha256:") and e.args_hash.startswith("sha256:")
