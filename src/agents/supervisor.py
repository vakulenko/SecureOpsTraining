"""Supervisor agent for routing requests to specialized agents."""

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, BaseMessage

from src.utils import (
    ACTION_ALERT_ANALYSIS,
    ACTION_ENDPOINT,
    ACTION_IDENTITY,
    ACTION_INCIDENT,
    ACTION_REPORTING,
    ACTION_RESPONSE,
    SOCWorkflowState,
    create_llm,
    get_settings,
)

SYSTEM_PROMPT = """You are the Supervisor in a Security Operations Center. Your job is to \
understand what the analyst is asking about and route their request to the right specialist.

DOMAIN ROUTING
The available specialists are:
1. Alert Analysis: handles alert searching, severity classification, threat summaries
2. Identity & Access: handles login history, user activity, account status, password resets, unlocks
3. Endpoint Security: handles device status, malware detection, device scans
4. Incident Response: handles incident creation, status checks, escalation, summaries
5. Reporting: handles generating reports, executive summaries, incident exports

REQUEST ANALYSIS
Carefully read the analyst's message and determine:
- What is the primary domain (alerts, identity, endpoint, incident, reporting)?
- Are multiple domains involved?
- What is the actual request (search, check status, create, escalate, report)?

YOUR RESPONSE
Output a JSON object with one of these structures:

Single agent: {"domains": ["alert_analysis"]}  OR  {"domains": ["identity"]}  etc.

Multiple agents: {"domains": ["alert_analysis", "endpoint"]}

If unclear/unsupported: {"domains": []}

NEVER output agent names like "incident_agent". Only output domain names from the list above."""


def build_supervisor_agent(model=None):
    """Build the supervisor routing agent using LLM for intelligent decisions.

    The model is injectable so tests can pass a fake one and run without an API key.
    """
    return create_agent(
        model=model if model is not None else create_llm(get_settings()),
        tools=[],  # Supervisor does not call tools; pure routing logic
        system_prompt=SYSTEM_PROMPT,
        name="supervisor_agent",
    )


def _parse_routing_decision(messages: list) -> list[str]:
    """Extract domain list from the supervisor's final message."""
    if not messages:
        return []

    last_message = messages[-1]
    if not isinstance(last_message, AIMessage):
        return []

    text = str(getattr(last_message, "content", "")).strip()

    import json
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict) and "domains" in parsed:
            domains = parsed.get("domains", [])
            return [d for d in domains if d]  # Filter out empty strings
    except (json.JSONDecodeError, ValueError):
        pass

    return []


def _routing_to_actions(routing_domains: list[str]) -> list[str]:
    """Convert domain names to workflow action names."""
    domain_to_action = {
        "alert_analysis": ACTION_ALERT_ANALYSIS,
        "identity": ACTION_IDENTITY,
        "endpoint": ACTION_ENDPOINT,
        "incident": ACTION_INCIDENT,
        "reporting": ACTION_REPORTING,
    }

    actions = [domain_to_action[d] for d in routing_domains if d in domain_to_action]
    if not actions:
        actions = [ACTION_RESPONSE]

    return actions


def supervisor_agent_node(state: SOCWorkflowState) -> dict:
    """Route user request to appropriate agents based on request type."""
    user_message = state.get("user_message", "")
    requested_actions = state.get("requested_actions", [])
    completed_actions = list(state.get("completed_actions", []))

    # If this is the first pass, use LLM to determine routing
    if not requested_actions:
        try:
            agent = build_supervisor_agent()
            response = agent.invoke(
                {"messages": [{"role": "user", "content": user_message}]},
                config={
                    "run_name": "supervisor_agent",
                    "tags": ["supervisor_agent"],
                    "metadata": {"agent": "supervisor"},
                },
            )

            routing_domains = _parse_routing_decision(response.get("messages", []))
            requested_actions = _routing_to_actions(routing_domains)
        except Exception:
            # On error, default to response generation
            requested_actions = [ACTION_RESPONSE]

    # Find next action to execute
    next_action = ACTION_RESPONSE
    for action in requested_actions:
        if action not in completed_actions:
            next_action = action
            break

    return {
        "requested_actions": requested_actions,
        "completed_actions": completed_actions,
    }
