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

from langchain_core.messages import ToolMessage


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
