from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

try:
    from langgraph.types import Send
except Exception:  # pragma: no cover - older langgraph
    from langgraph.constants import Send

from app.agents import comparator, company_analyst, document_research, portfolio, router, sentiment
from app.agents.state import AgentState

SPECIALISTS = ["company_analyst", "comparator", "sentiment", "portfolio", "document_research"]

_graph = None


def _dispatch(state: dict):
    agents = state.get("plan", {}).get("agents", [])
    return [Send(agent, state) for agent in agents if agent in SPECIALISTS]


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
