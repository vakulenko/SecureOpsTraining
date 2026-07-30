"""Endpoint security agent for device and malware operations."""

from langchain_core.tools import tool
from langgraph.errors import GraphBubbleUp

from src.tools.endpoint_tools import (
    check_endpoint_status,
    get_malware_details,
    scan_device,
    search_device,
)
from src.utils import EndpointResult, SOCWorkflowState
from src.utils.agent_loop import run_tool_agent

SYSTEM_PROMPT = """You are the Endpoint Security Agent for SecureTech's SOC assistant.

You help analysts check device health, malware status, and endpoint details
using the tools provided. If the analyst gives a hostname or IP address
instead of a device_id, use search_device first to resolve it.

Only call scan_device when the analyst explicitly asks to scan or remediate
a device — never call it just to check status, since it is a sensitive
action that requires separate analyst approval."""

ENDPOINT_TOOLS = [
    tool(check_endpoint_status),
    tool(search_device),
    tool(scan_device),
    tool(get_malware_details),
]

APPROVAL_REQUIRED = frozenset({"scan_device"})


def endpoint_agent_node(state: SOCWorkflowState) -> dict:
    """Handle endpoint security requests."""
    user_message = state.get("user_message", "")

    result: EndpointResult = {
        "device_status": {},
        "malware_details": [],
        "actions_taken": [],
        "error": None,
    }

    try:
        _, tool_log = run_tool_agent(
            SYSTEM_PROMPT, user_message, ENDPOINT_TOOLS, APPROVAL_REQUIRED
        )
    except GraphBubbleUp:
        raise  # interrupt() pausing the graph for approval - not an error
    except Exception as exc:
        result["error"] = str(exc)
        return {"endpoint": result}

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

        if name == "check_endpoint_status" and isinstance(output, dict):
            result["device_status"] = output
        elif name == "search_device" and isinstance(output, list):
            result["actions_taken"].append(f"search_device -> {len(output)} match(es)")
        elif name == "get_malware_details" and isinstance(output, list):
            result["malware_details"] = output

    return {"endpoint": result}
