"""Rotas de saúde e status do sistema."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from valen import __version__
from valen.interfaces.api.deps import get_kernel_dep
from valen.kernel import Kernel

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Healthcheck usado pelo Docker Compose e pelo Nexus."""
    return {"status": "ok", "version": __version__}


@router.get("/status")
async def status(kernel: Kernel = Depends(get_kernel_dep)) -> dict:
    """Status detalhado: agentes, tools e providers ativos."""
    return {
        "version": __version__,
        "env": kernel.settings.valen_env,
        "agents": [
            {"id": a.id, "symbol": a.symbol, "state": a.state.value}
            for a in kernel.orchestrator.list_agents()
        ],
        "tools": kernel.tools.names,
        "providers": kernel.providers.names,
    }
