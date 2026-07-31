"""Incident response tools for incident management operations."""

from datetime import datetime, timezone

from src.tools.common import find_mock_record
from src.tools.mock_store import insert_record, load_records, update_record

INCIDENTS_FILE = "mock_incidents.json"


def _now() -> str:
    """Current UTC time as an ISO-8601 Z timestamp, matching the mock data format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _next_incident_id(existing: list[dict]) -> str:
    """Next sequential INC-2025-NNN id, based on how many incidents already exist."""
    return f"INC-2025-{len(existing) + 1:03d}"


def create_incident(
    title: str, severity: str, description: str, related_alerts: list[str] | None = None
) -> dict:
    """Create a new security incident (requires human approval).

    Writes the incident, so a later status check finds it.
    """
    existing = load_records(INCIDENTS_FILE)
    incident_id = _next_incident_id(existing)
    created_at = _now()

    record = {
        "incident_id": incident_id,
        "title": title,
        "severity": severity,
        "description": description,
        "status": "created",
        "created": created_at,
        "related_alerts": related_alerts or [],
        "assigned_to": "unassigned",
    }

    if insert_record(INCIDENTS_FILE, record) is None:
        return {"error": "Could not create the incident", "title": title}

    return {
        "incident_id": incident_id,
        "title": title,
        "severity": severity,
        "description": description,
        "status": "created",
        "related_alerts": related_alerts or [],
        "timestamp": created_at,
    }


def check_incident_status(incident_id: str) -> dict:
    """Check the current status and timeline of an incident.

    Reflects any incident already created or escalated in this run.
    """
    incidents = load_records(INCIDENTS_FILE)
    incident = find_mock_record(incidents, "incident_id", incident_id)

    if not incident:
        return {"error": "Incident not found", "incident_id": incident_id}

    return {
        "incident_id": incident_id,
        "title": incident.get("title"),
        "severity": incident.get("severity"),
        "status": incident.get("status"),
        "created": incident.get("created"),
        "related_alerts": incident.get("related_alerts", []),
    }


def escalate_incident(incident_id: str, level: str) -> dict:
    """Escalate an incident to a higher severity level (requires human approval).

    Writes the change, so a later status check reports it.
    """
    incidents = load_records(INCIDENTS_FILE)

    if not find_mock_record(incidents, "incident_id", incident_id):
        return {"error": "Incident not found", "incident_id": incident_id}

    escalated_at = _now()

    updated = update_record(
        INCIDENTS_FILE,
        "incident_id",
        incident_id,
        {"status": "escalated", "severity": level},
    )

    if updated is None:
        return {"error": "Could not record the escalation", "incident_id": incident_id}

    return {
        "incident_id": incident_id,
        "escalation_level": level,
        "status": "escalated",
        "message": f"Incident {incident_id} escalated to level {level}",
        "timestamp": escalated_at,
    }


def generate_incident_summary(incident_id: str) -> dict:
    """Generate an investigation summary for an incident."""
    incidents = load_records(INCIDENTS_FILE)
    incident = find_mock_record(incidents, "incident_id", incident_id)

    if not incident:
        return {"error": "Incident not found", "incident_id": incident_id}

    return {
        "incident_id": incident_id,
        "title": incident.get("title"),
        "summary": f"Investigation of {incident.get('title')} in progress",
        "findings": ["Alert correlation detected", "User activity anomaly identified"],
        "recommendations": ["Isolate affected endpoint", "Review access logs"],
    }
