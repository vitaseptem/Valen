"""Tracing OpenTelemetry do VALEN.

Setup mínimo e seguro: se OTEL não estiver configurado, vira no-op silencioso.
O exporter real (OTLP/Sentry) é plugado via variáveis de ambiente nas fases de
operação. `get_tracer` sempre devolve um tracer válido.
"""

from __future__ import annotations

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

_initialized = False


def configure_tracing(service_name: str = "valen") -> None:
    """Inicializa um TracerProvider básico (idempotente)."""
    global _initialized
    if _initialized:
        return
    trace.set_tracer_provider(TracerProvider())
    _initialized = True


def get_tracer(name: str = "valen") -> trace.Tracer:
    """Retorna um tracer. Auto-inicializa na primeira chamada."""
    if not _initialized:
        configure_tracing()
    return trace.get_tracer(name)
