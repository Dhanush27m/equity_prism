"""
Component: Backend -> AI Orchestration Layer (LangGraph)
Belongs to: the multi-agent chat pipeline (app/agents/*)
Purpose: defines the single shared state object that flows through every node of the
LangGraph graph (router -> specialists -> synthesizer). Specialist nodes only ever
return partial updates to this state; LangGraph merges them back in automatically.
"""

import operator
from typing import Annotated, TypedDict


# Shared graph state. question/symbols/snapshot/plan are overwritten by whichever node
# sets them; fragments/citations/meta use operator.add reducers so that when multiple
# specialist nodes run in parallel (via Send fan-out) their individual list outputs are
# concatenated together instead of one overwriting another.
class AgentState(TypedDict, total=False):
    question: str
    symbols: list[str]
    snapshot: dict
    plan: dict
    fragments: Annotated[list[dict], operator.add]
    citations: Annotated[list[dict], operator.add]
    meta: Annotated[list[dict], operator.add]
