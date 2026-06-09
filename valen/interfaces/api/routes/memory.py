"""Rotas do NeuroValen: criar e buscar notas."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from valen.interfaces.api.deps import get_kernel_dep
from valen.kernel import Kernel

router = APIRouter(prefix="/memory", tags=["memory"])


class NoteRequest(BaseModel):
    title: str
    content: str
    note_type: str = "concept"
    tags: list[str] = Field(default_factory=list)
    priority: str = "medium"


@router.post("")
async def remember(
    body: NoteRequest, kernel: Kernel = Depends(get_kernel_dep)
) -> dict:
    """Cria uma nota no NeuroValen."""
    note = await kernel.memory_service.create(
        title=body.title, content=body.content, note_type=body.note_type,
        tags=body.tags, priority=body.priority, created_by="api",
    )
    return {"id": note.id, "title": note.title}


@router.get("/search")
async def search(
    q: str = "", limit: int = 5, kernel: Kernel = Depends(get_kernel_dep)
) -> list[dict]:
    """Busca notas por relevância."""
    notes = await kernel.memory_service.search(q, limit=limit)
    return [
        {"id": n.id, "title": n.title, "note_type": n.note_type,
         "tags": n.tags, "content": n.content}
        for n in notes
    ]
