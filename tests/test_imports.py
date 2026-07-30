"""Test that all main modules import successfully."""

import sys


def test_config_import():
    """Test config module imports."""
    from src.utils.config import Settings, get_settings

    assert Settings is not None
    assert get_settings is not None


def test_state_import():
    """Test state definitions import."""
    from src.utils.state import SOCWorkflowState, RequestInfo

    assert SOCWorkflowState is not None
    assert RequestInfo is not None


def test_tools_import():
    """Test all tool modules import."""
    from src.tools import (
        search_security_alert,
        check_login_history,
        check_endpoint_status,
        create_incident,
    )

    assert search_security_alert is not None
    assert check_login_history is not None
    assert check_endpoint_status is not None
    assert create_incident is not None


def test_agents_import():
    """Test all agent modules import."""
    from src.agents import (
        request_intake_agent_node,
        supervisor_agent_node,
        alert_analysis_agent_node,
    )

    assert request_intake_agent_node is not None
    assert supervisor_agent_node is not None
    assert alert_analysis_agent_node is not None


def test_graph_import():
    """Test graph module imports."""
    from src.graph import get_graph, create_graph

    assert get_graph is not None
    assert create_graph is not None


def test_app_import():
    """Test Streamlit app imports."""
    # Import without running Streamlit
    with_pytest = True
    if with_pytest:
        # Simple import check
        import src.app

        assert src.app is not None
