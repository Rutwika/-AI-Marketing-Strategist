"""Pydantic models for the /api/analyze request and response.

Matches the output schema specified in docs/TRD.md exactly, so the LangChain
`with_structured_output` call in chain.py returns data the frontend can render
without any reshaping.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field

Segment = Literal[
    "Champions",
    "New Potential",
    "At-Risk High-Value",
    "High-Intent Window Shoppers",
    "Bargain Hunters",
    "Hibernating",
]

ValueTier = Literal["High", "Medium", "Low"]

Channel = Literal["email", "sms", "push", "paid_social", "none"]

Confidence = Literal["high", "medium", "low"]


class CustomerResult(BaseModel):
    customer_id: str = Field(description="Identifier copied from the uploaded CSV row.")
    segment: Segment = Field(description="Closest fitting segment (custom or default).")
    value_tier: ValueTier
    fits_custom_segment: bool = Field(
        description="True only if a user-provided custom segment definition was used."
    )
    reason: str = Field(description="One plain-language sentence, no scores or formulas.")
    channel: Channel
    action: str = Field(description="Short description of the recommended action.")
    offer: str = Field(description='e.g. "15% off next order" or "No discount - VIP perks".')
    discount_pct: int = Field(ge=0, le=100, description="0 when no discount is offered.")
    timing: str = Field(description='e.g. "Within 7 days".')
    confidence: Confidence


class SummaryBlock(BaseModel):
    total_customers: int
    segments: dict[str, int] = Field(description="Segment name -> count of customers in it.")


class AnalyzeResult(BaseModel):
    """Exact shape returned by the LLM (via with_structured_output) and by POST /api/analyze."""

    summary: SummaryBlock
    results: list[CustomerResult]


class AnalyzeRequestMeta(BaseModel):
    """Non-file form fields sent alongside the CSV upload."""

    custom_segments: Optional[str] = Field(
        default=None, max_length=1000, description="Free-text segment definitions, optional."
    )


class RunRecord(BaseModel):
    """Row shape returned by GET /api/runs and /api/runs/{id}."""

    id: str
    file_name: str
    row_count: int
    custom_segments: Optional[str] = None
    created_at: str
    result: Optional[AnalyzeResult] = None


class ErrorResponse(BaseModel):
    detail: str
