"""Test SQLite conversation persistence."""

from src.utils.conversation_store import (
    delete_thread,
    init_db,
    list_threads,
    load_messages,
    save_message,
)


def test_save_and_load_round_trip(tmp_db):
    """Messages come back in the shape conversation_history uses."""
    save_message("t1", "user", "Is rjohnson locked?", tmp_db)
    save_message("t1", "assistant", "Yes, locked.", tmp_db)

    assert load_messages("t1", tmp_db) == [
        {"role": "user", "content": "Is rjohnson locked?"},
        {"role": "assistant", "content": "Yes, locked."},
    ]


def test_messages_keep_insertion_order(tmp_db):
    """Messages are returned oldest first, not alphabetically."""
    for text in ("zebra", "apple", "mango"):
        save_message("t1", "user", text, tmp_db)

    assert [m["content"] for m in load_messages("t1", tmp_db)] == [
        "zebra",
        "apple",
        "mango",
    ]


def test_threads_are_isolated(tmp_db):
    """One thread's messages never leak into another."""
    save_message("t1", "user", "first thread", tmp_db)
    save_message("t2", "user", "second thread", tmp_db)

    assert len(load_messages("t1", tmp_db)) == 1
    assert load_messages("t2", tmp_db)[0]["content"] == "second thread"


def test_list_threads_reports_count_and_title(tmp_db):
    """Each thread is listed with its message count and first message as the title."""
    save_message("t1", "user", "Investigate jsmith", tmp_db)
    save_message("t1", "assistant", "Found 5 failed logins.", tmp_db)

    threads = list_threads(tmp_db)

    assert len(threads) == 1
    assert threads[0]["thread_id"] == "t1"
    assert threads[0]["message_count"] == 2
    assert threads[0]["title"] == "Investigate jsmith"


def test_delete_thread(tmp_db):
    """Deleting a thread removes its messages and leaves others alone."""
    save_message("t1", "user", "gone soon", tmp_db)
    save_message("t2", "user", "still here", tmp_db)

    delete_thread("t1", tmp_db)

    assert load_messages("t1", tmp_db) == []
    assert load_messages("t2", tmp_db) != []


def test_empty_database_returns_empty(tmp_db):
    """Reading a thread that was never written returns an empty list."""
    init_db(tmp_db)

    assert load_messages("never-used", tmp_db) == []
    assert list_threads(tmp_db) == []


def test_unusable_path_degrades_quietly():
    """A broken database path must not raise: the chat matters more than the history."""
    bad_path = "/nonexistent\x00/bad.db"

    save_message("t1", "user", "hello", bad_path)

    assert load_messages("t1", bad_path) == []
    assert list_threads(bad_path) == []
