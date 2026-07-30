"""Shared LLM tool-calling loop for domain agents (endpoint, incident, etc.)."""

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.types import interrupt

from src.utils.config import get_settings
from src.utils.llm import create_llm

MAX_TOOL_ITERATIONS = 4


def run_tool_agent(
    system_prompt: str,
    user_message: str,
    tools: list,
    approval_required: frozenset = frozenset(),
    llm=None,
) -> tuple[str, list[dict]]:
    """Run an LLM tool-calling loop and return (final_text, tool_call_log).

    Tools named in `approval_required` are gated behind LangGraph's
    interrupt() so the graph pauses for analyst approval (Command(resume=
    True/False)) before the tool actually executes. Requires the compiled
    graph to be run with a checkpointer, or interrupt() will raise.

    Each tool_call_log entry: {"tool", "args", "result", "approved"}.
    "approved" is None for tools that don't require approval.
    """
    llm = (llm or create_llm(get_settings())).bind_tools(tools)
    tools_by_name = {t.name: t for t in tools}

    messages = [SystemMessage(system_prompt), HumanMessage(user_message)]
    tool_log: list[dict] = []

    for _ in range(MAX_TOOL_ITERATIONS):
        response: AIMessage = llm.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            return response.content, tool_log

        for call in response.tool_calls:
            name, args = call["name"], call["args"]
            approved = None

            if name in approval_required:
                approved = interrupt(
                    {"action": name, "args": args, "reason": f"{name} requires analyst approval"}
                )
                if not approved:
                    result = {"status": "denied", "message": f"{name} was not approved by analyst"}
                    tool_log.append({"tool": name, "args": args, "result": result, "approved": False})
                    messages.append(ToolMessage(content=str(result), tool_call_id=call["id"]))
                    continue

            tool_fn = tools_by_name.get(name)
            result = tool_fn.invoke(args) if tool_fn else {"error": f"Unknown tool {name}"}
            tool_log.append({"tool": name, "args": args, "result": result, "approved": approved})
            messages.append(ToolMessage(content=str(result), tool_call_id=call["id"]))

    return "Unable to complete the request after multiple tool calls.", tool_log
