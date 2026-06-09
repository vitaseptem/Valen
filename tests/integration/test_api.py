"""Testes de integração da API FastAPI (TestClient, sem rede externa)."""

import pytest
from fastapi.testclient import TestClient

from valen.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:  # dispara o lifespan (monta o Kernel)
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_status_lista_componentes(client):
    r = client.get("/status")
    data = r.json()
    assert {a["id"] for a in data["agents"]} == {"CEO", "Forge", "Nexus", "Analyst"}
    assert "MemoryTool" in data["tools"]
    assert "mock" in data["providers"]


def test_listar_agentes(client):
    r = client.get("/agents")
    assert r.status_code == 200 and len(r.json()) == 4


def test_chat_ceo(client):
    r = client.post("/agents/CEO/chat", json={"message": "olá"})
    assert r.status_code == 200
    assert "olá" in r.json()["reply"]


def test_chat_agente_invalido(client):
    r = client.post("/agents/Hacker/chat", json={"message": "x"})
    assert r.status_code == 404


def test_tool_via_agente_e_memoria(client):
    # CEO grava nota via MemoryTool
    r = client.post("/agents/CEO/tools", json={
        "tool": "MemoryTool", "action": "remember",
        "args": {"title": "Infra", "content": "docker e nexus"},
    })
    assert r.status_code == 200 and r.json()["ok"]
    # busca via endpoint de memória
    s = client.get("/memory/search", params={"q": "docker"})
    assert s.status_code == 200 and s.json()[0]["title"] == "Infra"


def test_tool_acl_negada(client):
    # Analyst não tem FilesystemTool
    r = client.post("/agents/Analyst/tools", json={
        "tool": "FilesystemTool", "action": "read", "args": {"path": "x"},
    })
    assert r.status_code == 403


def test_tool_destrutiva_requer_aprovacao(client):
    r = client.post("/agents/Forge/tools", json={
        "tool": "FilesystemTool", "action": "write",
        "args": {"path": "t.txt", "content": "x"},
    })
    assert r.json()["ok"] is True
    # delete sem approved → falha controlada (ok=False), não exceção
    d = client.post("/agents/Forge/tools", json={
        "tool": "FilesystemTool", "action": "delete", "args": {"path": "t.txt"},
    })
    assert d.json()["ok"] is False and "aprovação" in d.json()["error"]


def test_websocket_chat(client):
    with client.websocket_connect("/ws/chat") as ws:
        hello = ws.receive_json()
        assert hello["agent"] == "CEO"
        ws.send_json({"agent": "Forge", "message": "compile"})
        resp = ws.receive_json()
        assert resp["agent"] == "Forge" and "compile" in resp["reply"]
