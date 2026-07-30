# Complete Startup Scripts Guide

Comprehensive guide to all Windows startup scripts for SecureOps AI development and debugging.

## Overview

You now have **4 startup scripts** for different development workflows:

| Script | Purpose | Best For |
|--------|---------|----------|
| **start.bat** | Normal production mode | Demos, stable testing |
| **debug.bat** | Debug with LangSmith tracing | Development, debugging agents |
| **studio.bat** | Local graph visualization | Understanding graph flow |
| **dev-setup.bat** | Interactive launcher menu | Choosing your setup dynamically |

---

## 1. start.bat - Normal Production Mode

**Purpose:** Start the application in clean, production-ready mode

**Usage:**
```powershell
.\start.bat
```

**What it does:**
- Checks Python installation
- Creates virtual environment (if needed)
- Installs dependencies
- Creates .env file (if needed)
- Starts Streamlit on http://localhost:8501

**Output:**
- Clean Streamlit interface
- Minimal console logging
- No debug output clutter

**When to use:**
- Presenting to non-technical audiences
- Stable, known-good behavior
- Performance testing
- Regular development work

---

## 2. debug.bat - Debug Mode with LangSmith Tracing

**Purpose:** Start app with verbose logging and LangSmith monitoring

**Usage:**
```powershell
.\debug.bat
```

**What it does:**
- All start.bat features
- Enables DEBUG=true environment variable
- Sets verbose logging level
- Detects LangSmith configuration
- **Automatically opens LangSmith Studio** in browser
- Shows project name and endpoint

