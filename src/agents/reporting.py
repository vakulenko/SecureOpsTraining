"""Reporting agent for incident reports and summaries."""

from src.utils import NODE_REPORTING, ReportingResult, SOCWorkflowState


def reporting_agent_node(state: SOCWorkflowState) -> dict:
    """Generate reports based on incident information."""
    request_info = state.get("request_info", {})

    result: ReportingResult = {
        "report_content": "",
        "export_format": "text",
        "error": None,
    }

    # Stub: LLM will call tools to generate reports
    # For now, return placeholder

    return {
        "reporting": result,
    }
