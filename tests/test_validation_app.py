"""Test the Streamlit validation harness by driving its widgets headlessly.

Uses Streamlit's own AppTest, so the approval buttons are really clicked. Without this,
a broken harness would only show up when someone opens a browser.
"""

from streamlit.testing.v1 import AppTest

APP = "scripts/validate_identity_app.py"
UNLOCK_EXAMPLE = "Unlock rjohnson@company.com"
STATUS_EXAMPLE = "Is rjohnson@company.com locked?"


def start():
    """Load the app in scripted mode (its default) and run the first render."""
    return AppTest.from_file(APP, default_timeout=60).run()


def click(app, label: str):
    """Click a button by its visible label."""
    matches = [button for button in app.button if button.label == label]
    assert matches, f"no button labelled {label!r}"

    return matches[0].click().run()


def test_app_renders_without_error():
    """The harness loads cleanly."""
    app = start()

    assert not app.exception
    assert app.chat_input[0].disabled is False


def test_sensitive_request_pauses_and_disables_input():
    """Asking to unlock an account shows an approval prompt and blocks further chat."""
    app = click(start(), UNLOCK_EXAMPLE)

    assert not app.exception
    assert any("Approval required" in warning.value for warning in app.warning)
    assert "unlock_account" in app.code[0].value

    labels = [button.label for button in app.button]
    assert "Approve" in labels and "Reject" in labels
    assert app.chat_input[0].disabled is True


def test_approve_button_executes_the_action():
    """Clicking Approve runs the tool and reports it."""
    app = click(click(start(), UNLOCK_EXAMPLE), "Approve")

    assert not app.exception
    assert [message.value for message in app.success] == ["unlock_account: unlocked"]
    assert app.chat_input[0].disabled is False


def test_reject_button_does_not_execute_the_action():
    """Clicking Reject leaves the tool unrun."""
    app = click(click(start(), UNLOCK_EXAMPLE), "Reject")

    assert not app.exception
    assert [message.value for message in app.success] == []
    assert app.chat_input[0].disabled is False


def test_read_only_request_never_prompts():
    """A status lookup completes without an approval prompt."""
    app = click(start(), STATUS_EXAMPLE)

    assert not app.exception
    assert not app.warning
    assert ("Account status", "locked") in [(m.label, m.value) for m in app.metric]


def test_missing_username_is_surfaced_as_an_error():
    """A request with no email address shows an error instead of guessing a user."""
    app = click(start(), "unlock bob")

    assert not app.exception
    assert any("No username found" in error.value for error in app.error)
