# Local Agent Server Setup - LangGraph CLI (Proven Solution)

Connect your local SecureOps AI agent to LangSmith Studio using the built-in LangGraph CLI.

This is the **production-tested solution** from the reference project.

## Quick Start

### 1. Start the Debug Server

```powershell
python debug.py
```

**Output should show:**
```
=======================================================================
SecureOps AI - LangGraph Studio Debug Mode
=======================================================================

[OK] .env configured
[OK] LANGSMITH_API_KEY set
[OK] langgraph.json found
[OK] src/graph.py found

=======================================================================
Starting LangGraph Development Server
=======================================================================

Server will start on: http://127.0.0.1:2024
Studio will connect automatically

Next steps:
  1. Open https://smith.langchain.com
  2. Click 'Configure Studio connection'
  3. Enter Base URL: http://127.0.0.1:2024
  4. Click 'Connect'
  5. Your agent will appear in the graph view
  6. Test your agent in the playground
```

Keep this window open.

### 2. Configure LangSmith Studio

1. Open [LangSmith Studio](https://smith.langchain.com/) in your browser
2. Click the **"Configure Studio connection"** dialog (top right)
3. Enter **Base URL**: `http://127.0.0.1:2024`
4. Click **"Connect"**

You should see:
```
✅ Connection successful
```

### 3. View Your Agent

In LangSmith Studio you can now:
- See graph structure (all agent nodes)
- Watch real-time execution flow
- View node execution and state changes
- Monitor tool calls and LLM interactions
- Test agent directly in the playground

---

## What This Does

The **LangGraph CLI** (included with `langgraph` package) provides:

✅ **Native development server** - Built-in HTTP server on port 2024
✅ **Hot-reload** - Changes to code automatically reload
✅ **Graph visualization** - See structure in LangSmith Studio
✅ **Playground testing** - Test agent directly in Studio
✅ **Full tracing** - All execution visible in Studio
✅ **No Docker required** - Pure Python on Windows 11
✅ **Production-tested** - Used in reference projects

---

## How It Works

```
┌─────────────────────────────────────────────────────┐
│ Windows 11 Terminal                                 │
│                                                     │
│  PS> python debug.py                               │
│                                                     │
│  Starts:                                            │
│  ├─ LangGraph CLI dev server                       │
│  ├─ Listens on http://127.0.0.1:2024              │
│  ├─ Loads graph from src/graph.py                 │
│  └─ Exposes via langgraph.json config             │
└─────────────────────────────────────────────────────┘
         │
         │ HTTP Connection (127.0.0.1:2024)
         │
┌────────▼──────────────────────────┐
│ Browser: LangSmith Studio          │
│                                    │
│ Configure Studio connection:       │
│ Base URL: 127.0.0.1:2024          │
│                                    │
│ Shows:                             │
│ ├─ Graph structure                │
│ ├─ Real-time execution            │
│ ├─ Playground for testing         │
│ └─ Full tracing data              │
└────────────────────────────────────┘
```

---

## Configuration Files

### langgraph.json (Updated)
```json
{
  "dependencies": ["langchain", "langchain-core", "langchain-google-genai", "langgraph", "langsmith", "python-dotenv"],
  "graphs": {
    "soc_assistant": "src.graph:graph"
  },
  "env": ".env"
}
```

Key points:
- `graphs.soc_assistant`: Points to `src.graph:graph` (the exported graph object)
- `env`: Points to `.env` for configuration
- `dependencies`: Lists required packages

### src/graph.py (Updated)
At the end of the file, the graph is exported for CLI:
```python
# Export graph for LangGraph CLI
graph = get_graph()
```

This makes the graph available as `src.graph:graph` in langgraph.json

### .env (Must have LangSmith configured)
```bash
GOOGLE_API_KEY=your_key_here
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_key_here
LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com  # or your region
LANGSMITH_PROJECT=SecureOps-SOC-Assistant
```

---

## Complete Workflow

### Terminal 1: Start Debug Server
```powershell
PS> python debug.py
```

Server starts on `http://127.0.0.1:2024`

### Terminal 2 (Optional): Start Streamlit
```powershell
PS> .\debug.bat
```

Opens Streamlit at `localhost:8501`

### Browser: Connect Studio

1. Go to https://smith.langchain.com/
2. Click "Configure Studio connection"
3. Enter: `http://127.0.0.1:2024`
4. Click "Connect"

### Now You Have:

| Window | Purpose |
|--------|---------|
| Terminal 1 | Debug server on 127.0.0.1:2024 |
| Terminal 2 | Streamlit chat + logs |
| Browser | LangSmith Studio connected |

---

## What You'll See in Studio

### Graph View
- All agent nodes displayed (request_intake, supervisor, alert_analysis, etc.)
- Connections between agents shown
- Routing logic visualized

### Execution Flow
- Nodes light up as they execute
- State changes shown at each step
- Tool calls displayed with parameters
- LLM interactions visible

### Playground
- Test your agent directly in Studio
- Send requests and see responses
- Watch execution trace in real-time

---

## Advantages of This Solution

✅ **No Custom Code** - Uses LangGraph's built-in CLI
✅ **Production-Tested** - Same approach as reference projects
✅ **No Docker Required** - Pure Python, Windows 11 native
✅ **Hot-Reload** - Edit code and changes apply instantly
✅ **Full Integration** - Native LangSmith Studio support
✅ **Professional Grade** - Enterprise-ready setup
✅ **Easy to Use** - Just `python debug.py`

---

## Troubleshooting

### "langgraph not found"

Install LangGraph CLI:
```powershell
pip install langgraph-cli
```

Or let `debug.py` install it (automatically done)

### Connection failed in Studio

**Error:** "Connection failed. Ensure your server is running"

**Checklist:**
1. ✓ Is `python debug.py` still running?
2. ✓ Does the PowerShell show "Server will start on"?
3. ✓ Test health: `curl http://127.0.0.1:2024`
4. ✓ Firewall not blocking port 2024?
5. ✓ Try refreshing LangSmith Studio

### Port 2024 already in use

The LangGraph CLI will auto-select the next available port. Check the output in `python debug.py` for the actual port being used.

### .env configuration missing

**Error:** "LANGSMITH_API_KEY not set in .env"

Make sure .env has:
```bash
LANGSMITH_API_KEY=your_actual_key_here
LANGSMITH_TRACING=true
```

---

## Using with Streamlit

For full development with chat interface AND graph visualization:

**Terminal 1:**
```powershell
python debug.py
```

**Terminal 2:**
```powershell
.\debug.bat
```

**Browser 1:**
```
http://127.0.0.1:2024/
```
(Configure Studio connection)

**Browser 2:**
```
http://localhost:8501
```
(Streamlit chat interface)

Now you have:
- Chat interface for testing
- Graph visualization in Studio
- Trace data and metrics
- Debug logging in Terminal 2

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│ Windows 11 Local Environment                         │
│                                                      │
│  Terminal 1: python debug.py                         │
│  ├─ Loads: langgraph.json                           │
│  ├─ Loads: src/graph.py (the graph)                 │
│  ├─ Loads: .env (API keys)                          │
│  └─ Server: http://127.0.0.1:2024 (LangGraph CLI)  │
│                                                      │
│  Terminal 2 (Optional): .\debug.bat                 │
│  ├─ Streamlit: http://localhost:8501               │
│  ├─ LangSmith traces: smith.langchain.com          │
│  └─ Debug logs to console                           │
│                                                      │
└──────────────────────────────────────────────────────┘
        │                          │
        │                    HTTP Connection
        │                          │
        │      ┌────────────────────┘
        │      │
        │      ├─ Graph structure
        │      ├─ Real-time execution
        │      ├─ Playground testing
        │      └─ Full tracing
        │
        └─ Traces to LangSmith (HTTPS)
           ├─ Agent execution
           ├─ LLM calls
           ├─ Tool invocations
           └─ Performance metrics
```

---

## Next Steps

1. Run: `python debug.py`
2. Open: https://smith.langchain.com/
3. Click: "Configure Studio connection"
4. Enter: `http://127.0.0.1:2024`
5. Click: "Connect"
6. See your graph structure appear!

---

## Summary

This is the **proven, production-ready solution** for connecting your local LangGraph agent to LangSmith Studio:

- ✅ Uses LangGraph CLI (no custom server code)
- ✅ Works on Windows 11 without Docker
- ✅ Professional enterprise setup
- ✅ Full graph visualization and tracing
- ✅ Simple to use: `python debug.py`

Just run the script and connect Studio to `http://127.0.0.1:2024`!

---

## Reference

This approach is based on the verified implementation in the `medassistai-langsmith` reference project, which successfully uses:
- LangGraph CLI dev server
- LangSmith Studio integration
- Hot-reload during development
- Full graph visualization

Same proven solution, now adapted for SecureOps AI.
