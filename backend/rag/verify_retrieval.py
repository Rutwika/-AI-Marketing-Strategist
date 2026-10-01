"""Dev-only manual verification script - not a pytest test, since it needs
live Pinecone + Gemini credentials. Run after `python -m rag.ingest`:

    python -m rag.verify_retrieval

Prints each segment's retrieved chunks + source filenames so you can
eyeball whether retrieval is actually finding relevant research content
for real segment names ("test the feature with real questions").
"""

from chain import DEFAULT_SEGMENTS
from rag.retrieval import get_research_context

SAMPLE_CUSTOM_SEGMENT = "__custom__"


def main() -> None:
    segment_names = [*DEFAULT_SEGMENTS, SAMPLE_CUSTOM_SEGMENT]
    context_by_segment, warning = get_research_context(segment_names)

    if warning:
        print(f"WARNING: {warning}")

    for segment_name in segment_names:
        context = context_by_segment.get(segment_name)
        print(f"\n=== {segment_name} ===")
        if not context or not context.chunks:
            print("  (no results)")
            continue
        print(f"  sources: {context.sources}")
        for i, chunk in enumerate(context.chunks):
            preview = chunk[:200].replace("\n", " ")
            print(f"  [{i}] {preview}...")


if __name__ == "__main__":
    main()
