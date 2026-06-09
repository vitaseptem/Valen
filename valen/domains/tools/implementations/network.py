"""NetworkTool — requisições HTTP e checagem de saúde de hosts.

Ações: get (READ_ONLY), post (REVERSIBLE), ping (READ_ONLY — HTTP HEAD/GET).
"""

from __future__ import annotations

from typing import Any

import httpx

from valen.domains.tools.base import ToolBase, ToolContext, ToolError
from valen.domains.tools.sandbox import ExecutionTier

_TIER_BY_ACTION = {
    "get": ExecutionTier.READ_ONLY,
    "ping": ExecutionTier.READ_ONLY,
    "post": ExecutionTier.REVERSIBLE,
}


class NetworkTool(ToolBase):
    """Cliente HTTP controlado para os agentes."""

    name = "NetworkTool"
    description = "Requisições HTTP e checagem de saúde de endpoints."
    required_permissions = {"network"}
    risk_level = "medium"
    timeout_seconds = 30
    default_tier = ExecutionTier.REVERSIBLE

    def tier_for(self, action: str, args: dict) -> ExecutionTier:
        return _TIER_BY_ACTION.get(action, ExecutionTier.SYSTEM_LEVEL)

    async def _run(self, action: str, args: dict, context: ToolContext) -> Any:
        url = args.get("url")
        if not url:
            raise ToolError("argumento 'url' obrigatório")
        timeout = float(args.get("timeout", self.timeout_seconds))

        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            if action == "get":
                resp = await client.get(url, headers=args.get("headers"))
            elif action == "post":
                resp = await client.post(
                    url, headers=args.get("headers"), json=args.get("json"),
                    data=args.get("data"),
                )
            elif action == "ping":
                resp = await client.get(url, headers=args.get("headers"))
                return {"url": url, "status": resp.status_code, "ok": resp.is_success}
            else:
                raise ToolError(f"ação desconhecida: {action}")

        body = resp.text
        return {
            "status": resp.status_code,
            "ok": resp.is_success,
            "body": body[:10000],
            "truncated": len(body) > 10000,
        }
