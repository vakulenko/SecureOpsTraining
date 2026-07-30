"""Checkpointer factory: durable SQLite when asked for, in-memory otherwise.

LangGraph needs a checkpointer to pause at an approval request and resume afterwards.
InMemorySaver is enough for a single session; SqliteSaver additionally survives an
app restart, so an analyst can approve an action after the process has been restarted.
"""

import os
import sqlite3
from pathlib import Path

from langgraph.checkpoint.memory import InMemorySaver

DEFAULT_DB_PATH = "data/soc_assistant.db"


def get_db_path() -> str:
    """Path to the SQLite file, overridable with SOC_DB_PATH."""
    return os.getenv("SOC_DB_PATH", DEFAULT_DB_PATH)


def create_checkpointer():
    """Return a SqliteSaver when SOC_PERSISTENCE=sqlite, else an InMemorySaver.

    Falls back to InMemorySaver if the optional sqlite package is not installed, so a
    missing dependency degrades the feature instead of breaking the app.
    """
    if os.getenv("SOC_PERSISTENCE", "").lower() != "sqlite":
        return InMemorySaver()

    try:
        from langgraph.checkpoint.sqlite import SqliteSaver
    except ImportError:
        return InMemorySaver()

    db_path = get_db_path()
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    # check_same_thread=False is safe here: SqliteSaver guards the connection with a
    # lock, and Streamlit reruns scripts on different threads.
    connection = sqlite3.connect(db_path, check_same_thread=False)
    checkpointer = SqliteSaver(connection)
    checkpointer.setup()

    return checkpointer
