"""Endpoint security agent for device and malware operations."""

from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain_core.messages import ToolMessage
from langgraph.errors import GraphBubbleUp

from src.tools.endpoint_tools import (
    check_endpoint_status,
    get_malware_details,
    scan_device,
    search_device,
)
from src.utils import EndpointResult, SOCWorkflowState, create_llm, get_settings
from src.utils.agent_loop import (
    DEVICE_ID_PATTERN,
    agent_request,
    find_entity,
    message_text,
    tool_payload,
)
from src.utils.approvals import approval_error_hint

ENDPOINT_TOOLS = [check_endpoint_status, search_device, scan_device, get_malware_details]

# scan_device changes device state (kicks off a scan), so it needs analyst sign-off.
# Anything not listed here is auto-approved by HumanInTheLoopMiddleware.
APPROVAL_TOOLS = {"scan_device": {"allowed_decisions": ["approve", "reject"]}}

SYSTEM_PROMPT = """You are the Endpoint Security specialist in a Security Operations \
Center. You are speaking to a security analyst investigating a device.

DEVICE IDENTIFIERS
A device_id looks like "DEV-001" (the prefix "DEV-" followed by digits). If the \
analyst already gave something in that form, use it directly - do not call \
search_device on it. Only call search_device when the analyst instead gave a \
hostname (e.g. "workstation-02") or an IP address, to resolve it to a device_id first.

WHICH TOOL TO USE
- "is device X healthy", "device status", "last check-in" -> check_endpoint_status
- "malware on X", "any infections", "AV status" -> get_malware_details
- "scan X", "run a scan", "remediate" -> scan_device. Never call this just to check \
status - it changes device state and requires analyst approval.

GROUNDING
Report only what the tools returned. Never invent a device_id, hostname, or malware \
name that a tool did not return. If a device isn't found, say so plainly.

YOUR ANSWER
Plain prose: what you found, how risky it looks, and the recommended next step."""


def build_endpoint_agent(model=None):
    """Build the endpoint agent: an LLM tool-calling loop with an approval gate.

    The model is injectable so tests can pass a fake one and run without an API key.
    No checkpointer is set here on purpose -- the approval pause is checkpointed by
    the top-level graph this agent runs inside.
    """
    return create_agent(
        model=model if model is not None else create_llm(get_settings()),
        tools=ENDPOINT_TOOLS,
        system_prompt=SYSTEM_PROMPT,
        middleware=[
            HumanInTheLoopMiddleware(
                interrupt_on=APPROVAL_TOOLS,
                description_prefix="Endpoint action pending analyst approval",
            )
        ],
        name="endpoint_agent",
    )


def _empty_result(summary: str, error: str | None = None) -> EndpointResult:
    """Build an EndpointResult with every field set, for early returns and failures."""
    return {
        "device_status": {},
        "malware_details": [],
        "actions_taken": [],
        "summary": summary,
        "error": error,
    }


def _result_from_messages(messages: list) -> EndpointResult:
    """Fold the agent's message history into an EndpointResult for the shared state."""
    result = _empty_result(summary="")

    for message in messages:
        if not isinstance(message, ToolMessage):
            continue

        payload = tool_payload(message)

        if message.name == "check_endpoint_status" and isinstance(payload, dict):
            result["device_status"] = payload
        elif message.name == "search_device" and isinstance(payload, list) and payload:
            result["device_status"] = payload[0]
        elif message.name == "get_malware_details" and isinstance(payload, list):
            result["malware_details"] = payload
        elif message.name in APPROVAL_TOOLS:
            # A rejected call's payload is a plain rejection message, not JSON.
            outcome = (
                payload.get("error") or payload.get("scan_status", "unknown")
                if isinstance(payload, dict)
                else str(payload)
            )
            result["actions_taken"].append(f"{message.name}: {outcome}")

        if isinstance(payload, dict) and payload.get("error"):
            result["error"] = payload["error"]

    # Once the model stops calling tools, its closing answer is the last message.
    if messages:
        result["summary"] = message_text(messages[-1])

    return result


def endpoint_agent_node(state: SOCWorkflowState) -> dict:
    """Handle endpoint security requests."""
    return run_endpoint_agent(state)


def run_endpoint_agent(state: SOCWorkflowState, agent=None) -> dict:
    """Do the actual work. `agent` is injectable so tests can supply a fake model."""
    # The device may have been named in an earlier turn ("check DEV-001" then "scan it"),
    # in which case it reaches us through request_info rather than this message.
    # No hard guard here: search_device can still resolve a hostname or IP on its own.
    device = find_entity(
        state, "device_id", "hostname", "ip_address", pattern=DEVICE_ID_PATTERN
    )

    try:
        if agent is None:
            agent = build_endpoint_agent()
        response = agent.invoke(
            {"messages": [{"role": "user", "content": agent_request(state, device)}]},
            config={
                "run_name": "endpoint_agent",
                "tags": ["endpoint_agent"],
                "metadata": {"agent": "endpoint"},
            },
        )
    except GraphBubbleUp:
        # An approval request pauses the graph by raising. That is control flow, not a
        # failure, so it must reach LangGraph instead of being turned into an error.
        raise
    except Exception as exc:
        detail = approval_error_hint(exc)

        return {
            "endpoint": _empty_result(
                summary=detail,
                error=f"Endpoint agent failed: {detail}",
            )
        }

    return {"endpoint": _result_from_messages(response["messages"])}
