"""Memory orchestration for MARS.

Copyright (c) 2026 Destiny Growrich. All rights reserved.
Project: MARS (Multifunctional Autonomous Reasoning System)
Provenance marker: MARS-DG-2026
"""

from .formation import MemoryCandidate, MemoryExtractor, MemoryFormation
from .models import Memory
from .store import SQLiteMemoryStore


class MemoryManager:
    """High-level interface for storing, retrieving, and forming memories."""

    def __init__(
        self,
        store: SQLiteMemoryStore,
        formation: MemoryExtractor | None = None,
    ) -> None:
        self.store = store
        self.formation = formation or MemoryFormation()

    def remember(self, content: str, category: str = "general") -> Memory:
        return self.store.add(content, category)

    def forget(self, query: str) -> list[Memory]:
        return self.store.delete_matching(query)

    def recall(self, query: str, limit: int = 5) -> list[Memory]:
        return self.store.search(query, limit=limit)

    def recent(self, limit: int = 20) -> list[Memory]:
        return self.store.list_recent(limit=limit)

    def extract(self, message: str) -> MemoryCandidate | None:
        return self.formation.extract(message)

    def remember_if_explicit(self, message: str) -> Memory | None:
        candidate = self.extract(message)
        if candidate is None:
            return None
        return self.remember(candidate.content, candidate.category)

    def remember_if_worthwhile(self, message: str) -> Memory | None:
        candidate = self.extract(message)
        if candidate is None:
            return None
        return self.remember(candidate.content, candidate.category)
