# LangSmith Tracing Setup for SecureOps AI

This guide explains how to enable and use LangSmith for monitoring and tracing agent execution in the SecureOps AI application.

## What is LangSmith?

[LangSmith](https://smith.langchain.com/) is LangChain's platform for:
- **Tracing**: Capture every LLM call, tool execution, and agent decision
- **Debugging**: Understand exactly what your agents are doing at each step
- **Monitoring**: Track performance metrics, latencies, and error rates
- **Evaluation**: Test and iterate on agent behavior with structured evaluation runs
- **Prompt iteration**: Version and improve prompts based on production traces

## Getting Started

### 1. Sign Up for LangSmith

1. Go to [https://smith.langchain.com/](https://smith.langchain.com/)
2. Click "Sign Up" and create a free account
3. You'll be redirected to your LangSmith dashboard

### 2. Get Your API Key

1. Click on your **profile icon** (top right) → **API Keys**
2. Click **Create API Key** (or copy existing key)
3. Copy the API key to your clipboard

### 3. Configure Your Environment

Add your LangSmith API key to the `.env` file in your project root:

```bash
# Enable LangSmith tracing
LANGSMITH_TRACING=true

# Your LangSmith API key
LANGSMITH_API_KEY=lsv2_pt_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Project name (optional, defaults to SecureOps-SOC-Assistant)
LANGSMITH_PROJECT=SecureOps-SOC-Assistant

# API endpoint (use correct region)
# For US (default): https://api.smith.langchain.com
# For EU: https://eu.api.smith.langchain.com
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
```

## Running the Application with Tracing

### Starting the App

Run the application normally:

```bash
streamlit run src/app.py
```

Or use the Windows startup script:

```bash
.\start.bat
```

### Verify Tracing is Enabled

When the app starts, check the **Streamlit sidebar** for the "📊 Monitoring & Tracing" section:

- **✅ LangSmith Tracing: Enabled** - Tracing is active
- **⏸️ LangSmith Tracing: Disabled** - Tracing is off (LANGSMITH_TRACING=false)

### View Traces in Real-Time

1. Open [LangSmith Studio](https://smith.langchain.com)
2. Navigate to your project: `SecureOps-SOC-Assistant` (or your configured project name)
3. As you interact with the app, new traces will appear in the **Runs** tab
4. Click on any trace to inspect:
   - **Inputs**: What the agent received
   - **Outputs**: What the agent returned
   - **Metadata**: Execution time, tokens used, etc.
   - **Logs**: Tool calls, LLM prompts, intermediate reasoning

## Understanding Traces

### Trace Structure

Each conversation in SecureOps AI creates a trace showing:

```
request_intake_agent
├── LLM call (extract entities from user message)
└── Response (parsed request info)

supervisor_agent
├── LLM call (route to appropriate specialist agent)
└── Response (routing decision)

[specialist agents - one or more of:]
├── alert_analysis_agent
├── identity_agent
├── endpoint_agent
├── incident_agent
└── reporting_agent

response_generator
└── Final synthesized response
```

### Example: Inspecting an Alert Analysis Trace

1. Open a trace from **LangSmith Studio**
2. Look for the `alert_analysis_agent` span
3. Inspect the **Inputs**:
   - Query from user
   - Search parameters
4. Inspect the **Outputs**:
   - Alerts found
   - Severity classification
5. Check **Tool Calls**:
   - Which mock tools were invoked
   - Parameters passed
   - Results returned

## Performance Monitoring

### Key Metrics to Track

In LangSmith, monitor these metrics for each agent:

- **Latency**: How long each agent takes to respond
- **Token Usage**: Input/output tokens consumed by the LLM
- **Error Rate**: How often agents fail
- **Tool Invocation Count**: Which tools are used most

### Example Dashboard Query

To see all traces for the Alert Analysis agent:

```
agent_name = "alert_analysis_agent"
status = "success"
```

## Prompt Evaluation & Iteration

After running 10+ conversations:

1. **Export Traces**: Download traces from LangSmith
2. **Analyze Results**: Look for patterns in agent behavior
3. **Identify Issues**: Find prompts that cause confusion or errors
4. **Improve Prompts**: Update agent prompts in `src/agents/`
5. **A/B Test**: Use LangSmith evaluation to compare old vs. new prompts

## Disabling Tracing

To turn off tracing temporarily:

```bash
# In .env, set:
LANGSMITH_TRACING=false
```

The app will continue to work normally, but no traces will be sent to LangSmith.

## Troubleshooting

### "Failed to initialize LangSmith"

**Causes:**
- Invalid or expired API key
- Network connectivity issue
- Incorrect endpoint URL

**Solution:**
1. Verify your API key at [https://smith.langchain.com/settings/api_keys](https://smith.langchain.com/settings/api_keys)
2. Check your `.env` file for typos
3. Ensure you're using the correct endpoint (US or EU)
4. Try connecting from a different network

### Traces Not Appearing in Studio

**Causes:**
- `LANGSMITH_TRACING=false` in `.env`
- API key not set or invalid
- Project name doesn't match

**Solution:**
1. Check sidebar status: is tracing "Enabled"?
2. Verify `.env` has `LANGSMITH_TRACING=true` and valid `LANGSMITH_API_KEY`
3. Restart the Streamlit app after changing `.env`
4. Check that project exists in LangSmith (create if needed)

### High Latency or Performance Issues

**Note**: Tracing adds ~50-100ms per agent invocation due to network I/O.

If you need real-time performance:
1. Disable tracing with `LANGSMITH_TRACING=false`
2. Or run on-premises LangSmith (Enterprise only)

## Using LangSmith for Evaluation

### Setting Up an Evaluation Dataset

1. **Record Production Traces**: Let the app run naturally and capture conversations
2. **Create Dataset in LangSmith**: Export successful traces as a dataset
3. **Define Criteria**: What makes a response "good"?
   - Correct entities extracted?
   - Appropriate agent selected?
   - Clear final response?
4. **Run Evaluation**: Test new prompts against the dataset

### Example Evaluation Question

```
Evaluator: "Did the Alert Analysis agent identify the correct severity level?"
Expected: CRITICAL
Agent Output: CRITICAL
Score: ✅ PASS
```

## Resources

- **LangSmith Docs**: https://docs.smith.langchain.com/
- **LangSmith Studio**: https://smith.langchain.com/
- **API Reference**: https://docs.smith.langchain.com/reference/
- **LangChain Docs**: https://python.langchain.com/

## Next Steps

1. ✅ Enable tracing in `.env`
2. ✅ Start the app and send a few requests
3. ✅ View traces in LangSmith Studio
4. ✅ Analyze agent behavior and performance
5. ✅ Iterate on prompts based on real execution data
