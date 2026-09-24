from rules import MAX_DISCOUNT_PCT, check_guardrails
from schemas import AnalyzeResult, CustomerResult, SummaryBlock


def _result(**overrides) -> CustomerResult:
    base = dict(
        customer_id="C001",
        segment="At-Risk High-Value",
        value_tier="High",
        fits_custom_segment=False,
        reason="Test reason",
        channel="email",
        action="Win-back email",
        offer="10% off",
        discount_pct=10,
        timing="Within 7 days",
        confidence="medium",
    )
    base.update(overrides)
    return CustomerResult(**base)


def _analyze_result(rows: list[CustomerResult]) -> AnalyzeResult:
    return AnalyzeResult(summary=SummaryBlock(total_customers=len(rows), segments={}), results=rows)


def test_passes_when_everything_is_within_the_rules():
    rows = [_result(customer_id="C001"), _result(customer_id="C002", segment="Champions", discount_pct=0)]
    violations = check_guardrails(["C001", "C002"], _analyze_result(rows))
    assert violations == []


def test_flags_discount_above_cap():
    rows = [_result(discount_pct=MAX_DISCOUNT_PCT + 5)]
    violations = check_guardrails(["C001"], _analyze_result(rows))
    assert any("exceeds" in v for v in violations)


def test_flags_champion_with_any_discount():
    rows = [_result(segment="Champions", discount_pct=1)]
    violations = check_guardrails(["C001"], _analyze_result(rows))
    assert any("Champions must never receive a discount" in v for v in violations)


def test_flags_missing_customer():
    rows = [_result(customer_id="C001")]
    violations = check_guardrails(["C001", "C002"], _analyze_result(rows))
    assert any("Missing results" in v for v in violations)


def test_flags_unexpected_customer():
    rows = [_result(customer_id="C999")]
    violations = check_guardrails(["C001"], _analyze_result(rows))
    assert any("not present in the upload" in v for v in violations)


def test_flags_duplicate_customer():
    rows = [_result(customer_id="C001"), _result(customer_id="C001")]
    violations = check_guardrails(["C001"], _analyze_result(rows))
    assert any("Duplicate result" in v for v in violations)


def test_flags_hibernating_with_paid_social():
    rows = [_result(segment="Hibernating", channel="paid_social", discount_pct=0)]
    violations = check_guardrails(["C001"], _analyze_result(rows))
    assert any("must not get paid_social" in v for v in violations)
