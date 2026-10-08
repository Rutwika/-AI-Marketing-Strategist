"""Builds and compiles the chatbot's StateGraph:

    START -> router --(route="table_qa")--> table_qa --> simplify --> END
                    --(route="exa_rag")--> exa_rag  --> simplify --> END

run_chat() is the only entry point main.py needs - everything else here is
internal graph wiring. See docs/TRD_chatbot.md > "Frontend & backend".
"""

from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from chatbot.exa_rag import answer_with_web_search
from chatbot.router import classify_route
from chatbot.simplify import simplify_answer
from chatbot.state import ChatState
from chatbot.table_qa import answer_table_question
from schemas import AnalyzeResult, ChatResponse


def _route_selector(state: ChatState) -> str:
    return state.get("route", "table_qa")


@lru_cache
def _build_graph():
    builder = StateGraph(ChatState)
    builder.add_node("router", classify_route)
    builder.add_node("table_qa", answer_table_question)
    builder.add_node("exa_rag", answer_with_web_search)
    builder.add_node("simplify", simplify_answer)

    builder.add_edge(START, "router")
    builder.add_conditional_edges("router", _route_selector, {"table_qa": "table_qa", "exa_rag": "exa_rag"})
    builder.add_edge("table_qa", "simplify")
    builder.add_edge("exa_rag", "simplify")
    builder.add_edge("simplify", END)

    return builder.compile()


def run_chat(question: str, table: AnalyzeResult) -> ChatResponse:
    graph = _build_graph()
    result: ChatState = graph.invoke({"question": question, "table": table})

    return ChatResponse(
        answer=result.get("final_answer", "") or "I couldn't come up with an answer to that.",
        route=result.get("route", "table_qa"),
        warning=result.get("warning"),
        citations=result.get("citations", []),
    )
