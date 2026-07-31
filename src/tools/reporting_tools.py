"""Reporting tools for generating incident reports and summaries."""

from datetime import datetime
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


def generate_daily_security_report() -> dict:
    """Generate a comprehensive daily security report covering alerts, devices, incidents, logins, and user activity."""
    alerts = load_mock_data("mock_alerts.json")
    devices = load_mock_data("mock_devices.json")
    incidents = load_mock_data("mock_incidents.json")
    logins = load_mock_data("mock_logins.json")
    user_activity = load_mock_data("mock_user_activity.json")

    alert_severity_count = {
        "HIGH": len([a for a in alerts if a.get("severity") == "HIGH"]),
        "MEDIUM": len([a for a in alerts if a.get("severity") == "MEDIUM"]),
        "LOW": len([a for a in alerts if a.get("severity") == "LOW"]),
    }

    device_status_count = {
        "healthy": len([d for d in devices if d.get("status") == "healthy"]),
        "compromised": len([d for d in devices if d.get("status") == "compromised"]),
        "at_risk": len([d for d in devices if d.get("status") == "at_risk"]),
    }

    incident_status_count = {
        "open": len([i for i in incidents if i.get("status") == "open"]),
        "investigating": len([i for i in incidents if i.get("status") == "investigating"]),
        "resolved": len([i for i in incidents if i.get("status") == "resolved"]),
    }

    failed_logins = len([l for l in logins if l.get("outcome") == "failure"])
    successful_logins = len([l for l in logins if l.get("outcome") == "success"])

    suspicious_activity = len([a for a in user_activity if a.get("activity_type") == "suspicious"])

    report = f"""
DAILY SECURITY REPORT
Generated: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}

ALERTS SUMMARY
─────────────────────────────────────
Total Alerts: {len(alerts)}
  • HIGH Severity: {alert_severity_count['HIGH']}
  • MEDIUM Severity: {alert_severity_count['MEDIUM']}
  • LOW Severity: {alert_severity_count['LOW']}

DEVICE STATUS
─────────────────────────────────────
Total Devices: {len(devices)}
  • Healthy: {device_status_count['healthy']}
  • At Risk: {device_status_count['at_risk']}
  • Compromised: {device_status_count['compromised']}

INCIDENTS
─────────────────────────────────────
Total Incidents: {len(incidents)}
  • Open: {incident_status_count['open']}
  • Investigating: {incident_status_count['investigating']}
  • Resolved: {incident_status_count['resolved']}

LOGIN ACTIVITY
─────────────────────────────────────
Total Login Attempts: {len(logins)}
  • Successful: {successful_logins}
  • Failed: {failed_logins}
  • Success Rate: {successful_logins / len(logins) * 100:.1f}%

USER ACTIVITY
─────────────────────────────────────
Total Activity Events: {len(user_activity)}
  • Suspicious Events: {suspicious_activity}
  • Normal Events: {len(user_activity) - suspicious_activity}

KEY FINDINGS
─────────────────────────────────────
• Review all HIGH severity alerts for immediate action
• Address {device_status_count['compromised']} compromised devices
• Investigate {failed_logins} failed login attempts
• Monitor {suspicious_activity} suspicious user activities
"""

    return {
        "report_type": "daily_security",
        "report_content": report,
        "format": "text",
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "total_alerts": len(alerts),
            "high_severity_alerts": alert_severity_count["HIGH"],
            "compromised_devices": device_status_count["compromised"],
            "open_incidents": incident_status_count["open"],
            "failed_logins": failed_logins,
            "suspicious_activities": suspicious_activity,
        }
    }


def generate_executive_summary_report() -> dict:
    """Generate an executive-level security summary covering all key metrics."""
    alerts = load_mock_data("mock_alerts.json")
    devices = load_mock_data("mock_devices.json")
    incidents = load_mock_data("mock_incidents.json")
    logins = load_mock_data("mock_logins.json")
    user_activity = load_mock_data("mock_user_activity.json")

    alert_severity_count = {
        "HIGH": len([a for a in alerts if a.get("severity") == "HIGH"]),
        "MEDIUM": len([a for a in alerts if a.get("severity") == "MEDIUM"]),
        "LOW": len([a for a in alerts if a.get("severity") == "LOW"]),
    }

    device_status_count = {
        "healthy": len([d for d in devices if d.get("status") == "healthy"]),
        "compromised": len([d for d in devices if d.get("status") == "compromised"]),
        "at_risk": len([d for d in devices if d.get("status") == "at_risk"]),
    }

    incident_severity_count = {
        "CRITICAL": len([i for i in incidents if i.get("severity") == "CRITICAL"]),
        "HIGH": len([i for i in incidents if i.get("severity") == "HIGH"]),
        "MEDIUM": len([i for i in incidents if i.get("severity") == "MEDIUM"]),
    }

    failed_logins = len([l for l in logins if l.get("outcome") == "failure"])
    suspicious_activity = len([a for a in user_activity if a.get("activity_type") == "suspicious"])

    summary = f"""
EXECUTIVE SECURITY SUMMARY
Generated: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}

SECURITY POSTURE OVERVIEW
─────────────────────────────────────
The organization's security status is under active monitoring with {len(incidents)} active incidents
requiring leadership attention.

CRITICAL METRICS
─────────────────────────────────────
Active Incidents: {len(incidents)}
  └─ CRITICAL: {incident_severity_count['CRITICAL']} | HIGH: {incident_severity_count['HIGH']} | MEDIUM: {incident_severity_count['MEDIUM']}

Security Alerts: {len(alerts)} (HIGH: {alert_severity_count['HIGH']})
  └─ Immediate attention required for {alert_severity_count['HIGH']} high-severity alerts

Device Security: {device_status_count['healthy']} healthy, {device_status_count['at_risk']} at-risk, {device_status_count['compromised']} compromised
  └─ {device_status_count['compromised']} devices require remediation

ACCESS CONTROL
─────────────────────────────────────
Failed Login Attempts: {failed_logins}
Suspicious User Activities: {suspicious_activity}

RISK ASSESSMENT
─────────────────────────────────────
Overall Risk Level: {"CRITICAL" if alert_severity_count['HIGH'] > 2 or device_status_count['compromised'] > 0 else "HIGH" if alert_severity_count['HIGH'] > 0 or incident_severity_count['CRITICAL'] > 0 else "MEDIUM"}

Priority Actions:
1. Address {alert_severity_count['HIGH']} high-severity security alerts
2. Investigate {incident_severity_count['CRITICAL']} critical incidents
3. Remediate {device_status_count['compromised']} compromised endpoint(s)
4. Review {failed_logins} failed login attempts for intrusion patterns

COMPLIANCE & REPORTING
─────────────────────────────────────
All security incidents are being tracked and logged for compliance purposes.
Detailed forensic reports are available on request.
"""

    return {
        "report_type": "executive_summary",
        "report_content": summary,
        "format": "text",
        "generated_at": datetime.utcnow().isoformat(),
        "summary_metrics": {
            "total_incidents": len(incidents),
            "critical_incidents": incident_severity_count["CRITICAL"],
            "total_alerts": len(alerts),
            "high_severity_alerts": alert_severity_count["HIGH"],
            "compromised_devices": device_status_count["compromised"],
            "failed_logins": failed_logins,
            "suspicious_activities": suspicious_activity,
        }
    }
