"""Test state structure and assumptions."""

from src.utils.state import SOCWorkflowState


def test_workflow_state_structure():
    """Test that SOCWorkflowState has expected fields."""
    state: SOCWorkflowState = {
        "user_message": "Check alerts",
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

    assert state["user_message"] == "Check alerts"
    assert isinstance(state["conversation_history"], list)
    assert isinstance(state["requested_actions"], list)
    assert state["final_response"] is None
