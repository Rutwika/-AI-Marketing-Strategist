"""Week 1 static business rules (docs/TRD.md > "Week 1 business rules (rules.py)").

Two jobs:
1. `BUSINESS_RULES_PROMPT` is interpolated into chain.py's prompt so the model
   applies the rules when it writes each recommendation.
2. `check_guardrails` is the backend's independent re-check of the model's
   output, since a prompt is a request, not a guarantee. main.py retries the
   chain once if this fails, then returns a 502.
"""

from schemas import AnalyzeResult

MAX_DISCOUNT_PCT = 20

ALLOWED_CHANNELS = {"email", "sms", "push", "paid_social", "none"}

# Cheapest-first order used only for documentation / prompt context; the
# guardrail below enforces the one rule that's cheap to check mechanically
# (no paid_social for Hibernating). Full channel-cost ordering is judged by
# the model, per the TRD.
CHEAPEST_FIRST_CHANNELS = ["email", "push", "sms", "paid_social"]

BUSINESS_RULES_PROMPT = f"""\
- Never offer a discount above {MAX_DISCOUNT_PCT}%.
- Never discount Champions; use perks or early access instead (discount_pct must be 0).
- Prefer the cheapest channel that fits: email or push before SMS; paid_social \
only as a last resort, and never for Hibernating customers.
- Allowed channels: {", ".join(sorted(ALLOWED_CHANNELS))}.
- Recommend exactly one action per customer."""


def check_guardrails(input_customer_ids: list[str], result: AnalyzeResult) -> list[str]:
    """Returns a list of human-readable violations; empty list means the
    output passed every Week 1 guardrail and is safe to return to the UI."""

    violations: list[str] = []

    result_ids = [row.customer_id for row in result.results]

    missing = set(input_customer_ids) - set(result_ids)
    if missing:
        violations.append(f"Missing results for customer_id(s): {sorted(missing)}")

    unexpected = set(result_ids) - set(input_customer_ids)
    if unexpected:
        violations.append(f"Result customer_id(s) not present in the upload: {sorted(unexpected)}")

    seen: set[str] = set()
    for row in result.results:
        if row.customer_id in seen:
            violations.append(f"Duplicate result for customer_id {row.customer_id!r}")
        seen.add(row.customer_id)

        if row.discount_pct > MAX_DISCOUNT_PCT:
            violations.append(
                f"{row.customer_id}: discount_pct {row.discount_pct} exceeds the "
                f"{MAX_DISCOUNT_PCT}% cap"
            )

        if row.segment == "Champions" and row.discount_pct > 0:
            violations.append(f"{row.customer_id}: Champions must never receive a discount")

        if row.channel not in ALLOWED_CHANNELS:
            violations.append(f"{row.customer_id}: channel {row.channel!r} is not an allowed channel")

        if row.segment == "Hibernating" and row.channel == "paid_social":
            violations.append(f"{row.customer_id}: Hibernating customers must not get paid_social")

    return violations
