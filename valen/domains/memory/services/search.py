"""MemorySearchService — busca e gestão de notas do NeuroValen.

Busca híbrida: scoring por palavra-chave (título > tags > conteúdo) com boost de
prioridade. A camada vetorial (Qdrant) é um gancho opcional para a Fase 4+; na
ausência dela, o ranking lexical já entrega resultados úteis.
"""

from __future__ import annotations

import re

from valen.domains.memory.entities.note import Note, NoteType, Priority
from valen.domains.memory.repositories.base import IMemoryRepository

_WORD_RE = re.compile(r"\w+", re.UNICODE)
_PRIORITY_BOOST = {"high": 1.5, "medium": 1.0, "low": 0.7}


def _tokens(text: str) -> list[str]:
    return [t.lower() for t in _WORD_RE.findall(text)]


class MemorySearchService:
    """Operações de alto nível sobre o repositório de notas."""

    def __init__(self, repo: IMemoryRepository) -> None:
        self.repo = repo

    async def create(
        self,
        title: str,
        content: str,
        note_type: NoteType = "concept",
        tags: list[str] | None = None,
        priority: Priority = "medium",
        created_by: str | None = None,
    ) -> Note:
        note = Note(
            title=title, content=content, note_type=note_type,
            tags=tags or [], priority=priority, created_by=created_by,
        )
        return await self.repo.add(note)

    async def get(self, note_id: str) -> Note | None:
        return await self.repo.get(note_id)

    async def delete(self, note_id: str) -> bool:
        return await self.repo.delete(note_id)

    def _score(self, note: Note, terms: list[str]) -> float:
        title_t = _tokens(note.title)
        tag_t = _tokens(" ".join(note.tags))
        body_t = _tokens(note.content)
        score = 0.0
        for term in terms:
            score += 3.0 * title_t.count(term)
            score += 2.0 * tag_t.count(term)
            score += 1.0 * body_t.count(term)
        return score * _PRIORITY_BOOST.get(note.priority, 1.0)

    async def search(
        self,
        query: str,
        limit: int = 10,
        note_type: NoteType | None = None,
        tags: list[str] | None = None,
    ) -> list[Note]:
        """Retorna notas ordenadas por relevância ao query (+ filtros opcionais)."""
        terms = _tokens(query)
        notes = await self.repo.all()
        if note_type:
            notes = [n for n in notes if n.note_type == note_type]
        if tags:
            wanted = set(tags)
            notes = [n for n in notes if wanted & set(n.tags)]

        if not terms:
            # sem query: mais recentes primeiro
            return sorted(notes, key=lambda n: n.created_at, reverse=True)[:limit]

        scored = [(self._score(n, terms), n) for n in notes]
        scored = [(s, n) for s, n in scored if s > 0]
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [n for _, n in scored[:limit]]
