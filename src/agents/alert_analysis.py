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
gives you an alert_id directly, use get_alert_details on it. Only call search_security_alert \
when the analyst gives you a general query (keyword, IP, source).

WHICH TOOL TO USE
- "find alerts about X", "search for X alerts" -> search_security_alert with relevant query
- "details for alert X", "what happened in ALERT-001" -> get_alert_details with alert_id
- "is alert X severe", "severity of alert X" -> classify_alert_severity after get_alert_details
- "correlate alerts A and B", "threat summary for A,B,C" -> summarize_threat with list of alert_ids

GROUNDING
Report only what the tools returned. Never invent an alert_id, severity, or detail that a tool \
did not return. If an alert isn't found, say so plainly. If a tool returns no results, acknowledge \
that explicitly.

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
        "threat_summary": summary,
        "error": error,
    }


def _result_from_messages(messages: list) -> AlertAnalysisResult:
    """Fold the agent's message history into an AlertAnalysisResult for the shared state."""
    result = _empty_result(summary="")

    for message in messages:
        if not isinstance(message, ToolMessage):
            continue

        payload = tool_payload(message)

        if message.name == "search_security_alert" and isinstance(payload, list):
            result["alerts"] = payload
        elif message.name == "get_alert_details" and isinstance(payload, dict):
            result["alerts"] = [payload] if payload else []
        elif message.name == "classify_alert_severity" and isinstance(payload, dict):
            result["severity_classification"] = payload
        elif message.name == "summarize_threat" and isinstance(payload, dict):
            result["threat_summary"] = payload.get("summary", "")

    # Once the model stops calling tools, its closing answer is the last message.
    if messages:
        final_text = message_text(messages[-1])
        if final_text and not result["threat_summary"]:
            result["threat_summary"] = final_text

    return result


def alert_analysis_agent_node(state: SOCWorkflowState) -> dict:
    """Search and analyze security alerts based on extracted request info.

    Uses LLM tool-calling loop to invoke alert tools and returns structured results.
    """
    user_message = state.get("user_message", "")
    conversation_history = state.get("conversation_history") or []
    completed_actions = state.get("completed_actions") or []

    if not user_message:
        result = _empty_result(
            summary="No request provided for alert analysis.",
            error="Missing user message",
        )
        new_history = conversation_history + [
            {"role": "system", "content": f"Alert Analysis: {result['error']}"}
        ]
        new_completed_actions = completed_actions + ["alert_analysis"]
        return {
            "alert_analysis": result,
            "conversation_history": new_history,
            "completed_actions": new_completed_actions,
        }

    try:
        agent = build_alert_analysis_agent()
        response = agent.invoke(
            {"messages": [{"role": "user", "content": user_message}]},
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
        new_history = conversation_history + [
            {"role": "system", "content": f"Alert Analysis: {result['error']}"}
        ]
        new_completed_actions = completed_actions + ["alert_analysis"]
        return {
            "alert_analysis": result,
            "conversation_history": new_history,
            "completed_actions": new_completed_actions,
        }

    result = _result_from_messages(response["messages"])

    # Update conversation history
    new_history = conversation_history + [
        {
            "role": "system",
            "content": f"Alert Analysis: Found {len(result['alerts'])} alerts. "
                      f"Severity: {result['severity_classification'].get('severity', 'Unknown')}. "
                      f"Summary: {result['threat_summary'][:100] if result['threat_summary'] else 'No summary'}...",
        }
    ]

    new_completed_actions = completed_actions + ["alert_analysis"]

    return {
        "alert_analysis": result,
        "conversation_history": new_history,
        "completed_actions": new_completed_actions,
    }
