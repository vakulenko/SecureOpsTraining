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

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Supervisor in a Security Operations Center. Your job is to \
understand what the analyst is asking and route their request to the right specialist agents.

AVAILABLE SPECIALISTS AND THEIR DOMAINS:
1. alert_analysis: searches alerts, classifies severity, analyzes threats
2. identity: checks login history, user activity, account status, password resets, unlocks
3. endpoint: checks device status, detects malware, scans devices, checks antivirus
4. incident: creates incidents, checks status, escalates, generates summaries
5. reporting: generates reports, executive summaries, investigation reports, exports data

YOUR TASK:
Read the analyst's request carefully and determine which specialist(s) should handle it.
You may need to route to multiple specialists if the request involves multiple domains.

RESPOND WITH VALID JSON ONLY:
{"domains": ["domain1", "domain2"]}

Examples:
- "Check alert ALT-123" -> {"domains": ["alert_analysis"]}
- "Unlock user john.doe" -> {"domains": ["identity"]}
- "Scan device DEV-001" -> {"domains": ["endpoint"]}
- "Create an incident" -> {"domains": ["incident"]}
- "Generate a report for INC-456" -> {"domains": ["reporting"]}
- "Check if john.doe is locked out and scan his device" -> {"domains": ["identity", "endpoint"]}
- "I don't understand what you want" -> {"domains": []}

CRITICAL RULES:
1. ALWAYS return valid JSON, nothing else
2. Use only domain names from the list above
3. If the request is unclear or unsupported, return {"domains": []}
4. Do NOT include explanations or additional text
5. Do NOT use "agent" or "node" in the domain names - only the domain names"""


def build_supervisor_agent(model=None):
    """Build the supervisor agent using LLM for intelligent routing."""
    return create_agent(
        model=model if model is not None else create_llm(get_settings()),
        tools=[],
        system_prompt=SYSTEM_PROMPT,
        name="supervisor_agent",
    )


def _parse_routing_decision(messages: list) -> list[str]:
    """Extract domain list from the supervisor's response."""
    if not messages:
        logger.warning("No messages in response")
        return []

    # Find the last AI message
    last_message = None
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            last_message = message
            break

    if not last_message:
        logger.warning("No AI message found in response")
        return []

    # Extract content, handling both string and content blocks (Gemini)
    content = getattr(last_message, "content", "")
    if isinstance(content, list):
        text = " ".join([str(block) for block in content])
    else:
        text = str(content).strip()

    logger.debug(f"Parsing response: {text[:300]}")

    try:
        # Try to find JSON in the response
        # Some LLMs may wrap it in markdown code blocks
        if "```json" in text:
            json_str = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            json_str = text.split("```")[1].split("```")[0].strip()
        else:
            json_str = text

        parsed = json.loads(json_str)

        if isinstance(parsed, dict) and "domains" in parsed:
            domains = parsed.get("domains", [])
            # Filter out empty strings and validate
            valid_domains = [
                d for d in domains
                if d in ["alert_analysis", "identity", "endpoint", "incident", "reporting"]
            ]
            logger.info(f"Parsed domains: {valid_domains}")
            return valid_domains
        else:
            logger.warning(f"Response missing 'domains' key: {parsed}")
            return []
    except (json.JSONDecodeError, ValueError, KeyError, IndexError) as e:
        logger.warning(f"Failed to parse routing response: {e}")
        logger.debug(f"Raw response was: {text[:300]}")
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
                {"messages": [{"role": "user", "content": user_message}]},
                config={
                    "run_name": "supervisor_agent",
                    "tags": ["supervisor_agent"],
                    "metadata": {"agent": "supervisor"},
                },
            )

            routing_domains = _parse_routing_decision(response.get("messages", []))
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
