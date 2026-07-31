# Alert Analysis Agent

**Status:** ✅ Production-ready  
**Location:** `src/agents/alert_analysis.py`  
**Owner:** TM1 (Pavlo)

---

## Overview

Specialized agent that searches, retrieves, and analyzes security alerts. Uses LLM tool-calling loop to intelligently route between search, detail lookup, severity classification, and threat correlation tools.

---

## Core Functions

### `alert_analysis_agent_node(state: SOCWorkflowState) → dict`

LangGraph node implementing tool-calling agent loop for alert analysis.

**Input:**
- `state.user_message`: Alert query or request (e.g., "Find malware alerts", "Details on ALERT-001")
- `state.conversation_history`: Multi-turn context (optional)

**Output:** Updated state with `alert_analysis`, `conversation_history`, `completed_actions`

```python
{
    "alert_analysis": {
        "alerts": [{"alert_id": "ALERT-001", "severity": 8, ...}],
        "severity_classification": {"alert_id": "ALERT-001", "severity": 8, "rationale": "..."},
        "threat_summary": "Detected 2 correlated security events",
        "error": None
    },
    "conversation_history": [...],
    "completed_actions": ["alert_analysis"]
}
```

---

## Tools

All tools are deterministic mock implementations returning data from `data/mock_alerts.json`.

| Tool | Purpose | Input | Output |
|------|---------|-------|--------|
| `search_security_alert` | Search alerts by keyword, IP, or source | `query: str` | `list[dict]` |
| `get_alert_details` | Retrieve full alert record | `alert_id: str` | `dict \| None` |
| `classify_alert_severity` | Assess severity with rationale | `alert_id: str` | `dict \| None` |
| `summarize_threat` | Correlate multiple alerts | `alert_ids: list[str]` | `dict` |

**Tool Signatures:**
```python
def search_security_alert(query: str) -> list[dict]:
    """Search alerts by description, source, device_ip, or target_ip."""

def get_alert_details(alert_id: str) -> dict | None:
    """Get full alert record or None if not found."""

def classify_alert_severity(alert_id: str) -> dict | None:
    """Return {alert_id, severity, rationale} or None if alert not found."""

def summarize_threat(alert_ids: list[str]) -> dict:
    """Return {alert_count, max_severity, sources, summary}."""
```

**Example Outputs:**
```python
# search_security_alert("malware")
[
    {"alert_id": "ALERT-001", "severity": 8, "source": "IDS", "description": "Malware detected", ...},
    {"alert_id": "ALERT-003", "severity": 5, "source": "EDR", "description": "Suspicious file", ...}
]

# classify_alert_severity("ALERT-001")
{"alert_id": "ALERT-001", "severity": 8, "rationale": "Alert from IDS regarding Malware detected"}

# summarize_threat(["ALERT-001", "ALERT-003"])
{"alert_count": 2, "max_severity": 8, "sources": ["IDS", "EDR"], "summary": "Detected 2 correlated security events"}
```

---

## System Prompt & Tool Routing

The agent uses LLM reasoning to select the right tool:

```
- "find alerts about X", "search for X alerts" → search_security_alert
- "details for alert X", "what happened in ALERT-001" → get_alert_details
- "is alert X severe", "severity of alert X" → classify_alert_severity
- "correlate alerts A and B" → summarize_threat
```

Agent grounding rules prevent hallucination:
- Reports only what tools return
- Acknowledges "not found" explicitly
- Never invents alert IDs or details

---

## Core Workflows

1. **Keyword search**: "Find malware alerts" → search → returns matching alerts
2. **Alert details**: "Details on ALERT-001" → get_alert_details → returns full record
3. **Severity check**: "How severe is ALERT-001?" → get_alert_details → classify_alert_severity
4. **Threat correlation**: "Link ALERT-001 and ALERT-003" → summarize_threat
5. **IP search**: "Find alerts for 192.168.1.100" → search (searches device_ip/target_ip fields)
6. **Complex query**: "Critical malware alerts" → LLM selects search with appropriate query
7. **Multi-alert summary**: "Summarize alerts A, B, C" → summarize_threat

---

## Testing Example

```python
from src.agents.alert_analysis import alert_analysis_agent_node

state = {
    "user_message": "Find malware alerts",
    "conversation_history": [],
}
result = alert_analysis_agent_node(state)

# Verify outputs
assert "alert_analysis" in result
assert isinstance(result["alert_analysis"]["alerts"], list)
assert result["alert_analysis"]["error"] is None
assert "alert_analysis" in result["completed_actions"]
```

---

## Configuration

**Environment Variables:**
```bash
GOOGLE_API_KEY=sk-...          # Required for LLM
LANGSMITH_API_KEY=...          # Optional, for tracing
LANGSMITH_PROJECT=...          # Optional, project name
```

**Mock Data:**
- Source: `data/mock_alerts.json`
- Format: List of alert dicts with `alert_id`, `severity`, `source`, `description`, etc.
- Deterministic: Same query always returns same results

---

## Internals

### `build_alert_analysis_agent(model=None) → agent`
Constructs LLM tool-calling agent with 4 tools and system prompt. Model is injectable for testing.

### `_result_from_messages(messages: list) → AlertAnalysisResult`
Folds agent message history into structured result by extracting tool calls and final response.

### Error Handling
- **Missing user_message**: Returns early with error="Missing user message"
- **Tool failures**: Agent handles gracefully; None results acknowledged
- **Agent exception**: Caught, logged, returned as error in result

---

## Graph Integration

In `src/graph.py`:
```python
graph_builder.add_node(NODE_ALERT_ANALYSIS, alert_analysis_agent_node)
```

Flow: User request → Request Intake (entity extraction) → Supervisor (routing) → Alert Analysis (if routed) → Response Generator

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "No alerts found" | Verify query terms match `description`, `source`, `device_ip`, or `target_ip` in mock_alerts.json |
| "Alert not found" | Check alert_id format (e.g., "ALERT-001" not "ALR-001") |
| "GOOGLE_API_KEY not set" | Add `GOOGLE_API_KEY=sk-...` to `.env` |
| "Agent hangs" | Check tool implementation for infinite loops; verify mock_alerts.json is valid JSON |
| "Tool call fails" | Verify tool signature matches; check return types match TypedDict |

---

## Files

| File | Purpose |
|------|---------|
| `src/agents/alert_analysis.py` | Agent node, system prompt, result folding |
| `src/tools/alert_tools.py` | Tool implementations (search, details, classify, summarize) |
| `data/mock_alerts.json` | Mock alert data |
| `src/utils/state.py` | AlertAnalysisResult, SOCWorkflowState TypedDicts |
| `src/graph.py` | Graph node registration |

