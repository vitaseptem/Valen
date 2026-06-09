"""Métricas Prometheus do VALEN.

Counters/histograms centrais de execução de Tools e chamadas de agentes. Exponha
`render()` num endpoint /metrics quando quiser scrapping pelo Prometheus.
"""

from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

TOOL_EXECUTIONS = Counter(
    "valen_tool_executions_total",
    "Total de execuções de Tools.",
    ["tool", "tier", "ok"],
)
TOOL_DURATION = Histogram(
    "valen_tool_duration_seconds",
    "Duração das execuções de Tools.",
    ["tool"],
)
AGENT_CHATS = Counter(
    "valen_agent_chats_total",
    "Total de turnos de chat por agente.",
    ["agent"],
)


def render() -> tuple[bytes, str]:
    """Retorna (payload, content_type) para o endpoint /metrics."""
    return generate_latest(), CONTENT_TYPE_LATEST
