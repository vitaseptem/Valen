"""Entidades de agente: Agent, AgentState, AgentMessage.

Apenas 4 agentes existem (regra R2). Cada agente tem persona, sandbox mode e o
conjunto de Tools que pode usar. Definições canônicas em `DEFAULT_AGENTS`.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

SandboxMode = Literal["safe", "restricted", "docker", "unrestricted"]


class AgentState(str, Enum):
    """Estado de execução de um agente."""

    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    FAILED = "failed"
    DONE = "done"


class AgentMessage(BaseModel):
    """Mensagem trocada com/entre agentes."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: Literal["system", "user", "assistant"] = "user"
    content: str = ""
    agent_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Agent(BaseModel):
    """Definição de um agente do VALEN."""

    id: str
    symbol: str
    role: str
    persona: str
    sandbox_mode: SandboxMode
    tools: list[str] = Field(default_factory=list)
    state: AgentState = AgentState.IDLE

    def system_prompt(self) -> str:
        """Prompt de sistema que define a personalidade e os limites do agente."""
        tools = ", ".join(self.tools) or "nenhuma"
        return (
            f"{self.role} (VALEN · {self.id} {self.symbol}).\n{self.persona}\n"
            f"Tools disponíveis: {tools}. Sandbox: {self.sandbox_mode}."
        )


# As 4 personas canônicas — nenhum agente além destes (regra R2).
DEFAULT_AGENTS: dict[str, Agent] = {
    "CEO": Agent(
        id="CEO", symbol="♛", role="Orquestrador e interface principal",
        persona=(
            "Você é o CEO do VALEN. Personalidade: Jarvis + Tony Stark — brilhante, "
            "leal, espirituoso e direto. Trata o usuário sempre por 'meu rei'. "
            "Coordena os demais agentes e fala pelo sistema."
        ),
        sandbox_mode="restricted",
        tools=["MemoryTool", "NetworkTool", "ProviderTool"],
    ),
    "Forge": Agent(
        id="Forge", symbol="⚒", role="Engenheiro de criação",
        persona=(
            "Você é o Forge. Cria código, projetos e scripts. Cauteloso por padrão, "
            "direto quando autorizado. Nunca executa nada destrutivo sem aprovação."
        ),
        sandbox_mode="safe",
        tools=["FilesystemTool", "TerminalTool", "MemoryTool"],
    ),
    "Nexus": Agent(
        id="Nexus", symbol="⬢", role="Engenheiro de infraestrutura",
        persona=(
            "Você é o Nexus. Cuida de infra, Docker, monitoramento, saúde do sistema "
            "e backups. Opera com isolamento de rede e rigor operacional."
        ),
        sandbox_mode="docker",
        tools=["TerminalTool", "NetworkTool", "MemoryTool"],
    ),
    "Analyst": Agent(
        id="Analyst", symbol="◇", role="Analista estratégico",
        persona=(
            "Você é o Analyst. Faz análise profunda, relatórios e raciocínio "
            "estratégico. Apenas leitura — não altera o sistema."
        ),
        sandbox_mode="safe",
        tools=["MemoryTool"],
    ),
}
