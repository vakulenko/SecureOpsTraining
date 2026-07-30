"""Supervisor agent for routing requests to specialized agents."""

import logging
from src.utils import (
    ACTION_ALERT_ANALYSIS,
    ACTION_ENDPOINT,
    ACTION_IDENTITY,
    ACTION_INCIDENT,
    ACTION_REPORTING,
    ACTION_RESPONSE,
    SOCWorkflowState,
)

logger = logging.getLogger(__name__)


def _classify_request(user_message: str) -> list[str]:
    """Classify the user request into domains using keyword matching.

    Returns a list of action names that should be executed.
    """
    message_lower = user_message.lower()
    actions = []

    # Keywords for each domain
    alert_keywords = ["alert", "severity", "threat", "attack", "threat summary", "analyze alert"]
    identity_keywords = [
        "login", "password", "account", "user activity", "unlock", "reset",
        "failed login", "access", "authentication", "credentials"
    ]
    endpoint_keywords = ["device", "endpoint", "malware", "scan", "antivirus", "health", "infection"]
    incident_keywords = ["incident", "escalate", "create incident", "incident status", "investigation"]
    reporting_keywords = ["report", "summary", "export", "investigation report", "executive summary"]

    # Match keywords and add actions
    if any(kw in message_lower for kw in alert_keywords):
        actions.append(ACTION_ALERT_ANALYSIS)
    if any(kw in message_lower for kw in identity_keywords):
        actions.append(ACTION_IDENTITY)
    if any(kw in message_lower for kw in endpoint_keywords):
        actions.append(ACTION_ENDPOINT)
    if any(kw in message_lower for kw in incident_keywords):
        actions.append(ACTION_INCIDENT)
    if any(kw in message_lower for kw in reporting_keywords):
        actions.append(ACTION_REPORTING)

    # If no domains matched, default to response
    if not actions:
        actions = [ACTION_RESPONSE]

    return actions


def supervisor_agent_node(state: SOCWorkflowState) -> dict:
    """Route user request to appropriate agents based on request type."""
    user_message = state.get("user_message", "")
    requested_actions = state.get("requested_actions", [])
    completed_actions = list(state.get("completed_actions", []))

    logger.info(f"Supervisor processing: '{user_message[:100]}'")

    # If this is the first pass, determine routing
    if not requested_actions:
        requested_actions = _classify_request(user_message)
        logger.info(f"Determined actions: {requested_actions}")

    return {
        "requested_actions": requested_actions,
        "completed_actions": completed_actions,
    }
