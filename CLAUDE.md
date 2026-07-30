# SecureOps AI: SOC Assistant Capstone Project

## Project Overview

**SecureOps AI** is a 2-day MVP for an AI-powered Security Operations Center (SOC) Assistant built for SecureTech Solutions.

The assistant helps security analysts by:
- Understanding natural language security requests
- Extracting relevant entities (usernames, IPs, device IDs, alert IDs)
- Routing requests to specialized agents
- Coordinating multi-agent workflows when multiple domains are involved
- Providing human-in-the-loop approvals for sensitive actions
- Generating final responses combining all agent outputs

**Client:** SecureTech Solutions (global SOC with 5 regional teams, 20,000 endpoints)
**Deadline:** Production-ready MVP (2 days)
**Team:** 4 engineers, each owning specific agents

---

## MVP Goals

1. **One unified chat interface** that routes requests to specialized agents instead of analysts using separate dashboards
2. **Seven core workflows** fully implemented and tested:
   - Search/analyze alerts
   - Check login history & activity
   - Review endpoint/device status
   - Create security incidents
   - Generate incident reports
   - Investigate suspicious IPs (alert + identity correlation)
   - Escalate incidents
3. **Multi-agent coordination** where Supervisor routes requests to 1+ specialized agents
4. **Human-in-the-loop approvals** for sensitive actions (account unlock, device scan, incident escalation)
5. **LangSmith tracing** on 10+ conversations with prompt improvement feedback
6. **Streamlit deployment** with conversation history and clear agent reasoning visibility
7. **Architecture diagram + technical presentation** explaining multi-agent design

---

## Explicit Non-Goals

- **Real integrations** — All external systems (SIEM, IAM, endpoint detection, etc.) are represented via mock APIs or JSON data
- **Persistent application state** — Conversation history and incidents live for a session only; no database
- **Advanced NLU** — Use LLM prompt engineering, not custom entity extraction or NER models
- **Role-based access control** — Assume all analysts have full permissions
- **Sophisticated memory/RAG** — No external knowledge base; agents work from request context only
- **Automatic retries or fallbacks** — Recoverable tool errors are handled gracefully; non-recoverable errors escalate
- **Complex approval workflows** — Simple pending-action flag + UI pause model is sufficient
- **Real-time collaboration** — Single-user session model (no multi-analyst chat)
- **Compliance reporting** — Incident exports are basic text; no formal audit trail

---

## Technology Stack

| Layer | Technology | Role |
|-------|-----------|------|
| **LLM** | Google Gemini (via `langchain-google-genai==4.3.1`) | Primary reasoning engine |
| **Orchestration** | LangGraph (via `langgraph==1.2.9`) | State machine for agent routing & workflow coordination |
| **Framework** | LangChain (via `langchain==1.3.14`) | Tool integration, agent abstractions |
| **UI** | Streamlit (via `streamlit==1.60.0`) | Web chat interface, conversation display |
| **Config** | python-dotenv (via `python-dotenv==1.2.2`) | Environment variable management (API keys, LangSmith endpoints) |
| **Monitoring** | LangSmith (via `langsmith==0.10.11`) | Trace collection, prompt evaluation, run analysis |

**Python Version:** 3.9+ (match LangChain/LangGraph support)
**No additional frameworks** without explicit justification to the team.

---

## Architecture

**See [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) for detailed system design, workflow flow, state management, HITL pattern, tool organization, and deployment strategy.**

High-level: Streamlit UI → LangGraph orchestration → 7 agents → 21 mock tools → JSON data.

---

## Agent Responsibilities

| Agent | Owner | Domain | Approval-Required Actions |
|-------|-------|--------|---------------------------|
| Request Intake | TM1 | Parse user message, extract entities | None |
| Supervisor | TM4 | Route to agents based on request type | None |
| Alert Analysis | TM1 | Search/analyze alerts, severity, threats | None |
| Identity & Access | TM2 | Logins, activity, account status | unlock_account, request_password_reset |
| Endpoint Security | TM3 | Device status, malware, antivirus | scan_device |
| Incident Response | TM3 | Create/escalate incidents, summarize | create_incident, escalate_incident |
| Reporting | TM4 | Generate reports, summaries, exports | None |

