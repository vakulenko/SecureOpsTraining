"""Conversation history stored in SQLite so chats survive an app restart.

Uses only the Python standard library. Every function takes an optional db_path so
tests can point at a temporary file. No function raises: if persistence fails the chat
must keep working, so errors are swallowed the same way load_mock_data does.
"""

import sqlite3
from pathlib import Path

from src.utils.checkpointer import get_db_path

# A database error, an unusable directory, or a malformed path must all degrade to
# "no history" rather than break the chat.
_STORAGE_ERRORS = (sqlite3.Error, OSError, ValueError)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id  TEXT NOT NULL,
    role       TEXT NOT NULL,
    content    TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_conversations_thread ON conversations(thread_id, id);
"""


def _connect(db_path: str | None = None) -> sqlite3.Connection:
    """Open the database, creating the file, parent directory and schema if needed."""
    path = db_path or get_db_path()
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(path, check_same_thread=False)
    connection.executescript(_SCHEMA)

    return connection


def init_db(db_path: str | None = None) -> None:
    """Create the conversations table if it does not exist. Safe to call repeatedly."""
    try:
        with _connect(db_path) as connection:
            connection.commit()
    except _STORAGE_ERRORS:
        pass


def save_message(
    thread_id: str, role: str, content: str, db_path: str | None = None
) -> None:
    """Append one chat message to a conversation thread."""
    try:
        with _connect(db_path) as connection:
            connection.execute(
                "INSERT INTO conversations (thread_id, role, content) VALUES (?, ?, ?)",
                (thread_id, role, content),
            )
    except _STORAGE_ERRORS:
        pass


def load_messages(thread_id: str, db_path: str | None = None) -> list[dict]:
    """Load one thread's messages, oldest first, as [{"role": ..., "content": ...}].

    Returns the same shape as SOCWorkflowState["conversation_history"].
    """
    try:
        with _connect(db_path) as connection:
            rows = connection.execute(
                "SELECT role, content FROM conversations WHERE thread_id = ? ORDER BY id",
                (thread_id,),
            ).fetchall()
    except _STORAGE_ERRORS:
        return []

    return [{"role": role, "content": content} for role, content in rows]


def list_threads(db_path: str | None = None) -> list[dict]:
    """List saved conversations, most recently updated first."""
    try:
        with _connect(db_path) as connection:
            rows = connection.execute(
                """
                SELECT c.thread_id,
                       COUNT(*)        AS message_count,
                       MAX(c.created_at) AS updated_at,
                       (SELECT content FROM conversations
                         WHERE thread_id = c.thread_id ORDER BY id LIMIT 1) AS first_content
                FROM conversations c
                GROUP BY c.thread_id
                ORDER BY MAX(c.id) DESC
                """
            ).fetchall()
    except _STORAGE_ERRORS:
        return []

    return [
        {
            "thread_id": thread_id,
            "message_count": message_count,
            "updated_at": updated_at,
            "title": (first_content or "")[:60],
        }
        for thread_id, message_count, updated_at, first_content in rows
    ]


def delete_thread(thread_id: str, db_path: str | None = None) -> None:
    """Delete one conversation's messages."""
    try:
        with _connect(db_path) as connection:
            connection.execute(
                "DELETE FROM conversations WHERE thread_id = ?", (thread_id,)
            )
    except _STORAGE_ERRORS:
        pass
