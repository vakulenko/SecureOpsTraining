# QuickStart - SecureOps AI

## For the Impatient 🚀

### First Time? Do This:
```powershell
.\dev-setup.bat
# Choose option 1 for full development environment
```

### Just Want to Run the App?
```powershell
.\start.bat
```

### Want to Debug an Agent?
```powershell
.\debug.bat
```

### Want to See Graph Visualization?
```powershell
.\studio.bat
# Requires Docker - if not installed, use debug.bat instead
# Then configure in LangSmith Studio dialog: http://localhost:8023
```

---

## The 4 Scripts at a Glance

| Script | What it does | When to use |
|--------|--------------|------------|
| `start.bat` | Run app normally | Demos, testing |
| `debug.bat` | Run app + show traces + open LangSmith | Debugging |
| `studio.bat` | Show graph visualization | Understanding flow |
| `dev-setup.bat` | Choose from menu (best for first time) | Guided setup |

---

## What Opens Where

### start.bat
```
Browser: http://localhost:8501 (Streamlit)
Console: Minimal output
```

### debug.bat
```
Browser 1: http://localhost:8501 (Streamlit)
Browser 2: smith.langchain.com (LangSmith - opens automatically)
Console: Verbose debug output
```

### studio.bat
```
Console: Server running on http://localhost:8023
(Use this URL in LangSmith Studio dialog)
```

### dev-setup.bat Option 1 (Full Dev Environment)
```
Browser 1: http://localhost:8501 (Streamlit)
Browser 2: smith.langchain.com (LangSmith - opens automatically)
Browser 3: http://localhost:8023 (Graph visualization)
Console 1: LangGraph server logs
Console 2: Streamlit debug logs
```

---

## Common Tasks

### Task: Test the app quickly
```powershell
.\start.bat
```
Open http://localhost:8501 and send test requests.

### Task: Debug why an agent is failing
```powershell
.\debug.bat
# Streamlit opens at localhost:8501
# LangSmith Studio opens automatically
# Send test request, view trace in LangSmith
# Check console for debug output
```

### Task: Understand the graph structure
```powershell
# Terminal 1:
.\studio.bat

# Terminal 2:
.\debug.bat

# In LangSmith Studio:
# - Click "Configure Studio connection"
# - Enter: http://localhost:8023
# - Click "Connect"
# Now you see the graph structure + execution flow
```

### Task: Full development with all monitoring
```powershell
.\dev-setup.bat
# Choose: 1
# Everything starts automatically
```

### Task: Stop the app
```
Press Ctrl+C in the terminal
```

---

## API Keys in .env

Make sure your `.env` has:
```bash
GOOGLE_API_KEY=your_gemini_key_here
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_key_here
```

Without these, the app will fail to start.

---

## URLs Reference

| Component | URL |
|-----------|-----|
| Streamlit App | http://localhost:8501 |
| LangSmith Studio | https://smith.langchain.com |
| Local Graph Server | http://localhost:8023 |
| LangSmith Web | https://smith.langchain.com |

---

## Keyboard Shortcuts

| Action | Keys |
|--------|------|
| Stop any script | Ctrl+C |
| Rerun Streamlit | R (in browser) |
| Clear Streamlit cache | C (in browser) |

---

## Troubleshooting Quick Fixes

**Script won't run?**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Python not found?**
- Install from https://www.python.org
- Make sure "Add to PATH" is checked
- Restart PowerShell

**LangSmith trace not appearing?**
- Check .env has `LANGSMITH_TRACING=true`
- Check API key is correct
- Check browser shows "✅ LangSmith Tracing: Enabled"

**Port already in use?**
```bash
# For port 8501 (Streamlit):
streamlit run src/app.py --server.port 8502

# For port 8023 (LangGraph):
langgraph up --port 8024
```

---

## Next Steps

1. ✅ Run `.\dev-setup.bat`
2. ✅ Send test request in Streamlit
3. ✅ View trace in LangSmith Studio
4. ✅ Debug and iterate
5. ✅ Commit when happy

---

## Full Docs

- **All scripts details**: `STARTUP_SCRIPTS_COMPLETE.md`
- **LangSmith setup**: `docs/LANGSMITH_SETUP.md`
- **Architecture**: `docs/ARCHITECTURE.md`
- **Main README**: `README.md`

---

**That's it! You're ready to develop.** 🎉

Questions? Check the appropriate guide above.
