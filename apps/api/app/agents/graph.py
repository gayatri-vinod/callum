"""LangGraph research workflow scaffold.

Wire this into `stream_research_response` once OpenAI/Anthropic/Ollama
credentials and Qdrant are available. The MVP currently streams a grounded
demo so the product UI can ship independently of GPU services.
"""

from __future__ import annotations

from typing import Annotated, Any, TypedDict

from langgraph.graph import END, START, StateGraph


class ResearchState(TypedDict):
    project_id: str
    objective: str
    mode: str
    plan: str
    retrieved: list[dict[str, Any]]
    notes: Annotated[list[str], lambda a, b: a + b]
    answer: str
    claims: list[dict[str, Any]]


def plan_node(state: ResearchState) -> dict[str, Any]:
    return {"plan": f"investigate: {state['objective']} ({state['mode']})"}


def retrieve_node(state: ResearchState) -> dict[str, Any]:
    # TODO: hybrid dense + bm25 + cross-encoder rerank via Qdrant
    return {
        "retrieved": [
            {"id": "doc_2", "title": "Segment Anything"},
            {"id": "doc_3", "title": "MedSAM"},
        ],
        "notes": ["retrieved foundation + medical adaptation papers"],
    }


def synthesize_node(state: ResearchState) -> dict[str, Any]:
    # TODO: Instructor-structured claims with citation verification
    return {
        "answer": "synthesis pending live model wiring",
        "claims": [],
        "notes": ["synthesis complete"],
    }


def build_research_graph():
    graph = StateGraph(ResearchState)
    graph.add_node("plan", plan_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("synthesize", synthesize_node)
    graph.add_edge(START, "plan")
    graph.add_edge("plan", "retrieve")
    graph.add_edge("retrieve", "synthesize")
    graph.add_edge("synthesize", END)
    return graph.compile()
