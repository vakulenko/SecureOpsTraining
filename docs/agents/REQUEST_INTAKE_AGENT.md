# Request Intake Agent

**Status:** ✅ Production-ready  
**Location:** `src/agents/request_intake.py`  
**Owner:** TM1 (Pavlo)

---

## Overview

Entry point agent that parses natural language security requests and extracts structured information (request type, entities, confidence) for the Supervisor Agent.

---

## Core Functions

### `extract_request_info(user_message: str, conversation_history=None) → RequestInfo`

Extracts structured request data using Gemini LLM.

**Configuration:**
- Uses `Settings` from `src/utils/config.py`
- Model: `settings.google_model` (env: `GOOGLE_MODEL`, default: `gemini-1.5-flash`)
- API Key: `settings.google_api_key` (env: `GOOGLE_API_KEY`)

**Returns:**
```python
{
    "request_type": ["alert_search"],  # list of intents
    "entities": {"severity": "high"},  # extracted params
    "missing_fields": [],
    "confidence": 0.95  # 0.0-1.0
}
```

**Error Handling:**
- Empty message → unknown, confidence 0.1
- JSON parse error → unknown, confidence 0.3
- LLM exception → unknown, confidence 0.0

### `request_intake_agent_node(state: SOCWorkflowState) → dict`

LangGraph node that calls `extract_request_info()` and threads state immutably:
- Extracts RequestInfo from user message
- Updates conversation_history with metadata
- Tracks in completed_actions

**Returns:** Updated state dict with `request_info`, `conversation_history`, `completed_actions`

---

## Supported Request Types

| Type | Description | Example |
|------|-------------|---------|
| `alert_search` | Search security alerts | "Find critical alerts" |
| `identity_check` | Check user login/account | "Check logins for john@company.com" |
| `endpoint_check` | Device status | "Status of WIN-12345?" |
| `incident_create` | Create incident | "Create incident for IP 192.168.1.100" |
| `incident_escalate` | Escalate incident | "Escalate INC-001 to critical" |
| `reporting` | Generate reports | "Report for last 7 days" |
| `ip_investigation` | Investigate IP | "Investigate 10.0.0.50" |
| `unknown` | Intent unclear | Request needs clarification |

**Multi-action:** Supported (e.g., `["alert_search", "identity_check"]`)

---

## Extracted Entities

| Entity | Type | Example |
|--------|------|---------|
| `username` | str | `john@company.com` |
| `ip_address` | str | `192.168.1.100` |
| `device_id` | str | `WIN-ABC123` |
| `alert_id` | str | `ALT-001` |
| `incident_id` | str | `INC-001` |
| `severity` | str | `high`, `critical` |
| `time_range` | str | `last 24 hours` |
| `escalation_level` | str | `critical` |

---

## Configuration

**Environment Variables:**
```bash
GOOGLE_API_KEY=sk-...  # Required
GOOGLE_MODEL=gemini-3.5-flash-lite  # Optional, defaults to gemini-1.5-flash
```

**Usage:**
```python
from src.utils.config import get_settings
settings = get_settings()  # Singleton
# settings.google_api_key
# settings.google_model
```

---

## Graph Integration

In `src/graph.py`:
```python
graph_builder.add_node(NODE_REQUEST_INTAKE, request_intake_agent_node)
graph_builder.add_edge(NODE_REQUEST_INTAKE, NODE_SUPERVISOR)
```

Flow: Request Intake → Supervisor → 1+ Specialized Agents

---

## Testing (7 Core Workflows)

Test in Streamlit UI:

1. "Find critical alerts from the last 24 hours" → `alert_search`
2. "Check login history for john@company.com" → `identity_check`
3. "Status of device WIN-12345?" → `endpoint_check`
4. "Create incident for IP 192.168.1.100" → `incident_create`
5. "Generate report for last 7 days" → `reporting`
6. "Investigate 10.0.0.50" → `ip_investigation`
7. "Escalate INC-001 to critical" → `incident_escalate`

**Unit test:**
```python
from src.agents.request_intake import extract_request_info
result = extract_request_info("Find alerts")
assert result["request_type"] == ["alert_search"]
assert result["confidence"] > 0.8
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "GOOGLE_API_KEY must be set" | Add `GOOGLE_API_KEY=sk-...` to `.env` |
| request_type is ["unknown"] | Request may be ambiguous, try being more specific |
| Graph won't compile | Verify `request_intake_agent_node` is exported from `src/agents/__init__.py` |
| Settings not loading | Check `GOOGLE_API_KEY` is set: `python -c "from src.utils.config import get_settings; print(get_settings())"` |

---

## Files

| File | Purpose |
|------|---------|
| `src/agents/request_intake.py` | Agent node + extraction logic |
| `src/utils/config.py` | Settings class (centralized config) |
| `src/utils/state.py` | RequestInfo TypedDict |
| `src/graph.py` | Graph integration |
