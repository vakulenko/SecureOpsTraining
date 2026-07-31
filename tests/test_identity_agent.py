"""Test the identity agent node with a fake model, so no API key is needed."""

import pytest
from langchain_core.messages import AIMessage, ToolMessage

from src.agents.identity import (
    _result_from_messages,
    build_identity_agent,
    identity_agent_node,
    run_identity_agent,
)
from tests.conftest import tool_call

RJOHNSON = "rjohnson@company.com"


def test_missing_username_returns_error_without_calling_model():
    """A request with no email address is rejected before any model call."""
    result = identity_agent_node({"user_message": "is bob locked?"})["identity"]

    assert result["error"] == "No username found in the request"
    assert "jsmith@company.com" in result["summary"]


def test_username_taken_from_parsed_entities(fake_model):
    """The username comes from request_info.entities when the intake agent supplied it."""
    agent = build_identity_agent(fake_model(AIMessage(content="Account is locked.")))
    state = {
        "user_message": "check that account",
        "request_info": {"entities": {"username": RJOHNSON}},
    }

    assert run_identity_agent(state, agent)["identity"]["username"] == RJOHNSON


def test_username_is_resolved_from_an_earlier_turn():
    """A follow-up like "reset password" picks up the username from request_info."""
    from src.agents.identity import _find_username

    state = {
        "user_message": "reset password",
        "request_info": {"entities": {"username": RJOHNSON}},
    }

    assert _find_username(state) == RJOHNSON


def test_account_status_is_extracted(fake_model):
    """A check_account_status tool call populates account_status."""
    agent = build_identity_agent(
        fake_model(
            AIMessage(
                content="",
                tool_calls=[tool_call("check_account_status", {"username": RJOHNSON})],
            ),
            AIMessage(content="Account is locked after 7 failed logins."),
        )
    )
    result = run_identity_agent({"user_message": f"is {RJOHNSON} locked?"}, agent)["identity"]

    assert result["account_status"] == "locked"
    assert result["summary"] == "Account is locked after 7 failed logins."
    assert result["error"] is None


def test_login_history_is_extracted(fake_model):
    """A check_login_history tool call populates login_history."""
    agent = build_identity_agent(
        fake_model(
            AIMessage(
                content="",
                tool_calls=[
                    tool_call(
                        "check_login_history",
                        {"username": RJOHNSON, "outcome": "failure"},
                    )
                ],
            ),
            AIMessage(content="Seven failed VPN logins from 198.51.100.7."),
        )
    )
    result = run_identity_agent({"user_message": f"failed logins for {RJOHNSON}"}, agent)["identity"]

    assert len(result["login_history"]) == 7
    assert all(r["outcome"] == "failure" for r in result["login_history"])


def test_model_failure_is_reported_not_raised(fake_model):
    """If the model raises, the node still returns a well-formed result."""

    class BrokenAgent:
        def invoke(self, *args, **kwargs):
            raise RuntimeError("model unavailable")

    result = run_identity_agent({"user_message": f"check {RJOHNSON}"}, BrokenAgent())["identity"]

    assert "model unavailable" in result["error"]
    assert result["account_status"] == "unknown"


def test_approval_interrupt_is_not_swallowed_as_an_error():
    """An approval pause must propagate, not be caught by the generic error handler.

    interrupt() works by raising GraphInterrupt. If the broad `except Exception` in
    run_identity_agent catches it, the graph never pauses and sensitive tools execute
    without approval -- so this guards the approval gate itself.
    """
    from langgraph.errors import GraphInterrupt

    class InterruptingAgent:
        def invoke(self, *args, **kwargs):
            raise GraphInterrupt(())

    with pytest.raises(GraphInterrupt):
        run_identity_agent({"user_message": f"unlock {RJOHNSON}"}, InterruptingAgent())


def test_node_returns_only_the_identity_key(fake_model):
    """The node writes exactly one state key, and fills in every result field."""
    agent = build_identity_agent(fake_model(AIMessage(content="Done.")))
    update = run_identity_agent({"user_message": f"check {RJOHNSON}"}, agent)

    assert list(update) == ["identity"]
    assert set(update["identity"]) == {
        "username",
        "login_history",
        "user_activity",
        "account_status",
        "actions_taken",
        "summary",
        "error",
    }


def test_result_from_messages_records_approved_actions():
    """An executed approval tool is recorded in actions_taken."""
    messages = [
        ToolMessage(
            content='{"username": "rjohnson@company.com", "status": "unlocked"}',
            name="unlock_account",
            tool_call_id="call_1",
        ),
        AIMessage(content="Account unlocked."),
    ]

    result = _result_from_messages(messages, RJOHNSON)

    assert result["actions_taken"] == ["unlock_account: unlocked"]
    assert result["summary"] == "Account unlocked."


def test_summary_handles_gemini_content_blocks():
    """Gemini returns content as blocks; the summary must be readable text, not dicts."""
    messages = [AIMessage(content=[{"type": "text", "text": "Account is locked."}])]

    assert _result_from_messages(messages, RJOHNSON)["summary"] == "Account is locked."


def test_result_from_messages_records_failed_actions():
    """A tool that returned an error is recorded with the error, not as a success."""
    messages = [
        ToolMessage(
            content='{"error": "User not found", "username": "nobody@company.com"}',
            name="unlock_account",
            tool_call_id="call_1",
        ),
        AIMessage(content="That user does not exist."),
    ]

    result = _result_from_messages(messages, "nobody@company.com")

    assert result["actions_taken"] == ["unlock_account: User not found"]
