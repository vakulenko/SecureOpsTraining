"""Alert analysis agent for searching and analyzing security alerts."""

import logging

from langchain.agents import create_agent
from langchain_core.messages import ToolMessage
from langgraph.errors import GraphBubbleUp

from src.tools.alert_tools import (
    search_security_alert,
    get_alert_details,
    classify_alert_severity,
    summarize_threat,
)
from src.utils import AlertAnalysisResult, SOCWorkflowState, create_llm, get_settings
from src.utils.agent_loop import message_text, tool_payload

logger = logging.getLogger(__name__)

ALERT_ANALYSIS_TOOLS = [
    search_security_alert,
    get_alert_details,
    classify_alert_severity,
    summarize_threat,
]

SYSTEM_PROMPT = """You are a security alert analysis specialist in a Security Operations Center. \
Your role is to search for alerts, classify their severity, and identify threats.

ALERT IDENTIFIERS
An alert_id looks like "ALERT-001" (prefix "ALERT-" followed by digits). If the analyst \
gives you an alert_id directly, use get_alert_details on it.

EXTRACTED ENTITIES
The analyst's request may include extracted entities. Use ONLY the entity value, not the full phrase:
- Device ID "DEV-001" -> search for "DEV-001" (not "DEV-001 device")
- Username "jsmith@company.com" -> search for "jsmith@company.com"
- IP Address "192.168.1.42" -> search for "192.168.1.42"
- Severity "high" -> search for "high"

WHICH TOOL TO USE
- Alert ID (ALERT-###) given -> use get_alert_details with the alert_id
- Keywords, IPs, usernames, device IDs, or severity given -> use search_security_alert
- After get_alert_details, optionally call classify_alert_severity for the alert
- Multiple alert IDs -> call summarize_threat to correlate them

GROUNDING
Report only what the tools returned. Never invent an alert_id, severity, or detail that a tool \
did not return. If an alert isn't found, say so plainly.

YOUR ANSWER
Plain prose: what alerts you found, why they matter (severity, threat context), and the \
recommended next step."""


def build_alert_analysis_agent(model=None):
    """Build the alert analysis agent: an LLM tool-calling loop.

    The model is injectable so tests can pass a fake one and run without an API key.
    No checkpointer is set here on purpose -- the agent is invoked by the top-level
    graph which handles checkpointing.
    """
    return create_agent(
        model=model if model is not None else create_llm(get_settings()),
        tools=ALERT_ANALYSIS_TOOLS,
        system_prompt=SYSTEM_PROMPT,
        name="alert_analysis_agent",
    )


def _empty_result(summary: str, error: str | None = None) -> AlertAnalysisResult:
    """Build an AlertAnalysisResult with every field set, for early returns and failures."""
    return {
        "alerts": [],
        "severity_classification": {},
        "summary": summary,
        "error": error,
    }


def _result_from_messages(messages: list) -> AlertAnalysisResult:
    """Fold the agent's message history into an AlertAnalysisResult for the shared state."""
    result = _empty_result(summary="")
    seen_alert_ids = set()

    for message in messages:
        if not isinstance(message, ToolMessage):
            continue

        payload = tool_payload(message)

        if message.name == "search_security_alert" and isinstance(payload, list):
            # Accumulate alerts, avoiding duplicates by alert_id
            for alert in payload:
                alert_id = alert.get("alert_id")
                if alert_id and alert_id not in seen_alert_ids:
                    result["alerts"].append(alert)
                    seen_alert_ids.add(alert_id)
        elif message.name == "get_alert_details" and isinstance(payload, dict):
            # Add single alert if not already seen
            alert_id = payload.get("alert_id")
            if alert_id and alert_id not in seen_alert_ids:
                result["alerts"].append(payload)
                seen_alert_ids.add(alert_id)
        elif message.name == "classify_alert_severity" and isinstance(payload, dict):
            result["severity_classification"] = payload
        elif message.name == "summarize_threat" and isinstance(payload, dict):
            result["summary"] = payload.get("summary", "")

    # Once the model stops calling tools, its closing answer is the last message.
    if messages:
        final_text = message_text(messages[-1])
        if final_text and not result.get("summary"):
            result["summary"] = final_text

    return result


def alert_analysis_agent_node(state: SOCWorkflowState) -> dict:
    """Search and analyze security alerts based on extracted request info.

    Uses LLM tool-calling loop to invoke alert tools and returns structured results.
    Optionally uses extracted entities (username, device_id, ip_address, severity) to
    construct targeted search queries.
    """
    user_message = state.get("user_message", "")
    request_info = state.get("request_info") or {}
    completed_actions = state.get("completed_actions") or []

    if not user_message:
        result = _empty_result(
            summary="No request provided for alert analysis.",
            error="Missing user message",
        )
        new_completed_actions = completed_actions + ["alert_analysis"]
        return {
            "alert_analysis": result,
            "completed_actions": new_completed_actions,
        }

    # Build agent message with extracted entities if available
    entities = request_info.get("entities", {})
    agent_input_message = user_message
    if entities:
        entity_lines = [f'{key.replace("_", " ").title()} "{value}"' for key, value in entities.items() if value]
        if entity_lines:
            search_terms = " and ".join(entity_lines)
            agent_input_message = f"{user_message}\n\nUse these extracted values for searching: {search_terms}"

    try:
        agent = build_alert_analysis_agent()
        response = agent.invoke(
            {"messages": [{"role": "user", "content": agent_input_message}]},
            config={
                "run_name": "alert_analysis_agent",
                "tags": ["alert_analysis_agent"],
                "metadata": {"agent": "alert_analysis"},
            },
        )
    except GraphBubbleUp:
        raise
    except Exception as exc:
        logger.error(f"Alert analysis agent failed: {exc}", exc_info=True)
        result = _empty_result(
            summary="The alert analysis could not be completed.",
            error=f"Alert analysis agent failed: {exc}",
        )
        new_completed_actions = completed_actions + ["alert_analysis"]
        return {
            "alert_analysis": result,
            "completed_actions": new_completed_actions,
        }

    result = _result_from_messages(response["messages"])
    new_completed_actions = completed_actions + ["alert_analysis"]

    return {
        "alert_analysis": result,
        "completed_actions": new_completed_actions,
    }
