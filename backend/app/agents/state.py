import operator
from typing import Annotated, TypedDict


class AgentState(TypedDict, total=False):
    question: str
    symbols: list[str]
    snapshot: dict
    plan: dict
    fragments: Annotated[list[dict], operator.add]
    citations: Annotated[list[dict], operator.add]
    meta: Annotated[list[dict], operator.add]
