"""Test tool functionality and mock data."""

from src.tools import (
    search_security_alert,
    check_account_status,
    check_endpoint_status,
    create_incident,
)


def test_search_security_alert():
    """Test alert search returns list."""
    result = search_security_alert("suspicious")
    assert isinstance(result, list)


def test_check_account_status():
    """Test account status lookup."""
    result = check_account_status("jsmith@company.com")
    assert isinstance(result, dict)
    assert "status" in result


def test_check_endpoint_status():
    """Test endpoint status lookup."""
    result = check_endpoint_status("DEV-001")
    assert isinstance(result, dict)


def test_create_incident():
    """Test incident creation returns dict with incident_id."""
    result = create_incident(
        title="Test Incident",
        severity="HIGH",
        description="Test",
        related_alerts=["ALR-2025-001"],
    )
    assert isinstance(result, dict)
    assert "incident_id" in result
