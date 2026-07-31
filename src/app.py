"""Streamlit chat UI for SecureOps AI SOC Assistant."""

import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Ensure project root is in path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import uuid
import streamlit as st

from langgraph.types import Command

from src import get_graph, get_settings
from src.utils import (
    SOCWorkflowState,
    get_langsmith_info,
    init_db,
    list_threads,
    load_messages,
    save_message,
    setup_langsmith_tracing,
)
from src.utils.approvals import build_resume, describe_action, describe_interrupt
from src.utils.trace import RunTrace


def initialize_session_state():
    """Initialize Streamlit session state."""
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    if "graph" not in st.session_state:
        st.session_state.graph = get_graph()
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())
    if "pending_approval" not in st.session_state:
        st.session_state.pending_approval = None
    if "current_trace" not in st.session_state:
        st.session_state.current_trace = RunTrace()
    if "debug" not in st.session_state:
        st.session_state.debug = False
    if "langsmith_initialized" not in st.session_state:
        setup_langsmith_tracing()
        init_db()
        st.session_state.langsmith_initialized = True


def start_new_thread() -> None:
    """Begin a fresh conversation. The current one stays saved and reopenable."""
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.conversation_history = []
    st.session_state.pending_approval = None
    st.session_state.current_trace = RunTrace()


def open_thread(thread_id: str) -> None:
    """Reopen a saved conversation."""
    st.session_state.thread_id = thread_id
    st.session_state.conversation_history = load_messages(thread_id)
    st.session_state.pending_approval = None
    st.session_state.current_trace = RunTrace()


def _history_for_graph() -> list[dict]:
    """Conversation history as the graph expects it.

    Assistant entries also carry a debug trace for the UI; that is display-only, so it
    is stripped here rather than being threaded through the workflow state.
    """
    return [
        {"role": message.get("role", "assistant"), "content": message.get("content", "")}
        for message in st.session_state.conversation_history
    ]


def _record_message(role: str, content: str, trace: dict | None = None) -> None:
    """Add a message to the transcript and save it so the thread can be reopened.

    The trace is display-only and stays in memory; a reopened thread shows its messages
    without the debug detail.
    """
    entry = {"role": role, "content": content}
    if trace is not None:
        entry["trace"] = trace

    st.session_state.conversation_history.append(entry)
    save_message(st.session_state.thread_id, role, content)


def _record_answer(response: str) -> None:
    """Add an assistant answer to the transcript with the trace for that turn."""
    _record_message("assistant", response, st.session_state.current_trace.summary())


def _drive_graph(graph_input, progress_placeholder=None) -> str:
    """Run the graph until it finishes or pauses for approval.

    Returns the text to show the analyst. If a sensitive tool needs sign-off, the
    request is stored in session state and the caller renders Approve/Reject buttons.
    """
    graph = st.session_state.graph
    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    final_response = ""
    # One trace per analyst turn. resume_workflow reuses it so a request that paused for
    # approval still ends up with a single trace covering the whole turn.
    trace = st.session_state.current_trace

    try:
        # subgraphs=True also surfaces events from inside each agent, which is the only
        # place the individual tool calls appear. The debug view is built from those.
        for namespace, event in graph.stream(
            graph_input, config=config, stream_mode="updates", subgraphs=True
        ):
            for node_name, updates in event.items():
                # An approval request pauses the graph. Without this branch the pause is
                # silently dropped and the analyst just sees "No response generated."
                if node_name == "__interrupt__":
                    st.session_state.pending_approval = describe_interrupt(
                        {"__interrupt__": updates}
                    )
                    return ""

                trace.record(namespace, node_name, updates)

                # Only announce top-level steps; the inner agent nodes are noise here.
                if progress_placeholder and not namespace:
                    with progress_placeholder.container():
                        st.info(f"✓ {node_name} completed")

                if isinstance(updates, dict) and updates.get("final_response"):
                    final_response = updates["final_response"]
    except Exception as e:
        return f"Error processing request: {str(e)}"

    st.session_state.pending_approval = None

    return final_response or "No response generated."


def run_workflow(user_message: str, progress_placeholder=None) -> str:
    """Start a new request."""
    st.session_state.current_trace = RunTrace()

    initial_state: SOCWorkflowState = {
        "user_message": user_message,
        "conversation_history": _history_for_graph(),
        "request_info": {},
        "requested_actions": [],
        "completed_actions": [],
        "alert_analysis": None,
        "identity": None,
        "endpoint": None,
        "incident": None,
        "reporting": None,
        "final_response": None,
    }

    return _drive_graph(initial_state, progress_placeholder)


def resume_workflow(approved: bool, message: str = "") -> str:
    """Continue a paused request with the analyst's decision."""
    st.session_state.pending_approval = None

    return _drive_graph(Command(resume=build_resume(approved, message)))


