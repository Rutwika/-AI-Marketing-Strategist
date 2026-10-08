"""Router node: classifies a question about the results table as needing
the table itself or outside/web knowledge. See docs/TRD_chatbot.md >
"AI model & prompt" for the exact prompt this mirrors.
"""

import logging
from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from chatbot.llm import get_chat_llm
from chatbot.state import ChatState

logger = logging.getLogger("ai_marketing_strategist")

DEFAULT_ROUTE: Literal["table_qa", "exa_rag"] = "table_qa"


class RouteDecision(BaseModel):
    route: Literal["table_qa", "exa_rag"]


_SYSTEM_PROMPT = """\
You classify a user's question about a customer-segmentation results table.
Return exactly one route:
- "table_qa"  - the question is about THIS table: a specific customer, a
  segment, a count, a filter, or "why" a row got its recommendation.
- "exa_rag"   - the question needs outside/general marketing knowledge not
  answerable from the table (definitions, industry benchmarks, best
  practice).

When in doubt, prefer "table_qa" - it never invents customer facts.

Examples:
"How many Champions are there?" -> table_qa
"Why is C002 At-Risk and not Hibernating?" -> table_qa
"What's the offer for C010?" -> table_qa
"What's a typical win-back discount for e-commerce?" -> exa_rag
"What does RFM mean?" -> exa_rag"""

_prompt = ChatPromptTemplate.from_messages(
    [("system", _SYSTEM_PROMPT), ("human", "TABLE COLUMNS: {column_names}\nQUESTION: {question}")]
)


def classify_route(state: ChatState) -> dict:
    table = state["table"]
    column_names = ", ".join(table.results[0].model_fields.keys()) if table.results else "(empty table)"

    try:
        llm = get_chat_llm().with_structured_output(RouteDecision)
        chain = _prompt | llm
        decision = chain.invoke({"column_names": column_names, "question": state["question"]})
        route = decision.route if isinstance(decision, RouteDecision) else RouteDecision.model_validate(decision).route
        return {"route": route}
    except Exception:
        logger.exception("Router classification failed - defaulting to %r.", DEFAULT_ROUTE)
        return {"route": DEFAULT_ROUTE}
