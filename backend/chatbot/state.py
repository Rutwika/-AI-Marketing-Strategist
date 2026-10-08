"""Shared LangGraph state for the results-table chatbot. A TypedDict (not
Pydantic) since LangGraph nodes return partial-dict updates with overwrite
semantics - no reducers needed, single-turn, no cross-node append logic.
"""

from typing import Literal, Optional, TypedDict

from schemas import AnalyzeResult, SourceCitation


class ChatState(TypedDict, total=False):
    question: str
    table: AnalyzeResult
    route: Literal["table_qa", "exa_rag"]
    raw_answer: str
    citations: list[SourceCitation]
    warning: Optional[str]
    final_answer: str
