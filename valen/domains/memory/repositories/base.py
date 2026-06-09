"""Repositório de memória do NeuroValen.

`IMemoryRepository` é o contrato (Protocol). `InMemoryRepository` é a
implementação default (dev/testes). Uma implementação PostgreSQL pode ser
injetada sem mudar o resto do sistema.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from valen.domains.memory.entities.note import Note


class IMemoryRepository(Protocol):
    """Contrato de persistência de notas."""

    async def add(self, note: Note) -> Note: ...
    async def get(self, note_id: str) -> Note | None: ...
    async def update(self, note: Note) -> Note | None: ...
    async def delete(self, note_id: str) -> bool: ...
    async def all(self) -> list[Note]: ...


class InMemoryRepository:
    """Repositório em memória — default para dev e testes."""

    def __init__(self) -> None:
        self._notes: dict[str, Note] = {}

    async def add(self, note: Note) -> Note:
        self._notes[note.id] = note
        return note

    async def get(self, note_id: str) -> Note | None:
        return self._notes.get(note_id)

    async def update(self, note: Note) -> Note | None:
        if note.id not in self._notes:
            return None
        note.updated_at = datetime.now(UTC)
        self._notes[note.id] = note
        return note

    async def delete(self, note_id: str) -> bool:
        return self._notes.pop(note_id, None) is not None

    async def all(self) -> list[Note]:
        return list(self._notes.values())
