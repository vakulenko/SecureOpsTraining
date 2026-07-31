"""Test that request intake carries context across conversation turns."""

import json

import pytest
from langchain_core.messages import AIMessage

from src.agents import request_intake
from src.agents.request_intake import extract_request_info, format_history


class CapturingLLM:
    """Records the prompt it was given and returns a canned extraction."""

    def __init__(self, entities=None):
        self.prompt = None
        self._entities = entities or {}

    def invoke(self, prompt):
        self.prompt = prompt
        return AIMessage(
            content=json.dumps(
                {
                    "request_type": ["identity_check"],
                    "entities": self._entities,
                    "missing_fields": [],
                    "confidence": 0.9,
                }
            )
        )


@pytest.fixture
def capture_llm(monkeypatch):
    """Replace the real model so these tests need no API key."""

    def _install(entities=None):
        llm = CapturingLLM(entities)
        monkeypatch.setattr(request_intake, "create_llm", lambda settings: llm)
        monkeypatch.setattr(request_intake, "get_settings", lambda: object())
        return llm

    return _install


HISTORY = [
    {"role": "user", "content": "Activity of jsmith@company.com"},
    {"role": "system", "content": "Extracted entities: {'username': 'jsmith@company.com'}"},
    {"role": "assistant", "content": "jsmith downloaded 412 files."},
]


def test_format_history_renders_recent_turns():
    """Prior messages are rendered with their role."""
    rendered = format_history(HISTORY)

    assert "user: Activity of jsmith@company.com" in rendered
    assert "jsmith@company.com" in rendered


def test_format_history_handles_no_history():
    """An empty history is stated explicitly rather than left blank."""
    assert format_history([]) == "(no earlier messages)"
    assert format_history(None) == "(no earlier messages)"


def test_format_history_is_capped():
    """Only the most recent turns are included, to keep the prompt small."""
    long_history = [{"role": "user", "content": f"message {i}"} for i in range(20)]
    rendered = format_history(long_history)

    assert "message 19" in rendered
    assert "message 0" not in rendered


def test_prompt_includes_the_conversation(capture_llm):
    """The earlier username must reach the model.

    It was previously passed into extract_request_info and then dropped, so a follow-up
    like "reset password" had no way to resolve who it was about.
    """
    llm = capture_llm()

    extract_request_info("reset password", HISTORY)

    assert "jsmith@company.com" in llm.prompt
    assert "reset password" in llm.prompt


def test_prompt_without_history_says_so(capture_llm):
    """A first message still produces a well-formed prompt."""
    llm = capture_llm()

    extract_request_info("reset password", [])

    assert "(no earlier messages)" in llm.prompt


def test_carried_forward_entity_is_returned(capture_llm):
    """An entity resolved from history comes back in request_info."""
    capture_llm({"username": "jsmith@company.com"})

    result = extract_request_info("reset password", HISTORY)

    assert result["entities"]["username"] == "jsmith@company.com"
    assert result["missing_fields"] == []
