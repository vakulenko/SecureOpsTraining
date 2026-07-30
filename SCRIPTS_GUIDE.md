# Windows Scripts Guide

Quick reference for running SecureOps AI on Windows with different configurations.

## Available Scripts

### 1. `start.bat` - Normal Production Mode

**Purpose:** Start the application with standard configuration

**Usage:**
```bash
.\start.bat
```

**What it does:**
- ✓ Checks Python installation
- ✓ Creates virtual environment (if needed)
- ✓ Installs dependencies from requirements.txt
- ✓ Creates .env from .env.example (if needed)
- ✓ Starts Streamlit app on http://localhost:8501

**When to use:**
- Normal daily development
- Testing the application
- Running presentations (stable, no debug output)

**Output:**
- Clean Streamlit interface
- No verbose logging
- Minimal console output

---

### 2. `debug.bat` - Debug Mode with LangSmith Monitoring

**Purpose:** Start the application in debug mode with LangSmith Studio monitoring

**Usage:**
```bash
.\debug.bat
```

**What it does:**
- ✓ All of start.bat tasks
- ✓ Sets DEBUG=true and verbose logging
- ✓ Reads .env to detect LangSmith configuration
- ✓ **Automatically opens LangSmith Studio in your browser**
- ✓ Starts Streamlit on http://localhost:8501
- ✓ Enables detailed console logging

**When to use:**
- Debugging agent behavior
- Investigating why something isn't working
- Developing new agents or tools
- Analyzing agent performance and token usage
- Iterating on prompts

**Output:**
- Verbose debug logging in console
- LangSmith Studio opens automatically
- Detailed information about every operation

---

## Quick Comparison

| Feature | start.bat | debug.bat |
|---------|-----------|-----------|
| Python check | ✓ | ✓ |
| Virtual environment setup | ✓ | ✓ |
| Dependency installation | ✓ | ✓ |
| .env creation | ✓ | ✓ |
| Streamlit UI | ✓ | ✓ |
| Debug logging | ✗ | ✓ |
| LangSmith Studio auto-open | ✗ | ✓ |
| Best for | Production | Development |

---

## Using the Scripts

### First Time Setup

1. **Navigate to project directory:**
   ```powershell
   cd C:\Projects\fde\github\SecureOpsTraining
   ```

2. **Run the startup script:**
   ```powershell
   .\start.bat
   ```

3. **Wait for the app to start** (first run takes longer)

4. **Streamlit should open automatically at:** http://localhost:8501

### Running in Debug Mode

1. **Make sure API keys are in `.env`:**
   ```bash
   GOOGLE_API_KEY=your_key_here
   LANGSMITH_API_KEY=your_key_here
   LANGSMITH_TRACING=true
   ```

2. **Run debug script:**
   ```powershell
   .\debug.bat
   ```

3. **Two windows will open:**
   - **Streamlit UI** at http://localhost:8501
   - **LangSmith Studio** showing live traces

### Stopping the Application

1. **Press Ctrl+C** in the console window
2. **Or close the console/Streamlit window**

---

## Environment Variables (in .env)

### LLM Configuration (Required)
```bash
GOOGLE_API_KEY=your_gemini_api_key
GOOGLE_MODEL=gemini-1.5-flash
```

### LangSmith Configuration (Optional but recommended)
```bash
LANGSMITH_TRACING=true                    # Enable tracing
LANGSMITH_API_KEY=your_langsmith_key      # Your API key
LANGSMITH_PROJECT=SecureOps-SOC-Assistant # Project name
LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com  # Your region
```

### Debug Configuration
```bash
DEBUG=false          # Set to true for verbose logging
```

---

## Viewing LangSmith Traces

### Via debug.bat (Automatic)
- LangSmith Studio opens automatically in your default browser
- Traces appear in real-time as you interact with the app

### Manual Access
1. Go to https://smith.langchain.com/
2. Navigate to your project: `SecureOps-SOC-Assistant`
3. View the **Runs** tab for recent traces
4. Click on any trace to inspect details

### What You'll See in Traces
- **Agent execution flow** - Which agents ran and in what order
- **LLM calls** - Prompts sent to Gemini and responses
- **Tool invocations** - Which mock tools were called
- **Performance metrics** - Latency, token usage
- **Errors** - Any failures or warnings

---

## Troubleshooting

### Script Won't Run
**Error:** "cannot be loaded because running scripts is disabled"

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then try running the script again.

### Python Not Found
**Error:** "Python is not installed or not in PATH"

**Solution:**
1. Install Python from https://www.python.org/
2. Make sure to check "Add Python to PATH" during installation
3. Restart your terminal/PowerShell
4. Try the script again

### LangSmith Tracing Not Working
**Symptoms:** Traces don't appear in Studio

**Checklist:**
1. ✓ API key is correct in `.env`
2. ✓ `LANGSMITH_TRACING=true` in `.env`
3. ✓ Network connectivity to smith.langchain.com
4. ✓ Sidebar shows "✅ LangSmith Tracing: Enabled"
5. ✓ Check .env file wasn't modified incorrectly

### Application Won't Start
**Solution:** Check the console output for errors, then:

1. Try deleting `venv` folder and running script again
2. Check that all API keys are in `.env`
3. Run with debug.bat to see verbose error messages

---

## Performance Tips

### For Development (debug.bat)
- Debug logging adds ~100-200ms to each request
- Use for investigating issues, not performance testing
- Monitor LangSmith for token usage and costs

### For Production/Demos (start.bat)
- Faster response times (~1-2 seconds per request)
- No debug output clutter
- Cleaner user experience

---

## Keyboard Shortcuts in Streamlit

- **Ctrl+C** - Stop the application
- **R** - Rerun the app (if needed)
- **C** - Clear cache

---

## Next Steps

1. ✅ Set up `.env` with API keys
2. ✅ Run `.\start.bat` to verify app works
3. ✅ Run `.\debug.bat` to enable LangSmith monitoring
4. ✅ Send test requests and view traces in Studio
5. ✅ Analyze agent behavior and optimize prompts

---

**Need Help?**

- **LangSmith Setup**: See `docs/LANGSMITH_SETUP.md`
- **General Setup**: See `README.md`
- **Architecture**: See `docs/ARCHITECTURE.md`
- **LangSmith Integration**: See `LANGSMITH_INTEGRATION_SUMMARY.md`
