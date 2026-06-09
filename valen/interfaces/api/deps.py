"""Dependências compartilhadas da API."""

from __future__ import annotations

from fastapi import Request

from valen.kernel import Kernel


def get_kernel_dep(request: Request) -> Kernel:
    """Recupera o Kernel anexado ao app (via lifespan)."""
    return request.app.state.kernel
