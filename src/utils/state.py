"""Shared state definitions for SOC workflow."""

from typing import Any, TypedDict


class RequestInfo(TypedDict, total=False):
    """Extracted request information from user message."""

    request_type: str
    entities: dict[str, Any]
    missing_fields: list[str]


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
