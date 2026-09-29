"""SQLite-backed persistent memory store."""

import sqlite3
from pathlib import Path

from .models import Memory


class SQLiteMemoryStore:
    """Stores durable MARS memories in SQLite."""

    def __init__(self, database_path: str = "data/mars.db") -> None:
        self.database_path = database_path
        self._connection: sqlite3.Connection | None = None

        if database_path == ":memory:":
            self._connection = sqlite3.connect(database_path)
            self._connection.row_factory = sqlite3.Row
        else:
            Path(database_path).parent.mkdir(parents=True, exist_ok=True)

        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        if self._connection is not None:
            return self._connection

        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        connection = self._connect()
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'general',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.commit()

    def add(self, content: str, category: str = "general") -> Memory:
        content = content.strip()
        if not content:
            raise ValueError("Memory content cannot be empty.")

        connection = self._connect()
        existing = connection.execute(
            """
            SELECT id, content, category
            FROM memories
            WHERE LOWER(TRIM(content)) = LOWER(?)
            ORDER BY id DESC
            LIMIT 1
            """,
            (content,),
        ).fetchone()
        if existing is not None:
            return Memory(
                id=existing["id"],
                content=existing["content"],
                category=existing["category"],
            )

        cursor = connection.execute(
            "INSERT INTO memories (content, category) VALUES (?, ?)",
            (content, category),
        )
        connection.commit()
        memory_id = cursor.lastrowid

        return Memory(id=memory_id, content=content, category=category)

    def search(self, query: str, limit: int = 5) -> list[Memory]:
        query = query.strip()
        if not query:
            return []

        terms = [term for term in query.lower().split() if term]
        if not terms:
            return []

        clauses = " OR ".join("LOWER(content) LIKE ?" for _ in terms)
        parameters = [f"%{term}%" for term in terms]

        connection = self._connect()
        rows = connection.execute(
            f"""
            SELECT id, content, category
            FROM memories
            WHERE {clauses}
            ORDER BY id DESC
            LIMIT ?
            """,
            [*parameters, limit],
        ).fetchall()

        return [
            Memory(id=row["id"], content=row["content"], category=row["category"])
            for row in rows
        ]

    def list_recent(self, limit: int = 20) -> list[Memory]:
        connection = self._connect()
        rows = connection.execute(
            """
            SELECT id, content, category
            FROM memories
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        return [
            Memory(id=row["id"], content=row["content"], category=row["category"])
            for row in rows
        ]

    def delete(self, memory_id: int) -> bool:
        connection = self._connect()
        cursor = connection.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        connection.commit()
        return cursor.rowcount > 0

    def delete_matching(self, query: str) -> list[Memory]:
        matches = self.search(query, limit=100)
        for memory in matches:
            if memory.id is not None:
                self.delete(memory.id)
        return matches

    def close(self) -> None:
        """Close the dedicated in-memory connection, if one exists."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def __enter__(self) -> "SQLiteMemoryStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
