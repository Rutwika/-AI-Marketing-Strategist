"""LangChain + Gemini chain that turns a CSV of customer rows into segments
and next-best-action recommendations. One call per upload (docs/TRD.md).

Requires GOOGLE_API_KEY in the environment (see .env.example). Get a free key
at https://aistudio.google.com/app/apikey.
"""

import os

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from rag import retrieval
from rules import BUSINESS_RULES_PROMPT
from schemas import (
    AnalyzeResult,
    Channel,
    Confidence,
    CustomerResult,
    Segment,
    SourceCitation,
    SummaryBlock,
    ValueTier,
)

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
TEMPERATURE = 0.2

DEFAULT_SEGMENTS: list[str] = [
    "Champions",
    "New Potential",
    "At-Risk High-Value",
    "High-Intent Window Shoppers",
    "Bargain Hunters",
    "Hibernating",
]
CUSTOM_SEGMENT_KEY = "__custom__"

# Fixed instructions (docs/TRD.md > "Prompt structure"). The variable parts -
# business rules, custom segments, and the CSV itself - go in the human
# message so the model clearly sees them as this request's inputs.
SYSTEM_PROMPT = """\
You are a senior B2C marketing strategist. You receive customer data exported
from different tools (CDP, orders, revenue, email engagement). Column names
and formats vary - infer what each column means.

SCORING (internal - never show scores to the user)
- Score each customer 1-5 on Recency, Frequency, Monetary (RFM),
  relative to the other customers in the file.
- If the columns exist, also consider: Length of relationship (first
  purchase/signup date), Engagement (opens, clicks, visits, app opens),
  Discount proportion (total discount / total paid, or % of
  orders with a coupon), Basket depth (items/categories per order).

Tasks for EVERY customer row:
1. Assign exactly one segment.
   - If custom segments are provided, use them. If a customer fits none,
     assign the closest default segment and set fits_custom_segment=false.
   - Default segments:
     Champions (high R, F, M, long relationship)
     New Potential (high R, low F; recent first purchase)
     At-Risk High-Value (low R, high F and M, engagement dropping)
     High-Intent Window Shoppers (no recent purchase, high engagement or
       abandoned cart)
     Bargain Hunters (high F, low M, high discount usage)
     Hibernating (low R, F, M)
2. Assign a value tier: High, Medium or Low. Weight average order value
   and tenure most, then retention signals (recency, engagement).
3. Give a one-sentence reason in plain business language.
4. Recommend the next best action (channel, action, offer, timing) using
   the segment playbook and business rules below. Scale offer strength
   and channel cost to the value tier.

SEGMENT PLAYBOOK
- Champions: no discount; early access, VIP perks, referral ask.
- New Potential: welcome/nurture email, cross-sell adjacent category.
- At-Risk High-Value: priority win-back via SMS or personal email,
  strongest allowed offer.
- High-Intent Window Shoppers: cart/browse reminder within 24 h,
  reviews or social proof.
- Bargain Hunters: clearance/overstock promos only.
- Hibernating: one low-cost re-engagement email; no paid channels.

If data for a customer is missing or unclear, say so in the reason and
lower the confidence. Every customer_id from the input must appear exactly
once in `results`.

RESEARCH CONTEXT below, when provided for a segment, is grounding evidence -
reflect it in that segment's `reason` text when relevant, in plain language.
Never mention filenames, citations, or "according to the research" - sources
are attached separately, not by you."""

HUMAN_PROMPT = """\
RESEARCH CONTEXT (grounding for segment reasoning, see note above)
{research_context}

BUSINESS RULES (never break these)
{business_rules}

CUSTOM SEGMENTS (optional)
{custom_segments}

CUSTOMER DATA (CSV)
{csv_text}"""

_prompt = ChatPromptTemplate.from_messages(
    [("system", SYSTEM_PROMPT), ("human", HUMAN_PROMPT)]
)


# Internal structured-output target: identical to the public CustomerResult/
# AnalyzeResult in schemas.py, minus `sources`. `sources` must never be a
# field the LLM populates via with_structured_output (even Field(exclude=True)
# wouldn't stop it - that only affects serialization, not the generated tool
# schema) - it's attached deterministically in analyze() below instead, so it
# can never be hallucinated.
class _LLMCustomerResult(BaseModel):
    customer_id: str
    segment: Segment
    value_tier: ValueTier
    fits_custom_segment: bool
    reason: str
    channel: Channel
    action: str
    offer: str
    discount_pct: int = Field(ge=0, le=100)
    timing: str
    confidence: Confidence


class _LLMAnalyzeResult(BaseModel):
    summary: SummaryBlock
    results: list[_LLMCustomerResult]


def build_chain():
    """Builds the prompt | model chain. Raises if GOOGLE_API_KEY is unset."""

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY is not set. Copy backend/.env.example to backend/.env "
            "and add a key from https://aistudio.google.com/app/apikey."
        )

    llm = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL, temperature=TEMPERATURE, google_api_key=api_key
    )
    structured_llm = llm.with_structured_output(_LLMAnalyzeResult)
    return _prompt | structured_llm


def analyze(csv_text: str, custom_segments: str | None) -> AnalyzeResult:
    """Runs the one-call chain and returns a validated AnalyzeResult.

    Retrieves research context once per distinct candidate segment name
    (never per customer row - at most len(DEFAULT_SEGMENTS) + 1 Pinecone
    queries regardless of how many rows are in the CSV), then attaches each
    customer's `sources` deterministically from what was actually retrieved
    for their assigned segment.
    """

    candidate_segments = [*DEFAULT_SEGMENTS, *([CUSTOM_SEGMENT_KEY] if custom_segments else [])]
    context_by_segment, rag_warning = retrieval.get_research_context(candidate_segments)
    research_context_block = retrieval.format_research_context_block(context_by_segment)

    chain = build_chain()
    result = chain.invoke(
        {
            "research_context": research_context_block,
            "business_rules": BUSINESS_RULES_PROMPT,
            "custom_segments": custom_segments or "(none provided - use the default segments above)",
            "csv_text": csv_text,
        }
    )
    # with_structured_output already returns an _LLMAnalyzeResult instance,
    # but be defensive in case a future langchain version returns a dict.
    llm_result = result if isinstance(result, _LLMAnalyzeResult) else _LLMAnalyzeResult.model_validate(result)

    # `segment` is always one of the 6 fixed Literal values (schemas.Segment),
    # even when a custom segment definition was used to decide it - so sources
    # are always looked up by the real segment name, never by
    # fits_custom_segment (that flag reflects the model's self-reported intent
    # and isn't reliable enough to branch key-lookup logic on).
    empty_context = retrieval.RetrievedContext()
    results = []
    for row in llm_result.results:
        context = context_by_segment.get(row.segment, empty_context)
        sources = [
            SourceCitation(document=src, excerpt=context.snippets.get(src, ""))
            for src in context.sources
        ]
        results.append(CustomerResult(**row.model_dump(), sources=sources))
    return AnalyzeResult(summary=llm_result.summary, results=results, rag_warning=rag_warning)
