"""Entidades do NeuroValen: Note e NoteLink.

Notas são a unidade de memória de longo prazo. Markdown no corpo + frontmatter
semântico (type, tags, priority). Links `[[outra-nota]]` viram NoteLink.
"""

from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

NoteType = Literal["architecture", "concept", "decision", "log", "agent", "visual"]
Priority = Literal["low", "medium", "high"]

_LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def _now() -> datetime:
    return datetime.now(UTC)


class Note(BaseModel):
    """Uma nota do NeuroValen."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    note_type: NoteType = "concept"
    tags: list[str] = Field(default_factory=list)
    priority: Priority = "medium"
    created_by: str | None = None
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

    def links(self) -> list[str]:
        """Títulos referenciados via `[[...]]` no corpo da nota."""
        return _LINK_RE.findall(self.content)

    def to_markdown(self) -> str:
        """Serializa a nota como Markdown + frontmatter."""
        tags = ", ".join(self.tags)
        return (
            "---\n"
            f"type: {self.note_type}\n"
            f"tags: [{tags}]\n"
            f"created: {self.created_at.date().isoformat()}\n"
            f"priority: {self.priority}\n"
            "---\n\n"
            f"# {self.title}\n\n{self.content}\n"
        )


class NoteLink(BaseModel):
    """Aresta direcionada entre duas notas (origem → alvo por título)."""

    source_id: str
    target_title: str
