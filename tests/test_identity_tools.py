"""Test the identity tools against the mock data files."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.tools.mock_store import DATA_DIR, reset_runtime_data, runtime_dir
from src.tools.identity_tools import (
    check_account_status,
    check_login_history,
    request_password_reset,
    search_user_activity,
    unlock_account,
)

JSMITH = "jsmith@company.com"
RJOHNSON = "rjohnson@company.com"
TARCHER = "tarcher@company.com"
UNKNOWN = "nobody@company.com"


def test_login_history_returns_list():
    """Login history returns a list of records."""
    result = check_login_history(JSMITH)
    assert isinstance(result, list)
    assert len(result) > 0


def test_login_history_failure_filter():
    """outcome='failure' returns only failed attempts."""
    result = check_login_history(JSMITH, outcome="failure")
    assert len(result) == 5
    assert all(record["outcome"] == "failure" for record in result)


def test_login_history_success_filter():
    """outcome='success' returns only successful logins."""
    result = check_login_history(JSMITH, outcome="success")
    assert all(record["outcome"] == "success" for record in result)


def test_login_history_tolerates_plural_outcome():
    """A plural outcome like 'failures' is treated as 'failure'."""
    assert check_login_history(JSMITH, outcome="failures") == check_login_history(
        JSMITH, outcome="failure"
    )


def test_login_history_honours_hours():
    """A narrower time window returns fewer records than a wide one."""
    assert len(check_login_history(JSMITH, hours=1)) < len(
        check_login_history(JSMITH, hours=24)
    )


def test_login_history_newest_first():
    """Records are ordered newest first."""
    timestamps = [r["timestamp"] for r in check_login_history(JSMITH)]
    assert timestamps == sorted(timestamps, reverse=True)


def test_login_history_unknown_user_is_empty():
    """An unknown user returns an empty list, not an error."""
    assert check_login_history(UNKNOWN) == []


def test_user_activity_includes_username():
    """Every activity record identifies which user it belongs to."""
    result = search_user_activity(JSMITH)
    assert len(result) > 0
    assert all(record["username"] == JSMITH for record in result)


def test_user_activity_unknown_user_is_empty():
    """An unknown user returns an empty list."""
    assert search_user_activity(UNKNOWN) == []


def test_account_status_active():
    """An active account reports status 'active'."""
    assert check_account_status(JSMITH)["status"] == "active"


def test_account_status_locked_has_reason():
    """A locked account reports why it was locked."""
    result = check_account_status(RJOHNSON)
    assert result["status"] == "locked"
    assert result["locked_reason"]


def test_account_status_unknown_user_returns_error():
    """An unknown user returns an error dict."""
    result = check_account_status(UNKNOWN)
    assert result["error"] == "User not found"


def test_unlock_locked_account():
    """Unlocking a locked account reports the previous status."""
    result = unlock_account(RJOHNSON)
    assert result["status"] == "unlocked"
    assert result["previous_status"] == "locked"


def test_unlock_active_account_is_a_no_op():
    """Unlocking an account that is not locked does nothing."""
    assert unlock_account(JSMITH)["status"] == "already_active"


def test_unlock_disabled_account_returns_error():
    """A disabled account cannot be unlocked."""
    assert "error" in unlock_account(TARCHER)


def test_unlock_unknown_user_returns_error():
    """Unlocking an unknown user returns an error rather than faking success."""
    assert "error" in unlock_account(UNKNOWN)


def test_password_reset_for_known_user():
    """A password reset for a real user is accepted."""
    assert request_password_reset(JSMITH)["status"] == "reset_requested"


def test_password_reset_unknown_user_returns_error():
    """A password reset for an unknown user returns an error."""
    assert "error" in request_password_reset(UNKNOWN)


def strip_timestamps(records: list[dict]) -> list[dict]:
    """Drop clock-dependent fields so two calls can be compared."""
    return [
        {key: value for key, value in record.items() if key != "timestamp"}
        for record in records
    ]


def test_event_content_is_stable_across_calls():
    """Repeated reads return the same events.

    Timestamps are excluded because they are rebased onto the current clock, so they
    move between calls by design. Everything else must be identical.
    """
    assert strip_timestamps(check_login_history(JSMITH)) == strip_timestamps(
        check_login_history(JSMITH)
    )
    assert strip_timestamps(search_user_activity(JSMITH)) == strip_timestamps(
        search_user_activity(JSMITH)
    )


def test_timestamps_are_rebased_onto_the_current_clock():
    """Events look recent, so 'in the last 24 hours' keeps working as the seed ages."""
    newest = check_login_history(JSMITH)[0]["timestamp"]
    age = datetime.now(timezone.utc).replace(tzinfo=None) - datetime.strptime(
        newest, "%Y-%m-%dT%H:%M:%SZ"
    )

    assert timedelta(0) <= age < timedelta(hours=24)


def test_events_outside_the_window_are_excluded():
    """A window shorter than the data's span drops the older records."""
    assert len(check_login_history(JSMITH, hours=1)) < len(
        check_login_history(JSMITH, hours=24)
    )


def test_unlock_is_visible_to_a_later_status_check():
    """An approved unlock actually changes state, not just the tool's return value."""
    assert check_account_status(RJOHNSON)["status"] == "locked"

    unlock_account(RJOHNSON)

    after = check_account_status(RJOHNSON)
    assert after["status"] == "active"
    assert after["failed_login_count"] == 0
    assert after["locked_reason"] is None


def test_unlocking_twice_is_safe():
    """A repeated unlock is a no-op, so re-running the node cannot corrupt state."""
    unlock_account(RJOHNSON)

    assert unlock_account(RJOHNSON)["status"] == "already_active"
    assert check_account_status(RJOHNSON)["status"] == "active"


def test_password_reset_is_recorded_on_the_account():
    """A password reset request shows up on a later status check."""
    assert check_account_status(JSMITH)["password_reset_pending"] is False

    request_password_reset(JSMITH)

    assert check_account_status(JSMITH)["password_reset_pending"] is True


def test_reset_runtime_data_restores_the_seed_state():
    """Resetting returns the demo to its starting point."""
    unlock_account(RJOHNSON)
    assert check_account_status(RJOHNSON)["status"] == "active"

    reset_runtime_data()

    assert check_account_status(RJOHNSON)["status"] == "locked"


def test_writes_never_touch_the_tracked_seed_file():
    """Writes land in the runtime folder, so `git status` stays clean after a demo."""
    seed_file = DATA_DIR / "mock_users.json"
    before = seed_file.read_text(encoding="utf-8")

    unlock_account(RJOHNSON)

    assert seed_file.read_text(encoding="utf-8") == before
    assert (Path(runtime_dir()) / "mock_users.json").exists()

    written = json.loads((Path(runtime_dir()) / "mock_users.json").read_text(encoding="utf-8"))
    assert any(u["username"] == RJOHNSON and u["status"] == "active" for u in written)


def test_failed_login_count_matches_login_records():
    """Each user's failed_login_count agrees with the login records.

    Guards the cross-agent demo against the two mock data files drifting apart.
    """
    for username in (JSMITH, RJOHNSON, "jdoe@company.com"):
        declared = check_account_status(username)["failed_login_count"]
        actual = len(check_login_history(username, hours=24, outcome="failure"))
        assert declared == actual, f"{username}: {declared} != {actual}"
