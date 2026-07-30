"""Test the endpoint and incident agent nodes with a fake model, no API key needed."""

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, ToolMessage

from src.agents.endpoint import build_endpoint_agent, run_endpoint_agent
from src.agents.incident import build_incident_agent, run_incident_agent


class FakeToolCallingModel(GenericFakeChatModel):
    """GenericFakeChatModel that can be used with create_agent.

    GenericFakeChatModel returns scripted replies but inherits BaseChatModel.bind_tools,
    which raises NotImplementedError. create_agent always binds tools, so without this
    passthrough every agent test fails before it starts.
    """

    def bind_tools(self, tools, **kwargs):
        return self


def fake_model(*messages: AIMessage) -> FakeToolCallingModel:
    return FakeToolCallingModel(messages=iter(messages))


def tool_call(name: str, args: dict, call_id: str = "call_1") -> dict:
    """Build a tool call for a scripted AIMessage."""
    return {"name": name, "args": args, "id": call_id, "type": "tool_call"}


# --- endpoint agent ---------------------------------------------------------


def test_endpoint_status_is_extracted():
    agent = build_endpoint_agent(
        fake_model(
            AIMessage(
                content="",
                tool_calls=[tool_call("check_endpoint_status", {"device_id": "DEV-001"})],
            ),
            AIMessage(content="DEV-001 is healthy."),
        )
    )
    result = run_endpoint_agent({"user_message": "check DEV-001"}, agent)["endpoint"]

    assert result["error"] is None
    assert result["summary"] == "DEV-001 is healthy."


def test_endpoint_model_failure_is_reported_not_raised():
    class BrokenAgent:
        def invoke(self, *args, **kwargs):
            raise RuntimeError("model unavailable")

    result = run_endpoint_agent({"user_message": "check DEV-001"}, BrokenAgent())["endpoint"]

    assert "model unavailable" in result["error"]
    assert result["device_status"] == {}


def test_endpoint_approval_interrupt_is_not_swallowed_as_an_error():
    """interrupt() works by raising GraphInterrupt; a broad except must not catch it,
    or the graph never pauses and scan_device runs without approval."""
    from langgraph.errors import GraphInterrupt

    class InterruptingAgent:
        def invoke(self, *args, **kwargs):
            raise GraphInterrupt(())

    with pytest.raises(GraphInterrupt):
        run_endpoint_agent({"user_message": "scan DEV-002"}, InterruptingAgent())


def test_endpoint_node_returns_only_the_endpoint_key():
    agent = build_endpoint_agent(fake_model(AIMessage(content="Done.")))
    update = run_endpoint_agent({"user_message": "check DEV-001"}, agent)

    assert list(update) == ["endpoint"]
    assert set(update["endpoint"]) == {
        "device_status",
        "malware_details",
        "actions_taken",
        "summary",
        "error",
    }


def test_endpoint_scan_device_is_recorded_in_actions_taken():
    from src.agents.endpoint import _result_from_messages

    messages = [
        ToolMessage(
            content='{"device_id": "DEV-002", "scan_status": "initiated"}',
            name="scan_device",
            tool_call_id="call_1",
        ),
        AIMessage(content="Scan started."),
    ]

    result = _result_from_messages(messages)

    assert result["actions_taken"] == ["scan_device: initiated"]
    assert result["summary"] == "Scan started."


# --- incident agent ----------------------------------------------------------


def test_incident_status_is_extracted():
    agent = build_incident_agent(
        fake_model(
            AIMessage(
                content="",
                tool_calls=[
                    tool_call("check_incident_status", {"incident_id": "INC-2025-001"})
                ],
            ),
            AIMessage(content="INC-2025-001 is open."),
        )
    )
    result = run_incident_agent(
        {"user_message": "status of INC-2025-001"}, agent
    )["incident"]

    assert result["error"] is None
    assert result["summary"] == "INC-2025-001 is open."


def test_incident_model_failure_is_reported_not_raised():
    class BrokenAgent:
        def invoke(self, *args, **kwargs):
            raise RuntimeError("model unavailable")

    result = run_incident_agent({"user_message": "status of INC-2025-001"}, BrokenAgent())[
        "incident"
    ]

    assert "model unavailable" in result["error"]
    assert result["status"] == "unknown"


def test_incident_approval_interrupt_is_not_swallowed_as_an_error():
    from langgraph.errors import GraphInterrupt

    class InterruptingAgent:
        def invoke(self, *args, **kwargs):
            raise GraphInterrupt(())

    with pytest.raises(GraphInterrupt):
        run_incident_agent({"user_message": "escalate INC-2025-001"}, InterruptingAgent())


def test_incident_node_returns_only_the_incident_key():
    agent = build_incident_agent(fake_model(AIMessage(content="Done.")))
    update = run_incident_agent({"user_message": "status of INC-2025-001"}, agent)

    assert list(update) == ["incident"]
    assert set(update["incident"]) == {
        "incident_id",
        "status",
        "timeline",
        "actions_taken",
        "summary",
        "error",
    }


def test_incident_escalate_is_recorded_in_actions_taken():
    from src.agents.incident import _result_from_messages

    messages = [
        ToolMessage(
            content='{"incident_id": "INC-2025-001", "status": "escalated"}',
            name="escalate_incident",
            tool_call_id="call_1",
        ),
        AIMessage(content="Escalated."),
    ]

    result = _result_from_messages(messages)

    assert result["actions_taken"] == ["escalate_incident: escalated"]
    assert result["incident_id"] == "INC-2025-001"
    assert result["status"] == "escalated"
