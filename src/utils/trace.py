"""Record which agents ran and which tools they called during one graph run.

Nothing in SOCWorkflowState carries this: each agent folds its tool results into its own
slice, and only approval-gated calls end up in actions_taken. So the debug view reads it
off the event stream instead, which means it reflects what actually happened rather than
what we can infer afterwards.

Requires streaming with subgraphs=True. LangGraph then reports events from inside each
agent with a namespace like ("identity:<uuid>",), which is how a tool call is attributed
to the agent that made it.
"""

from langchain_core.messages import AIMessage, ToolMessage

# Nodes in the top-level workflow. Everything else is inside an agent subgraph.
WORKFLOW_NODES = {
    "request_intake",
    "supervisor",
    "alert_analysis",
    "identity",
    "endpoint",
    "incident",
    "reporting",
    "response_generator",
}


def agent_from_namespace(namespace) -> str:
    """Get the agent name out of a LangGraph subgraph namespace.

    ("identity:38e088df-...",) -> "identity". Returns "" for top-level events.
    """
    if not namespace:
        return ""

    return str(namespace[0]).split(":")[0]


class RunTrace:
    """Accumulates the debug view for a single request."""

    def __init__(self):
        self.path: list[str] = []
        self._tools_by_agent: dict[str, list[dict]] = {}
        self._agent_order: list[str] = []

    def record(self, namespace, node: str, update) -> None:
        """Fold one streamed event into the trace."""
        agent = agent_from_namespace(namespace)

        if not agent:
            # Top-level node: records the route the request took through the workflow.
            if node in WORKFLOW_NODES:
                self.path.append(node)
            return

        if not isinstance(update, dict):
            return

        for message in update.get("messages") or []:
            if isinstance(message, AIMessage) and message.tool_calls:
                for call in message.tool_calls:
                    self._add_call(agent, call)
            elif isinstance(message, ToolMessage):
                self._add_result(agent, message)

    def _add_call(self, agent: str, call: dict) -> None:
        if agent not in self._tools_by_agent:
            self._tools_by_agent[agent] = []
            self._agent_order.append(agent)

        # Resuming after an approval replays the checkpointed messages, so the call that
        # triggered the pause is streamed a second time. Without this it would look like
        # the sensitive tool ran twice.
        call_id = call.get("id")
        if call_id and any(
            entry["id"] == call_id for entry in self._tools_by_agent[agent]
        ):
            return

        self._tools_by_agent[agent].append(
            {
                "name": call.get("name", "unknown"),
                "args": call.get("args", {}),
                "id": call.get("id"),
                "result": None,
            }
        )

    def _add_result(self, agent: str, message: ToolMessage) -> None:
        """Attach a result to the call it answers, matched on tool_call_id."""
        for entry in self._tools_by_agent.get(agent, []):
            if entry["id"] == message.tool_call_id:
                entry["result"] = str(message.content)
                return

    def summary(self) -> dict:
        """The finished trace: the route taken, and each agent's tool calls."""
        return {
            "path": self.path,
            "agents": [
                {"agent": agent, "tools": self._tools_by_agent[agent]}
                for agent in self._agent_order
            ],
        }
