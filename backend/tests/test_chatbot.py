"""Deterministic tests for the chatbot's pandas table logic (no LLM calls),
plus mocked-Exa tests for the web-search node's search/trim/citation shape.
See docs/TRD_chatbot.md > "Testing, risks & next steps".
"""

from types import SimpleNamespace
from unittest.mock import patch

from chatbot import exa_rag
from chatbot.state import ChatState
from chatbot.table_qa import TableQueryPlan, _apply_filters, _build_dataframe, answer_table_question
from schemas import AnalyzeResult, CustomerResult, SourceCitation, SummaryBlock


def _result(**overrides) -> CustomerResult:
    base = dict(
        customer_id="C001",
        segment="Champions",
        value_tier="High",
        fits_custom_segment=False,
        reason="Long relationship, frequent high-value orders.",
        channel="email",
        action="Early access offer",
        offer="No discount - VIP perks",
        discount_pct=0,
        timing="Within 7 days",
        confidence="high",
        sources=[],
    )
    base.update(overrides)
    return CustomerResult(**base)


def _table(rows: list[CustomerResult]) -> AnalyzeResult:
    return AnalyzeResult(summary=SummaryBlock(total_customers=len(rows), segments={}), results=rows)


# --- table_qa: pure pandas filtering (no LLM, fully deterministic) --------


def test_apply_filters_by_segment():
    rows = [
        _result(customer_id="C001", segment="Bargain Hunters"),
        _result(customer_id="C002", segment="Champions"),
        _result(customer_id="C003", segment="Bargain Hunters"),
    ]
    df = _build_dataframe(rows)
    matched = _apply_filters(df, TableQueryPlan(kind="aggregate", segment_filter="Bargain Hunters"))
    assert sorted(matched["customer_id"].tolist()) == ["C001", "C003"]


def test_apply_filters_by_customer_ids():
    rows = [_result(customer_id="C001"), _result(customer_id="C002"), _result(customer_id="C003")]
    df = _build_dataframe(rows)
    matched = _apply_filters(df, TableQueryPlan(kind="lookup", customer_ids=["C002"]))
    assert matched["customer_id"].tolist() == ["C002"]


def test_apply_filters_combines_multiple_filters():
    rows = [
        _result(customer_id="C001", segment="Champions", channel="email"),
        _result(customer_id="C002", segment="Champions", channel="sms"),
        _result(customer_id="C003", segment="Hibernating", channel="email"),
    ]
    df = _build_dataframe(rows)
    matched = _apply_filters(df, TableQueryPlan(kind="aggregate", segment_filter="Champions", channel_filter="email"))
    assert matched["customer_id"].tolist() == ["C001"]


def test_apply_filters_no_filters_returns_everything():
    rows = [_result(customer_id="C001"), _result(customer_id="C002")]
    df = _build_dataframe(rows)
    matched = _apply_filters(df, TableQueryPlan(kind="explanatory"))
    assert len(matched) == 2


# --- table_qa: full node, with _classify_plan/_explain mocked -------------


def test_empty_table_returns_friendly_message_without_calling_llm():
    state: ChatState = {"question": "How many Champions?", "table": _table([])}
    result = answer_table_question(state)
    assert "no customers" in result["raw_answer"].lower()
    assert result["citations"] == []


def test_aggregate_counts_and_lists_matching_customers():
    rows = [
        _result(customer_id="C001", segment="Bargain Hunters"),
        _result(customer_id="C002", segment="Champions"),
        _result(customer_id="C003", segment="Bargain Hunters"),
    ]
    state: ChatState = {"question": "How many Bargain Hunters?", "table": _table(rows)}
    with patch(
        "chatbot.table_qa._classify_plan",
        return_value=TableQueryPlan(kind="aggregate", segment_filter="Bargain Hunters"),
    ):
        result = answer_table_question(state)
    assert "2" in result["raw_answer"]
    assert "C001" in result["raw_answer"] and "C003" in result["raw_answer"]
    assert result["citations"] == []


