"""Reporting tools for generating incident reports and summaries."""

from src.tools.common import find_mock_record, load_mock_data


def generate_security_report(incident_id: str) -> dict:
    """Generate a formatted security report for an incident."""
    incidents = load_mock_data("mock_incidents.json")
    incident = find_mock_record(incidents, "incident_id", incident_id)

    if not incident:
        return {"error": "Incident not found", "incident_id": incident_id}

    report = f"""
SECURITY INCIDENT REPORT
Incident ID: {incident_id}
Title: {incident.get('title')}
Severity: {incident.get('severity')}
Status: {incident.get('status')}
Created: {incident.get('created')}

Related Alerts: {', '.join(incident.get('related_alerts', []))}

This report contains the investigation findings and recommendations
for the security incident listed above.
"""

    return {
        "incident_id": incident_id,
        "report_content": report,
        "format": "text",
    }


def generate_executive_summary(incident_ids: list[str]) -> dict:
    """Generate a high-level summary across multiple incidents."""
    incidents = load_mock_data("mock_incidents.json")
    matching = [i for i in incidents if i.get("incident_id") in incident_ids]

    summary = f"""
EXECUTIVE SECURITY SUMMARY
Total Incidents: {len(matching)}
High Severity: {len([i for i in matching if i.get('severity') == 'HIGH'])}
Medium Severity: {len([i for i in matching if i.get('severity') == 'MEDIUM'])}

This summary provides an overview of active security incidents
and their impact on the organization.
"""

    return {
        "incident_count": len(matching),
        "summary_content": summary,
    }


def create_investigation_report(incident_id: str, findings: list[str]) -> dict:
    """Create a detailed investigation report with findings."""
    return {
        "incident_id": incident_id,
        "report_type": "investigation",
        "findings": findings,
        "created": "2025-07-30T10:45:00Z",
        "message": "Investigation report created successfully",
    }


def export_incident_data(incident_id: str, format: str = "json") -> dict:
    """Export incident data in the specified format."""
    incidents = load_mock_data("mock_incidents.json")
    incident = find_mock_record(incidents, "incident_id", incident_id)

    if not incident:
        return {"error": "Incident not found", "incident_id": incident_id}

    return {
        "incident_id": incident_id,
        "format": format,
        "data": incident,
        "exported": True,
    }
