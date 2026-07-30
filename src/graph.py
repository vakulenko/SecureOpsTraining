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
    ACTION_ALERT_ANALYSIS,
    ACTION_ENDPOINT,
    ACTION_IDENTITY,
    ACTION_INCIDENT,
    ACTION_REPORTING,
    ACTION_RESPONSE,
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


def _make_agent_with_completion(agent_func, action_name):
    """Wrap an agent to mark itself as completed after execution."""
    def wrapper(state: SOCWorkflowState) -> dict:
        result = agent_func(state)
        completed = list(state.get("completed_actions", []))
        if action_name not in completed:
            completed.append(action_name)
        result["completed_actions"] = completed
        return result
    return wrapper


def create_graph():
    """Create and compile the SOC workflow graph."""
    graph_builder = StateGraph(SOCWorkflowState)

    # Add nodes
    graph_builder.add_node(NODE_REQUEST_INTAKE, request_intake_agent_node)
    graph_builder.add_node(NODE_SUPERVISOR, supervisor_agent_node)
    graph_builder.add_node(NODE_ALERT_ANALYSIS, _make_agent_with_completion(alert_analysis_agent_node, ACTION_ALERT_ANALYSIS))
    graph_builder.add_node(NODE_IDENTITY, _make_agent_with_completion(identity_agent_node, ACTION_IDENTITY))
    graph_builder.add_node(NODE_ENDPOINT, _make_agent_with_completion(endpoint_agent_node, ACTION_ENDPOINT))
    graph_builder.add_node(NODE_INCIDENT, _make_agent_with_completion(incident_agent_node, ACTION_INCIDENT))
    graph_builder.add_node(NODE_REPORTING, _make_agent_with_completion(reporting_agent_node, ACTION_REPORTING))

    # Response generator: synthesize all agent outputs into final response
    def response_generator_node(state: SOCWorkflowState) -> dict:
        """Synthesize all agent outputs into a final response for the analyst."""
        user_message = state.get("user_message", "")
        alert_result = state.get("alert_analysis")
        identity_result = state.get("identity")
        endpoint_result = state.get("endpoint")
        incident_result = state.get("incident")
        reporting_result = state.get("reporting")

        response_parts = [f"Request: {user_message}\n"]

        if alert_result and not alert_result.get("error"):
            response_parts.append(f"**Alert Analysis**\n{alert_result.get('summary', '')}\n")

        if identity_result and not identity_result.get("error"):
            response_parts.append(f"**Identity & Access**\n{identity_result.get('summary', '')}\n")

        if endpoint_result and not endpoint_result.get("error"):
            response_parts.append(f"**Endpoint Security**\n{endpoint_result.get('summary', '')}\n")

        if incident_result and not incident_result.get("error"):
            response_parts.append(f"**Incident Response**\n{incident_result.get('summary', '')}\n")

        if reporting_result and not reporting_result.get("error"):
            response_parts.append(f"**Report**\n{reporting_result.get('report_content', '')}\n")

        # Collect all errors
        errors = []
        for result in [alert_result, identity_result, endpoint_result, incident_result, reporting_result]:
            if result and result.get("error"):
                errors.append(result["error"])

        if errors:
            response_parts.append(f"**Warnings**\n{'; '.join(errors)}\n")

        return {
            "final_response": "\n".join(response_parts).strip() or "No results to report.",
        }

    graph_builder.add_node(NODE_RESPONSE_GENERATOR, response_generator_node)

    # Edges: request_intake -> supervisor
    graph_builder.add_edge(NODE_REQUEST_INTAKE, NODE_SUPERVISOR)

    # Conditional routing from supervisor to agents
    def route_supervisor_decision(state: SOCWorkflowState) -> str:
        """Route to next agent or response generator based on supervisor decision."""
        requested_actions = state.get("requested_actions", [])
        completed_actions = state.get("completed_actions", [])

        # Find next action to execute
        next_action = ACTION_RESPONSE
        for action in requested_actions:
            if action not in completed_actions:
                next_action = action
                break

        # Map action names to node names
        action_to_node = {
            ACTION_ALERT_ANALYSIS: NODE_ALERT_ANALYSIS,
            ACTION_IDENTITY: NODE_IDENTITY,
            ACTION_ENDPOINT: NODE_ENDPOINT,
            ACTION_INCIDENT: NODE_INCIDENT,
            ACTION_REPORTING: NODE_REPORTING,
            ACTION_RESPONSE: NODE_RESPONSE_GENERATOR,
        }

        return action_to_node.get(next_action, NODE_RESPONSE_GENERATOR)

    graph_builder.add_conditional_edges(NODE_SUPERVISOR, route_supervisor_decision)

    # Agent nodes -> back to supervisor to check if more agents needed
    def route_agent_to_supervisor(state: SOCWorkflowState) -> str:
        """After an agent runs, return to supervisor to route next."""
        return NODE_SUPERVISOR

    graph_builder.add_conditional_edges(NODE_ALERT_ANALYSIS, route_agent_to_supervisor)
    graph_builder.add_conditional_edges(NODE_IDENTITY, route_agent_to_supervisor)
    graph_builder.add_conditional_edges(NODE_ENDPOINT, route_agent_to_supervisor)
    graph_builder.add_conditional_edges(NODE_INCIDENT, route_agent_to_supervisor)
    graph_builder.add_conditional_edges(NODE_REPORTING, route_agent_to_supervisor)

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