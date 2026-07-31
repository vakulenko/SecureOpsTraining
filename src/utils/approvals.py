"""Helpers for reading and answering an analyst-approval pause.

Every agent gates its sensitive tools with LangChain's HumanInTheLoopMiddleware, which
pauses the graph by raising an interrupt carrying "action_requests" and "review_configs",
and expects Command(resume={"decisions": [...]}) to continue.

These two helpers keep that wire format in one place so the UI does not have to know it.
"""


def describe_interrupt(result: dict) -> dict | None:
    """Return the pending approval request, or None if the graph did not pause.

    Works with the dict returned by graph.invoke() and with an "__interrupt__" event
    seen while streaming. Returns {"tool", "args", "description", "allowed_decisions"}.
    """
    interrupts = result.get("__interrupt__") if isinstance(result, dict) else None

    if not interrupts:
        return None

    payload = getattr(interrupts[0], "value", interrupts[0])

    if not isinstance(payload, dict) or "action_requests" not in payload:
        # An unrecognised pause must still reach the analyst rather than vanish.
        return {
            "tool": "unknown",
            "args": {},
            "description": str(payload),
            "allowed_decisions": ["approve", "reject"],
        }

    request = payload["action_requests"][0]
    configs = payload.get("review_configs") or [{}]

    return {
        "tool": request.get("name", "unknown"),
        "args": request.get("args", {}),
        "description": request.get("description", ""),
        "allowed_decisions": configs[0].get("allowed_decisions", ["approve", "reject"]),
    }


# Plain-English rendering of each approval-gated tool. Analysts should not have to read
# a function signature to decide whether to approve something.
# "effect" says what changes if approved -- keep it to what the tool actually does.
_ACTIONS = {
    "unlock_account": {
        "title": "Unlock account",
        "sentence": "Unlock **{username}** so they can sign in again.",
        "effect": "The account becomes active and its failed-login count is cleared.",
    },
    "request_password_reset": {
        "title": "Send password reset",
        "sentence": "Issue a password reset for **{username}**.",
        "effect": "A reset token is sent to the user by email and the account is flagged as reset-pending.",
    },
    "scan_device": {
        "title": "Scan device",
        "sentence": "Start a malware scan on **{device_id}**.",
        "effect": "The scan runs on the endpoint and may affect its performance.",
    },
    "create_incident": {
        "title": "Create incident",
        "sentence": "Open a new **{severity}** incident: {title}.",
        "effect": "A new incident record is created and becomes visible to the SOC.",
    },
    "escalate_incident": {
        "title": "Escalate incident",
        "sentence": "Escalate **{incident_id}** to level **{level}**.",
        "effect": "The incident's severity is raised.",
    },
}


def describe_action(tool: str, args: dict) -> dict:
    """Describe a pending tool call in words an analyst can act on.

    Returns {"title", "detail", "effect"}. Any tool missing from the table still renders
    something usable, so adding a new approval-gated tool cannot produce a blank prompt.
    """
    spec = _ACTIONS.get(tool)

    if spec is None:
        return {
            "title": tool.replace("_", " ").capitalize(),
            "detail": f"Run `{tool}` with {args}.",
            "effect": "",
        }

    try:
        detail = spec["sentence"].format(**args)
    except (KeyError, IndexError):
        # The model called the tool with unexpected arguments; show them rather than
        # crashing or, worse, describing an action that is not the one being approved.
        detail = f"Run `{tool}` with {args}."

    return {"title": spec["title"], "detail": detail, "effect": spec["effect"]}


def approval_error_hint(exc: Exception) -> str:
    """Turn a malformed approval response into an actionable message.

    The middleware reads the resume value as resume["decisions"], so answering an
    interrupt with a bare "approve" or true -- easy to do by hand in LangGraph Studio --
    raises a cryptic TypeError like "string indices must be integers". Returns guidance
    for that case, and the original error text otherwise.
    """
    text = str(exc)

    if isinstance(exc, TypeError) and ("indices" in text or "subscriptable" in text):
        return (
            "The approval response was not in the expected format. Resume with "
            '{"decisions": [{"type": "approve"}]} to approve, or '
            '{"decisions": [{"type": "reject", "message": "why"}]} to reject. '
            'A bare "approve" or true will not work.'
        )

    return text


def build_resume(approved: bool, message: str = "") -> dict:
    """Build the resume payload for an analyst decision.

    Pass the result straight to Command(resume=...).
    """
    decision = {"type": "approve"} if approved else {"type": "reject"}

    if not approved and message:
        decision["message"] = message

    return {"decisions": [decision]}
