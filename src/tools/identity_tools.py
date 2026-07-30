"""Identity and access tools for user account and login operations."""

from src.tools.common import find_mock_record, filter_mock_records, load_mock_data


def check_login_history(username: str, hours: int = 24) -> list[dict]:
    """Get login history for a user in the last N hours."""
    # Mock implementation: return simulated login history
    return [
        {
            "username": username,
            "timestamp": "2025-07-30T10:00:00Z",
            "source_ip": "192.168.1.1",
            "service": "VPN",
        },
        {
            "username": username,
            "timestamp": "2025-07-30T09:30:00Z",
            "source_ip": "192.168.1.1",
            "service": "Email",
        },
    ]


def search_user_activity(username: str) -> list[dict]:
    """Get activity timeline for a user across services."""
    return [
        {
            "timestamp": "2025-07-30T10:00:00Z",
            "activity": "Logged in",
            "service": "VPN",
        },
        {
            "timestamp": "2025-07-30T10:15:00Z",
            "activity": "File accessed",
            "service": "Fileshare",
        },
    ]


def check_account_status(username: str) -> dict:
    """Check if account is locked, active, or disabled."""
    users = load_mock_data("mock_users.json")
    user = find_mock_record(users, "username", username)

    if not user:
        return {"status": "not_found", "username": username}

    return {
        "username": username,
        "status": user.get("status", "unknown"),
        "full_name": user.get("full_name"),
        "last_login": user.get("last_login"),
    }


def request_password_reset(username: str) -> dict:
    """Request a password reset for a user."""
    return {
        "username": username,
        "status": "reset_requested",
        "message": f"Password reset request initiated for {username}",
    }


def unlock_account(username: str) -> dict:
    """Unlock a locked account (requires human approval)."""
    return {
        "username": username,
        "status": "unlocked",
        "message": f"Account {username} has been unlocked",
        "timestamp": "2025-07-30T10:45:00Z",
    }
