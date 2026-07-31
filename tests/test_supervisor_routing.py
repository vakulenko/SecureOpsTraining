"""Test that the supervisor routes to an agent even when the model misbehaves."""

from langchain_core.messages import AIMessage

from src.agents.supervisor import (
    _classify_request_fallback,
    _parse_routing_decision,
    _routing_request,
    _routing_to_actions,
)
from src.utils import ACTION_ENDPOINT, ACTION_RESPONSE

DEVICE_REQUEST = "find the device with hostname workstation-02 and check its status"


def parse(content):
    return _parse_routing_decision([AIMessage(content=content)])


def test_valid_routing_reply_is_used():
    """A well-formed reply routes to the named domain."""
    assert parse('{"domains": ["endpoint"]}') == ["endpoint"]


def test_empty_domains_is_a_real_answer_not_a_failure():
    """{"domains": []} means "nothing handles this" and must not trigger the fallback.

    Distinguishing this from an unreadable reply is the whole point of returning None:
    "What's the weather?" should reach the response generator, not a keyword guess.
    """
    assert parse('{"domains": []}') == []
    assert _routing_to_actions([]) == [ACTION_RESPONSE]


def test_unreadable_replies_report_failure():
    """Anything the parser cannot read returns None so the caller can fall back.

    Previously these produced [] which routed straight to the response generator,
    silently skipping every agent -- the request looked answered but nothing ran.
    """
    for content in ("Route this to endpoint.", "", '{"route": "endpoint"}', "```\nnot json\n```"):
        assert parse(content) is None, content


def test_gemini_content_blocks_are_read():
    """Gemini returns content as blocks rather than a string."""
    message = AIMessage(content=[{"type": "text", "text": '{"domains": ["endpoint"]}'}])

    assert _parse_routing_decision([message]) == ["endpoint"]


def test_json_in_a_markdown_fence_is_read():
    """Models often wrap JSON in a code fence despite being told not to."""
    assert parse('```json\n{"domains": ["identity"]}\n```') == ["identity"]


def test_keyword_fallback_covers_the_failing_request():
    """The fallback must actually route the request that exposed this bug."""
    assert ACTION_ENDPOINT in _classify_request_fallback(DEVICE_REQUEST)


def test_unknown_domains_are_discarded():
    """A hallucinated domain name is dropped rather than routed to a missing node."""
    assert parse('{"domains": ["endpoint", "teleportation"]}') == ["endpoint"]


def test_routing_question_includes_earlier_turns():
    """A bare follow-up carries no routable keyword, so the router needs the history."""
    state = {
        "user_message": "and check its status",
        "conversation_history": [{"role": "user", "content": "check malware on DEV-001"}],
    }
    question = _routing_request(state)

    assert "check malware on DEV-001" in question
    assert "and check its status" in question


def test_first_message_is_routed_without_extra_wrapping():
    """With no history the router just sees the request."""
    state = {"user_message": DEVICE_REQUEST, "conversation_history": []}

    assert _routing_request(state) == DEVICE_REQUEST
