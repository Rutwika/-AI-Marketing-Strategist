"""LangChain + Gemini chain that turns a CSV of customer rows into segments
and next-best-action recommendations. One call per upload (docs/TRD.md).

Requires GOOGLE_API_KEY in the environment (see .env.example). Get a free key
at https://aistudio.google.com/app/apikey.
"""

import os

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from rules import BUSINESS_RULES_PROMPT
from schemas import AnalyzeResult

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
TEMPERATURE = 0.2

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
once in `results`."""

HUMAN_PROMPT = """\
BUSINESS RULES (never break these)
{business_rules}

CUSTOM SEGMENTS (optional)
{custom_segments}

CUSTOMER DATA (CSV)
{csv_text}"""

_prompt = ChatPromptTemplate.from_messages(
    [("system", SYSTEM_PROMPT), ("human", HUMAN_PROMPT)]
)


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
    structured_llm = llm.with_structured_output(AnalyzeResult)
    return _prompt | structured_llm


def analyze(csv_text: str, custom_segments: str | None) -> AnalyzeResult:
    """Runs the one-call chain and returns a validated AnalyzeResult."""

    chain = build_chain()
    result = chain.invoke(
        {
            "business_rules": BUSINESS_RULES_PROMPT,
            "custom_segments": custom_segments or "(none provided - use the default segments above)",
            "csv_text": csv_text,
        }
    )
    # with_structured_output already returns an AnalyzeResult instance, but
    # be defensive in case a future langchain version returns a dict.
    return result if isinstance(result, AnalyzeResult) else AnalyzeResult.model_validate(result)
