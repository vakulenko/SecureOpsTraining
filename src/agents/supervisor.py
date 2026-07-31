"""Supervisor agent for routing requests to specialized agents."""

import json
import logging
from langchain.agents import create_agent
from langchain_core.messages import AIMessage

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
from src.utils.agent_loop import format_history

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a request router in a Security Operations Center.

Your ONLY job: Read the analyst's request and output JSON routing information.

VALID DOMAIN NAMES (use these exactly):
- alert_analysis
- identity
- endpoint
- incident
- reporting

OUTPUT FORMAT (this is the ONLY thing you should output):
{"domains": ["domain1", "domain2"]}

EXAMPLES:
Request: "Check alert ALT-123"
Output: {"domains": ["alert_analysis"]}

Request: "Unlock user john.doe and scan his device"
Output: {"domains": ["identity", "endpoint"]}

Request: "Create an incident"
Output: {"domains": ["incident"]}

Request: "Generate a report"
Output: {"domains": ["reporting"]}

Request: "What's the weather?"
Output: {"domains": []}

ROUTING LOGIC:
- alert_analysis: for alerts, severity, threat analysis, alert details
- identity: for login history, user activity, account status, unlock, password reset, access
- endpoint: for device status, malware, scans, antivirus, device health
- incident: for creating incidents, incident status, escalation, investigation
- reporting: for reports, summaries, exports, investigation reports

CRITICAL:
1. Output ONLY valid JSON in the format {"domains": [...]}
2. Use ONLY the domain names listed above
3. Do NOT add any text before or after the JSON
4. Do NOT include explanations
5. Empty list {"domains": []} if request is unclear or unsupported"""


def build_supervisor_agent(model=None):
    """Build the supervisor agent using LLM for intelligent routing."""
    return create_agent(
        model=model if model is not None else create_llm(get_settings()),
        tools=[],
        system_prompt=SYSTEM_PROMPT,
        name="supervisor_agent",
    )


def _parse_routing_decision(messages: list) -> list[str] | None:
    """Extract the domain list from the supervisor's response.

    Returns the domains on success, or None if the reply could not be read at all.
    That distinction matters: an empty list is a valid answer meaning "no domain
    handles this", whereas None means the router failed and the caller should fall
    back to keyword matching rather than silently skipping every agent.
    """
    if not messages:
        logger.warning("No messages in response")
        return None

    # Find the last AI message
    last_message = None
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            last_message = message
            break

    if not last_message:
        logger.warning("No AI message found in response")
        return None

    # Extract content, handling both string and content blocks (Gemini)
    content = getattr(last_message, "content", "")

    # Handle content blocks (Gemini returns list of dicts with 'type' and 'text')
    if isinstance(content, list):
        text_parts = []
        for block in content:
            if isinstance(block, dict) and "text" in block:
                text_parts.append(block["text"])
            else:
                text_parts.append(str(block))
        text = " ".join(text_parts)
    else:
        text = str(content).strip()

    logger.debug(f"Raw response: {text[:500]}")

    # Try multiple strategies to extract JSON
    json_str = None

    # Strategy 1: Look for markdown code blocks
    if "```json" in text:
        try:
            json_str = text.split("```json")[1].split("```")[0].strip()
        except IndexError:
            pass

    # Strategy 2: Look for plain code blocks
    if json_str is None and "```" in text:
        try:
            json_str = text.split("```")[1].split("```")[0].strip()
        except IndexError:
            pass

    # Strategy 3: Find the first '{' and last '}' to extract JSON object
    if json_str is None:
        try:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = text[start:end]
        except Exception:
            pass

    # Strategy 4: Use the entire text
    if json_str is None:
        json_str = text

    logger.debug(f"Attempting to parse: {json_str[:300]}")

    try:
        parsed = json.loads(json_str)

        if isinstance(parsed, dict) and "domains" in parsed:
            domains = parsed.get("domains", [])
            # Filter out empty strings and validate
            valid_domains = [
                d for d in domains
                if d in ["alert_analysis", "identity", "endpoint", "incident", "reporting"]
            ]
            logger.info(f"Successfully parsed domains: {valid_domains}")
            return valid_domains
        logger.warning(f"Response missing 'domains' key: {parsed}")
        return None
    except (json.JSONDecodeError, ValueError, KeyError, IndexError) as e:
        logger.error(f"Failed to parse routing response: {e}")
        logger.error(f"Attempted to parse: {json_str[:500]}")
        return None


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
    # If no actions matched, default to response generation
    if not actions:
        actions = [ACTION_RESPONSE]

    return actions


def _classify_request_fallback(user_message: str) -> list[str]:
    """Fallback keyword-based routing if LLM routing fails."""
    message_lower = user_message.lower()
    actions = []

    alert_keywords = ["alert", "severity", "threat", "attack", "threat summary", "analyze alert"]
    identity_keywords = [
        "login", "password", "account", "user activity", "unlock", "reset",
        "failed login", "access", "authentication", "credentials"
    ]
    endpoint_keywords = ["device", "endpoint", "malware", "scan", "antivirus", "health", "infection"]
    incident_keywords = ["incident", "escalate", "create incident", "incident status", "investigation"]
    reporting_keywords = ["report", "summary", "export", "investigation report", "executive summary"]

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

    if not actions:
        actions = [ACTION_RESPONSE]

    return actions


def _routing_request(state: SOCWorkflowState) -> str:
    """Build the routing question, including recent turns.

    A follow-up like "and check its status" carries no routable keyword on its own, so
    without the earlier turns the router cannot tell which domain it belongs to.
    """
    user_message = state.get("user_message", "")
    history = format_history(state.get("conversation_history"))

    if history == "(no earlier messages)":
        return user_message

    return (
        f"CONVERSATION SO FAR (oldest first):\n{history}\n\n"
        f"Route this request: {user_message}"
    )


def supervisor_agent_node(state: SOCWorkflowState) -> dict:
    """Route user request to appropriate agents based on request type."""
    user_message = state.get("user_message", "")
    requested_actions = state.get("requested_actions", [])
    completed_actions = list(state.get("completed_actions", []))

    logger.info(f"Supervisor processing: '{user_message[:100]}'")

    # If this is the first pass, use LLM to determine routing
    if not requested_actions:
        try:
            logger.info("Using LLM to determine routing")
            agent = build_supervisor_agent()
            response = agent.invoke(
                {"messages": [{"role": "user", "content": _routing_request(state)}]},
                config={
                    "run_name": "supervisor_agent",
                    "tags": ["supervisor_agent"],
                    "metadata": {"agent": "supervisor"},
                },
            )

            routing_domains = _parse_routing_decision(response.get("messages", []))

            if routing_domains is None:
                # The model replied but the reply was unreadable. Falling through to
                # _routing_to_actions here would route straight to the response
                # generator and silently skip every agent, so use keywords instead.
                logger.warning("Could not read the routing reply; using keyword matching")
                requested_actions = _classify_request_fallback(user_message)
            else:
                requested_actions = _routing_to_actions(routing_domains)

            logger.info(f"LLM routing determined actions: {requested_actions}")

        except Exception as exc:
            logger.warning(f"LLM routing failed, falling back to keyword matching: {exc}")
            # Fallback to keyword-based routing
            fallback_actions = _classify_request_fallback(user_message)
            requested_actions = fallback_actions
            logger.info(f"Fallback routing determined actions: {requested_actions}")

    return {
        "requested_actions": requested_actions,
        "completed_actions": completed_actions,
    }
