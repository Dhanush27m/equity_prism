"""
Component: Backend -> AI Orchestration Layer (LangGraph)
Belongs to: the entry point of the whole multi-agent system.
Purpose: builds and compiles the actual LangGraph StateGraph — wires the router node,
the five specialist nodes, and the parallel fan-out edge together into one executable
graph object that app/api/routes/chat.py drives via graph.astream(...).
"""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

try:
    from langgraph.types import Send
except Exception:  # pragma: no cover - older langgraph
    from langgraph.constants import Send

from app.agents import comparator, company_analyst, document_research, portfolio, router, sentiment
from app.agents.state import AgentState

# The five specialist node names the router is allowed to select between.
SPECIALISTS = ["company_analyst", "comparator", "sentiment", "portfolio", "document_research"]

_graph = None


# Conditional-edge function: reads the router's chosen agent list out of state and turns
# it into a list of LangGraph Send objects, one per selected specialist. LangGraph runs
# every Send target concurrently and merges their outputs back into shared state.
def _dispatch(state: dict):
    agents = state.get("plan", {}).get("agents", [])
    return [Send(agent, state) for agent in agents if agent in SPECIALISTS]


# Lazily builds (once) and returns the compiled graph: START -> router -> conditional
# Send fan-out -> {selected specialists, run in parallel} -> END. A MemorySaver
# checkpointer is attached so each run is keyed by thread_id for tracing/checkpointing.
def get_graph():
    global _graph
    if _graph is None:
        builder = StateGraph(AgentState)
        builder.add_node("router", router.run)
        builder.add_node("company_analyst", company_analyst.run)
        builder.add_node("comparator", comparator.run)
        builder.add_node("sentiment", sentiment.run)
        builder.add_node("portfolio", portfolio.run)
        builder.add_node("document_research", document_research.run)

        builder.add_edge(START, "router")
        builder.add_conditional_edges("router", _dispatch, SPECIALISTS)
        for node in SPECIALISTS:
            builder.add_edge(node, END)

        _graph = builder.compile(checkpointer=MemorySaver())
    return _graph
