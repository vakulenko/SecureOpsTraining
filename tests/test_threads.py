"""Test the thread panel: current thread, new thread, and reopening earlier ones.

Drives the real Streamlit app headlessly. The workflow itself is not exercised here --
these tests cover the thread lifecycle only, so they need no API key.
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).parent.parent / "src" / "app.py")


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """Point the conversation store at a temp file, never the developer's database."""
    monkeypatch.setenv("SOC_DB_PATH", str(tmp_path / "threads.db"))


def start():
    return AppTest.from_file(APP, default_timeout=60).run()


def sidebar_button(app, text):
    return next((b for b in app.sidebar.button if text in b.label), None)


def thread_buttons(app):
    """Buttons for earlier threads carry a "title · count" label."""
    return [b for b in app.sidebar.button if " · " in b.label]


def seed(app, messages):
    """Put a conversation into the current thread without running the graph."""
    for role, content in messages:
        app.session_state.conversation_history.append({"role": role, "content": content})
        from src.utils.conversation_store import save_message

        save_message(app.session_state.thread_id, role, content)


def test_a_thread_id_exists_on_startup():
    """Every session starts on a thread, and it is shown."""
    app = start()

    assert app.session_state.thread_id
    assert any("Current thread" in c.value for c in app.sidebar.caption)


def test_no_earlier_threads_on_a_fresh_database():
    """A first run has nothing to reopen."""
    app = start()

    assert thread_buttons(app) == []
    assert any("No earlier threads" in c.value for c in app.sidebar.caption)


def test_new_thread_starts_an_empty_conversation():
    """Starting a new thread clears the transcript and changes the id."""
    app = start()
    seed(app, [("user", "check malware on DEV-001"), ("assistant", "clean")])
    first_id = app.session_state.thread_id

    sidebar_button(app, "New thread").click().run()

    assert app.session_state.thread_id != first_id
    assert app.session_state.conversation_history == []


def test_the_previous_thread_becomes_reopenable():
    """After starting a new thread, the old one is listed with its first message."""
    app = start()
    seed(app, [("user", "check malware on DEV-001"), ("assistant", "clean")])

    sidebar_button(app, "New thread").click().run()
    buttons = thread_buttons(app)

    assert len(buttons) == 1
    assert "check malware on DEV-001" in buttons[0].label
    assert buttons[0].label.strip().endswith("2"), "message count should be shown"


def test_reopening_a_thread_restores_its_messages():
    """Clicking an earlier thread loads its transcript and switches to its id."""
    app = start()
    seed(app, [("user", "check malware on DEV-001"), ("assistant", "clean")])
    first_id = app.session_state.thread_id

    sidebar_button(app, "New thread").click().run()
    thread_buttons(app)[0].click().run()

    assert app.session_state.thread_id == first_id
    assert [m["content"] for m in app.session_state.conversation_history] == [
        "check malware on DEV-001",
        "clean",
    ]


def test_the_current_thread_is_not_listed_as_an_earlier_one():
    """You cannot switch to the thread you are already on."""
    app = start()
    seed(app, [("user", "hello"), ("assistant", "hi")])
    app.run()

    for button in thread_buttons(app):
        assert app.session_state.thread_id not in button.key


def test_thread_controls_are_locked_while_an_approval_is_pending():
    """Switching mid-approval would strand the pending action on the other thread."""
    app = start()
    seed(app, [("user", "unlock rjohnson@company.com"), ("assistant", "pending")])
    sidebar_button(app, "New thread").click().run()

    app.session_state.pending_approval = {
        "tool": "unlock_account",
        "args": {"username": "rjohnson@company.com"},
        "description": "",
        "allowed_decisions": ["approve", "reject"],
    }
    app.run()

    assert sidebar_button(app, "New thread").disabled is True
    assert all(button.disabled for button in thread_buttons(app))
    assert app.chat_input[0].disabled is True
