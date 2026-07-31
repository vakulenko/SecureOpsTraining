"""Test graph structure and compilation."""

import json
import os
from pathlib import Path

import pytest

from src.graph import create_api_graph, create_graph
from src.utils.state import SOCWorkflowState


def test_graph_compiles():
    """Test that the graph can be created and compiled."""
    graph = create_graph()
    assert graph is not None


def test_graph_has_a_checkpointer():
    """The graph we run ourselves must be compiled with a checkpointer.

    Without one, interrupt() can pause the graph but nothing can resume it, so an
    approved action would never run.
    """
    assert create_graph().checkpointer is not None


def test_api_graph_has_no_checkpointer():
    """The graph handed to `langgraph dev` must NOT bring its own checkpointer.

    LangGraph Platform provides persistence itself and refuses to load a graph that
    supplies one, so shipping a checkpointer here breaks `langgraph dev`.
    """
    assert not create_api_graph().checkpointer


def test_langgraph_json_points_at_the_api_graph():
    """langgraph.json must reference the checkpointer-free entry point."""
    config = json.loads((Path(__file__).parent.parent / "langgraph.json").read_text())

    assert config["graphs"]["soc_assistant"].endswith(":create_api_graph")


@pytest.mark.skipif(
    not os.getenv("GOOGLE_API_KEY"),
    reason="Runs the real workflow end to end, which needs a Google API key.",
)
def test_graph_accepts_state():
    """Test that graph accepts a valid state."""
    graph = create_graph()

    initial_state: SOCWorkflowState = {
        "user_message": "Check security alerts",
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

    # The graph is compiled with a checkpointer so approvals can pause and resume,
    # and a checkpointer requires a thread_id on every call.
    config = {"configurable": {"thread_id": "test-graph"}}

    result = graph.invoke(initial_state, config=config)
    assert result is not None
    assert "final_response" in result
