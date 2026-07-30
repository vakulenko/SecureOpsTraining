"""Test the human-in-the-loop approval gate on the sensitive identity tools.

Each test builds a one-node graph around the identity agent, because the approval pause
needs a checkpointer on the graph that runs the agent. This mirrors how TM4's real
workflow graph will drive it.
"""

import pytest
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph
from langgraph.types import Command

from src.agents.identity import build_identity_agent, run_identity_agent
from src.utils import NODE_IDENTITY, SOCWorkflowState
from tests.conftest import tool_call

RJOHNSON = "rjohnson@company.com"


def build_app(model, checkpointer=None):
    """Wrap the identity agent in a single-node graph with a checkpointer."""
    agent = build_identity_agent(model)

    graph = StateGraph(SOCWorkflowState)
    graph.add_node(NODE_IDENTITY, lambda state: run_identity_agent(state, agent))
    graph.set_entry_point(NODE_IDENTITY)
    graph.set_finish_point(NODE_IDENTITY)

    return graph.compile(checkpointer=checkpointer or InMemorySaver())


def unlock_script(final_text: str) -> list[AIMessage]:
    """Scripted model replies: propose an unlock, then summarise the outcome."""
    return [
        AIMessage(
            content="",
            tool_calls=[tool_call("unlock_account", {"username": RJOHNSON})],
        ),
        AIMessage(content=final_text),
    ]


def test_sensitive_tool_raises_interrupt(fake_model):
    """Proposing unlock_account pauses the graph instead of running the tool."""
    app = build_app(fake_model(*unlock_script("Unlocked.")))
    config = {"configurable": {"thread_id": "interrupt"}}

    result = app.invoke({"user_message": f"unlock {RJOHNSON}"}, config)

    assert "__interrupt__" in result
    payload = result["__interrupt__"][0].value
    request = payload["action_requests"][0]

    assert request["name"] == "unlock_account"
    # The key is "args"; the published LangChain docs show "arguments", which is wrong
    # for langchain 1.3.14. Asserting on it here catches an upstream change.
    assert request["args"]["username"] == RJOHNSON
    assert payload["review_configs"][0]["allowed_decisions"] == ["approve", "reject"]
    assert "identity" not in result


def test_approve_executes_the_tool(fake_model):
    """Approving the request runs the tool and records the action."""
    app = build_app(fake_model(*unlock_script("Account unlocked.")))
    config = {"configurable": {"thread_id": "approve"}}

    app.invoke({"user_message": f"unlock {RJOHNSON}"}, config)
    result = app.invoke(Command(resume={"decisions": [{"type": "approve"}]}), config)

    assert result["identity"]["actions_taken"] == ["unlock_account: unlocked"]
    assert result["identity"]["summary"] == "Account unlocked."


def test_reject_does_not_execute_the_tool(fake_model):
    """Rejecting the request leaves the tool unrun and records no action."""
    app = build_app(fake_model(*unlock_script("Understood, leaving it locked.")))
    config = {"configurable": {"thread_id": "reject"}}

    app.invoke({"user_message": f"unlock {RJOHNSON}"}, config)
    result = app.invoke(
        Command(
            resume={
                "decisions": [
                    {"type": "reject", "message": "Verify identity out-of-band first."}
                ]
            }
        ),
        config,
    )

    assert result["identity"]["actions_taken"] == []
    assert result["identity"]["summary"] == "Understood, leaving it locked."


def test_read_only_tool_does_not_interrupt(fake_model):
    """A read-only lookup runs straight through with no approval prompt."""
    app = build_app(
        fake_model(
            AIMessage(
                content="",
                tool_calls=[tool_call("check_account_status", {"username": RJOHNSON})],
            ),
            AIMessage(content="Account is locked."),
        )
    )
    config = {"configurable": {"thread_id": "readonly"}}

    result = app.invoke({"user_message": f"is {RJOHNSON} locked?"}, config)

    assert "__interrupt__" not in result
    assert result["identity"]["account_status"] == "locked"


def test_approval_survives_restart_with_sqlite(fake_model, tmp_db, monkeypatch):
    """A pending approval can be resumed by a freshly built graph, as after a restart.

    This is what SqliteSaver buys over InMemorySaver.
    """
    pytest.importorskip("langgraph.checkpoint.sqlite")

    monkeypatch.setenv("SOC_PERSISTENCE", "sqlite")
    monkeypatch.setenv("SOC_DB_PATH", tmp_db)

    from src.utils import create_checkpointer

    config = {"configurable": {"thread_id": "restart"}}
    model = fake_model(*unlock_script("Account unlocked."))

    # First "process": pause at the approval request.
    first = build_app(model, create_checkpointer())
    assert "__interrupt__" in first.invoke({"user_message": f"unlock {RJOHNSON}"}, config)

    # Second "process": a new graph and checkpointer over the same database file.
    second = build_app(model, create_checkpointer())
    result = second.invoke(Command(resume={"decisions": [{"type": "approve"}]}), config)

    assert result["identity"]["actions_taken"] == ["unlock_account: unlocked"]