**Opens two windows:**
1. **Streamlit** (http://localhost:8501) - Chat interface
2. **LangSmith Studio** (smith.langchain.com) - Traces and metrics

**Console output includes:**
```
✅ LangSmith Tracing: ENABLED
✅ Project: SecureOps-SOC-Assistant
📈 Opening LangSmith Studio in browser...
```

**When to use:**
- Debugging agent behavior
- Understanding why something fails
- Analyzing token usage and costs
- Optimizing prompts
- Investigating performance issues

**What you'll see in LangSmith:**
- Agent execution flow
- LLM calls to Gemini
- Tool invocations and parameters
- Performance metrics
- Error traces

---

## 3. studio.bat - Local Graph Visualization Server

**Purpose:** Start local LangGraph server for real-time graph visualization

**Usage:**
```powershell
.\studio.bat
```

**What it does:**
- Checks Python and virtual environment
- Installs LangGraph CLI tools
- Verifies langgraph.json exists
- Starts local server on http://localhost:8023
- Displays setup instructions

**Console output:**
```
========================================
 Local Studio Server Configuration
========================================

Server will start on:
  http://localhost:8023

How to use with LangSmith Studio:
  1. Keep this window open
  2. Open LangSmith Studio in your browser
  3. Click "Configure Studio connection"
  4. Enter Base URL: http://localhost:8023
  5. Click "Connect"
```

**Keep this window open** while using other scripts.

**When to use:**
- Want to see graph structure visualization
- Debugging routing logic
- Understanding state transformations
- Learning how graph works visually
- Teaching/presenting graph architecture

**What you'll see:**
- Graph nodes and connections
- Real-time execution flow
- State changes at each step
- Routing decisions highlighted
- Node execution animation

---

## 4. dev-setup.bat - Interactive Setup Launcher

**Purpose:** Interactive menu to choose which setup you want

**Usage:**
```powershell
.\dev-setup.bat
```

**Menu options:**

```
1) Full Development Environment (Recommended)
   - Streamlit app (http://localhost:8501)
   - Debug logging enabled
   - LangSmith Studio opens automatically
   - Local graph visualization (localhost:8023)

2) Streamlit Only with Debug Logging
   - Streamlit app with debug output
   - LangSmith Studio opens automatically
   - (No local graph server)

3) Streamlit Normal Mode
   - Clean interface
   - Best for demos

4) Local Graph Studio Server Only
   - Just the graph visualization
   - Use with other windows

5) Exit
```

**When to use:**
- Can't remember which script does what
- Want to choose setup interactively
- Different needs each day
- First time setup (guides you through options)

---

## Development Workflows

### Workflow 1: Quick Debugging

**Goal:** Debug why an agent isn't working correctly

1. **Run:**
   ```powershell
   .\debug.bat
   ```

2. **What opens:**
   - Streamlit (chat interface)
   - LangSmith Studio (trace viewer)

3. **What to do:**
   - Send test query to agent
   - Watch trace appear in LangSmith
   - Click trace to inspect:
     - LLM prompt that was sent
     - LLM response received
     - Tools called and parameters
   - Check console for debug output
   - Update agent prompt based on findings
   - Refresh and test again

---

### Workflow 2: Understanding Graph Flow

**Goal:** See how requests flow through agents

1. **Terminal 1 - Start graph server:**
   ```powershell
   .\studio.bat
   ```
   Keep this window open.

2. **Terminal 2 - Start Streamlit:**
   ```powershell
   .\debug.bat
   ```

3. **Browser:**
   - Go to LangSmith Studio
   - Click "Configure Studio connection"
   - Enter: `http://localhost:8023`
   - Click "Connect"

4. **Send request** and watch:
   - Streamlit: Chat interface
   - LangSmith: Execution traces
   - Local Studio: Graph nodes lighting up as they execute

---

### Workflow 3: Full Development Environment

**Goal:** Maximum visibility into everything

1. **Run:**
   ```powershell
   .\dev-setup.bat
   ```

2. **Choose option 1: Full Development Environment**

3. **What opens automatically:**
   - New terminal with LangGraph server
   - Streamlit on http://localhost:8501
   - LangSmith Studio in browser
   - Local graph visualization on localhost:8023

4. **Now you have:**
   - Chat interface
   - Trace debugging
   - Graph visualization
   - Console logging
   All in one setup!

---

### Workflow 4: Clean Demo

**Goal:** Present to team without debug clutter

1. **Run:**
   ```powershell
   .\start.bat
   ```

2. **Clean interface opens**
   - No debug output
   - Professional appearance
   - Fast response times

---

## Comparing Features

### By Component

#### Streamlit App (Chat Interface)
- **start.bat:** ✅ Yes (normal)
- **debug.bat:** ✅ Yes (with debug logging)
- **studio.bat:** ❌ No (server only)
- **dev-setup.bat:** ✅ Configurable

#### LangSmith Tracing
- **start.bat:** ✓ If enabled in .env
- **debug.bat:** ✅ Yes, auto-opens Studio
- **studio.bat:** ❌ No
- **dev-setup.bat:** ✅ Option 1 & 2 include it

#### Local Graph Visualization
- **start.bat:** ❌ No
- **debug.bat:** ❌ No
- **studio.bat:** ✅ Yes (server only)
- **dev-setup.bat:** ✅ Option 1 includes it

#### Console Debug Output
- **start.bat:** ❌ No
- **debug.bat:** ✅ Yes (verbose)
- **studio.bat:** ❌ No (server logs only)
- **dev-setup.bat:** ✅ Options 1 & 2

#### Automatic Browser Opening
- **start.bat:** ❌ Streamlit opens on save
- **debug.bat:** ✅ LangSmith Studio
- **studio.bat:** ❌ Shows URL in console
- **dev-setup.bat:** Depends on choice

---

## Configuration Reference

### Environment Variables Set by Scripts

**debug.bat sets:**
```bash
DEBUG=true
STREAMLIT_LOGGER_LEVEL=debug
```

**studio.bat sets:**
```bash
(LangGraph CLI environment variables for graph execution)
```

**dev-setup.bat sets:**
Depends on your choice (1, 2, 3, or 4)

---

## Troubleshooting

### Script Won't Run

**Error:** "cannot be loaded because running scripts is disabled"

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Python Not Found

**Solution:**
1. Install Python 3.9+ from https://www.python.org
2. Check "Add Python to PATH"
3. Restart PowerShell

### LangGraph CLI Not Installing

**Manual install:**
```bash
pip install langgraph-cli --upgrade
```

### Port Already in Use

If `localhost:8023` is in use:
```bash
langgraph up --port 8024
```
Then use `http://localhost:8024` in Studio connection dialog.

### LangSmith Studio Won't Open

**Check:**
1. Is `.env` configured with API keys?
2. Is `LANGSMITH_TRACING=true`?
3. Is internet connection working?
4. Try opening manually: https://smith.langchain.com/

### Local Studio Connection Fails

**In LangSmith Studio dialog:**
1. Make sure `studio.bat` is running
2. Check URL is `http://localhost:8023`
3. Make sure port 8023 is not blocked
4. Try refreshing the dialog

---

## Performance Notes

### Response Times

| Script | Typical Latency | Notes |
|--------|-----------------|-------|
| start.bat | 1-2 seconds | Fastest, no tracing overhead |
| debug.bat | 2-3 seconds | Includes network calls to LangSmith |
| studio.bat | N/A | Server only, no latency impact |
| dev-setup (1) | 2-3 seconds | Combines debug.bat and studio.bat |

### Resource Usage

| Script | CPU | Memory | Network |
|--------|-----|--------|---------|
| start.bat | Low | ~200MB | Minimal |
| debug.bat | Low | ~250MB | High (LangSmith) |
| studio.bat | Low | ~150MB | Minimal |
| dev-setup (1) | Medium | ~400MB | High (LangSmith) |

---

## Quick Reference

### I want to...

**...start the app normally**
```powershell
.\start.bat
```

**...debug an agent**
```powershell
.\debug.bat
```

**...see the graph structure**
```powershell
.\studio.bat
```

**...use all features together**
```powershell
.\dev-setup.bat
# Choose option 1
```

**...choose interactively**
```powershell
.\dev-setup.bat
```

**...stop any script**
```
Press Ctrl+C in the terminal
```

---

## Next Steps

1. **Choose your first setup:**
   ```powershell
   .\dev-setup.bat
   ```

2. **Send test requests** to the app

3. **View traces** in LangSmith Studio

4. **Check console output** for debug information

5. **Iterate on prompts** based on findings

6. **Commit improvements** when satisfied

---

## Documentation Map

- **README.md** - Main setup instructions
- **SCRIPTS_GUIDE.md** - Individual script details
- **STARTUP_SCRIPTS_COMPLETE.md** - This file (complete reference)
- **LANGSMITH_SETUP.md** - Detailed LangSmith guide
- **docs/ARCHITECTURE.md** - System design

---

## Summary

| Need | Use This |
|------|----------|
| Quick start | `start.bat` |
| Debugging | `debug.bat` |
| Graph visualization | `studio.bat` |
| Everything | `dev-setup.bat` option 1 |
| Interactive menu | `dev-setup.bat` |

**All scripts are smart, self-contained, and handle setup automatically.**

Enjoy your development! 🚀
