"""Streamlit chat UI for SecureOps AI SOC Assistant."""

import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Ensure project root is in path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st

from src import get_graph, get_settings
from src.utils import SOCWorkflowState, setup_langsmith_tracing, get_langsmith_info


def initialize_session_state():
    """Initialize Streamlit session state."""
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    if "graph" not in st.session_state:
        st.session_state.graph = get_graph()
    if "langsmith_initialized" not in st.session_state:
        setup_langsmith_tracing()
        st.session_state.langsmith_initialized = True


def run_workflow(user_message: str) -> str:
    """Execute the workflow with the user message and return the response."""
    settings = get_settings()
    graph = st.session_state.graph

    initial_state: SOCWorkflowState = {
        "user_message": user_message,
        "conversation_history": st.session_state.conversation_history,
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

    try:
        result = graph.invoke(initial_state)
        return result.get("final_response", "No response generated.")
    except Exception as e:
        return f"Error processing request: {str(e)}"


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
    st.subheader("Conversation History")
    conversation_container = st.container(border=True)

    with conversation_container:
        for message in st.session_state.conversation_history:
            role = message.get("role", "assistant")
            content = message.get("content", "")

            if role == "user":
                st.chat_message("user").write(content)
            else:
                st.chat_message("assistant").write(content)

    # Chat input
    st.subheader("Send a Request")
    user_input = st.chat_input("Describe your security request...")

    if user_input:
        # Add user message to history
        st.session_state.conversation_history.append(
            {"role": "user", "content": user_input}
        )

        # Display user message
        st.chat_message("user").write(user_input)

        # Run workflow
        with st.spinner("Processing your request..."):
            response = run_workflow(user_input)

        # Add assistant response to history
        st.session_state.conversation_history.append(
            {"role": "assistant", "content": response}
        )

        # Display assistant response
        st.chat_message("assistant").write(response)

        st.rerun()


if __name__ == "__main__":
    main()
