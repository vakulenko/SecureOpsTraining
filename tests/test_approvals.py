"""Test the helpers the UI uses to read and answer an approval pause."""

from src.agents.endpoint import APPROVAL_TOOLS as endpoint_approvals
from src.agents.endpoint import run_endpoint_agent
from src.agents.identity import APPROVAL_TOOLS as identity_approvals
from src.agents.identity import run_identity_agent
from src.agents.incident import APPROVAL_TOOLS as incident_approvals
from src.agents.incident import run_incident_agent
from src.utils.approvals import (
    approval_error_hint,
    build_resume,
    describe_action,
    describe_interrupt,
)


class FakeInterrupt:
    """Stands in for a LangGraph Interrupt, which carries its payload on .value."""

    def __init__(self, value):
        self.value = value


MIDDLEWARE_PAYLOAD = {
    "action_requests": [
        {
            "name": "request_password_reset",
            "args": {"username": "jsmith@company.com"},
            "description": "Identity action pending analyst approval",
        }
    ],
    "review_configs": [
        {
            "action_name": "request_password_reset",
            "allowed_decisions": ["approve", "reject"],
        }
    ],
}


def test_no_interrupt_returns_none():
    """A completed run is not an approval request."""
    assert describe_interrupt({"identity": {}}) is None
    assert describe_interrupt({}) is None


def test_reads_the_approval_request():
    """The pause is flattened into what the UI needs to render."""
    pending = describe_interrupt({"__interrupt__": [FakeInterrupt(MIDDLEWARE_PAYLOAD)]})

    assert pending["tool"] == "request_password_reset"
    assert pending["args"] == {"username": "jsmith@company.com"}
    assert pending["allowed_decisions"] == ["approve", "reject"]


def test_reads_a_streamed_interrupt_tuple():
    """Streaming surfaces the interrupt as a tuple, which must read the same way."""
    pending = describe_interrupt({"__interrupt__": (FakeInterrupt(MIDDLEWARE_PAYLOAD),)})

    assert pending["tool"] == "request_password_reset"


def test_unrecognised_payload_still_reaches_the_analyst():
    """An unexpected pause must be surfaced, not silently dropped."""
    pending = describe_interrupt({"__interrupt__": [FakeInterrupt({"something": "else"})]})

    assert pending is not None
    assert pending["allowed_decisions"] == ["approve", "reject"]


def test_malformed_approval_gets_an_actionable_message():
    """Answering an interrupt with a bare "approve" must explain the right format.

    The middleware does resume["decisions"], so a plain string or bool raises a cryptic
    TypeError. Easy to hit by hand in LangGraph Studio.
    """
    for exc in (
        TypeError("string indices must be integers, not 'str'"),
        TypeError("'bool' object is not subscriptable"),
    ):
        hint = approval_error_hint(exc)
        assert '{"decisions": [{"type": "approve"}]}' in hint


def test_unrelated_errors_are_reported_unchanged():
    """A real failure must not be mislabelled as an approval-format problem."""
    assert approval_error_hint(RuntimeError("model outage")) == "model outage"
    assert approval_error_hint(TypeError("takes 2 positional arguments")) == (
        "takes 2 positional arguments"
    )


def test_every_approval_gated_agent_explains_a_malformed_response():
    """All three agents with approval gates must give the same actionable message.

    They share the middleware, so they share the trap: answering an interrupt with a
    bare "approve" raises TypeError inside the agent and gets caught as a generic error.
    """

    class BadResume:
        def invoke(self, *args, **kwargs):
            raise TypeError("string indices must be integers, not 'str'")

    agents = [
        (run_identity_agent, "identity", {"user_message": "unlock a@b.com"}),
        (run_endpoint_agent, "endpoint", {"user_message": "scan DEV-001"}),
        (run_incident_agent, "incident", {"user_message": "escalate INC-2025-001"}),
    ]

    for run_agent, key, state in agents:
        result = run_agent(state, BadResume())[key]

        assert '{"decisions": [{"type": "approve"}]}' in result["error"], key
        assert '{"decisions": [{"type": "approve"}]}' in result["summary"], key


def test_approval_prompt_is_readable_not_a_function_call():
    """The analyst sees plain English, not a tool signature."""
    action = describe_action("request_password_reset", {"username": "jsmith@company.com"})

    assert action["title"] == "Send password reset"
    assert "jsmith@company.com" in action["detail"]
    assert "request_password_reset(" not in action["detail"]
    assert action["effect"]


def test_every_gated_tool_has_readable_wording():
    """Each approval-gated tool across all three agents must have an entry.

    Without this, adding a gated tool silently falls back to showing raw arguments.
    """
    gated = (
        set(identity_approvals) | set(endpoint_approvals) | set(incident_approvals)
    )

    for tool in gated:
        action = describe_action(tool, {})
        assert tool not in action["title"], f"{tool} has no readable wording"


def test_unknown_tool_still_renders_something():
    """A tool missing from the table must not produce a blank prompt."""
    action = describe_action("brand_new_tool", {"foo": "bar"})

    assert action["title"] == "Brand new tool"
    assert "brand_new_tool" in action["detail"]


def test_unexpected_arguments_fall_back_instead_of_raising():
    """Wrong argument names must not crash the approval prompt or mis-describe it."""
    action = describe_action("unlock_account", {"wrong_key": "x"})

    assert "unlock_account" in action["detail"]
    assert "wrong_key" in action["detail"]


def test_build_resume_shapes():
    """Approve and reject produce the payload the middleware expects."""
    assert build_resume(True) == {"decisions": [{"type": "approve"}]}
    assert build_resume(False) == {"decisions": [{"type": "reject"}]}
    assert build_resume(False, "no") == {
        "decisions": [{"type": "reject", "message": "no"}]
    }
