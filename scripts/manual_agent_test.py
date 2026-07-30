"""Manual self-test harness for the endpoint + incident agents (TM3 scope).

Runs a tiny standalone LangGraph containing only the node you're testing,
compiled WITH a real checkpointer (InMemorySaver) so interrupt() actually
pauses and Command(resume=...) actually resumes it -- the same mechanics
the real app will use once the supervisor's conditional routing and
checkpointer are wired in by TM4. Talks to the real Gemini API.

Dev/testing tool only -- not part of the deployed app.

Usage:
    python scripts/manual_agent_test.py

Try messages like:
    endpoint: "check the status of DEV-001"
    endpoint: "is there malware on DEV-002"
    endpoint: "scan device DEV-002"            <- triggers approval
    incident: "what's the status of INC-2025-001"
    incident: "create an incident for suspicious outbound traffic on DEV-002, severity high"
    incident: "escalate INC-2025-001 to P1"     <- triggers approval
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph
from langgraph.types import Command

from src.agents.endpoint import endpoint_agent_node
from src.agents.incident import incident_agent_node
from src.utils import SOCWorkflowState

AGENTS = {"1": ("endpoint", endpoint_agent_node), "2": ("incident", incident_agent_node)}


def build_single_node_graph(node_name: str, node_fn):
    builder = StateGraph(SOCWorkflowState)
    builder.add_node(node_name, node_fn)
    builder.set_entry_point(node_name)
    builder.set_finish_point(node_name)
    return builder.compile(checkpointer=InMemorySaver())


def run_node(node_name: str, node_fn, user_message: str) -> dict:
    graph = build_single_node_graph(node_name, node_fn)
    config = {"configurable": {"thread_id": f"manual-test-{node_name}"}}

    state: SOCWorkflowState = {
        "user_message": user_message,
        "conversation_history": [],
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

    result = graph.invoke(state, config=config)

    while "__interrupt__" in result:
        payload = result["__interrupt__"][0].value
        print(f"\n>>> APPROVAL REQUIRED: {payload}")
        approved = input(">>> Approve? [y/N]: ").strip().lower() == "y"
        result = graph.invoke(Command(resume=approved), config=config)

    return result


def main():
    print("TM3 manual self-test: endpoint + incident agents (real Gemini + real interrupt).\n")

    while True:
        choice = input("Node [1=endpoint, 2=incident, q=quit]: ").strip().lower()
        if choice == "q":
            break
        if choice not in AGENTS:
            print("Enter 1, 2, or q.")
            continue

        node_name, node_fn = AGENTS[choice]
        message = input("Message: ").strip()
        if not message:
            continue

        result = run_node(node_name, node_fn, message)
        print("\n--- RESULT ---")
        print(result.get(node_name))
        print()


if __name__ == "__main__":
    main()
