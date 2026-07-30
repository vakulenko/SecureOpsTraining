# Identity & Access Agent — Integration Guide

**Owner:** TM2 · **For:** TM4 (graph + UI), TM3 (same approval pattern)

The identity agent is complete and tested. It does **not** touch `src/graph.py` or
`src/app.py` — this document is everything needed to wire it in.

---

## 0. How to validate it

All three work **without a `GOOGLE_API_KEY`**, because the model is swapped for a
scripted stand-in. The tools and mock data are always the real ones.

```bash
# 1. Test suite - 69 tests, pass/fail
python -m pytest tests -q

# 2. Narrated walkthrough - prints the real data at each step, good for the demo
python scripts/validate_identity.py
python scripts/validate_identity.py --live      # real Gemini, needs GOOGLE_API_KEY

# 3. Clickable UI - shows the approval gate pausing and resuming
streamlit run scripts/validate_identity_app.py
```

The Streamlit harness is **the reference for the approval UI you need to build**: the
pause, the Approve/Reject buttons, the disabled chat input, and the resume call are all
implemented in `scripts/validate_identity_app.py`. Its `send()` / `resume()` / `handle()`
functions map directly onto what `src/app.py` needs.

In scripted mode the tool *selection* is keyword-based rather than LLM-chosen, so it
validates plumbing and the approval gate, not prompt quality. Use `--live` / the sidebar
toggle for that (and for LangSmith traces).

---

## 1. What the node reads and writes

`identity_agent_node(state) -> dict` in `src/agents/identity.py`.

