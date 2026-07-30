# Endpoint & Incident Response Agents — Integration Guide

**Owner:** TM3 · **For:** TM4 (graph + UI)

The endpoint and incident agents are complete and tested. Neither touches
`src/graph.py` or `src/app.py` — this document is everything needed to wire them in.

They use the **same HITL protocol as the identity agent** (see
[`IDENTITY_INTEGRATION.md`](./IDENTITY_INTEGRATION.md), which remains the primary
reference for the approval mechanics). This document covers what's specific to
endpoint/incident and doesn't repeat what's already correct there.

---

## 0. How to validate it

```bash
# 1. Test suite
python -m pytest tests/test_endpoint_incident_agents.py tests/test_endpoint_incident_tools.py -q

# 2. Interactive CLI harness - real Gemini, real interrupt/resume, needs GOOGLE_API_KEY
python scripts/manual_agent_test.py
```

`manual_agent_test.py` is a CLI, not a Streamlit page (unlike identity's
`scripts/validate_identity_app.py`, if/when that lands) — it compiles a one-node graph
with a real `InMemorySaver`, sends a message, and if the graph pauses, prints the
`action_requests` descriptions and asks `[y/N]` in the terminal, then resumes with the
real `{"decisions": [...]}` payload. Good for confirming tool selection and the
approval gate against the live model; not a UI reference.

---

## 1. What the nodes read and write

`endpoint_agent_node(state) -> dict` and `incident_agent_node(state) -> dict` in
`src/agents/endpoint.py` / `src/agents/incident.py`.

**Reads:** only `user_message`. Unlike identity, neither pre-extracts an entity from
`request_info` before calling the model — there's no single required field to gate on
(a device can be named by `device_id`, hostname, or IP; an incident request might not
reference an existing `incident_id` at all). Tool selection and argument extraction are
left entirely to the LLM's tool-calling.

**Writes:** exactly one key each, `state["endpoint"]` / `state["incident"]`.

### `EndpointResult`

| Field | Type | Notes |
|---|---|---|
| `device_status` | `dict` | From `check_endpoint_status`, or the first match from `search_device`. |
| `malware_details` | `list[dict]` | From `get_malware_details`. Empty if not called or clean. |
| `actions_taken` | `list[str]` | e.g. `["scan_device: initiated"]` or `["scan_device: <rejection message>"]`. |
| `summary` | `str` | **Analyst-facing prose. Use this for the final response.** |
| `error` | `str \| None` | Set on a tool-level error (e.g. device not found) or agent failure. |

### `IncidentResult`

| Field | Type | Notes |
|---|---|---|
| `incident_id` | `str` | From whichever of `create_incident` / `check_incident_status` / `escalate_incident` ran. |
| `status` | `str` | `"unknown"` until a tool sets it. |
| `timeline` | `list[dict]` | Appended to by `generate_incident_summary`. |
| `actions_taken` | `list[str]` | Approval outcome for `create_incident` / `escalate_incident`. |
| `summary` | `str` | **Analyst-facing prose. Use this for the final response.** |
| `error` | `str \| None` | Set on a tool-level error or agent failure. |

`summary` is the field to render, same convention as identity — it's the model's own
closing answer, not a re-summarization of raw dicts.

---

## 2. HITL: same gate, same failure mode

Both nodes already do the `GraphBubbleUp` re-raise identity's doc warns about:

```python
try:
    response = agent.invoke(...)
except GraphBubbleUp:
    raise  # interrupt() pausing the graph - not an error
except Exception as exc:
    ...  # real failures become result["error"]
```

Gated tools: `scan_device` (endpoint), `create_incident` and `escalate_incident`
(incident). Everything else auto-approves. Confirmed against the live API — pausing on
`scan_device`, approving with `Command(resume={"decisions": [{"type": "approve"}]})`,
and rejecting both round-trip correctly (`scripts/manual_agent_test.py`).

One thing we hit that identity's tools don't: a **rejected** call's `ToolMessage`
content is a plain rejection sentence, not JSON — `tool_payload()` returns it as a raw
string in that case, not a dict. Both `_result_from_messages` functions handle this
(`isinstance(payload, dict)` check before doing dict lookups), but it's worth knowing
if you write generic code over `action_requests` results elsewhere.

---

## 3. Wiring it up

Identical shape to identity — same `NODE_ENDPOINT` / `NODE_INCIDENT` registered in
`graph.py`, same conditional-edge + checkpointer + `app.py` changes needed. See
`IDENTITY_INTEGRATION.md` sections 3-4 for the exact code; nothing endpoint/incident
-specific to add here.

---

## 4. Known limitation: no persisted state (unlike identity)

Identity's `unlock_account` / `request_password_reset` write through
`src/tools/mock_store.py`, so an approved unlock really flips `account_status` for
later calls in the same run. **`scan_device`, `create_incident`, and
`escalate_incident` do not** — they return a fixed mock response
(`scan_status: "initiated"`, a hardcoded `incident_id: "INC-2025-999"`, etc.) but
never write it anywhere. Calling `check_incident_status` right after an approved
`create_incident` will **not** show the new incident; it only sees `data/mock_incidents.json`
Approving a create/scan/escalate today only affects `actions_taken` and the model's own
`summary` text, not any tool's later view of the world.

This matches what the tools looked like when this integration doc was written and is a
reasonable MVP simplification, but if the demo needs "create an incident, then check its
status and see it," `incident_tools.py`/`endpoint_tools.py` need the same
`mock_store.py`-style runtime overlay identity's tools already have. Flagging here so
it's a deliberate call, not a surprise during the demo.

---

## 5. Bugs found along the way (already fixed here, worth knowing about)

1. **Prompt ambiguity between `device_id` and hostname.** Early on, the endpoint
   agent's prompt told it to "search first" whenever given anything that wasn't
   obviously already a `device_id`, so a request like *"scan device DEV-002"* made it
   call `search_device("DEV-002")` — which matches on hostname/IP substrings, not
   `device_id` — got no results, and told the analyst the device didn't exist. Fixed by
   telling the prompt what a `device_id` looks like (`"DEV-" + digits`) and to use it
   directly. If you see an agent claiming a clearly-valid ID "wasn't found," this class
   of bug is worth checking for.
2. **`interrupt` payload/resume shape** — same finding as `IDENTITY_INTEGRATION.md`
   section 3, independently reproduced against the live API for `scan_device`,
   `create_incident`, and `escalate_incident`.
