"""
Server-side conversation memory: persists each turn to a local SQLite file
so a client can continue a conversation across requests (and process
restarts) by passing back a conversation_id, instead of resending the
full message_history every time.

Rows are scoped by (tenant_id, conversation_id) so one tenant can never
read another tenant's conversation, even by guessing/reusing an id --
same isolation principle as artemis/auth.py's collection namespacing.
"""

import os
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

DEFAULT_HISTORY_LIMIT = 20


def _default_db_path() -> str:
    p = os.environ.get("ARTEMIS_MEMORY_DB_PATH")
    if p:
        return p
    base = os.path.join(os.getcwd(), ".artemis")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "conversations.db")


def new_conversation_id() -> str:
    return uuid.uuid4().hex


class ConversationStore:
    """
    SQLite-backed conversation history, keyed by (tenant_id, conversation_id).

    Opens a fresh connection per call and closes it afterward for a real
    file path -- sqlite3.connect() on a local file is cheap, and this avoids
    any cross-thread/cross-request connection-sharing concerns. ":memory:"
    is the one exception: each ":memory:" connection is its own isolated
    database, so a fresh connection per call would silently lose everything
    written by the previous call -- one connection is kept open for the
    store's lifetime instead (used by tests; not the production default).
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or _default_db_path()
        self._is_memory = self.db_path == ":memory:"
        self._shared_conn: Optional[sqlite3.Connection] = (
            sqlite3.connect(self.db_path, check_same_thread=False) if self._is_memory else None
        )
        if not self._is_memory:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        if self._is_memory:
            yield self._shared_conn
            self._shared_conn.commit()
            return
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _ensure_schema(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversation_messages (
                    tenant_id TEXT NOT NULL,
                    conversation_id TEXT NOT NULL,
                    turn_index INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    PRIMARY KEY (tenant_id, conversation_id, turn_index)
                )
                """
            )

    def append_turn(self, tenant_id: str, conversation_id: str, role: str, content: str) -> None:
        if not content:
            return
        with self._conn() as conn:
            row = conn.execute(
                "SELECT COALESCE(MAX(turn_index), -1) + 1 FROM conversation_messages "
                "WHERE tenant_id = ? AND conversation_id = ?",
                (tenant_id, conversation_id),
            ).fetchone()
            next_index = row[0] if row else 0
            conn.execute(
                "INSERT INTO conversation_messages (tenant_id, conversation_id, turn_index, role, content) "
                "VALUES (?, ?, ?, ?, ?)",
                (tenant_id, conversation_id, next_index, role, content),
            )

    def get_history(
        self,
        tenant_id: str,
        conversation_id: str,
        limit: int = DEFAULT_HISTORY_LIMIT,
    ) -> List[Dict[str, Any]]:
        """Most recent `limit` messages, in chronological order."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT role, content FROM conversation_messages "
                "WHERE tenant_id = ? AND conversation_id = ? "
                "ORDER BY turn_index DESC LIMIT ?",
                (tenant_id, conversation_id, limit),
            ).fetchall()
        return [{"role": role, "content": content} for role, content in reversed(rows)]


__all__ = ["ConversationStore", "new_conversation_id", "DEFAULT_HISTORY_LIMIT"]
