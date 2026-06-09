"""Contratos e orquestração do sistema de Tools — PILAR CENTRAL do VALEN.

Nada acontece fora deste sistema. Todo acesso a arquivos, shell, rede, memória e
providers passa por `ToolBase.execute`, que aplica em ordem:

    ACL → ALWAYS_BLOCKED → tier/aprovação → dry-run → timeout → Audit Trail

Subclasses implementam apenas `_run` (o trabalho real) e, opcionalmente,
`tier_for` (classificação de risco da ação).
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, ClassVar, Literal

from valen.domains.observability.logging import get_logger
from valen.domains.observability.metrics import TOOL_DURATION, TOOL_EXECUTIONS
from valen.domains.tools.acl import PermissionDenied, check_permissions
from valen.domains.tools.audit import (
    AuditEntry,
    AuditTrail,
    compute_audit_hash,
    hash_args,
)
from valen.domains.tools.sandbox import (
    ExecutionTier,
    SandboxViolation,
    requires_approval,
)

log = get_logger(__name__)

SandboxMode = Literal["safe", "restricted", "docker", "unrestricted"]


@dataclass
class ToolResult:
    """Resultado padronizado de qualquer execução de Tool."""

    ok: bool
    result: Any = None
    error: str | None = None
    duration_ms: int = 0
    audit_hash: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class ToolContext:
    """Contexto de execução: quem chama, com que permissões e em que sandbox."""

    agent_id: str
    user_id: str = "default"
    session_id: str = "default"
    permissions: set[str] = field(default_factory=set)
    sandbox_mode: SandboxMode = "safe"
    dry_run: bool = False
    approved: bool = False  # usuário pré-aprovou ações DESTRUCTIVE/SYSTEM_LEVEL


class ToolError(Exception):
    """Erro de domínio levantado por uma Tool dentro de `_run`."""


class ToolBase:
    """Classe base de toda Tool. Subclasses implementam `_run`."""

    name: ClassVar[str] = "tool"
    description: ClassVar[str] = ""
    version: ClassVar[str] = "1.0.0"
    required_permissions: ClassVar[set[str]] = set()
    risk_level: ClassVar[Literal["low", "medium", "high", "critical"]] = "low"
    timeout_seconds: ClassVar[int] = 60
    default_tier: ClassVar[ExecutionTier] = ExecutionTier.READ_ONLY

    def __init__(self, audit: AuditTrail | None = None) -> None:
        self.audit = audit or AuditTrail()

    # --- pontos de extensão ----------------------------------------------
    def tier_for(self, action: str, args: dict) -> ExecutionTier:
        """Classifica o risco da ação. Override em Tools de risco variável."""
        return self.default_tier

    async def _run(self, action: str, args: dict, context: ToolContext) -> Any:
        """Trabalho real da Tool. DEVE ser implementado pela subclasse."""
        raise NotImplementedError(f"{self.name}._run não implementado")

    # --- orquestração ----------------------------------------------------
    async def execute(
        self, action: str, args: dict, context: ToolContext
    ) -> ToolResult:
        """Executa uma ação aplicando segurança, dry-run, timeout e auditoria."""
        started = time.monotonic()
        args = args or {}
        tier = self.tier_for(action, args)
        occurred_at = datetime.now(UTC).isoformat()
        args_h = hash_args(args)

        async def finish(ok: bool, result: Any, error: str | None) -> ToolResult:
            duration_ms = int((time.monotonic() - started) * 1000)
            TOOL_EXECUTIONS.labels(tool=self.name, tier=tier.value, ok=str(ok)).inc()
            TOOL_DURATION.labels(tool=self.name).observe(duration_ms / 1000)
            audit_h = compute_audit_hash(
                agent_id=context.agent_id, tool_name=self.name, action=action,
                args_hash=args_h, result_ok=ok, occurred_at=occurred_at,
            )
            await self.audit.record(AuditEntry(
                agent_id=context.agent_id, tool_name=self.name, action=action,
                args_hash=args_h, tier=tier.value, sandbox_mode=context.sandbox_mode,
                dry_run=context.dry_run, result_ok=ok, duration_ms=duration_ms,
                audit_hash=audit_h, session_id=context.session_id,
                occurred_at=occurred_at,
            ))
            return ToolResult(
                ok=ok, result=result, error=error,
                duration_ms=duration_ms, audit_hash=audit_h,
                metadata={"tier": tier.value, "tool": self.name, "action": action},
            )

        # 1. ACL
        try:
            check_permissions(context.agent_id, self.required_permissions)
        except PermissionDenied as exc:
            return await finish(False, None, f"permissão negada: {exc}")

        # 2. aprovação por tier (DESTRUCTIVE / SYSTEM_LEVEL)
        if requires_approval(tier) and not context.approved and not context.dry_run:
            return await finish(
                False, None,
                f"ação {action!r} é {tier.value} e requer aprovação explícita",
            )

        # 3. dry-run: não executa, só descreve
        if context.dry_run:
            return await finish(
                True, {"dry_run": True, "would_execute": {"action": action, "args": args}},
                None,
            )

        # 4. execução real com timeout
        try:
            result = await asyncio.wait_for(
                self._run(action, args, context), timeout=self.timeout_seconds
            )
            return await finish(True, result, None)
        except TimeoutError:
            return await finish(False, None, f"timeout após {self.timeout_seconds}s")
        except SandboxViolation as exc:
            return await finish(False, None, f"sandbox: {exc}")
        except (ToolError, PermissionDenied) as exc:
            return await finish(False, None, str(exc))
        except Exception as exc:  # noqa: BLE001 — toda falha vira ToolResult
            log.error("tool_unhandled_error", tool=self.name, action=action, error=str(exc))
            return await finish(False, None, f"erro interno: {exc}")
