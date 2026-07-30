"""Endpoint security agent for device and malware operations."""

from src.utils import NODE_ENDPOINT, EndpointResult, SOCWorkflowState


def endpoint_agent_node(state: SOCWorkflowState) -> dict:
    """Handle endpoint security requests."""
    request_info = state.get("request_info", {})

    result: EndpointResult = {
        "device_status": {},
        "malware_details": [],
        "actions_taken": [],
        "error": None,
    }

    # Stub: LLM will call tools for endpoint status and scanning
    # For now, return placeholder

    return {
        "endpoint": result,
    }
