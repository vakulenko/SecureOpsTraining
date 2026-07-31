"""Test endpoint and incident tool mock implementations.

Runtime writes are isolated to a per-test temp folder by the autouse
`isolate_mock_writes` fixture in tests/conftest.py, so these never touch
data/runtime or leak state between tests.
"""

from src.tools.endpoint_tools import (
    check_endpoint_status,
    get_malware_details,
    scan_device,
    search_device,
)
from src.tools.incident_tools import (
    check_incident_status,
    create_incident,
    escalate_incident,
    generate_incident_summary,
)


def test_check_endpoint_status_not_found():
    result = check_endpoint_status("DEV-999")
    assert result["error"] == "Device not found"


def test_search_device_by_hostname():
    results = search_device("workstation-02")
    assert any(d["device_id"] == "DEV-002" for d in results)


def test_search_device_by_ip():
    results = search_device("192.168.1.100")
    assert any(d["device_id"] == "DEV-003" for d in results)


def test_get_malware_details_clean_device():
    assert get_malware_details("DEV-001") == []


def test_get_malware_details_infected_device():
    details = get_malware_details("DEV-002")
    assert len(details) == 2
    assert all("malware_name" in d for d in details)


def test_scan_device_not_found():
    result = scan_device("DEV-999")
    assert result["error"] == "Device not found"


def test_scan_device_is_reflected_by_a_later_status_check():
    scan_result = scan_device("DEV-002")
    assert scan_result["scan_status"] == "initiated"

    status = check_endpoint_status("DEV-002")
    assert status["last_scan_status"] == "initiated"
    assert status["last_scan_at"] == scan_result["timestamp"]


def test_check_incident_status_not_found():
    result = check_incident_status("INC-2025-999")
    assert result["error"] == "Incident not found"


def test_check_incident_status_found():
    result = check_incident_status("INC-2025-001")
    assert result["status"] == "open"


def test_create_incident_is_reflected_by_a_later_status_check():
    created = create_incident(
        title="Test Incident", severity="HIGH", description="Test"
    )
    assert created["incident_id"].startswith("INC-2025-")

    status = check_incident_status(created["incident_id"])
    assert status["title"] == "Test Incident"
    assert status["status"] == "created"


def test_escalate_incident_not_found():
    result = escalate_incident("INC-2025-999", "P1")
    assert result["error"] == "Incident not found"


def test_escalate_incident_is_reflected_by_a_later_status_check():
    result = escalate_incident("INC-2025-001", "P1")
    assert result["status"] == "escalated"
    assert result["escalation_level"] == "P1"

    status = check_incident_status("INC-2025-001")
    assert status["status"] == "escalated"
    assert status["severity"] == "P1"


def test_generate_incident_summary_not_found():
    result = generate_incident_summary("INC-2025-999")
    assert result["error"] == "Incident not found"
