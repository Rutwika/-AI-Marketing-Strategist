"""Table Q&A node: answers questions about the generated results table.

Hybrid by design (see docs/TRD_chatbot.md > "AI model & prompt"):
- "aggregate"/"lookup" questions are answered with plain pandas filtering
  over the table's own rows - no LLM call produces the count/list, so it's
  deterministic and unit-testable without mocking an LLM.
- "explanatory" ("why") questions reuse the matched row's own
  reason/action/offer/timing/sources - the LLM is explicitly forbidden from
  inventing new RFM reasoning not already in the table.
"""

import logging
from typing import Literal, Optional

import pandas as pd
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from chatbot.llm import get_chat_llm
from chatbot.state import ChatState
from schemas import Channel, Segment, ValueTier

logger = logging.getLogger("ai_marketing_strategist")


class TableQueryPlan(BaseModel):
    kind: Literal["aggregate", "lookup", "explanatory"]
    segment_filter: Optional[Segment] = None
    value_tier_filter: Optional[ValueTier] = None
    channel_filter: Optional[Channel] = None
    customer_ids: list[str] = Field(default_factory=list)


_PLAN_SYSTEM_PROMPT = """\
Classify this question about a customer-segmentation table into exactly one
kind, and extract any filters mentioned. Never invent customer facts - only
identify what the user is asking for.

kind:
- "aggregate"   - counts or lists across many rows (e.g. "how many Champions")
- "lookup"      - one or more specific customers' own fields (e.g. "what's
  the offer for C010")
- "explanatory" - why a row got its segment/recommendation (e.g. "why is
  C002 At-Risk")

Extract segment_filter / value_tier_filter / channel_filter only if the
question names one. Extract customer_ids only if the question names
specific customer ids."""

_plan_prompt = ChatPromptTemplate.from_messages([("system", _PLAN_SYSTEM_PROMPT), ("human", "{question}")])

_EXPLAIN_SYSTEM_PROMPT = """\
Answer the user's question using ONLY the fields given below for the
matched customer(s). Do not invent new RFM reasoning or new facts about any
customer - just explain using what is already here.

MATCHED ROWS
{rows_text}"""

_explain_prompt = ChatPromptTemplate.from_messages([("system", _EXPLAIN_SYSTEM_PROMPT), ("human", "{question}")])


def _build_dataframe(results) -> pd.DataFrame:
    return pd.DataFrame([r.model_dump() for r in results])


def _apply_filters(df: pd.DataFrame, plan: TableQueryPlan) -> pd.DataFrame:
    if plan.segment_filter:
        df = df[df["segment"] == plan.segment_filter]
    if plan.value_tier_filter:
        df = df[df["value_tier"] == plan.value_tier_filter]
    if plan.channel_filter:
        df = df[df["channel"] == plan.channel_filter]
    if plan.customer_ids:
        df = df[df["customer_id"].isin(plan.customer_ids)]
    return df


def _format_row(row: pd.Series) -> str:
    return (
        f"- {row['customer_id']}: segment={row['segment']}, value_tier={row['value_tier']}, "
        f"reason=\"{row['reason']}\", channel={row['channel']}, action=\"{row['action']}\", "
        f"offer=\"{row['offer']}\" ({row['discount_pct']}% discount), timing=\"{row['timing']}\", "
        f"confidence={row['confidence']}"
    )


def _classify_plan(question: str) -> TableQueryPlan:
    llm = get_chat_llm().with_structured_output(TableQueryPlan)
    plan_chain = _plan_prompt | llm
    plan = plan_chain.invoke({"question": question})
    return plan if isinstance(plan, TableQueryPlan) else TableQueryPlan.model_validate(plan)


def _explain(rows_text: str, question: str) -> str:
    explain_chain = _explain_prompt | get_chat_llm()
    response = explain_chain.invoke({"rows_text": rows_text, "question": question})
    return response.content if hasattr(response, "content") else str(response)


def answer_table_question(state: ChatState) -> dict:
    question = state["question"]
    table = state["table"]

    if not table.results:
        return {"raw_answer": "There are no customers in this table yet.", "citations": []}

    df = _build_dataframe(table.results)

    try:
        plan = _classify_plan(question)
    except Exception:
        logger.exception("table_qa plan classification failed - falling back to a plain row dump.")
        return {
            "raw_answer": "I couldn't quite parse that question against the table. "
            "Try asking about a specific customer id, segment, or count.",
            "citations": [],
            "warning": "Table question classification failed.",
        }

    matched = _apply_filters(df, plan)

    if plan.kind == "aggregate":
        if matched.empty:
            return {"raw_answer": "No customers in this table match that filter.", "citations": []}
        ids = ", ".join(matched["customer_id"].tolist())
        return {"raw_answer": f"{len(matched)} customer(s) match: {ids}.", "citations": []}

    if plan.kind == "lookup":
        if matched.empty:
            return {"raw_answer": "I couldn't find a matching customer in this table.", "citations": []}
        rows_text = "\n".join(_format_row(row) for _, row in matched.iterrows())
        return {"raw_answer": rows_text, "citations": []}

    # explanatory
    if matched.empty:
        matched = df  # no id/segment named - let the LLM figure out scope from the question itself
    rows_text = "\n".join(_format_row(row) for _, row in matched.iterrows())
    # Reuse this matched set's own sources (already attached server-side at analyze-time).
    matched_ids = set(matched["customer_id"].tolist())
    citations = [
        source
        for result in table.results
        if result.customer_id in matched_ids
        for source in result.sources
    ]

    try:
        raw_answer = _explain(rows_text, question)
        return {"raw_answer": raw_answer, "citations": citations}
    except Exception:
        logger.exception("table_qa explanatory answer failed - falling back to the raw row data.")
        return {
            "raw_answer": rows_text,
            "citations": citations,
            "warning": "Explanation generation failed; showing the raw row data instead.",
        }
