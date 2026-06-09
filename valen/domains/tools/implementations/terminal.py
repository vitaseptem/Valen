"""TerminalTool — execução de comandos shell sob Sandbox.

Classifica o tier pelo próprio comando, bloqueia padrões ALWAYS_BLOCKED e executa
de forma assíncrona com timeout. Ação única: `run` (args: command, cwd, timeout).
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from valen.domains.tools.base import ToolBase, ToolContext, ToolError
from valen.domains.tools.sandbox import (
    ExecutionTier,
    assert_not_blocked,
    classify_command,
)


class TerminalTool(ToolBase):
    """Executa comandos shell com classificação de risco e bloqueio de padrões."""

    name = "TerminalTool"
    description = "Execução de comandos shell sob Sandbox."
    required_permissions = {"execute"}
    risk_level = "critical"
    timeout_seconds = 120
    default_tier = ExecutionTier.SYSTEM_LEVEL

    def __init__(self, root: str | Path = ".", audit=None) -> None:
        super().__init__(audit=audit)
        self.root = Path(root).resolve()

    def tier_for(self, action: str, args: dict) -> ExecutionTier:
        command = (args or {}).get("command", "")
        return classify_command(command) if command else ExecutionTier.READ_ONLY

    async def _run(self, action: str, args: dict, context: ToolContext) -> Any:
        if action != "run":
            raise ToolError(f"ação desconhecida: {action}")

        command = args.get("command", "").strip()
        if not command:
            raise ToolError("argumento 'command' obrigatório")

        # Barreira de segurança: padrões nunca executados.
        assert_not_blocked(command)

        cwd = args.get("cwd")
        workdir = (self.root / cwd).resolve() if cwd else self.root
        timeout = int(args.get("timeout", self.timeout_seconds))

        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(workdir),
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except TimeoutError:
            proc.kill()
            await proc.wait()
            raise ToolError(f"comando excedeu timeout de {timeout}s") from None

        return {
            "exit_code": proc.returncode,
            "stdout": stdout.decode("utf-8", "replace"),
            "stderr": stderr.decode("utf-8", "replace"),
            "command": command,
        }
