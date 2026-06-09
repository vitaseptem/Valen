"""Testes de ACL: permissões por agente."""

import pytest

from valen.domains.tools.acl import (
    AGENT_PERMISSIONS,
    PermissionDenied,
    check_permissions,
    has_permissions,
)


def test_apenas_quatro_agentes():
    assert set(AGENT_PERMISSIONS) == {"CEO", "Forge", "Nexus", "Analyst"}


def test_forge_pode_escrever():
    assert has_permissions("Forge", {"read", "write"})
    check_permissions("Forge", {"write"})  # não levanta


def test_analyst_nao_escreve():
    assert not has_permissions("Analyst", {"write"})
    with pytest.raises(PermissionDenied):
        check_permissions("Analyst", {"write"})


def test_agente_desconhecido():
    with pytest.raises(PermissionDenied):
        check_permissions("Hacker", {"read"})


def test_nexus_docker_full():
    assert has_permissions("Nexus", {"docker_full", "system_monitor"})
