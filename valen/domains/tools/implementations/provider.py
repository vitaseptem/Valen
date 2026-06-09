"""ProviderTool — interface dos agentes com LLMs externos.

Encapsula o ProviderRegistry como uma Tool, sujeita a ACL e auditoria como
qualquer outra. Ação: complete (REVERSIBLE).
"""

from __future__ import annotations

from typing import Any

from valen.domains.providers.registry import ProviderRegistry
from valen.domains.tools.base import ToolBase, ToolContext, ToolError
from valen.domains.tools.sandbox import ExecutionTier


class ProviderTool(ToolBase):
    """Chamada a LLMs via ProviderRegistry (com fallback)."""

    name = "ProviderTool"
    description = "Completar prompts via providers de IA (Groq/Ollama/mock)."
    required_permissions = {"read"}
    risk_level = "low"
    timeout_seconds = 90
    default_tier = ExecutionTier.REVERSIBLE

    def __init__(self, providers: ProviderRegistry, audit=None) -> None:
        super().__init__(audit=audit)
        self.providers = providers

    async def _run(self, action: str, args: dict, context: ToolContext) -> Any:
        if action != "complete":
            raise ToolError(f"ação desconhecida: {action}")
        messages = args.get("messages")
        if not messages:
            prompt = args.get("prompt")
            if not prompt:
                raise ToolError("forneça 'messages' ou 'prompt'")
            messages = [{"role": "user", "content": prompt}]
        resp = await self.providers.complete(messages, args.get("tools"))
        return {"content": resp.content, "model": resp.model, "usage": resp.usage}