See `src/agents/` for implementation templates. Each agent:
- Accepts `SOCWorkflowState`, returns updated dict
- Uses LLM for reasoning
- Calls tools via LLM tool_calls
- Returns results or errors gracefully

---

## State Design

See [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md#state-management) for `SOCWorkflowState` structure and lifecycle.

Key principles:
- Single TypedDict state flows through graph
- Immutable per node (return new dict, never mutate in place)
- Approval state NOT in state; handled via LangGraph checkpointer

---

## Tool Design

See [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md#tool-organization) for tool organization and error handling.

All tools:
- Return mock data only (no real APIs)
- Deterministic: same input → same output
- Return structured dicts
- Handle missing data gracefully (empty list or error dict, no exceptions)

---

## Human-in-the-Loop (HITL)

See [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md#human-in-the-loop-hitl) for detailed HITL pattern and code examples.

Pattern: **LangGraph's `interrupt()` + `Command(resume=...)`**

Key actions requiring approval:
- `unlock_account(username)`
- `request_password_reset(username)`
- `scan_device(device_id)`
- `create_incident(...)`
- `escalate_incident(incident_id, level)`

Implementation:
1. Agent calls `interrupt({action, context, reason})` before sensitive tool call
2. LangGraph pauses and checkpoints state
3. Streamlit displays approval request to analyst
4. Analyst clicks Approve/Deny
5. Streamlit resumes with `Command(resume=True/False)`
6. Agent branches on approval result

**No separate approval state in SOCWorkflowState** — checkpointer handles it.

---

## Streamlit UI

- Chat input box + conversation history display
- Show agent reasoning and tool calls (transparency)
- Display approval requests (action, context, Approve/Deny buttons)
- Disable input while approval is pending
- Show errors gracefully (tool errors with partial results, graph errors with message)

---

## Conversation History

- Initialized in Streamlit app, passed in state, updated by each agent node
- Session-only persistence (no disk storage in MVP)
- For multi-turn: preserve full history in `conversation_history` list
- No external memory (no RAG, no vector DB)

---

## LangSmith Tracing

Enable via environment variables: `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`, `LANGSMITH_ENDPOINT`

Trace all:
- Agent invocations (prompt, tool calls, results)
- Routing decisions
- Tool execution
- Errors and fallbacks
- Approval workflow

Target: <5s per agent. After 10+ conversations, identify one prompt improvement.

---

## Error Handling

See [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md#error-handling) for detailed error handling patterns.

- **Recoverable:** Tool returns `{"error": "...", "partial_result": ...}`, agent interprets
- **Non-recoverable:** Missing info or unsupported request escalates to response_generator
- **No retries:** Supervisor decides on failure; doesn't auto-retry

---

## Testing

See [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md#testing-strategy) for testing strategy.

For MVP:
- Unit tests for imports, state, graph, tools
- Manual testing on 7 core workflows
- LangSmith evaluation on 10+ conversations

---

## Repository Structure

```
SecureOpsTraining/
├── CLAUDE.md                          # This file
├── README.md                          # Setup, running, deployment
├── requirements.txt                   # Python dependencies
├── .env.example                       # Template for environment variables
├── .gitignore                         # Git ignore patterns
│
├── src/
│   ├── __init__.py
│   ├── graph.py                       # LangGraph workflow & state definitions
│   ├── app.py                         # Streamlit main application
│   │
│   ├── agents/                        # Agent implementations
│   │   ├── __init__.py
│   │   ├── request_intake.py         # Request parsing & entity extraction
│   │   ├── supervisor.py             # Orchestration & routing logic
│   │   ├── alert_analysis.py         # Alert analysis agent
│   │   ├── identity.py               # Identity & access agent
│   │   ├── endpoint.py               # Endpoint security agent
│   │   ├── incident.py               # Incident response agent
│   │   └── reporting.py              # Reporting agent
│   │
│   ├── tools/                         # Mock tool implementations
│   │   ├── __init__.py
│   │   ├── alert_tools.py            # search_security_alert, classify_severity, etc.
│   │   ├── identity_tools.py         # check_login_history, unlock_account, etc.
│   │   ├── endpoint_tools.py         # check_endpoint_status, scan_device, etc.
│   │   ├── incident_tools.py         # create_incident, escalate_incident, etc.
│   │   ├── reporting_tools.py        # generate_security_report, etc.
│   │   └── common.py                 # Shared mock data, formatting utilities
│   │
│   └── utils/
│       ├── __init__.py
│       ├── tracing.py               # LangSmith setup & configuration
│       ├── state.py                 # State utilities, type definitions
│       └── formatting.py            # Format agent output for UI
│
├── data/                              # Mock data (optional)
│   ├── mock_alerts.json
│   ├── mock_users.json
│   ├── mock_devices.json
│   └── mock_incidents.json
│
├── docs/                              # Documentation
│   ├── CAPSTONE_PROBLEMSTATEMENT.md  # Client brief
│   ├── ARCHITECTURE.md               # Detailed architecture design
│   └── API.md                        # Tool API reference
│
└── langgraph.json                     # LangGraph Studio configuration
```

---

## Environment Variable Conventions

### Required Variables (Production)
```bash
GOOGLE_API_KEY=sk-...                        # Google Gemini API key
LANGSMITH_API_KEY=...                        # LangSmith API key
LANGSMITH_PROJECT=SecureOps-SOC-Assistant    # LangSmith project name
```

### Optional Variables
```bash
DEBUG=true                                  # Enable verbose logging
STREAMLIT_LOGGER_LEVEL=info                 # Streamlit log level
STREAMLIT_TRACING=true                      # Enable LangChain tracing
LANGSMITH_ENDPOINT=https://api.smith...     # Optional LangSmith endpoint override
```

### Configuration Defaults
- **Checkpointer:** `InMemorySaver()` (MVP session-only; no persistence)
- **Thread ID:** Generated per conversation with `uuid.uuid4()` and stored in Streamlit `session_state`

### Development (.env file)
Use `.env.example` as template. Never commit `.env` to git.

---

## Coding Conventions

### Python Style
- **Follow PEP 8** (use `black` formatter if available, but not required for MVP)
- **Type hints on all functions:** `def search_alert(query: str) -> list[dict]:`
- **No f-strings for complex logic:** Use them for display strings only
- **Docstrings:** One-line for simple functions; multi-line for complex logic with examples

### LangChain/LangGraph Code
- **Agents as functions, not classes** (per state design)
- **Explicit state threading:** Every state modification is visible in return value
- **Tool definitions via LangChain StructuredTool or simple callables**
- **No magic kwargs:** All tool parameters explicit in signature

### Naming Conventions
- **Agent functions:** `{domain}_agent_node()` (e.g., `alert_analysis_agent_node`)
- **Tool functions:** `verb_noun()` (e.g., `search_security_alert`, `check_endpoint_status`)
- **State fields:** `snake_case` (e.g., `request_info`, `completed_actions`)
- **TypedDict classes:** `PascalCase` ending in `Result` or `Info` (e.g., `AlertAnalysisResult`)

### Comments
- Only comment WHY, not WHAT (code is clear; explain constraints/assumptions)
- Mark TODOs with Team Member initials: `# TODO(TM1): implement entity extraction`

### No Over-Abstraction
- **Use simple functions** over complex class hierarchies
- **Inline tool definitions** in agent modules, not a separate tool registry
- **Direct state passing** rather than builder patterns or middleware

---

## Security Constraints

### Data Handling
- **No PII persistence:** Conversation history is in-memory only; cleared on session end
- **Mock data only:** No real credentials, real IP addresses, or real hostnames in tools
- **Log sanitization:** When printing state or history, redact any mock credentials

### Approval Enforcement
- **UI enforces approval blocks:** Graph does not execute sensitive tools without approval
- **Supervisor validates approval:** Before executing unlock_account, verify approval_response is True

### No External API Calls
- **All tools are local:** No actual SIEM, IAM, or endpoint detection API calls
- **Mock data is deterministic:** Same request → same response (test reproducibility)

### API Key Management
- **Read from environment only:** Never hardcode API keys
- **Validate on startup:** If GOOGLE_API_KEY or LANGSMITH_API_KEY missing, fail with clear error

---

## Definition of Done

A feature or agent is "done" when:

1. **Code is written** and follows conventions in CLAUDE.md
2. **Agent logic is implemented** (e.g., request_intake extracts entities)
3. **Tools are mocked** and deterministic
4. **Approval workflow** (if applicable) blocks and resumes correctly
5. **Error handling** covers tool failures gracefully
6. **Streamlit UI displays** the agent's output clearly
7. **LangSmith traces** the agent's execution
8. **Manual testing confirms** the happy path works end-to-end
9. **Code is merged to main** and documented in README
10. **Team reviews and approves** in daily standup

---

## Commands to Run After Code Changes

### After Agent or Tool Implementation
```bash
# Test graph structure (no errors on import)
python -c "from src.graph import SOCAssistantWorkflow; print('Graph imports successfully')"

# Spot-check tool signatures
python -c "from src.tools.alert_tools import search_security_alert; help(search_security_alert)"
```

### After Streamlit UI Changes
```bash
# Run UI and manually test a request
streamlit run src/app.py
# In browser, try a request and verify output displays correctly
```

### Before Committing
```bash
# Check Python syntax
python -m py_compile src/**/*.py

# Verify environment variables are set
python -c "import os; assert os.getenv('GOOGLE_API_KEY'), 'Missing GOOGLE_API_KEY'"
```

### For LangSmith Analysis
```bash
# Pull recent traces (manual via LangSmith UI; no CLI export needed for MVP)
# Review in https://smith.langchain.com/projects/SecureOps-SOC-Assistant
```

---

## Rules Preventing Scope Creep and Overengineering

### Core Scope (DO)
1. ✅ Implement 7 core workflows (alert search, login check, endpoint status, incident create/check/escalate, reporting)
2. ✅ Multi-agent routing via Supervisor
3. ✅ Approval workflow for sensitive actions
4. ✅ Streamlit chat UI with conversation display
5. ✅ LangSmith tracing on 10+ conversations
6. ✅ Deployment to Streamlit Cloud (or local demo if no internet)

### Out of Scope (DON'T)
1. ❌ **Real integrations:** No actual API clients to SIEM, IAM, endpoints (mock only)
2. ❌ **Database persistence:** No incident storage beyond session memory
3. ❌ **Advanced NLU:** No custom NER, intent classifiers; rely on LLM prompt engineering
4. ❌ **RBAC/permissions:** Assume all analysts have full access
5. ❌ **Sophisticated memory:** No vector DB, no knowledge base; context from conversation only
6. ❌ **Automatic retries:** Tools don't retry; supervisor decides on failure
7. ❌ **Complex approval workflows:** Just a simple pending-action flag
8. ❌ **Real-time collaboration:** Single-user session model
9. ❌ **Formal audit logs:** Session-only conversation history is sufficient
10. ❌ **CI/CD pipelines:** No automated tests or linting for MVP
11. ❌ **Monitoring dashboards:** LangSmith alone is sufficient

### Decision Gates
Before adding a feature:
1. **Is it in the problem statement?** If no, don't implement.
2. **Does it fit in 2 days?** If uncertain, don't start.
3. **Can it be mocked or simplified?** If not, reconsider scope.
4. **Have 3+ team members agree** on the feature? If not, defer to v2.

### Simplification Rules
1. **Prefer functions over classes** (unless state demands objects)
2. **Prefer TypedDict over Pydantic** (unless validation demands it)
3. **Prefer synchronous code over async** (LangGraph handles concurrency; agents are sequential)
4. **Prefer deterministic mock data** over realistic randomness
5. **Prefer local files over external services** (JSON, not APIs)

---

## Team Responsibilities Summary

| Team Member | Primary Agents | Shared Responsibility |
|-------------|---|---|
| **TM1: Alert & Intake** | Request Intake, Alert Analysis | LangSmith, testing, docs |
| **TM2: Identity** | Identity & Access | LangSmith, testing, docs |
| **TM3: Endpoint & Incident** | Endpoint, Incident | LangSmith, testing, docs |
| **TM4: Reporting & Supervisor** | Reporting, Supervisor | LangGraph workflow, response generation, UI integration, final presentation |

**All team members:** Help with Streamlit UI, LangSmith tracing, final presentation.

---

## Version History

- **v0.1 (2025-07-30):** Initial CLAUDE.md for 2-day MVP capstone project
