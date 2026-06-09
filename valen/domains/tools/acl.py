"""ACL: permissões por agente e enforcement.

Apenas 4 agentes existem (regra R2). Cada Tool declara `required_permissions`;
a ACL garante que o agente chamador tem todas elas.
"""

from __future__ import annotations

# Apenas 4 agentes existem no sistema (regra R2). Nenhum a mais.
AGENT_PERMISSIONS: dict[str, set[str]] = {
    "CEO":     {"read", "write", "execute", "network", "memory", "docker_inspect"},
    "Forge":   {"read", "write", "execute", "memory"},
    "Nexus":   {"read", "write", "execute", "network", "docker_full", "memory", "system_monitor"},
    "Analyst": {"read", "memory", "network_read"},
}

VALID_AGENTS: frozenset[str] = frozenset(AGENT_PERMISSIONS)


class PermissionDenied(Exception):
    """Levantada quando um agente não possui as permissões exigidas."""


def permissions_for(agent_id: str) -> set[str]:
    """Retorna as permissões do agente (set vazio se desconhecido)."""
    return set(AGENT_PERMISSIONS.get(agent_id, set()))


def has_permissions(agent_id: str, required: set[str]) -> bool:
    """True se o agente possui todas as permissões exigidas."""
    return required.issubset(permissions_for(agent_id))


def check_permissions(agent_id: str, required: set[str]) -> None:
    """Levanta PermissionDenied se faltar alguma permissão ao agente."""
    if agent_id not in AGENT_PERMISSIONS:
        raise PermissionDenied(f"agente desconhecido: {agent_id!r}")
    missing = required - permissions_for(agent_id)
    if missing:
        raise PermissionDenied(
            f"{agent_id} sem permissões {sorted(missing)} (exigidas {sorted(required)})"
        )
