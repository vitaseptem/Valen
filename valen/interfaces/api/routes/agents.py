"""Rotas dos agentes: listagem, chat e execução de Tools."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from valen.domains.agents.services.orchestration import AgentNotFound
from valen.domains.tools.acl import PermissionDenied
from valen.interfaces.api.deps import get_kernel_dep
from valen.kernel import Kernel

router = APIRouter(prefix="/agents", tags=["agents"])


class ChatRequest(BaseModel):
    message: str
    history: list[dict] | None = None


class ToolRequest(BaseModel):
    tool: str
    action: str
    args: dict = Field(default_factory=dict)
    approved: bool = False
    dry_run: bool = False


@router.get("")
async def list_agents(kernel: Kernel = Depends(get_kernel_dep)) -> list[dict]:
    """Lista os 4 agentes e seus papéis."""
    return [
        {"id": a.id, "symbol": a.symbol, "role": a.role,
         "sandbox_mode": a.sandbox_mode, "tools": a.tools, "state": a.state.value}
        for a in kernel.orchestrator.list_agents()
    ]


@router.post("/{agent_id}/chat")
async def chat(
    agent_id: str, body: ChatRequest, kernel: Kernel = Depends(get_kernel_dep)
) -> dict:
    """Conversa com um agente (usa ProviderRegistry com fallback)."""
    try:
        return await kernel.orchestrator.chat(agent_id, body.message, history=body.history)
    except AgentNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{agent_id}/tools")
async def run_tool(
    agent_id: str, body: ToolRequest, kernel: Kernel = Depends(get_kernel_dep)
) -> dict:
    """Executa uma Tool em nome de um agente (ACL/sandbox/audit aplicados)."""
    try:
        result = await kernel.orchestrator.use_tool(
            agent_id, body.tool, body.action, body.args,
            approved=body.approved, dry_run=body.dry_run,
        )
    except AgentNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return {
        "ok": result.ok, "result": result.result, "error": result.error,
        "duration_ms": result.duration_ms, "audit_hash": result.audit_hash,
        "metadata": result.metadata,
    }
