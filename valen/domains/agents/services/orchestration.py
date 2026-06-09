"""AgentOrchestrationService — coordena os 4 agentes, Tools e Providers.

Toda interação do usuário passa por aqui. Agentes acessam o mundo exclusivamente
via Tools (regra inquebrável) e pensam via ProviderRegistry (com fallback).
"""

from __future__ import annotations

from valen.domains.agents.entities.agent import (
    DEFAULT_AGENTS,
    Agent,
    AgentState,
)
from valen.domains.observability.logging import get_logger
from valen.domains.observability.metrics import AGENT_CHATS
from valen.domains.providers.registry import ProviderRegistry
from valen.domains.tools.acl import PermissionDenied
from valen.domains.tools.base import ToolBase, ToolContext, ToolResult

log = get_logger(__name__)


class ToolRegistry:
    """Registro de instâncias de Tool, acessíveis por nome."""

    def __init__(self, tools: dict[str, ToolBase] | None = None) -> None:
        self._tools: dict[str, ToolBase] = tools or {}

    def register(self, tool: ToolBase) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolBase | None:
        return self._tools.get(name)

    @property
    def names(self) -> list[str]:
        return list(self._tools)


class AgentNotFound(Exception):
    """Agente solicitado não existe (apenas os 4 canônicos)."""


class AgentOrchestrationService:
    """Ponto central de coordenação dos agentes."""

    def __init__(
        self,
        providers: ProviderRegistry,
        tools: ToolRegistry,
        agents: dict[str, Agent] | None = None,
    ) -> None:
        self.providers = providers
        self.tools = tools
        self.agents = agents or {k: v.model_copy() for k, v in DEFAULT_AGENTS.items()}

    def get_agent(self, agent_id: str) -> Agent:
        agent = self.agents.get(agent_id)
        if agent is None:
            raise AgentNotFound(f"agente desconhecido: {agent_id!r} (válidos: {list(self.agents)})")
        return agent

    def list_agents(self) -> list[Agent]:
        return list(self.agents.values())

    def _context_for(self, agent: Agent, *, approved: bool = False,
                     dry_run: bool = False, session_id: str = "default") -> ToolContext:
        """Cria o ToolContext de um agente com seu sandbox e permissões da ACL."""
        from valen.domains.tools.acl import permissions_for
        return ToolContext(
            agent_id=agent.id,
            session_id=session_id,
            permissions=permissions_for(agent.id),
            sandbox_mode=agent.sandbox_mode,
            approved=approved,
            dry_run=dry_run,
        )

    async def use_tool(
        self,
        agent_id: str,
        tool_name: str,
        action: str,
        args: dict | None = None,
        *,
        approved: bool = False,
        dry_run: bool = False,
        session_id: str = "default",
    ) -> ToolResult:
        """Executa uma Tool em nome de um agente (ACL/sandbox aplicados em execute)."""
        agent = self.get_agent(agent_id)
        if tool_name not in agent.tools:
            raise PermissionDenied(f"{agent_id} não tem acesso à {tool_name}")
        tool = self.tools.get(tool_name)
        if tool is None:
            raise AgentNotFound(f"tool não registrada: {tool_name}")
        ctx = self._context_for(agent, approved=approved, dry_run=dry_run,
                                session_id=session_id)
        agent.state = AgentState.ACTING
        try:
            return await tool.execute(action, args or {}, ctx)
        finally:
            agent.state = AgentState.IDLE

    async def chat(
        self, agent_id: str, message: str, *, history: list[dict] | None = None
    ) -> dict:
        """Conversa com um agente: monta o prompt e chama o ProviderRegistry."""
        agent = self.get_agent(agent_id)
        AGENT_CHATS.labels(agent=agent.id).inc()
        agent.state = AgentState.THINKING
        messages: list[dict] = [{"role": "system", "content": agent.system_prompt()}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": message})
        try:
            resp = await self.providers.complete(messages)
            agent.state = AgentState.DONE
            return {
                "agent": agent.id, "symbol": agent.symbol,
                "reply": resp.content, "model": resp.model,
            }
        except Exception as exc:  # noqa: BLE001
            agent.state = AgentState.FAILED
            log.error("agent_chat_failed", agent=agent.id, error=str(exc))
            raise
        finally:
            if agent.state not in (AgentState.DONE, AgentState.FAILED):
                agent.state = AgentState.IDLE
