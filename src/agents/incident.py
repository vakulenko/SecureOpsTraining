"""Incident response agent for incident management."""

from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain_core.messages import ToolMessage
from langgraph.errors import GraphBubbleUp

from src.tools.incident_tools import (
    check_incident_status,
    create_incident,
    escalate_incident,
    generate_incident_summary,
)
from src.utils import IncidentResult, SOCWorkflowState, create_llm, get_settings
from src.utils.agent_loop import (
    INCIDENT_ID_PATTERN,
    agent_request,
    find_entity,
    message_text,
    tool_payload,
)
from src.utils.approvals import approval_error_hint

INCIDENT_TOOLS = [
    create_incident,
    check_incident_status,
    escalate_incident,
    generate_incident_summary,
]

# create_incident and escalate_incident change incident state, so they need analyst
# sign-off. Anything not listed here is auto-approved by HumanInTheLoopMiddleware.
APPROVAL_TOOLS = {
    "create_incident": {"allowed_decisions": ["approve", "reject"]},
    "escalate_incident": {"allowed_decisions": ["approve", "reject"]},
}

SYSTEM_PROMPT = """You are the Incident Response specialist in a Security Operations \
Center. You are speaking to a security analyst managing an incident.

WHICH TOOL TO USE
- "what's the status of INC-...", "incident timeline" -> check_incident_status
- "summarize the investigation", "investigation summary" -> generate_incident_summary
- "open an incident", "create an incident" -> create_incident. Never call this just \
to check status - it requires analyst approval.
- "escalate INC-... to ...", "raise the severity" -> escalate_incident. Also requires \
analyst approval.

GROUNDING
Report only what the tools returned. Never invent an incident_id, severity, or status \
that a tool did not return. If an incident isn't found, say so plainly.

YOUR ANSWER
Plain prose: current status, what changed, and the recommended next step."""


def build_incident_agent(model=None):
    """Build the incident agent: an LLM tool-calling loop with an approval gate.

    The model is injectable so tests can pass a fake one and run without an API key.
    No checkpointer is set here on purpose -- the approval pause is checkpointed by
    the top-level graph this agent runs inside.
    """
    return create_agent(
        model=model if model is not None else create_llm(get_settings()),
        tools=INCIDENT_TOOLS,
        system_prompt=SYSTEM_PROMPT,
        middleware=[
            HumanInTheLoopMiddleware(
                interrupt_on=APPROVAL_TOOLS,
                description_prefix="Incident action pending analyst approval",
            )
        ],
        name="incident_agent",
    )


def _empty_result(summary: str, error: str | None = None) -> IncidentResult:
    """Build an IncidentResult with every field set, for early returns and failures."""
    return {
        "incident_id": "",
        "status": "unknown",
        "timeline": [],
        "actions_taken": [],
        "summary": summary,
        "error": error,
    }


def _result_from_messages(messages: list) -> IncidentResult:
    """Fold the agent's message history into an IncidentResult for the shared state."""
    result = _empty_result(summary="")

    for message in messages:
        if not isinstance(message, ToolMessage):
            continue

        payload = tool_payload(message)

        if message.name in ("create_incident", "check_incident_status", "escalate_incident"):
            if message.name in APPROVAL_TOOLS:
                # A rejected call's payload is a plain rejection message, not JSON.
                outcome = (
                    payload.get("error") or payload.get("status", "unknown")
                    if isinstance(payload, dict)
                    else str(payload)
                )
                result["actions_taken"].append(f"{message.name}: {outcome}")

            if isinstance(payload, dict):
                result["incident_id"] = payload.get("incident_id", result["incident_id"])
                result["status"] = payload.get("status", result["status"])
        elif message.name == "generate_incident_summary" and isinstance(payload, dict):
            result["timeline"].append(payload)

        if isinstance(payload, dict) and payload.get("error"):
            result["error"] = payload["error"]

    # Once the model stops calling tools, its closing answer is the last message.
    if messages:
        result["summary"] = message_text(messages[-1])

    return result


def incident_agent_node(state: SOCWorkflowState) -> dict:
    """Handle incident response requests."""
    return run_incident_agent(state)


def run_incident_agent(state: SOCWorkflowState, agent=None) -> dict:
    """Do the actual work. `agent` is injectable so tests can supply a fake model."""
    # The incident may have been named in an earlier turn ("status of INC-2025-001" then
    # "escalate it to high"), in which case it arrives through request_info.
    # No hard guard here: create_incident opens a new incident and has no id yet.
    incident_id = find_entity(state, "incident_id", pattern=INCIDENT_ID_PATTERN)

    try:
        if agent is None:
            agent = build_incident_agent()
        response = agent.invoke(
            {"messages": [{"role": "user", "content": agent_request(state, incident_id)}]},
            config={
                "run_name": "incident_agent",
                "tags": ["incident_agent"],
                "metadata": {"agent": "incident"},
            },
        )
    except GraphBubbleUp:
        # An approval request pauses the graph by raising. That is control flow, not a
        # failure, so it must reach LangGraph instead of being turned into an error.
        raise
    except Exception as exc:
        detail = approval_error_hint(exc)

        return {
            "incident": _empty_result(
                summary=detail,
                error=f"Incident agent failed: {detail}",
            )
        }

    return {"incident": _result_from_messages(response["messages"])}
