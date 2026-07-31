"""Shared state definitions for SOC workflow."""

from typing import Any, TypedDict


class RequestInfo(TypedDict, total=False):
    """Extracted request information from user message.

    Fields:
    - request_type: List of workflow intents. Allows multi-action requests.
        Valid values: {alert_search, identity_check, endpoint_check,
                       incident_create, incident_escalate, reporting,
                       ip_investigation, unknown}
        Examples: ["alert_search"] or ["alert_search", "identity_check"]
    - entities: Extracted parameters such as:
        * username: str - user account name
        * ip_address: str - IP to investigate
        * device_id: str - endpoint device identifier
        * alert_id: str - security alert identifier
        * incident_id: str - incident identifier
        * severity: str - "high", "critical", etc.
        * time_range: str - "last 24 hours", "last 7 days"
        * query: str - search query for alerts
        * report_type: str - "incident", "threat_summary", etc.
        * escalation_level: str - "high", "critical"
    - missing_fields: Which required fields are absent from the user message
    - confidence: 0.0-1.0, how confident the extraction is (default 1.0)
    """

    request_type: list[str]
    entities: dict[str, Any]
    missing_fields: list[str]
    confidence: float


class AlertAnalysisResult(TypedDict, total=False):
    """Result from alert analysis agent."""

    alerts: list[dict]
    severity_classification: dict
    threat_summary: str
    error: str | None


class IdentityResult(TypedDict, total=False):
    """Result from identity & access agent."""

    username: str
    login_history: list[dict]
    user_activity: list[dict]
    account_status: str
    actions_taken: list[str]
    summary: str
    error: str | None


class EndpointResult(TypedDict, total=False):
    """Result from endpoint security agent."""

    device_status: dict
    malware_details: list[dict]
    actions_taken: list[str]
    summary: str
    error: str | None


class IncidentResult(TypedDict, total=False):
    """Result from incident response agent."""

    incident_id: str
    status: str
    timeline: list[dict]
    actions_taken: list[str]
    summary: str
    error: str | None


class ReportingResult(TypedDict, total=False):
    """Result from reporting agent."""

    report_content: str
    export_format: str
    error: str | None


class SOCWorkflowState(TypedDict, total=False):
    """Shared workflow state for the SOC Assistant."""

    # Input & context
    user_message: str
    conversation_history: list[dict]

    # Request parsing
    request_info: RequestInfo

    # Orchestration
    requested_actions: list[str]
    completed_actions: list[str]

    # Agent results
    alert_analysis: AlertAnalysisResult | None
    identity: IdentityResult | None
    endpoint: EndpointResult | None
    incident: IncidentResult | None
    reporting: ReportingResult | None

    # Final output
    final_response: str | None
