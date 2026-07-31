"""Reporting agent for incident reports and summaries."""

from langchain.agents import create_agent
from langchain_core.messages import ToolMessage
from langgraph.errors import GraphBubbleUp

from src.tools.reporting_tools import (
    create_investigation_report,
    export_incident_data,
    generate_executive_summary,
    generate_security_report,
)
from src.utils import ReportingResult, SOCWorkflowState, create_llm, get_settings
from src.utils.agent_loop import message_text, tool_payload

REPORTING_TOOLS = [
    generate_security_report,
    generate_executive_summary,
    create_investigation_report,
    export_incident_data,
]

SYSTEM_PROMPT = """You are the Reporting specialist in a Security Operations Center. \
You are speaking to a security analyst who needs formal reports and summaries.

WHICH TOOL TO USE
- "generate report for INC-...", "security report" -> generate_security_report
- "executive summary", "summary of incidents", "high-level overview" -> generate_executive_summary
- "investigation report", "findings report", "document findings" -> create_investigation_report
- "export INC-...", "export data", "export as JSON" -> export_incident_data

INCIDENT IDENTIFIERS
An incident_id looks like "INC-..." (the prefix "INC-" followed by numbers or identifiers). \
If the analyst already gave something in that form, use it directly.

GROUNDING
Report only what the tools returned. Never invent an incident_id or report content that a \
tool did not return. If an incident isn't found, say so plainly.

YOUR ANSWER
Provide the generated report or summary exactly as returned, or explain what report was \
created and how the analyst can access it."""


def build_reporting_agent(model=None):
    """Build the reporting agent: an LLM tool-calling loop.

    The model is injectable so tests can pass a fake one and run without an API key.
    No checkpointer is set here on purpose -- the approval pause is checkpointed by
    the top-level graph this agent runs inside.
    """
    return create_agent(
        model=model if model is not None else create_llm(get_settings()),
        tools=REPORTING_TOOLS,
        system_prompt=SYSTEM_PROMPT,
        name="reporting_agent",
    )


def _empty_result(summary: str, error: str | None = None) -> ReportingResult:
    """Build a ReportingResult with every field set, for early returns and failures."""
    return {
        "report_content": summary,
        "export_format": "text",
        "error": error,
    }


def _result_from_messages(messages: list) -> ReportingResult:
    """Fold the agent's message history into a ReportingResult for the shared state."""
    result = _empty_result(summary="")

    for message in messages:
        if not isinstance(message, ToolMessage):
            continue

        payload = tool_payload(message)

        if message.name == "generate_security_report" and isinstance(payload, dict):
            result["report_content"] = payload.get("report_content", result["report_content"])
            result["export_format"] = payload.get("format", "text")
        elif message.name == "generate_executive_summary" and isinstance(payload, dict):
            result["report_content"] = payload.get("summary_content", result["report_content"])
        elif message.name == "create_investigation_report" and isinstance(payload, dict):
            result["report_content"] = (
                f"Investigation Report Created\nFindings: {payload.get('findings', [])}"
            )
        elif message.name == "export_incident_data" and isinstance(payload, dict):
            result["report_content"] = f"Data exported as {payload.get('format', 'json')}"
            result["export_format"] = payload.get("format", "json")

        if isinstance(payload, dict) and payload.get("error"):
            result["error"] = payload["error"]

    # Once the model stops calling tools, its closing answer is the last message.
    if messages:
        result["report_content"] = message_text(messages[-1])

    return result


def reporting_agent_node(state: SOCWorkflowState) -> dict:
    """Handle reporting and summary requests."""
    return run_reporting_agent(state)


def run_reporting_agent(state: SOCWorkflowState, agent=None) -> dict:
    """Do the actual work. `agent` is injectable so tests can supply a fake model."""
    try:
        if agent is None:
            agent = build_reporting_agent()
        response = agent.invoke(
            {"messages": [{"role": "user", "content": state.get("user_message", "")}]},
            config={
                "run_name": "reporting_agent",
                "tags": ["reporting_agent"],
                "metadata": {"agent": "reporting"},
            },
        )
    except GraphBubbleUp:
        # An approval request pauses the graph by raising. That is control flow, not a
        # failure, so it must reach LangGraph instead of being turned into an error.
        raise
    except Exception as exc:
        return {
            "reporting": _empty_result(
                summary="The reporting request could not be completed.",
                error=f"Reporting agent failed: {exc}",
            )
        }

    return {"reporting": _result_from_messages(response["messages"])}
