"""Tools package for SecureOps AI."""

from src.tools.alert_tools import (
    classify_alert_severity,
    get_alert_details,
    search_security_alert,
    summarize_threat,
)
from src.tools.endpoint_tools import (
    check_endpoint_status,
    get_malware_details,
    scan_device,
    search_device,
)
from src.tools.identity_tools import (
    check_account_status,
    check_login_history,
    request_password_reset,
    search_user_activity,
    unlock_account,
)
from src.tools.incident_tools import (
    check_incident_status,
    create_incident,
    escalate_incident,
    generate_incident_summary,
)
from src.tools.reporting_tools import (
    create_investigation_report,
    export_incident_data,
    generate_executive_summary,
    generate_security_report,
)

__all__ = [
    "search_security_alert",
    "get_alert_details",
    "classify_alert_severity",
    "summarize_threat",
    "check_login_history",
    "search_user_activity",
    "check_account_status",
    "request_password_reset",
    "unlock_account",
    "check_endpoint_status",
    "search_device",
    "scan_device",
    "get_malware_details",
    "create_incident",
    "check_incident_status",
    "escalate_incident",
    "generate_incident_summary",
    "generate_security_report",
    "generate_executive_summary",
    "create_investigation_report",
    "export_incident_data",
]
