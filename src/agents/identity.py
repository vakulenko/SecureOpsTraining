"""Identity and access agent for user account operations."""

import json

from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain_core.messages import ToolMessage
from langgraph.errors import GraphBubbleUp

from src.agents.identity_prompts import IDENTITY_PROMPT_VERSION, IDENTITY_SYSTEM_PROMPT
from src.tools.identity_tools import (
    check_account_status,
    check_login_history,
    request_password_reset,
    search_user_activity,
    unlock_account,
)
from src.utils import IdentityResult, SOCWorkflowState, create_llm, get_settings
from src.utils.agent_loop import EMAIL_PATTERN, agent_request, find_entity
from src.utils.approvals import approval_error_hint

IDENTITY_TOOLS = [
    check_login_history,
    search_user_activity,
    check_account_status,
    request_password_reset,
    unlock_account,
]

# Tools that change something and therefore need analyst sign-off. Anything not listed
# here is auto-approved by HumanInTheLoopMiddleware, so the read-only tools never prompt.
APPROVAL_TOOLS = {
    "unlock_account": {"allowed_decisions": ["approve", "reject"]},
    "request_password_reset": {"allowed_decisions": ["approve", "reject"]},
}



def build_identity_agent(model=None):
    """Build the identity agent: an LLM tool-calling loop with an approval gate.

    The model is injectable so tests can pass a fake one and run without an API key.
    No checkpointer is set here on purpose -- the approval pause is checkpointed by
    the top-level graph this agent runs inside.
    """
    return create_agent(
        model=model if model is not None else create_llm(get_settings()),
        tools=IDENTITY_TOOLS,
        system_prompt=IDENTITY_SYSTEM_PROMPT,
        middleware=[
            HumanInTheLoopMiddleware(
                interrupt_on=APPROVAL_TOOLS,
                description_prefix="Identity action pending analyst approval",
            )
        ],
        name="identity_agent",
    )


def _empty_result(username: str, summary: str, error: str | None = None) -> IdentityResult:
    """Build an IdentityResult with every field set, for early returns and failures."""
    return {
        "username": username,
        "login_history": [],
        "user_activity": [],
        "account_status": "unknown",
        "actions_taken": [],
        "summary": summary,
        "error": error,
    }


def _find_username(state: SOCWorkflowState) -> str:
    """Get the username from the parsed entities, falling back to the raw message."""
    return find_entity(state, "username", "user", "email", pattern=EMAIL_PATTERN)


def _tool_payload(message: ToolMessage):
    """Decode a ToolMessage's content, which arrives as a JSON string."""
    if isinstance(message.content, (dict, list)):
        return message.content

    try:
        return json.loads(message.content)
    except (TypeError, ValueError):
        return message.content


def _message_text(message) -> str:
    """Get the plain text of a model reply.

    Gemini returns content as a list of blocks rather than a string, so reading
    `.content` directly would show raw dicts to the analyst. `.text` flattens both.
    """
    text = getattr(message, "text", None)

    if text is not None:
        return str(text).strip()

    return str(getattr(message, "content", "")).strip()


def _result_from_messages(messages: list, username: str) -> IdentityResult:
    """Fold the agent's message history into an IdentityResult for the shared state."""
    result = _empty_result(username, summary="")

    for message in messages:
        if not isinstance(message, ToolMessage):
            continue

        payload = _tool_payload(message)

        if message.name == "check_login_history" and isinstance(payload, list):
            result["login_history"] = payload
        elif message.name == "search_user_activity" and isinstance(payload, list):
            result["user_activity"] = payload
        elif message.name == "check_account_status" and isinstance(payload, dict):
            result["account_status"] = payload.get("status", "unknown")
        elif message.name in APPROVAL_TOOLS and isinstance(payload, dict):
            outcome = payload.get("error") or payload.get("status", "unknown")
            result["actions_taken"].append(f"{message.name}: {outcome}")

    # Once the model stops calling tools, its closing answer is the last message.
    if messages:
        result["summary"] = _message_text(messages[-1])

    return result


def identity_agent_node(state: SOCWorkflowState) -> dict:
    """Handle identity and access requests."""
    return run_identity_agent(state)


def run_identity_agent(state: SOCWorkflowState, agent=None) -> dict:
    """Do the actual work. `agent` is injectable so tests can supply a fake model."""
    username = _find_username(state)

    if not username:
        return {
            "identity": _empty_result(
                username="",
                summary=(
                    "I need the full username as an email address "
                    "(for example jsmith@company.com) before I can look this up."
                ),
                error="No username found in the request",
            )
        }

    try:
        if agent is None:
            agent = build_identity_agent()
        response = agent.invoke(
            {"messages": [{"role": "user", "content": agent_request(state, username)}]},
            config={
                "run_name": "identity_agent",
                "tags": ["identity_agent", f"prompt:{IDENTITY_PROMPT_VERSION}"],
                "metadata": {
                    "agent": "identity",
                    "prompt_version": IDENTITY_PROMPT_VERSION,
                },
            },
        )
    except GraphBubbleUp:
        # An approval request pauses the graph by raising. That is control flow, not a
        # failure, so it must reach LangGraph instead of being turned into an error.
        raise
    except Exception as exc:
        detail = approval_error_hint(exc)

        return {
            "identity": _empty_result(
                username=username,
                summary=detail,
                error=f"Identity agent failed: {detail}",
            )
        }

    return {"identity": _result_from_messages(response["messages"], username)}
