"""Supervisor agent for routing requests to specialized agents."""

from src.utils import (
    NODE_SUPERVISOR,
    ACTION_ALERT_ANALYSIS,
    ACTION_IDENTITY,
    ACTION_ENDPOINT,
    ACTION_INCIDENT,
    ACTION_REPORTING,
    ACTION_RESPONSE,
    SOCWorkflowState,
)


def supervisor_agent_node(state: SOCWorkflowState) -> dict:
    """Route user request to appropriate agents based on request type."""
    request_info = state.get("request_info", {})
    requested_actions = state.get("requested_actions", [])
    completed_actions = state.get("completed_actions", [])

    # Stub: Supervisor logic to determine which agents to call
    # For now, return placeholder routing

    if not requested_actions:
        # First call: analyze request and decide which agents to route to
        requested_actions = []

    next_action = ACTION_RESPONSE

    # Determine next agent to call
    for action in requested_actions:
        if action not in completed_actions:
            next_action = action
            break

    return {
        "requested_actions": requested_actions,
        "completed_actions": completed_actions,
    }
