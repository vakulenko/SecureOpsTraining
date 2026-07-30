# SecureOps AI Architecture

## System Layers

### 1. UI Layer (Streamlit)
- Chat interface for analyst interaction
- Conversation history display
- Approval request handling
- Error and result presentation

### 2. Graph Layer (LangGraph)
- State machine orchestration
- Agent node routing
- Conditional edge logic
- Checkpoint-based HITL support

### 3. Agent Layer
- Request Intake: Natural language parsing
- Supervisor: Routing and orchestration
- Specialized Agents: Domain-specific logic
  - Alert Analysis
  - Identity & Access
  - Endpoint Security
  - Incident Response
  - Reporting

### 4. Tool Layer
- Mock implementations of security operations
- Deterministic mock data loading
- No real API integrations (MVP scope)

### 5. Data Layer
- JSON mock data files
- Session-only conversation history
- No persistent database

## Workflow Flow

```
User Message (Streamlit)
         ↓
    Request Intake Agent
    (Parse & extract entities)
         ↓
    Supervisor Agent
    (Decide routing strategy)
         ↓
    Conditional Routing
    ↙        ↓        ↘
Alert    Identity   Endpoint
Analysis  & Access   Security
         ↓
    Incident Response
         ↓
    Reporting
         ↓
Response Generator
    (Synthesize results)
         ↓
Final Response (Streamlit)
```

## State Management

### SOCWorkflowState (TypedDict)
```
{
  "user_message": str              # Input from analyst
  "conversation_history": list     # Multi-turn context
  "request_info": RequestInfo      # Parsed request
  "requested_actions": [str]       # Planned agent calls
  "completed_actions": [str]       # Executed agents
  "alert_analysis": dict | None    # Alert agent result
  "identity": dict | None          # Identity agent result
  "endpoint": dict | None          # Endpoint agent result
  "incident": dict | None          # Incident agent result
  "reporting": dict | None         # Reporting agent result
  "final_response": str | None     # Final synthesized response
}
```

State is immutable: nodes return new dict with updated fields only.

## Human-in-the-Loop (HITL)

Uses LangGraph's `interrupt()` + `Command(resume=...)` pattern:

1. Agent detects sensitive action needed (unlock account, create incident, etc.)
2. Agent calls `interrupt({action, context, reason})`
3. LangGraph pauses execution and checkpoints state
4. Streamlit displays approval request to analyst
5. Analyst clicks Approve/Deny
6. Streamlit resumes with `Command(resume=True/False)`
7. Agent branches based on approval result

Sensitive actions requiring approval:
- `unlock_account(username)`
- `request_password_reset(username)`
- `scan_device(device_id)`
- `create_incident(...)`
- `escalate_incident(incident_id, level)`

## LangSmith Observability

All agent nodes emit traces including:
- Request input and LLM prompt
- Tool calls and responses
- Final output
- Errors and fallbacks
- Approval workflow events

Traces enable:
- Latency analysis (target: <5s per agent)
- Tool failure investigation
- Prompt quality evaluation
- Workflow debugging

## Tool Organization

```
tools/
├── common.py              # Mock data loading utilities
├── alert_tools.py         # search_security_alert, etc.
├── identity_tools.py      # check_login_history, unlock_account, etc.
├── endpoint_tools.py      # check_endpoint_status, scan_device, etc.
├── incident_tools.py      # create_incident, escalate_incident, etc.
└── reporting_tools.py     # generate_security_report, etc.
```

All tools:
- Return mock data only (no real APIs)
- Provide deterministic results (same input → same output)
- Return structured dicts, not strings
- Handle "not found" gracefully (empty list or error dict)

## Error Handling

### Tool Errors (Recoverable)
- Tool returns `{"error": "...", "partial_result": ...}`
- Agent interprets and decides if fatal or recoverable
- Returns partial results to supervisor

### Non-Recoverable Errors
- Missing required info → supervisor escalates
- Unsupported request → request intake detects → escalates
- Graph execution error → caught by Streamlit → error message

### Supervisor's Role
- No automatic retries
- Passes error state to response generator
- Response generator synthesizes best-effort answer

## Testing Strategy

### Unit Tests
- Config validation
- State structure
- Tool determinism
- Graph compilation

### Integration Tests
- End-to-end workflows
- Multi-agent coordination
- Approval workflow
- Error cases

### Manual Testing
- Happy path for 7 core workflows
- Approval request handling
- Error display
- Conversation persistence

## Deployment

### MVP (Current)
- Streamlit Community Cloud or local
- In-memory checkpointer (session-only)
- No authentication
- No database

### Production (Future)
- Kubernetes or Cloud Run
- Durable checkpointer (persistent storage)
- Authentication layer
- Audit logging
- Analytics dashboard

## Security Considerations

- **Mock data only**: No PII in tools
- **No credentials**: API keys via environment only
- **Session-only history**: No disk persistence
- **Approval gates**: Sensitive actions blocked by HITL
- **No external APIs**: All data local to MVP

## Performance Targets

- Request intake: <1s
- Agent execution: <5s per agent
- Approval wait: <5 min (analyst-driven)
- Graph round trip: <10s total (without approval)
