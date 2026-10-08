"""Web-search RAG node: query rewrite -> Exa neural search + highlights ->
trim to top-k by Exa's own relevance score -> grounded answer generation.

Fails open (see docs/TRD_chatbot.md > "AI model & prompt"): any Gemini/Exa
error here is caught, logged, and turned into a warning + honest fallback
message instead of crashing the chat turn - same posture as
rag/retrieval.py's get_research_context().
"""

import logging

from langchain_core.prompts import ChatPromptTemplate

from chatbot import config
from chatbot.exa_client import get_exa_client
from chatbot.llm import get_chat_llm
from chatbot.state import ChatState
from schemas import SourceCitation

logger = logging.getLogger("ai_marketing_strategist")

_REWRITE_SYSTEM_PROMPT = """\
Rewrite the user's question into a focused web search query about e-commerce
or marketing practice. Strip conversational framing. Return only the query
text, nothing else."""

_rewrite_prompt = ChatPromptTemplate.from_messages([("system", _REWRITE_SYSTEM_PROMPT), ("human", "{question}")])

_ANSWER_SYSTEM_PROMPT = """\
Answer the user's question using ONLY the web search results below. Cite
what you used - don't state anything the results don't support.

SEARCH RESULTS
{snippets_text}"""

_answer_prompt = ChatPromptTemplate.from_messages([("system", _ANSWER_SYSTEM_PROMPT), ("human", "{question}")])


def _rewrite_query(question: str) -> str:
    chain = _rewrite_prompt | get_chat_llm()
    response = chain.invoke({"question": question})
    text = response.content if hasattr(response, "content") else str(response)
    return text.strip() or question


def _generate_answer(snippets_text: str, question: str) -> str:
    chain = _answer_prompt | get_chat_llm()
    response = chain.invoke({"snippets_text": snippets_text, "question": question})
    return response.content if hasattr(response, "content") else str(response)


def answer_with_web_search(state: ChatState) -> dict:
    question = state["question"]

    try:
        rewritten_query = _rewrite_query(question)
        exa = get_exa_client()
        response = exa.search_and_contents(
            rewritten_query,
            num_results=config.EXA_NUM_RESULTS,
            type="neural",
            highlights={"num_sentences": 3, "highlights_per_url": 2},
        )
    except Exception:
        logger.exception("exa_rag web search failed - continuing without it.")
        return {
            "raw_answer": "I couldn't search the web for this right now, so I can't answer that question.",
            "citations": [],
            "warning": "Web lookup failed.",
        }

    results = sorted(response.results, key=lambda r: r.score or 0, reverse=True)[: config.EXA_TOP_K]
    if not results:
        return {
            "raw_answer": "I searched the web but couldn't find anything relevant to that question.",
            "citations": [],
            "warning": "Web search returned no results.",
        }

    snippets_text = "\n\n".join(
        f"[{i + 1}] {r.title or r.url} ({r.url})\n" + "\n".join(r.highlights or ([r.text] if r.text else []))
        for i, r in enumerate(results)
    )
    citations = [
        SourceCitation(
            document=f"{r.title or r.url} ({r.url})",
            excerpt=(r.highlights or [r.text or ""])[0],
        )
        for r in results
    ]

    try:
        raw_answer = _generate_answer(snippets_text, question)
    except Exception:
        logger.exception("exa_rag answer generation failed - falling back to raw snippets.")
        return {
            "raw_answer": snippets_text,
            "citations": citations,
            "warning": "Answer generation failed; showing raw search results instead.",
        }

    return {"raw_answer": raw_answer, "citations": citations}
