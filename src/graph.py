"""LangGraph workflow definition for SOC Assistant."""

from langgraph.graph import StateGraph

from src.agents import (
    alert_analysis_agent_node,
    endpoint_agent_node,
    identity_agent_node,
    incident_agent_node,
    reporting_agent_node,
    request_intake_agent_node,
    supervisor_agent_node,
)
from src.utils import (
    NODE_ALERT_ANALYSIS,
    NODE_ENDPOINT,
    NODE_IDENTITY,
    NODE_INCIDENT,
    NODE_REPORTING,
    NODE_REQUEST_INTAKE,
    NODE_RESPONSE_GENERATOR,
    NODE_SUPERVISOR,
    SOCWorkflowState,
)


def create_graph():
    """Create and compile the SOC workflow graph."""
    graph_builder = StateGraph(SOCWorkflowState)

    # Add nodes
    graph_builder.add_node(NODE_REQUEST_INTAKE, request_intake_agent_node)
    graph_builder.add_node(NODE_SUPERVISOR, supervisor_agent_node)
    graph_builder.add_node(NODE_ALERT_ANALYSIS, alert_analysis_agent_node)
    graph_builder.add_node(NODE_IDENTITY, identity_agent_node)
    graph_builder.add_node(NODE_ENDPOINT, endpoint_agent_node)
    graph_builder.add_node(NODE_INCIDENT, incident_agent_node)
    graph_builder.add_node(NODE_REPORTING, reporting_agent_node)

    # Add stub response generator
    def response_generator_node(state: SOCWorkflowState) -> dict:
        return {
            "final_response": "Response synthesized from all agents.",
        }

    graph_builder.add_node(NODE_RESPONSE_GENERATOR, response_generator_node)

    # Add edges (stub: will be expanded with conditional routing)
    graph_builder.add_edge(NODE_REQUEST_INTAKE, NODE_SUPERVISOR)
    graph_builder.add_edge(NODE_SUPERVISOR, NODE_RESPONSE_GENERATOR)

    # Set entry and finish points
    graph_builder.set_entry_point(NODE_REQUEST_INTAKE)
    graph_builder.set_finish_point(NODE_RESPONSE_GENERATOR)

    # Compile
    return graph_builder.compile()


# Create a singleton instance
_graph_instance = None


def get_graph():
    """Get or create the compiled graph."""
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = create_graph()
    return _graph_instance


# Export graph for LangGraph CLI
graph = get_graph()