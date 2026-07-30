# SecureOps AI - SOC Assistant MVP

An AI-powered Security Operations Center (SOC) Assistant built with LangGraph and Streamlit for SecureTech Solutions.

## Overview

SecureOps AI is a 2-day MVP that provides:
- Unified chat interface for security analysts
- Multi-agent workflow orchestration via LangGraph
- 7 core security workflows (alert analysis, login checks, endpoint status, incident management, reporting)
- Human-in-the-loop approvals for sensitive actions
- LangSmith tracing for observability

## Quick Start

### Prerequisites

- Python 3.9+
- Google Gemini API key
- LangSmith API key (optional, for tracing)

### Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create `.env` file (copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```

5. Add your API keys to `.env`:
   ```
   GOOGLE_API_KEY=your-gemini-api-key
   LANGSMITH_API_KEY=your-langsmith-api-key (optional)
   LANGSMITH_TRACING=true (optional)
   ```

## Running the Application

### Start the Streamlit App

```bash
.\start.bat
```

The app will open at `http://localhost:8501`

### Start LangSmith Studio Connection

To connect to LangSmith Studio for graph visualization and monitoring:

```bash
.\debug.bat
```

This starts the LangGraph development server on `http://127.0.0.1:2024`.

Then in LangSmith Studio:
1. Click "Configure Studio connection"
2. Enter Base URL: `http://127.0.0.1:2024`
3. Click "Connect"

You'll see your agent graph structure and can test it in the playground.

## Running Tests

```bash
pytest tests/
```

## Project Structure

```
src/
├── agents/           # Agent implementations
├── tools/            # Mock tool implementations
├── utils/            # Configuration, state, routing
└── app.py           # Streamlit UI

tests/               # Test suite
data/                # Mock data JSON files
docs/                # Documentation
```

## Environment Variables

### Required
- `GOOGLE_API_KEY` - Google Gemini API key

### Optional
- `GOOGLE_MODEL` - Gemini model name (default: `gemini-1.5-flash`)
- `LANGSMITH_TRACING` - Enable LangSmith tracing (default: `false`)
- `LANGSMITH_API_KEY` - LangSmith API key for trace upload
- `LANGSMITH_PROJECT` - LangSmith project name (default: `SecureOps-SOC-Assistant`)
- `LANGSMITH_ENDPOINT` - LangSmith endpoint (default: `https://api.smith.langchain.com`)
- `DEBUG` - Enable debug logging (default: `false`)

## Features

### Implemented
- Project scaffolding
- Configuration module with environment variable support
- LLM factory for Google Gemini
- Shared state definitions (TypedDict)
- Routing constants and node names
- Mock tools for all 5 domains
- Agent stubs for all 7 agents
- LangGraph workflow creation and compilation
- Streamlit chat UI
- Basic test suite
- Mock data (alerts, users, devices, incidents)
- LangSmith tracing integration

### In Progress
- Agent LLM implementations
- Tool integration with agent nodes
- Conditional routing in supervisor
- Human-in-the-loop approval workflow
- Enhanced error handling

## Known Limitations

1. All tools return mock data; no real API integrations
2. Conversation history is session-only (not persisted to disk)
3. Agent logic uses placeholder implementations
4. Approval workflow not yet implemented
5. No authentication or RBAC
6. Limited error handling

## Team Responsibilities

- **TM1 (Alert & Intake)**: Request Intake, Alert Analysis agents
- **TM2 (Identity)**: Identity & Access agent
- **TM3 (Endpoint & Incident)**: Endpoint, Incident agents
- **TM4 (Reporting & Supervisor)**: Reporting, Supervisor agents, response generation

**All**: Streamlit UI, LangSmith tracing, final presentation

## Next Steps

1. Implement agent LLM logic with tool calling
2. Integrate approval workflow with LangGraph interrupt()
3. Connect Streamlit UI to approval pauses
4. Run manual testing on 7 core workflows
5. Prepare for production deployment

## References

- [CLAUDE.md](./CLAUDE.md) - Full project specification
- [Architecture Documentation](./docs/ARCHITECTURE.md) - Detailed design