**Reads:** `user_message`, `request_info.entities.username` (falls back to finding an
email address in `user_message` if intake didn't extract one).

**Writes:** exactly one key, `state["identity"]`. Nothing else.

| Field | Type | Notes |
|---|---|---|
| `username` | `str` | Who the result is about. `""` if none was found. |
| `login_history` | `list[dict]` | From `check_login_history`. Empty if not called. |
| `user_activity` | `list[dict]` | From `search_user_activity`. |
| `account_status` | `str` | `active` / `locked` / `disabled` / `unknown`. |
| `actions_taken` | `list[str]` | e.g. `["unlock_account: unlocked"]`. Empty if rejected. |
| `summary` | `str` | **Analyst-facing prose. Use this for the final response.** |
| `error` | `str \| None` | Set on missing username or agent failure. |

`summary` is the field to render — it saves the response generator from re-summarising
raw dicts with another model call.

---

## 2. ⚠️ The one thing that will silently break the approval gate

`interrupt()` pauses the graph by **raising** `GraphInterrupt`. If a node wraps its work
in `except Exception`, it swallows that exception, the graph never pauses, and **the
sensitive tool executes without approval**. It fails silently — the run looks successful.

This bit us during development. The fix is to let LangGraph's control-flow exceptions
through first (`src/agents/identity.py`):

```python
from langgraph.errors import GraphBubbleUp

try:
    response = agent.invoke(...)
except GraphBubbleUp:
    # An approval request pauses the graph by raising. That is control flow, not a
    # failure, so it must reach LangGraph instead of being turned into an error.
    raise
except Exception as exc:
    ...  # real failures become result["error"]
```

**TM3: the same applies to `scan_device`, `create_incident`, and `escalate_incident`.**
`tests/test_identity_agent.py::test_approval_interrupt_is_not_swallowed_as_an_error`
is the regression guard — copy the pattern.

---

## 3. Interrupt payload — verified against the installed versions

`HumanInTheLoopMiddleware` on `langchain==1.3.14` emits:

```python
result["__interrupt__"][0].value == {
    "action_requests": [
        {
            "name": "unlock_account",
            "args": {"username": "rjohnson@company.com"},
            "description": "Identity action pending analyst approval\n\n"
                           "Tool: unlock_account\nArgs: {'username': 'rjohnson@company.com'}",
        }
    ],
    "review_configs": [
        {"action_name": "unlock_account", "allowed_decisions": ["approve", "reject"]}
    ],
}
```

Render `description` and build the buttons from `allowed_decisions`.

Two corrections to our own docs:

- `ARCHITECTURE.md` and `CLAUDE.md` specify `{action, context, reason}` and
  `Command(resume=True/False)`. **Both are wrong** for the middleware. They should be
  updated once, for all three approval-gated agents.
- The published LangChain docs show the argument key as `arguments`. The installed
  version emits **`args`**. Trust this document, not the docs.

**Resume protocol:**

```python
from langgraph.types import Command

# Approve
graph.invoke(Command(resume={"decisions": [{"type": "approve"}]}), config)

# Reject (message is optional but recommended - the model reads it)
graph.invoke(
    Command(resume={"decisions": [{"type": "reject",
                                  "message": "Verify identity out-of-band first."}]}),
    config,
)
```

Decisions are a list, one per entry in `action_requests`, **in the same order**.

---

## 4. Wiring it up

### `src/graph.py`

```python
from src.utils import create_checkpointer

# A checkpointer is REQUIRED or approvals cannot pause and resume.
return graph_builder.compile(checkpointer=create_checkpointer())
```

Then route to the node. It is currently registered but **unreachable** — no edges in or out:

```python
graph_builder.add_conditional_edges(
    NODE_SUPERVISOR, route_next_action, {ACTION_IDENTITY: NODE_IDENTITY, ...}
)
graph_builder.add_edge(NODE_IDENTITY, NODE_SUPERVISOR)   # back for multi-agent requests
```

> **Blocker on your side:** `supervisor_agent_node` (`src/agents/supervisor.py:28`)
> computes `next_action` but never returns it, so no router can read it. Identity stays
> unreachable until that's fixed.

### `src/app.py`

```python
import uuid
from langgraph.types import Command

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

config = {"configurable": {"thread_id": st.session_state.thread_id}}
result = graph.invoke(initial_state, config)

if "__interrupt__" in result:
    request = result["__interrupt__"][0].value["action_requests"][0]
    st.warning(request["description"])
    # Show Approve / Reject, disable chat input while pending, then resume with the
    # decisions payload from section 3 and the SAME thread_id.
```

Use `result["__interrupt__"]` (what we tested). `invoke(..., version="v2")` instead
returns a `GraphOutput` with `.interrupts` — pick one and stay with it.

---

## 5. Optional SQLite persistence

Off by default; unset behaves exactly as documented today (`InMemorySaver`, session-only).

| Variable | Effect |
|---|---|
| `SOC_PERSISTENCE=sqlite` | Use `SqliteSaver`, so approvals survive a restart |
| `SOC_DB_PATH` | DB location (default `data/soc_assistant.db`) |

`create_checkpointer()` falls back to `InMemorySaver` if the sqlite package is missing.

Chat history helpers in `src/utils/conversation_store.py` — `save_message`,
`load_messages(thread_id)` (returns the same `{"role", "content"}` shape `app.py`
already uses), `list_threads`, `delete_thread`. None of them raise; if the database is
unusable they degrade to empty so the chat keeps working.

**Caveats:** the DB holds analyst conversation text, so `*.db` is gitignored — don't
commit it. `SqliteSaver` is documented as suitable for demos and small projects, not
production scale. Streamlit Community Cloud disks are ephemeral: persistence survives
restarts but **not** a redeploy.

⚠️ `CLAUDE.md` lists "no database persistence" as an explicit non-goal. This is off by
default so we can ship either way, but **the team should agree before merging to `main`.**

---

## 6. How the mock data behaves

**Approved actions really change state.** `unlock_account` and `request_password_reset`
write their change, so a later `check_account_status` reflects it — an approved unlock
turns `rjohnson@company.com` from `locked` to `active` and clears `failed_login_count`.

Writes go to **`data/runtime/`** (gitignored), never to the seed files in `data/`. So:

- `git status` stays clean after a demo.
- Resetting is `reset_runtime_data()` from `src/tools/mock_store.py`, the **Reset mock
  data** button in the Streamlit harness, or just deleting `data/runtime/`.
- Tests set `SOC_RUNTIME_DIR` to a temp folder (autouse fixture in `tests/conftest.py`),
  so they never touch developer state or each other.

Writes are **idempotent** — unlock sets the account to a known state rather than
incrementing anything. That matters because LangGraph re-runs a node from the top on
resume. (With `HumanInTheLoopMiddleware` the tool itself only executes after approval, so
it runs once, but idempotency means a retry cannot corrupt anything either.)

**Timestamps use the real clock.** The seed files are written around a fixed anchor
(`SEED_ANCHOR`, `2025-07-30T10:30:00Z`) and every timestamp is shifted onto the current
time when loaded. Relative gaps are preserved — the failed-login burst is still one
minute apart — but the events are always recent, so "in the last 24 hours" keeps working
as the seed data ages. Without this, the fixed 2025 timestamps would fall outside every
time window and all queries would return empty.

One consequence: `check_login_history` no longer returns byte-identical results across
calls, because the timestamps track the clock. The *content* is stable — see
`test_event_content_is_stable_across_calls`.

Other notes:

- Read-only tools have no approval gate, by design.
- Only `unlock_account` and `request_password_reset` are gated. Anything absent from
  `APPROVAL_TOOLS` is auto-approved by the middleware.

---

## 7. Repo bugs found along the way

1. **`.env.example` published the wrong variable name — FIXED.** `config.py` reads
   `GOOGLE_MODEL`; `.env.example` documented `GEMINI_MODEL`. A `.env` copied from the
   example silently fell back to `gemini-1.5-flash`, **which now returns 404 (retired)**,
   so live mode failed for anyone following the example. `Settings.from_env()` now accepts
   either name, the default is `gemini-3.5-flash-lite`, and `.env.example` says
   `GOOGLE_MODEL`. Verified working against the live API.
2. **Gemini returns content as blocks, not a string — FIXED.** Reading `message.content`
   directly put `[{'type': 'text', 'text': ...}]` into the analyst-facing summary. The
   agent now uses `message.text`, which flattens both shapes. Anyone else surfacing model
   output (response generator, UI) will hit this too.
3. **`CLAUDE.md:65` says Python 3.9+.** The code uses `str | None` in TypedDict bodies,
   which needs **3.10+**. The venv is on 3.12.10.
