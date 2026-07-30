"""Request intake agent for parsing user messages and extracting entities."""

from src.utils import NODE_REQUEST_INTAKE, RequestInfo, SOCWorkflowState


def request_intake_agent_node(state: SOCWorkflowState) -> dict:
    """Parse user message and extract request information."""
    user_message = state.get("user_message", "")

    request_info: RequestInfo = {
        "request_type": "unknown",
        "entities": {},
        "missing_fields": [],
    }

    # Stub: LLM will extract entities from user_message
    # For now, return placeholder

    return {
        "request_info": request_info,
    }
