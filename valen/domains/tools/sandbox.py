"""Sandbox: Execution Tiers, classificação de risco e padrões ALWAYS_BLOCKED.

Camada de segurança do sistema de Tools. Decide o tier de uma ação e bloqueia
comandos perigosos antes de qualquer execução.
"""

from __future__ import annotations

import re
import shlex
from enum import Enum


class ExecutionTier(str, Enum):
    """Classificação de risco obrigatória de toda ação."""

    READ_ONLY = "READ_ONLY"        # ls, cat, ps, df, curl GET — sem aprovação
    REVERSIBLE = "REVERSIBLE"      # mkdir, cp, echo, curl POST — dry-run padrão
    DESTRUCTIVE = "DESTRUCTIVE"    # rm, mv, sed -i, truncate — aprovação sempre
    SYSTEM_LEVEL = "SYSTEM_LEVEL"  # systemctl, docker, apt, kill — aprovação sempre


# Tiers que exigem aprovação explícita do usuário antes de executar.
REQUIRES_APPROVAL: frozenset[ExecutionTier] = frozenset(
    {ExecutionTier.DESTRUCTIVE, ExecutionTier.SYSTEM_LEVEL}
)

# Padrões NUNCA executados, independente de permissão ou sandbox.
ALWAYS_BLOCKED: list[str] = [
    r"rm\s+-rf\s+/", r"rm\s+-rf\s+\*", r"rm\s+-rf\s+~",
    "dd if=", "mkfs", "format", "fdisk", "parted",
    "reboot", "shutdown", "halt", "poweroff", "init 0", "init 6",
    "sudo ", "su -", "doas ",
    "chmod 777", "chown -R root",
    "pkill -f valen", "killall python", "kill -9 1",
]

_BLOCKED_RE = [re.compile(p) for p in ALWAYS_BLOCKED]

# Heurística de classificação de comandos shell por binário inicial.
_READ_ONLY_CMDS = {"ls", "cat", "ps", "df", "du", "pwd", "whoami", "echo",
                   "head", "tail", "grep", "find", "stat", "wc", "env", "date",
                   "uname", "hostname", "uptime", "free", "which", "id"}
_REVERSIBLE_CMDS = {"mkdir", "cp", "touch", "ln", "tee", "curl", "wget", "git",
                    "python", "python3", "pip", "uv", "node", "npm"}
_DESTRUCTIVE_CMDS = {"rm", "mv", "truncate", "shred", "dd"}
_SYSTEM_CMDS = {"systemctl", "service", "docker", "docker-compose", "apt",
                "apt-get", "yum", "dnf", "kill", "pkill", "killall", "mount",
                "umount", "iptables", "ufw", "modprobe"}


class SandboxViolation(Exception):
    """Levantada quando um comando casa com um padrão ALWAYS_BLOCKED."""


def _normalize(command: str) -> str:
    """Normaliza o comando para reduzir bypass trivial (espaços/caixa)."""
    return re.sub(r"\s+", " ", command.strip())


def is_blocked(command: str) -> bool:
    """True se o comando casa com qualquer padrão ALWAYS_BLOCKED."""
    norm = _normalize(command)
    return any(rx.search(norm) for rx in _BLOCKED_RE)


def assert_not_blocked(command: str) -> None:
    """Levanta SandboxViolation se o comando for sempre-bloqueado."""
    if is_blocked(command):
        raise SandboxViolation(f"comando bloqueado pelo sandbox: {command!r}")


def classify_command(command: str) -> ExecutionTier:
    """Classifica um comando shell em um ExecutionTier (heurística conservadora).

    Na dúvida, eleva o tier (default SYSTEM_LEVEL) — fail-safe, não fail-open.
    """
    norm = _normalize(command)
    try:
        tokens = shlex.split(norm)
    except ValueError:
        return ExecutionTier.SYSTEM_LEVEL
    if not tokens:
        return ExecutionTier.READ_ONLY

    binary = tokens[0].rsplit("/", 1)[-1]
    flags = " ".join(tokens[1:])

    # sed -i e redirecionamentos de escrita são destrutivos
    if binary == "sed" and "-i" in tokens:
        return ExecutionTier.DESTRUCTIVE
    if binary in _SYSTEM_CMDS:
        return ExecutionTier.SYSTEM_LEVEL
    if binary in _DESTRUCTIVE_CMDS:
        return ExecutionTier.DESTRUCTIVE
    # curl/wget com método de escrita sobe de READ_ONLY
    if binary in {"curl", "wget"} and re.search(r"-X\s+(POST|PUT|DELETE|PATCH)", flags):
        return ExecutionTier.REVERSIBLE
    if binary in _REVERSIBLE_CMDS:
        return ExecutionTier.REVERSIBLE
    if binary in _READ_ONLY_CMDS:
        return ExecutionTier.READ_ONLY

    return ExecutionTier.SYSTEM_LEVEL


def requires_approval(tier: ExecutionTier) -> bool:
    """True se o tier exige aprovação explícita antes de executar."""
    return tier in REQUIRES_APPROVAL
