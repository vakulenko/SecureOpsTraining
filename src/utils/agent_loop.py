"""Shared helpers for domain agents built on LangChain's create_agent + HITL middleware.

Agents (endpoint, incident, identity, ...) get their tool-calling loop and their
analyst-approval gate for free from langchain.agents.create_agent +
HumanInTheLoopMiddleware. What's left to each agent is folding the resulting
message list back into its slice of SOCWorkflowState -- these two helpers cover
the two recurring, non-obvious parts of that: decoding a ToolMessage's JSON
payload, and reading a model reply's text across both plain-string and Gemini
content-block formats.
"""

import json
import re

from langchain_core.messages import ToolMessage

# Identifiers the agents look for when the analyst did not repeat them in a follow-up.
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
DEVICE_ID_PATTERN = re.compile(r"\bDEV-\d+\b", re.IGNORECASE)
INCIDENT_ID_PATTERN = re.compile(r"\bINC-\d{4}-\d+\b", re.IGNORECASE)


def find_entity(state, *keys: str, pattern: re.Pattern | None = None) -> str:
    """Find the identifier a request is about, or "" if there is none.

    Looks in the entities that request intake extracted -- which is where a value
    carried over from an earlier turn arrives -- then falls back to reading it out of
    the current message.

    Keys are matched case-insensitively: the extraction model is inconsistent about
    capitalisation and emits both "device_id" and "device_ID" for the same thing.
    """
    entities = (state.get("request_info") or {}).get("entities") or {}
    by_lower_key = {str(key).lower(): value for key, value in entities.items()}

    for key in keys:
        value = by_lower_key.get(key.lower())
        if value:
            return str(value)

    if pattern:
        match = pattern.search(state.get("user_message", ""))
        if match:
            return match.group(0)

    return ""


# How many prior messages to show an agent. Enough to resolve a follow-up, small enough
# to keep the prompt cheap.
HISTORY_LIMIT = 6


def format_history(conversation_history: list[dict] | None) -> str:
    """Render recent turns so a model can resolve follow-ups like "reset password"."""
    if not conversation_history:
        return "(no earlier messages)"

    lines = []
    for message in conversation_history[-HISTORY_LIMIT:]:
        content = str(message.get("content", "")).strip()
        if content:
            lines.append(f"{message.get('role', 'user')}: {content[:300]}")

    return "\n".join(lines) or "(no earlier messages)"


def agent_request(state, entity: str) -> str:
    """Build the message for the agent, naming the entity the request is about.

    On a follow-up like "reset password" or "scan it", the identifier comes from a
    previous turn and is absent from user_message. Without stating it here the model
    only sees the bare instruction and asks for something the analyst already gave.
    """
    user_message = state.get("user_message", "")

    if entity and entity.lower() not in user_message.lower():
        return f"{user_message}\n\n(This request is about {entity}.)"

    return user_message


def tool_payload(message: ToolMessage):
    """Decode a ToolMessage's content, which arrives as a JSON string."""
    if isinstance(message.content, (dict, list)):
        return message.content

    try:
        return json.loads(message.content)
    except (TypeError, ValueError):
        return message.content


def message_text(message) -> str:
    """Get the plain text of a model reply.

    Gemini returns content as a list of blocks rather than a string, so reading
    `.content` directly would show raw dicts to the analyst. `.text` flattens both.
    """
    text = getattr(message, "text", None)

    if text is not None:
        return str(text).strip()

    return str(getattr(message, "content", "")).strip()
