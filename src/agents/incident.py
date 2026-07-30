"""Incident response agent for incident management."""

from langchain_core.tools import tool
from langgraph.errors import GraphBubbleUp

from src.tools.incident_tools import (
    check_incident_status,
    create_incident,
    escalate_incident,
    generate_incident_summary,
)
from src.utils import IncidentResult, SOCWorkflowState
from src.utils.agent_loop import run_tool_agent

SYSTEM_PROMPT = """You are the Incident Response Agent for SecureTech's SOC assistant.

You help analysts create incidents, check incident status, escalate
incidents, and generate investigation summaries using the tools provided.

Only call create_incident or escalate_incident when the analyst explicitly
asks for that action — both are sensitive actions that require separate
analyst approval."""

INCIDENT_TOOLS = [
    tool(create_incident),
    tool(check_incident_status),
    tool(escalate_incident),
    tool(generate_incident_summary),
]

APPROVAL_REQUIRED = frozenset({"create_incident", "escalate_incident"})


def incident_agent_node(state: SOCWorkflowState) -> dict:
    """Handle incident response requests."""
    user_message = state.get("user_message", "")

    result: IncidentResult = {
        "incident_id": "",
        "status": "unknown",
        "timeline": [],
        "actions_taken": [],
        "error": None,
    }

    try:
        _, tool_log = run_tool_agent(
            SYSTEM_PROMPT, user_message, INCIDENT_TOOLS, APPROVAL_REQUIRED
        )
    except GraphBubbleUp:
        raise  # interrupt() pausing the graph for approval - not an error
    except Exception as exc:
        result["error"] = str(exc)
        return {"incident": result}

    for call in tool_log:
        name, output = call["tool"], call["result"]

        if isinstance(output, dict) and output.get("error"):
            result["error"] = output["error"]

        if name in APPROVAL_REQUIRED:
            result["actions_taken"].append(
                f"{name}: {'approved' if call['approved'] else 'denied'}"
            )
            if not call["approved"]:
                continue

        if name in ("create_incident", "check_incident_status", "escalate_incident") and isinstance(
            output, dict
        ):
            result["incident_id"] = output.get("incident_id", result["incident_id"])
            result["status"] = output.get("status", result["status"])
        elif name == "generate_incident_summary" and isinstance(output, dict):
            result["timeline"].append(output)

    return {"incident": result}
