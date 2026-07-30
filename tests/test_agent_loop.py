"""Test the shared LLM tool-calling loop, including the HITL approval gate."""

from langchain_core.messages import AIMessage
from langchain_core.tools import tool

from src.utils.agent_loop import run_tool_agent


@tool
def echo(text: str) -> dict:
    """Echo the given text back."""
    return {"echoed": text}


class FakeLLM:
    """Stub chat model returning a scripted sequence of AIMessage responses."""

    def __init__(self, responses: list[AIMessage]):
        self._responses = list(responses)

    def bind_tools(self, _tools):
        return self

    def invoke(self, _messages):
        return self._responses.pop(0)


def test_run_tool_agent_returns_final_text_without_tool_calls():
    llm = FakeLLM([AIMessage(content="no tools needed")])

    final_text, tool_log = run_tool_agent("system", "hello", [echo], llm=llm)

    assert final_text == "no tools needed"
    assert tool_log == []


def test_run_tool_agent_executes_tool_call():
    call_response = AIMessage(
        content="",
        tool_calls=[{"name": "echo", "args": {"text": "hi"}, "id": "1"}],
    )
    final_response = AIMessage(content="done")
    llm = FakeLLM([call_response, final_response])

    final_text, tool_log = run_tool_agent("system", "hello", [echo], llm=llm)

    assert final_text == "done"
    assert tool_log == [
        {"tool": "echo", "args": {"text": "hi"}, "result": {"echoed": "hi"}, "approved": None}
    ]


def test_run_tool_agent_blocks_unapproved_sensitive_tool(monkeypatch):
    monkeypatch.setattr("src.utils.agent_loop.interrupt", lambda payload: False)

    call_response = AIMessage(
        content="",
        tool_calls=[{"name": "echo", "args": {"text": "hi"}, "id": "1"}],
    )
    final_response = AIMessage(content="done")
    llm = FakeLLM([call_response, final_response])

    _, tool_log = run_tool_agent(
        "system", "hello", [echo], approval_required=frozenset({"echo"}), llm=llm
    )

    assert tool_log[0]["approved"] is False
    assert tool_log[0]["result"]["status"] == "denied"


def test_run_tool_agent_executes_approved_sensitive_tool(monkeypatch):
    monkeypatch.setattr("src.utils.agent_loop.interrupt", lambda payload: True)

    call_response = AIMessage(
        content="",
        tool_calls=[{"name": "echo", "args": {"text": "hi"}, "id": "1"}],
    )
    final_response = AIMessage(content="done")
    llm = FakeLLM([call_response, final_response])

    _, tool_log = run_tool_agent(
        "system", "hello", [echo], approval_required=frozenset({"echo"}), llm=llm
    )

    assert tool_log[0]["approved"] is True
    assert tool_log[0]["result"] == {"echoed": "hi"}
