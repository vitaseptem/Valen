"""MemoryTool — único ponto de acesso ao NeuroValen.

Nenhum agente fala com a memória direto; tudo passa por aqui.
Ações: remember, recall, get, forget. Ações de escrita são REVERSIBLE.
"""

from __future__ import annotations

from typing import Any

from valen.domains.memory.services.search import MemorySearchService
from valen.domains.tools.base import ToolBase, ToolContext, ToolError
from valen.domains.tools.sandbox import ExecutionTier

_TIER_BY_ACTION = {
    "recall": ExecutionTier.READ_ONLY,
    "get": ExecutionTier.READ_ONLY,
    "remember": ExecutionTier.REVERSIBLE,
    "forget": ExecutionTier.DESTRUCTIVE,
}


class MemoryTool(ToolBase):
    """Leitura/escrita no NeuroValen via MemorySearchService."""

    name = "MemoryTool"
    description = "Acesso ao NeuroValen (memória de longo prazo)."
    required_permissions = {"memory"}
    risk_level = "medium"
    default_tier = ExecutionTier.REVERSIBLE

    def __init__(self, service: MemorySearchService, audit=None) -> None:
        super().__init__(audit=audit)
        self.service = service

    def tier_for(self, action: str, args: dict) -> ExecutionTier:
        return _TIER_BY_ACTION.get(action, ExecutionTier.SYSTEM_LEVEL)

    async def _run(self, action: str, args: dict, context: ToolContext) -> Any:
        if action == "remember":
            title = args.get("title")
            content = args.get("content")
            if not title or content is None:
                raise ToolError("'title' e 'content' obrigatórios para remember")
            note = await self.service.create(
                title=title,
                content=content,
                note_type=args.get("note_type", "concept"),
                tags=args.get("tags", []),
                priority=args.get("priority", "medium"),
                created_by=context.agent_id,
            )
            return {"id": note.id, "title": note.title}

        if action == "recall":
            query = args.get("query", "")
            notes = await self.service.search(
                query=query,
                limit=int(args.get("limit", 5)),
                note_type=args.get("note_type"),
                tags=args.get("tags"),
            )
            return [
                {"id": n.id, "title": n.title, "note_type": n.note_type,
                 "tags": n.tags, "content": n.content}
                for n in notes
            ]

        if action == "get":
            note = await self.service.get(args.get("id", ""))
            if not note:
                raise ToolError(f"nota não encontrada: {args.get('id')}")
            return note.model_dump(mode="json")

        if action == "forget":
            ok = await self.service.delete(args.get("id", ""))
            if not ok:
                raise ToolError(f"nota não encontrada: {args.get('id')}")
            return {"forgotten": args.get("id")}

        raise ToolError(f"ação desconhecida: {action}")
