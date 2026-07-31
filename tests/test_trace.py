"""Test the debug trace: which agents ran and which tools they called."""

from langchain_core.messages import AIMessage, ToolMessage

from src.utils.trace import RunTrace, agent_from_namespace

ENDPOINT_NS = ("endpoint:74f9cc35-18d6-b767-a783-7e317f454006",)
IDENTITY_NS = ("identity:38e088df-b488-3e79-0e4c-1b93ec0f6bbb",)


def call_message(name, args, call_id):
    return AIMessage(
        content="",
        tool_calls=[{"name": name, "args": args, "id": call_id, "type": "tool_call"}],
    )


def test_agent_name_is_read_from_the_namespace():
    """LangGraph tags subgraph events with "<agent>:<uuid>"."""
    assert agent_from_namespace(ENDPOINT_NS) == "endpoint"
    assert agent_from_namespace(()) == ""
    assert agent_from_namespace(None) == ""


def test_workflow_path_is_recorded():
    """Top-level nodes make up the route the request took."""
    trace = RunTrace()
    for node in ("request_intake", "supervisor", "endpoint", "response_generator"):
        trace.record((), node, {})

    assert trace.summary()["path"] == [
        "request_intake",
        "supervisor",
        "endpoint",
        "response_generator",
    ]


def test_internal_agent_nodes_stay_out_of_the_path():
    """The agent's own model/tools steps are not workflow nodes."""
    trace = RunTrace()
    trace.record((), "endpoint", {})
    trace.record(ENDPOINT_NS, "model", {})
    trace.record(ENDPOINT_NS, "tools", {})

    assert trace.summary()["path"] == ["endpoint"]


def test_tool_call_is_attributed_to_its_agent_with_its_result():
    """A call and the ToolMessage answering it are paired on tool_call_id."""
    trace = RunTrace()
    trace.record(
        ENDPOINT_NS, "model", {"messages": [call_message("get_malware_details", {"device_id": "DEV-001"}, "c1")]}
    )
    trace.record(
        ENDPOINT_NS,
        "tools",
        {"messages": [ToolMessage(content="[]", name="get_malware_details", tool_call_id="c1")]},
    )

    agents = trace.summary()["agents"]
    assert len(agents) == 1
    assert agents[0]["agent"] == "endpoint"

    tool = agents[0]["tools"][0]
    assert tool["name"] == "get_malware_details"
    assert tool["args"] == {"device_id": "DEV-001"}
    assert tool["result"] == "[]"


def test_results_are_matched_to_the_right_call():
    """Two calls from one agent must not have their results swapped."""
    trace = RunTrace()
    trace.record(IDENTITY_NS, "model", {"messages": [call_message("check_account_status", {}, "a")]})
    trace.record(IDENTITY_NS, "model", {"messages": [call_message("check_login_history", {}, "b")]})
    trace.record(IDENTITY_NS, "tools", {"messages": [ToolMessage(content="STATUS", name="check_account_status", tool_call_id="a")]})
    trace.record(IDENTITY_NS, "tools", {"messages": [ToolMessage(content="HISTORY", name="check_login_history", tool_call_id="b")]})

    tools = trace.summary()["agents"][0]["tools"]
    assert [(t["name"], t["result"]) for t in tools] == [
        ("check_account_status", "STATUS"),
        ("check_login_history", "HISTORY"),
    ]


def test_multiple_agents_are_kept_separate_and_in_order():
    """Each agent's calls are grouped under it, in the order they first ran."""
    trace = RunTrace()
    trace.record(IDENTITY_NS, "model", {"messages": [call_message("check_account_status", {}, "a")]})
    trace.record(ENDPOINT_NS, "model", {"messages": [call_message("scan_device", {}, "b")]})

    agents = trace.summary()["agents"]
    assert [entry["agent"] for entry in agents] == ["identity", "endpoint"]


def test_pending_approval_has_no_result_yet():
    """A gated call that has not been approved shows no result rather than a fake one."""
    trace = RunTrace()
    trace.record(IDENTITY_NS, "model", {"messages": [call_message("unlock_account", {}, "c1")]})

    assert trace.summary()["agents"][0]["tools"][0]["result"] is None


def test_a_replayed_call_is_not_counted_twice():
    """Resuming after an approval replays the checkpointed messages.

    Without deduplication the gated tool appears twice, as though it ran once before
    the approval and once after.
    """
    trace = RunTrace()
    proposal = {"messages": [call_message("unlock_account", {"username": "a@b.com"}, "c1")]}

    trace.record(IDENTITY_NS, "model", proposal)
    trace.record(IDENTITY_NS, "model", proposal)  # replayed on resume
    trace.record(
        IDENTITY_NS,
        "tools",
        {"messages": [ToolMessage(content="unlocked", name="unlock_account", tool_call_id="c1")]},
    )

    tools = trace.summary()["agents"][0]["tools"]
    assert len(tools) == 1
    assert tools[0]["result"] == "unlocked"


def test_distinct_calls_to_the_same_tool_are_both_kept():
    """Deduplication is by call id, so genuine repeat calls still show up."""
    trace = RunTrace()
    trace.record(IDENTITY_NS, "model", {"messages": [call_message("check_account_status", {"username": "a@b.com"}, "c1")]})
    trace.record(IDENTITY_NS, "model", {"messages": [call_message("check_account_status", {"username": "z@b.com"}, "c2")]})

    assert len(trace.summary()["agents"][0]["tools"]) == 2


def test_events_without_messages_are_ignored():
    """State updates that carry no messages must not break the trace."""
    trace = RunTrace()
    trace.record(ENDPOINT_NS, "model", {"endpoint": {"device_status": {}}})
    trace.record(ENDPOINT_NS, "model", None)

    assert trace.summary()["agents"] == []