def render_thread_panel() -> None:
    """Sidebar: the current conversation, a way to start a new one, and past ones."""
    st.markdown("### 💬 Threads")

    # Switching mid-approval would strand the pending action on the other thread, so
    # thread controls are locked while a decision is outstanding, like the chat input.
    locked = st.session_state.pending_approval is not None
    current = st.session_state.thread_id

    st.caption(f"Current thread: `{current[:8]}`")

    if st.button("➕ New thread", use_container_width=True, disabled=locked):
        start_new_thread()
        st.rerun()

    others = [thread for thread in list_threads() if thread["thread_id"] != current]

    if not others:
        st.caption("No earlier threads yet.")
    else:
        st.caption(f"Earlier threads ({len(others)})")

        for thread in others[:10]:
            label = thread["title"] or "(empty)"
            if st.button(
                f"{label[:34]}  ·  {thread['message_count']}",
                key=f"thread-{thread['thread_id']}",
                use_container_width=True,
                disabled=locked,
            ):
                open_thread(thread["thread_id"])
                st.rerun()

    if locked:
        st.caption("Locked until you approve or reject the pending action.")


def render_debug_panel(trace: dict | None) -> None:
    """Show which agents ran and which tools they called for one answer."""
    if not trace:
        return

    agents = trace.get("agents") or []
    label = ", ".join(entry["agent"] for entry in agents) or "no agents"

    with st.expander(f"🔧 Debug — agents used: {label}", expanded=False):
        path = trace.get("path") or []
        if path:
            st.markdown("**Workflow path**")
            st.code(" → ".join(path), language=None)

        if not agents:
            st.caption("No agent was called for this request.")
            return

        for entry in agents:
            st.markdown(f"**{entry['agent']}** — {len(entry['tools'])} tool call(s)")

            if not entry["tools"]:
                st.caption("Answered without calling a tool.")
                continue

            for call in entry["tools"]:
                st.markdown(f"`{call['name']}({call['args']})`")
                result = call["result"]
                if result is None:
                    st.caption("awaiting approval — not executed")
                else:
                    st.caption(
                        result[:400] + ("…" if len(result) > 400 else "")
                    )


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="SecureOps AI - SOC Assistant",
        page_icon="🔒",
        layout="centered",
    )

    st.title("🔒 SecureOps AI - SOC Assistant")
    st.markdown(
        "Intelligent security operations center assistant powered by multi-agent AI"
    )

    initialize_session_state()

    # Display LangSmith status in sidebar
    with st.sidebar:
        render_thread_panel()

        st.divider()
        st.markdown("### 🔧 Debug")
        st.session_state.debug = st.toggle(
            "Show agents and tools",
            value=st.session_state.debug,
            help="After each request, show which agents ran and which tools they called.",
        )

        st.divider()
        st.markdown("### 📊 Monitoring & Tracing")
        langsmith_info = get_langsmith_info()

        if langsmith_info["tracing_enabled"]:
            st.success("✅ LangSmith Tracing: **Enabled**")
            st.markdown(
                f"**Project:** `{langsmith_info['project']}`\n\n"
                f"📈 [View Traces in LangSmith Studio](https://smith.langchain.com/projects/{langsmith_info['project']})"
            )
        else:
            st.info("⏸️ LangSmith Tracing: **Disabled**\n\nEnable by setting `LANGSMITH_TRACING=true` in .env")

    # Display conversation history
    conversation_container = st.container()
    with conversation_container:
        for message in st.session_state.conversation_history:
            role = message.get("role", "assistant")
            content = message.get("content", "")

            if role == "user":
                st.chat_message("user").write(content)
            else:
                with st.chat_message("assistant"):
                    st.write(content)
                    # Each answer keeps its own trace, so earlier turns stay inspectable
                    # after later ones arrive.
                    if st.session_state.debug:
                        render_debug_panel(message.get("trace"))

    # Approval gate: a sensitive tool is waiting on the analyst before it runs.
    pending = st.session_state.pending_approval

    if pending:
        action = describe_action(pending["tool"], pending["args"])

        with st.container(border=True):
            st.subheader(f"⏸️ {action['title']}")
            st.markdown(action["detail"])

            if action["effect"]:
                st.caption(action["effect"])

            st.warning("This has **not** run yet. It needs your approval.")

            with st.expander("Technical details"):
                st.code(f"{pending['tool']}({pending['args']})", language="python")

        approve_column, reject_column = st.columns(2)
        decision = None

        if "approve" in pending["allowed_decisions"] and approve_column.button(
            "✅ Approve", type="primary", use_container_width=True
        ):
            decision = True

        if "reject" in pending["allowed_decisions"] and reject_column.button(
            "❌ Reject", use_container_width=True
        ):
            decision = False

        if decision is not None:
            with st.spinner("Applying your decision..."):
                response = resume_workflow(
                    decision, "" if decision else "Analyst rejected the action."
                )

            if response:
                _record_answer(response)
            st.rerun()

        st.caption("Chat is paused until you approve or reject.")

    # Chat input - disabled while an approval is pending
    user_input = st.chat_input(
        "Describe your security request...", disabled=pending is not None
    )

    if user_input:
        _record_message("user", user_input)

        # Display user message
        st.chat_message("user").write(user_input)

        # Create placeholder for progress updates
        progress_placeholder = st.empty()

        # Run workflow with streaming
        response = run_workflow(user_input, progress_placeholder)

        # Clear progress placeholder
        progress_placeholder.empty()

        # An empty response means the graph paused for approval; the buttons are
        # rendered on the next run, so there is nothing to add to the transcript yet.
        if response:
            _record_answer(response)

        st.rerun()


if __name__ == "__main__":
    main()
