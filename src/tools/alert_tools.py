"""Alert analysis tools for security alert search and classification."""

from src.tools.common import find_mock_record, filter_mock_records, load_mock_data


def search_security_alert(query: str) -> list[dict]:
    """Search for security alerts by query string."""
    alerts = load_mock_data("mock_alerts.json")
    query_lower = query.lower()

    results = [
        a
        for a in alerts
        if query_lower in a.get("description", "").lower()
        or query_lower in a.get("source", "").lower()
        or query_lower in a.get("device_ip", "").lower()
        or query_lower in a.get("target_ip", "").lower()
        or query_lower in a.get("severity", "").lower()
        or query_lower in a.get("username", "").lower()
        or query_lower in a.get("device_id", "").lower()
        or query_lower in a.get("source_ip", "").lower()
    ]

    return results


def get_alert_details(alert_id: str) -> dict | None:
    """Get full details for a specific alert."""
    alerts = load_mock_data("mock_alerts.json")
    return find_mock_record(alerts, "alert_id", alert_id)


def classify_alert_severity(alert_id: str) -> dict | None:
    """Classify alert severity and provide rationale."""
    alert = get_alert_details(alert_id)
    if not alert:
        return None

    return {
        "alert_id": alert_id,
        "severity": alert.get("severity", "UNKNOWN"),
        "rationale": f"Alert from {alert.get('source')} regarding {alert.get('description')}",
    }


def summarize_threat(alert_ids: list[str]) -> dict:
    """Summarize threat across multiple related alerts."""
    alerts = load_mock_data("mock_alerts.json")
    related = [a for a in alerts if a.get("alert_id") in alert_ids]

    return {
        "alert_count": len(related),
        "max_severity": max((a.get("severity") for a in related), default="LOW"),
        "sources": list(set(a.get("source") for a in related)),
        "summary": f"Detected {len(related)} correlated security events",
    }
