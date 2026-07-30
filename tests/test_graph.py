"""Test graph structure and compilation."""

from src.graph import create_graph
from src.utils.state import SOCWorkflowState


def test_graph_compiles():
    """Test that the graph can be created and compiled."""
    graph = create_graph()
    assert graph is not None


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

    # Should not raise
    result = graph.invoke(initial_state)
    assert result is not None
    assert "final_response" in result
