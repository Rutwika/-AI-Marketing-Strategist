"""Query-time retrieval for grounding segment reasoning in the research
knowledge base. The only rag.* module chain.py imports.

Fails open: any Pinecone/embedding error is logged and swallowed, returning
{} so /api/analyze degrades to its pre-RAG behavior instead of breaking the
request - same best-effort philosophy as main.py's _save_run.
"""

import logging
from dataclasses import dataclass, field

from rag import config
from rag.embeddings import embed_query
from rag.pinecone_client import get_index

logger = logging.getLogger("ai_marketing_strategist")


@dataclass
class RetrievedContext:
    chunks: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)


def _query_segment(segment_name: str) -> RetrievedContext:
    query_text = (
        f"Customer segmentation research and RFM methodology relevant to the "
        f"'{segment_name}' customer segment."
    )
    vector = embed_query(query_text)
    index = get_index()
    response = index.query(vector=vector, top_k=config.RAG_TOP_K, include_metadata=True)

    chunks: list[str] = []
    sources: list[str] = []
    for match in response.matches:
        metadata = match.metadata or {}
        text = metadata.get("text")
        source = metadata.get("source")
        if text:
            chunks.append(text)
        if source and source not in sources:
            sources.append(source)
    return RetrievedContext(chunks=chunks, sources=sources)


def get_research_context(
    segment_names: list[str],
) -> tuple[dict[str, RetrievedContext], str | None]:
    """One Pinecone query per distinct segment name (never per customer row).

    Returns the context found so far, plus a human-readable warning (or None)
    naming any segments whose retrieval failed - so the caller can surface it
    to the API response instead of it only living in the server log.
    """

    context_by_segment: dict[str, RetrievedContext] = {}
    failed_segments: list[str] = []
    for segment_name in dict.fromkeys(segment_names):  # de-dupe, preserve order
        try:
            context_by_segment[segment_name] = _query_segment(segment_name)
        except Exception:
            logger.exception("RAG retrieval failed for segment %r - continuing without it.", segment_name)
            failed_segments.append(segment_name)

    warning = None
    if failed_segments:
        warning = (
            "Research retrieval failed for: " + ", ".join(failed_segments) + ". "
            "Recommendations for these segments were generated without grounding research."
        )
    return context_by_segment, warning


def format_research_context_block(context_by_segment: dict[str, RetrievedContext]) -> str:
    if not context_by_segment:
        return "(no research context available)"

    sections = []
    for segment_name, context in context_by_segment.items():
        if not context.chunks:
            continue
        bullets = "\n".join(f"  - {chunk}" for chunk in context.chunks)
        sections.append(f"{segment_name}:\n{bullets}")

    return "\n\n".join(sections) if sections else "(no research context available)"
