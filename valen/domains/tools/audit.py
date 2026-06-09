"""Audit Trail imutável (append-only) com hashing.

Toda execução de Tool gera uma `AuditEntry`. O sink padrão é em memória (para
dev/testes); quando um pool PostgreSQL é injetado, também persiste em `audit_trail`.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol

from valen.domains.observability.logging import get_logger

log = get_logger(__name__)


def hash_args(args: dict[str, Any]) -> str:
    """sha256 determinístico dos argumentos (chaves ordenadas)."""
    blob = json.dumps(args, sort_keys=True, default=str, ensure_ascii=False)
    return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()


def compute_audit_hash(
    *, agent_id: str, tool_name: str, action: str, args_hash: str,
    result_ok: bool, occurred_at: str,
) -> str:
    """Hash imutável da entrada (encadeável no futuro)."""
    blob = f"{occurred_at}|{agent_id}|{tool_name}|{action}|{args_hash}|{result_ok}"
    return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class AuditEntry:
    """Entrada imutável do Audit Trail (espelha a tabela `audit_trail`)."""

    agent_id: str
    tool_name: str
    action: str
    args_hash: str
    tier: str
    sandbox_mode: str
    dry_run: bool
    result_ok: bool
    duration_ms: int
    audit_hash: str
    session_id: str | None = None
    occurred_at: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )


class AuditSink(Protocol):
    """Destino de escrita de entradas de auditoria."""

    async def write(self, entry: AuditEntry) -> None: ...


class InMemoryAuditSink:
    """Sink em memória — usado em dev e testes."""

    def __init__(self) -> None:
        self.entries: list[AuditEntry] = []

    async def write(self, entry: AuditEntry) -> None:
        self.entries.append(entry)


class PostgresAuditSink:
    """Sink que persiste em `audit_trail` via pool asyncpg (append-only)."""

    def __init__(self, pool: Any) -> None:
        self._pool = pool

    async def write(self, entry: AuditEntry) -> None:
        await self._pool.execute(
            """
            INSERT INTO audit_trail
                (agent_id, tool_name, action, args_hash, tier, sandbox_mode,
                 dry_run, result_ok, duration_ms, audit_hash, session_id, executed_at)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
            """,
            entry.agent_id, entry.tool_name, entry.action, entry.args_hash,
            entry.tier, entry.sandbox_mode, entry.dry_run, entry.result_ok,
            entry.duration_ms, entry.audit_hash, entry.session_id,
            datetime.fromisoformat(entry.occurred_at),
        )


class AuditTrail:
    """Registra entradas no(s) sink(s) configurado(s)."""

    def __init__(self, sinks: list[AuditSink] | None = None) -> None:
        self._sinks: list[AuditSink] = sinks or [InMemoryAuditSink()]

    @property
    def primary(self) -> AuditSink:
        return self._sinks[0]

    def add_sink(self, sink: AuditSink) -> None:
        self._sinks.append(sink)

    async def record(self, entry: AuditEntry) -> None:
        """Persiste a entrada em todos os sinks. Falha de sink não derruba a Tool."""
        for sink in self._sinks:
            try:
                await sink.write(entry)
            except Exception as exc:  # noqa: BLE001 — auditoria nunca derruba execução
                log.error("audit_sink_failed", sink=type(sink).__name__, error=str(exc))
        log.info("audit", **asdict(entry))
