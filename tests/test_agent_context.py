"""Test that agents carry an identifier across conversation turns.

An analyst says "check DEV-001" and then "scan it". The identifier only appears in the
first message, so each agent has to pick it up from the entities request intake
extracted, and then tell its model about it.
"""

from src.utils.agent_loop import (
    DEVICE_ID_PATTERN,
    EMAIL_PATTERN,
    INCIDENT_ID_PATTERN,
    agent_request,
    find_entity,
)

JSMITH = "jsmith@company.com"


def state_with(message: str, entities: dict | None = None) -> dict:
    return {"user_message": message, "request_info": {"entities": entities or {}}}


def test_entity_comes_from_the_parsed_request():
    """A value carried over from an earlier turn arrives via request_info."""
    state = state_with("reset password", {"username": JSMITH})

    assert find_entity(state, "username", pattern=EMAIL_PATTERN) == JSMITH


def test_entity_falls_back_to_the_current_message():
    """With no parsed entities, the identifier is read out of the message."""
    state = state_with(f"unlock {JSMITH}")

    assert find_entity(state, "username", pattern=EMAIL_PATTERN) == JSMITH


def test_entity_keys_are_matched_case_insensitively():
    """The extraction model emits both "device_id" and "device_ID" for the same thing."""
    state = state_with("scan it", {"device_ID": "DEV-001"})

    assert find_entity(state, "device_id", pattern=DEVICE_ID_PATTERN) == "DEV-001"


def test_alternate_keys_are_accepted():
    """A device may be identified by hostname or IP instead of a device id."""
    state = state_with("is it healthy?", {"hostname": "workstation-02"})

    assert find_entity(state, "device_id", "hostname", "ip_address") == "workstation-02"


def test_device_and_incident_ids_are_read_from_the_message():
    """The id patterns match the formats the mock data uses."""
    assert find_entity(state_with("scan DEV-007"), pattern=DEVICE_ID_PATTERN) == "DEV-007"
    assert (
        find_entity(state_with("escalate INC-2025-001"), pattern=INCIDENT_ID_PATTERN)
        == "INC-2025-001"
    )


def test_missing_entity_returns_empty_string():
    """Nothing to find means nothing is invented."""
    assert find_entity(state_with("reset password"), "username", pattern=EMAIL_PATTERN) == ""


def test_followup_message_names_the_entity():
    """The model is told which thing a bare instruction refers to."""
    request = agent_request(state_with("scan it"), "DEV-001")

    assert "scan it" in request
    assert "DEV-001" in request


def test_message_is_unchanged_when_it_already_names_the_entity():
    """No redundant restatement when the analyst spelled the identifier out."""
    assert agent_request(state_with("scan DEV-001"), "DEV-001") == "scan DEV-001"


def test_message_is_unchanged_when_there_is_no_entity():
    """With nothing resolved, the message is passed through untouched."""
    assert agent_request(state_with("what can you do?"), "") == "what can you do?"