def test_lookup_returns_formatted_row_without_llm():
    rows = [_result(customer_id="C010", offer="15% off next order", discount_pct=15)]
    state: ChatState = {"question": "What's the offer for C010?", "table": _table(rows)}
    with patch("chatbot.table_qa._classify_plan", return_value=TableQueryPlan(kind="lookup", customer_ids=["C010"])):
        result = answer_table_question(state)
    assert "C010" in result["raw_answer"]
    assert "15% off next order" in result["raw_answer"]
    assert result["citations"] == []


def test_explanatory_reuses_the_matched_rows_own_sources_as_citations():
    source = SourceCitation(document="paper.pdf", excerpt="Some grounding text.")
    rows = [_result(customer_id="C002", segment="At-Risk High-Value", sources=[source])]
    state: ChatState = {"question": "Why is C002 At-Risk High-Value?", "table": _table(rows)}
    with (
        patch("chatbot.table_qa._classify_plan", return_value=TableQueryPlan(kind="explanatory", customer_ids=["C002"])),
        patch("chatbot.table_qa._explain", return_value="Because they stopped ordering recently."),
    ):
        result = answer_table_question(state)
    assert result["raw_answer"] == "Because they stopped ordering recently."
    assert result["citations"] == [source]


def test_plan_classification_failure_fails_open_with_warning():
    rows = [_result(customer_id="C001")]
    state: ChatState = {"question": "???", "table": _table(rows)}
    with patch("chatbot.table_qa._classify_plan", side_effect=RuntimeError("boom")):
        result = answer_table_question(state)
    assert result["warning"]
    assert result["raw_answer"]


# --- exa_rag: mocked Exa client, no live search or LLM calls ---------------


def _fake_result(title: str, url: str, score: float, highlights=None, text=None) -> SimpleNamespace:
    return SimpleNamespace(title=title, url=url, score=score, highlights=highlights, text=text)


def test_web_search_trims_to_top_k_sorted_by_score():
    fake_results = [
        _fake_result("Low relevance", "https://a.com", 0.2, highlights=["a snippet"]),
        _fake_result("High relevance", "https://b.com", 0.9, highlights=["b snippet"]),
        _fake_result("Mid relevance", "https://c.com", 0.5, highlights=["c snippet"]),
        _fake_result("Lowest relevance", "https://d.com", 0.1, highlights=["d snippet"]),
    ]
    fake_client = SimpleNamespace(search_and_contents=lambda *a, **k: SimpleNamespace(results=fake_results))

    with (
        patch("chatbot.exa_rag.get_exa_client", return_value=fake_client),
        patch("chatbot.exa_rag._rewrite_query", return_value="rewritten query"),
        patch("chatbot.exa_rag._generate_answer", return_value="Final grounded answer."),
        patch("chatbot.exa_rag.config.EXA_TOP_K", 2),
    ):
        state: ChatState = {"question": "What's a typical win-back discount?", "table": _table([])}
        result = exa_rag.answer_with_web_search(state)

    assert result["raw_answer"] == "Final grounded answer."
    assert result.get("warning") is None
    assert len(result["citations"]) == 2
    assert result["citations"][0].document == "High relevance (https://b.com)"
    assert result["citations"][1].document == "Mid relevance (https://c.com)"


def test_web_search_fails_open_when_search_errors():
    with (
        patch("chatbot.exa_rag.get_exa_client", side_effect=RuntimeError("EXA_API_KEY is not set.")),
        patch("chatbot.exa_rag._rewrite_query", return_value="rewritten query"),
    ):
        state: ChatState = {"question": "What's a typical win-back discount?", "table": _table([])}
        result = exa_rag.answer_with_web_search(state)

    assert result["warning"] == "Web lookup failed."
    assert result["citations"] == []
    assert result["raw_answer"]


def test_web_search_fails_open_when_no_results():
    fake_client = SimpleNamespace(search_and_contents=lambda *a, **k: SimpleNamespace(results=[]))
    with (
        patch("chatbot.exa_rag.get_exa_client", return_value=fake_client),
        patch("chatbot.exa_rag._rewrite_query", return_value="rewritten query"),
    ):
        state: ChatState = {"question": "Something obscure", "table": _table([])}
        result = exa_rag.answer_with_web_search(state)

    assert result["warning"] == "Web search returned no results."
    assert result["citations"] == []
