# Local Agent Server Setup (No Docker Required)

Connect your local SecureOps AI agent to LangSmith Studio without Docker.

## What This Does

This creates a simple HTTP server that:
- Runs your agent locally on Windows
- Connects to LangSmith Studio for visualization
- Shows graph execution flow in real-time
- No Docker required - pure Python

## Quick Start

### 1. Start the Local Server

```powershell
.\server.bat
```

**Output should show:**
```
========================================
 LOCAL AGENT SERVER STARTED
========================================

Server Information:
  URL: http://localhost:8000
  Status: http://localhost:8000/health

How to connect to LangSmith Studio:
  1. Open LangSmith Studio in your browser
  2. Click "Configure Studio connection"
  3. Enter Base URL: http://localhost:8000
  4. Click "Connect"
```

**Keep this window open.**

### 2. Connect to LangSmith Studio

1. Open [LangSmith Studio](https://smith.langchain.com/) in your browser
2. Click the **"Configure Studio connection"** dialog (top right)
3. Enter **Base URL**: `http://localhost:8000`
4. Click **"Connect"**

You should see:
```
✅ Connection successful
```

### 3. View Your Agent Execution

Now you can:
- See graph structure in Studio
- Watch agent execution in real-time
- View node execution flow
- Monitor state changes

---

## How It Works

### Server Architecture

```
Windows 11 (Your Machine)
├─ server.bat (startup script)
├─ src/server.py (FastAPI HTTP server)
│  ├─ Loads your LangGraph
│  ├─ Exposes HTTP endpoints
│  └─ Listens on localhost:8000
└─ Traces sent to LangSmith (cloud)

LangSmith Studio (Browser)
├─ Connects to http://localhost:8000
├─ Requests graph structure
├─ Shows real-time execution
└─ Displays traces
```

### API Endpoints

The server exposes:

```
GET  http://localhost:8000/
     └─ API documentation

GET  http://localhost:8000/health
     └─ Health check status

GET  http://localhost:8000/graph
     └─ Graph structure (for visualization)

POST http://localhost:8000/invoke
     └─ Execute your agent
     └─ Input: {"user_message": "...", "conversation_history": [...]}
     └─ Output: Agent response
```

---

## Complete Workflow

### Terminal 1: Start Local Server

```powershell
PS> .\server.bat
```

Output:
```
Server Information:
  URL: http://localhost:8000
  Status: http://localhost:8000/health

How to connect to LangSmith Studio:
  1. Open LangSmith Studio in your browser
  2. Click "Configure Studio connection"
  3. Enter Base URL: http://localhost:8000
  4. Click "Connect"
```

### Terminal 2: Start Streamlit (Optional)

```powershell
PS> .\debug.bat
```

This opens:
- Streamlit at http://localhost:8501 (chat interface)
- LangSmith Studio at smith.langchain.com (traces)

### Browser: Connect Studio

1. Go to [LangSmith Studio](https://smith.langchain.com/)
2. Click "Configure Studio connection"
3. Enter: `http://localhost:8000`
4. Click "Connect"

### Now You Have:

| Window | Purpose |
|--------|---------|
| Terminal 1 | Local server (localhost:8000) |
| Terminal 2 | Streamlit UI + debug logs |
| Browser 1 | LangSmith Studio |
| Browser 2 | Streamlit app |

---

## Testing the Server

### Test Health Check

```powershell
# In another PowerShell window:
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "service": "SecureOps AI Agent Server",
  "version": "1.0.0"
}
```

### Test Invoke Endpoint

```powershell
$body = @{
    user_message = "Check alert status"
    conversation_history = @()
} | ConvertTo-Json

curl -Method POST `
     -Uri http://localhost:8000/invoke `
     -ContentType "application/json" `
     -Body $body
```

**Expected response:**
```json
{
  "status": "success",
  "result": {
    "final_response": "...",
    "request_info": {...},
    "completed_actions": [...]
  }
}
```

### View Graph Structure

```powershell
curl http://localhost:8000/graph
```

---

## What You'll See in Studio

Once connected, LangSmith Studio shows:

### Graph Visualization
- Nodes for each agent (request_intake, supervisor, etc.)
- Connections between agents
- Execution flow animation

### Real-time Execution
- Nodes light up as they execute
- State changes shown at each step
- Tool calls displayed with parameters
- LLM prompts and responses visible

### Performance Metrics
- Execution time per node
- Token usage
- Error tracking

---

## Advantages of This Approach

✅ **No Docker required** - Pure Python on Windows
✅ **Lightweight** - ~50 MB memory usage
✅ **Fast startup** - Starts in seconds
✅ **Native Windows** - Uses standard Python HTTP server
✅ **Full tracing** - All execution visible in Studio
✅ **Graph visualization** - See flow in real-time
✅ **Easy to debug** - Console output shows everything

---

## Troubleshooting

### Server won't start

**Error:** "Python is not installed"

**Solution:**
```powershell
pip install fastapi uvicorn
python src\server.py
```

### Connection failed in Studio

**Error:** "Connection failed. Ensure your server is running at this endpoint."

**Checklist:**
1. ✓ Is `server.bat` still running?
2. ✓ Does the PowerShell window show "Server running"?
3. ✓ Test health: `curl http://localhost:8000/health`
4. ✓ Check firewall not blocking port 8000
5. ✓ Try different URL: `127.0.0.1:8000` instead of `localhost:8000`

### Port 8000 already in use

**Error:** "Address already in use"

**Solution - Use different port:**
1. Edit `src/server.py` - change line:
   ```python
   uvicorn.run(..., port=8001, ...)
   ```
2. Or edit `server.bat` - add to last command:
   ```batch
   python src\server.py 8001
   ```
3. Connect Studio to: `http://localhost:8001`

### LangSmith not tracing

**Check:**
1. `.env` has `LANGSMITH_TRACING=true`
2. `.env` has valid `LANGSMITH_API_KEY`
3. Check Studio sidebar shows "✅ Tracing: Enabled"
4. Send request and check Studio for traces

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│ Windows 11 Local Environment                            │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Terminal 1: server.bat                          │   │
│  │  ├─ Starts: src/server.py                       │   │
│  │  ├─ Port: 8000                                  │   │
│  │  ├─ Graph: get_graph()                          │   │
│  │  └─ API Endpoints: /health, /graph, /invoke     │   │
│  └─────────────────────────────────────────────────┘   │
│           │                                             │
│           ├─── Localhost Connection ───┐               │
│           │                            │               │
│  ┌────────▼──────────────────────┐    │               │
│  │ Browser: LangSmith Studio      │    │               │
│  │ ├─ "Configure Studio          │    │               │
│  │ │  connection"                 │    │               │
│  │ ├─ Base URL: localhost:8000 ◄─┼────┘               │
│  │ ├─ Shows graph structure       │                   │
│  │ ├─ Shows execution flow        │                   │
│  │ └─ Shows real-time traces      │                   │
│  └────────────────────────────────┘                   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Terminal 2 (Optional): debug.bat                │   │
│  │  ├─ Streamlit UI (localhost:8501)               │   │
│  │  ├─ LangSmith traces (smith.langchain.com)      │   │
│  │  └─ Debug logging                               │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
         │
         ├─────────── Traces (HTTPS) ──────────────┐
         │                                        │
    ┌────▼──────────────────────────────────┐    │
    │ LangSmith Cloud                        │    │
    │ ├─ Receives traces from server.py      │◄───┘
    │ ├─ Stores execution data               │
    │ ├─ Provides Studio interface           │
    │ └─ Shows metrics & analysis            │
    └────────────────────────────────────────┘
```

---

## Next Steps

1. **Start server:** `.\server.bat`
2. **Open Studio:** https://smith.langchain.com/
3. **Connect:** Click "Configure Studio connection" → `http://localhost:8000`
4. **View traces:** Send requests and watch execution
5. **Optimize:** Use traces to improve prompts

---

## Requirements

- Python 3.9+ (you have it)
- FastAPI (automatically installed)
- Uvicorn (automatically installed)
- Windows 11 (you have it)
- **No Docker needed!**

---

## Summary

This gives you:
- ✅ Local agent execution on Windows
- ✅ Real-time visualization in LangSmith Studio
- ✅ No Docker required
- ✅ Full graph flow visibility
- ✅ Complete tracing integration
- ✅ Professional development setup

Just run `server.bat` and connect Studio to `http://localhost:8000`!

---

## Advanced: Custom Port

If port 8000 is taken, modify `src/server.py`:

```python
if __name__ == "__main__":
    main()
    # Then change in main():
    uvicorn.run(..., port=8001, ...)  # Change 8001 to any free port
```

Or run from command line:
```powershell
cd C:\path\to\project
python -m uvicorn src.server:app --host 127.0.0.1 --port 8001
```

Then connect Studio to: `http://localhost:8001`
