# SecureOps AI — Quick Setup Guide

## Prerequisites

- **Python 3.9+** (check with `python --version`)
- **pip** package manager
- **Google Gemini API key** (from [Google AI Studio](https://aistudio.google.com/apikey))
- **LangSmith API key** (optional, for tracing; from [smith.langchain.com](https://smith.langchain.com))

## Installation

### 1. Clone and enter the repo
```bash
cd /path/to/SecureOpsTraining
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

## Configuration

### 1. Create `.env` file
Copy the template and fill in your API keys:
```bash
cp .env.example .env
```

### 2. Edit `.env` with your keys
```bash
# Required
GOOGLE_API_KEY=your_google_gemini_api_key_here

# Optional (for LangSmith tracing)
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT=SecureOps-SOC-Assistant
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
```

### 3. Verify configuration
```bash
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('✓ .env loaded' if os.getenv('GOOGLE_API_KEY') else '✗ GOOGLE_API_KEY missing')"
```

## Running the Application

### Start the Streamlit app
```bash
streamlit run src/app.py
```

The app will open automatically in your browser at `http://localhost:8501`

### First-time checks
1. **Chat interface loads** — Single input box and conversation area visible
2. **No API errors** — Check terminal for import or configuration errors
3. **Try a test message** — "Check login history for user123" to verify graph execution

## Troubleshooting

### `ModuleNotFoundError: No module named 'langgraph'`
→ Reinstall dependencies: `pip install -r requirements.txt`

### `GOOGLE_API_KEY not found`
→ Verify `.env` file exists in project root and contains `GOOGLE_API_KEY=...`

### Graph import fails
→ Check Python syntax: `python -m py_compile src/**/*.py`

### Streamlit hangs on startup
→ Check terminal for verbose errors: `streamlit run src/app.py --logger.level=debug`

## Architecture at a Glance

```
User Message (Streamlit)
    ↓
Request Intake Agent (parse entities)
    ↓
Supervisor (route to specialists)
    ↓
Alert / Identity / Endpoint / Incident / Reporting Agents
    ↓
Response Generator (synthesize final answer)
    ↓
Streamlit UI (display result)
```

See [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) and [CLAUDE.md](./CLAUDE.md) for full details.

## Next Steps

- **Run 7 core workflows** (alert search, login check, endpoint status, incident creation, reporting)
- **Enable LangSmith tracing** (set API key in `.env` to capture execution traces)
- **Manual testing** on approval workflows (unlock account, create incident, etc.)

---

**Deployment:** For production, see [docs/ARCHITECTURE.md#deployment](./docs/ARCHITECTURE.md#deployment).
