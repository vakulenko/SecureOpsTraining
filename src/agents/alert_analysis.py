"""Alert analysis agent for searching and analyzing security alerts."""

from src.utils import NODE_ALERT_ANALYSIS, AlertAnalysisResult, SOCWorkflowState


def alert_analysis_agent_node(state: SOCWorkflowState) -> dict:
    """Analyze security alerts based on request."""
    request_info = state.get("request_info", {})

    result: AlertAnalysisResult = {
        "alerts": [],
        "severity_classification": {},
        "threat_summary": "",
        "error": None,
    }

    # Stub: LLM will call tools to search and analyze alerts
    # For now, return placeholder

    return {
        "alert_analysis": result,
    }
