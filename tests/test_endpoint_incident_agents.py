"""Test endpoint and incident agent node result-mapping logic.

The LLM tool-calling loop itself is covered in test_agent_loop.py; here we
mock run_tool_agent to verify each agent maps tool results into its
SOCWorkflowState slice correctly, including the approval-denied path.
"""

from src.agents.endpoint import endpoint_agent_node
from src.agents.incident import incident_agent_node


def test_endpoint_agent_populates_device_status(monkeypatch):
    tool_log = [
        {
            "tool": "check_endpoint_status",
            "args": {"device_id": "DEV-001"},
            "result": {"device_id": "DEV-001", "status": "healthy"},
            "approved": None,
        }
    ]
    monkeypatch.setattr(
        "src.agents.endpoint.run_tool_agent", lambda *a, **k: ("ok", tool_log)
    )

    output = endpoint_agent_node({"user_message": "check status of DEV-001"})

    assert output["endpoint"]["device_status"] == {"device_id": "DEV-001", "status": "healthy"}
    assert output["endpoint"]["error"] is None


def test_endpoint_agent_records_denied_scan(monkeypatch):
    tool_log = [
        {
            "tool": "scan_device",
            "args": {"device_id": "DEV-002"},
            "result": {"status": "denied", "message": "scan_device was not approved by analyst"},
            "approved": False,
        }
    ]
    monkeypatch.setattr(
        "src.agents.endpoint.run_tool_agent", lambda *a, **k: ("ok", tool_log)
    )

    output = endpoint_agent_node({"user_message": "scan DEV-002"})

    assert output["endpoint"]["actions_taken"] == ["scan_device: denied"]
    assert output["endpoint"]["malware_details"] == []


def test_endpoint_agent_handles_loop_exception(monkeypatch):
    def boom(*_a, **_k):
        raise RuntimeError("LLM unavailable")

    monkeypatch.setattr("src.agents.endpoint.run_tool_agent", boom)

    output = endpoint_agent_node({"user_message": "check status of DEV-001"})

    assert output["endpoint"]["error"] == "LLM unavailable"


def test_incident_agent_populates_incident_id_on_approval(monkeypatch):
    tool_log = [
        {
            "tool": "create_incident",
            "args": {"title": "x", "severity": "HIGH", "description": "y"},
            "result": {"incident_id": "INC-2025-999", "status": "created"},
            "approved": True,
        }
    ]
    monkeypatch.setattr(
        "src.agents.incident.run_tool_agent", lambda *a, **k: ("ok", tool_log)
    )

    output = incident_agent_node({"user_message": "create an incident"})

    assert output["incident"]["incident_id"] == "INC-2025-999"
    assert output["incident"]["actions_taken"] == ["create_incident: approved"]


def test_incident_agent_skips_result_when_denied(monkeypatch):
    tool_log = [
        {
            "tool": "escalate_incident",
            "args": {"incident_id": "INC-2025-001", "level": "P1"},
            "result": {"status": "denied", "message": "escalate_incident was not approved by analyst"},
            "approved": False,
        }
    ]
    monkeypatch.setattr(
        "src.agents.incident.run_tool_agent", lambda *a, **k: ("ok", tool_log)
    )

    output = incident_agent_node({"user_message": "escalate INC-2025-001"})

    assert output["incident"]["status"] == "unknown"
    assert output["incident"]["actions_taken"] == ["escalate_incident: denied"]
