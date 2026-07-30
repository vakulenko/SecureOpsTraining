"""Identity and access tools for user account and login operations."""

from datetime import datetime, timedelta, timezone

from src.tools.mock_store import load_records, update_record

# The seed files in data/ are written around this anchor. On load, every timestamp is
# shifted onto the current clock by the same amount, so the events keep their relative
# spacing (the failed-login burst stays one minute apart) but always look recent. Without
# this, "logins in the last 24 hours" would return nothing once the seed data aged.
SEED_ANCHOR = "2025-07-30T10:30:00Z"

_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

USERS_FILE = "mock_users.json"
LOGINS_FILE = "mock_logins.json"
ACTIVITY_FILE = "mock_user_activity.json"


def _now() -> datetime:
    """Current UTC time, as a naive datetime to match the mock timestamp format."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _parse(timestamp: str) -> datetime | None:
    """Parse an ISO-8601 Z timestamp, or None if it is missing or malformed."""
    try:
        return datetime.strptime(timestamp, _TIMESTAMP_FORMAT)
    except (TypeError, ValueError):
        return None


def _format(moment: datetime) -> str:
    """Render a datetime as an ISO-8601 Z timestamp."""
    return moment.strftime(_TIMESTAMP_FORMAT)


def _seed_offset() -> timedelta:
    """How far the seed data must move to line up with the current clock."""
    anchor = _parse(SEED_ANCHOR)

    return _now() - anchor if anchor else timedelta(0)


def _shift(timestamp: str, offset: timedelta) -> str:
    """Move one seed timestamp onto the current clock, leaving bad values untouched."""
    moment = _parse(timestamp)

    return _format(moment + offset) if moment else timestamp


def _load_events(filename: str, username: str, hours: int) -> list[dict]:
    """Load one user's events, rebased onto the current clock and newest first.

    Shared by the login-history and activity tools: same filtering, different file.
    """
    offset = _seed_offset()
    cutoff = _now() - timedelta(hours=hours)
    events = []

    for record in load_records(filename):
        if record.get("username") != username:
            continue

        shifted = dict(record)
        shifted["timestamp"] = _shift(record.get("timestamp", ""), offset)

        moment = _parse(shifted["timestamp"])
        if moment is None or moment >= cutoff:
            # Keep records with an unreadable timestamp rather than hiding them.
            events.append(shifted)

    return sorted(events, key=lambda r: r.get("timestamp", ""), reverse=True)


def _normalize_outcome(outcome: str) -> str:
    """Map loose LLM phrasing ('Failures', 'failed') onto 'success' / 'failure' / 'all'."""
    cleaned = str(outcome).strip().lower()

    if cleaned.startswith("fail"):
        return "failure"
    if cleaned.startswith("success"):
        return "success"
    return "all"


def check_login_history(
    username: str, hours: int = 24, outcome: str = "all"
) -> list[dict]:
    """Get login history for a user, newest first.

    Args:
        username: Full email address, e.g. "jsmith@company.com".
        hours: How far back to look. Defaults to 24.
        outcome: "failure" for failed attempts only, "success" for successful
            logins only, or "all" for both. Use "failure" to investigate
            brute-force or failed login questions.
    """
    wanted = _normalize_outcome(outcome)
    events = _load_events(LOGINS_FILE, username, hours)

    if wanted == "all":
        return events

    return [event for event in events if event.get("outcome") == wanted]


def search_user_activity(username: str, hours: int = 24) -> list[dict]:
    """Get the activity timeline for a user across services, newest first.

    Args:
        username: Full email address, e.g. "jsmith@company.com".
        hours: How far back to look. Defaults to 24.
    """
    return _load_events(ACTIVITY_FILE, username, hours)


def check_account_status(username: str) -> dict:
    """Check whether an account is active, locked, or disabled.

    Reflects any unlock or password reset that has already been approved.

    Args:
        username: Full email address, e.g. "rjohnson@company.com".
    """
    users = load_records(USERS_FILE)
    user = next((u for u in users if u.get("username") == username), None)

    if not user:
        return {"error": "User not found", "username": username}

    offset = _seed_offset()

    return {
        "username": username,
        "status": user.get("status", "unknown"),
        "user_id": user.get("user_id"),
        "full_name": user.get("full_name"),
        "department": user.get("department"),
        "mfa_enabled": user.get("mfa_enabled"),
        "failed_login_count": user.get("failed_login_count"),
        "locked_reason": user.get("locked_reason"),
        "last_login": _shift(user.get("last_login", ""), offset),
        "password_reset_pending": user.get("password_reset_pending", False),
    }


def request_password_reset(username: str) -> dict:
    """Request a password reset for a user (requires human approval).

    Records the request against the account, so a later status check shows it pending.

    Args:
        username: Full email address, e.g. "jsmith@company.com".
    """
    users = load_records(USERS_FILE)
    user = next((u for u in users if u.get("username") == username), None)

    if not user:
        return {"error": "User not found", "username": username}

    requested_at = _now()
    expires_at = requested_at + timedelta(minutes=15)

    updated = update_record(
        USERS_FILE,
        "username",
        username,
        {
            "password_reset_pending": True,
            "password_reset_requested_at": _format(requested_at),
        },
    )

    if updated is None:
        return {
            "error": "Could not record the password reset request",
            "username": username,
        }

    return {
        "username": username,
        "status": "reset_requested",
        "reset_token_id": "PWR-2025-001",
        "delivery": "email",
        "expires": _format(expires_at),
        "message": f"Password reset request initiated for {username}",
        "timestamp": _format(requested_at),
    }


def unlock_account(username: str) -> dict:
    """Unlock a locked account (requires human approval).

    Writes the change, so a later status check reports the account as active.

    Args:
        username: Full email address, e.g. "rjohnson@company.com".
    """
    users = load_records(USERS_FILE)
    user = next((u for u in users if u.get("username") == username), None)

    if not user:
        return {"error": "User not found", "username": username}

    current_status = user.get("status", "unknown")

    if current_status == "disabled":
        return {
            "error": "Account is disabled and cannot be unlocked; requires HR/IT provisioning",
            "username": username,
            "status": "disabled",
        }

    if current_status != "locked":
        return {
            "username": username,
            "status": "already_active",
            "previous_status": current_status,
            "message": f"Account {username} was not locked; no action taken",
        }

    unlocked_at = _now()

    # Setting the account to a known state, rather than incrementing anything, keeps
    # this safe to apply twice -- LangGraph may re-run a node after an approval.
    updated = update_record(
        USERS_FILE,
        "username",
        username,
        {
            "status": "active",
            "failed_login_count": 0,
            "locked_reason": None,
            "unlocked_at": _format(unlocked_at),
        },
    )

    if updated is None:
        return {"error": "Could not write the unlock", "username": username}

    return {
        "username": username,
        "status": "unlocked",
        "previous_status": "locked",
        "message": f"Account {username} has been unlocked",
        "timestamp": _format(unlocked_at),
    }
