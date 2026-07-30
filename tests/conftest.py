"""Shared test fixtures: a fake chat model and a temporary database path."""

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage


class FakeToolCallingModel(GenericFakeChatModel):
    """GenericFakeChatModel that can be used with create_agent.

    GenericFakeChatModel returns scripted replies but inherits BaseChatModel.bind_tools,
    which raises NotImplementedError. create_agent always binds tools, so without this
    passthrough every agent test fails before it starts.
    """

    def bind_tools(self, tools, **kwargs):
        return self


def tool_call(name: str, args: dict, call_id: str = "call_1") -> dict:
    """Build a tool call for a scripted AIMessage."""
    return {"name": name, "args": args, "id": call_id, "type": "tool_call"}


@pytest.fixture
def fake_model():
    """Return a factory that builds a fake model from scripted replies.

    Pass AIMessage objects in the order the model should return them, e.g. one with
    tool_calls to trigger a tool, then one with plain text as the final answer.
    """

    def _build(*messages: AIMessage) -> FakeToolCallingModel:
        return FakeToolCallingModel(messages=iter(messages))

    return _build


@pytest.fixture
def tmp_db(tmp_path):
    """Path to a throwaway SQLite file, so tests never touch the real database."""
    return str(tmp_path / "test.db")


@pytest.fixture(autouse=True)
def isolate_mock_writes(tmp_path, monkeypatch):
    """Send every mock-data write to a per-test temp folder.

    unlock_account and request_password_reset now change state, so without this a test
    that unlocks an account would alter what later tests see, and would leave changes in
    the developer's data/runtime folder.
    """
    monkeypatch.setenv("SOC_RUNTIME_DIR", str(tmp_path / "runtime"))
