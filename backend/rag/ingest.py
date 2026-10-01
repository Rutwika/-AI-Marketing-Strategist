"""One-time/developer-run ingestion script. Never imported by main.py or
chain.py - the live /api/analyze flow only ever queries Pinecone, never
writes to it.

Run from backend/ (with the venv active):
    python -m rag.ingest

Re-run whenever the PDF set in rag/knowledge_base/ changes. Safe to re-run:
each file's old vectors are deleted (by metadata filter) before its current
chunks are re-embedded and upserted, so edits never leave stale trailing
chunks behind.

Known limitation: a PDF *removed* from knowledge_base/ entirely is not
auto-pruned from the index. Remove it manually with:
    get_index().delete(filter={"source": "<old filename>"})
"""

import logging
import time
from pathlib import Path

from pinecone import ServerlessSpec
from pinecone.errors.exceptions import NotFoundError

from rag import config
from rag.chunking import chunk_text, load_pdf_text
from rag.embeddings import embed_documents
from rag.pinecone_client import get_pinecone_client

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("rag.ingest")

EMBED_BATCH_SIZE = 100


def ensure_index_exists() -> None:
    client = get_pinecone_client()
    if config.PINECONE_INDEX_NAME in client.list_indexes().names():
        return

    logger.info("Creating Pinecone index %r (dim=%s)", config.PINECONE_INDEX_NAME, config.EMBEDDING_DIMENSION)
    client.create_index(
        name=config.PINECONE_INDEX_NAME,
        dimension=config.EMBEDDING_DIMENSION,
        metric="cosine",
        spec=ServerlessSpec(cloud=config.PINECONE_CLOUD, region=config.PINECONE_REGION),
    )
    while not client.describe_index(config.PINECONE_INDEX_NAME).status.ready:
        time.sleep(1)


def ingest_pdf(index, path: Path) -> int:
    text = load_pdf_text(path)
    chunks = chunk_text(text, chunk_size=config.CHUNK_SIZE, overlap=config.CHUNK_OVERLAP)
    if not chunks:
        logger.warning("No extractable text in %s - skipping.", path.name)
        return 0

    # Delete this file's old vectors first, so a PDF edited down to fewer
    # chunks doesn't leave stale trailing chunks behind. Pinecone serverless
    # 404s on delete-by-filter against a namespace with no vectors yet
    # (e.g. a brand-new index) - treat that as "nothing to delete".
    try:
        index.delete(filter={"source": path.name})
    except NotFoundError:
        pass

    for batch_start in range(0, len(chunks), EMBED_BATCH_SIZE):
        batch = chunks[batch_start : batch_start + EMBED_BATCH_SIZE]
        vectors = embed_documents(batch)
        index.upsert(
            vectors=[
                {
                    "id": f"{path.stem}::chunk-{batch_start + i:04d}",
                    "values": vector,
                    "metadata": {
                        "source": path.name,
                        "chunk_index": batch_start + i,
                        "text": chunk,
                    },
                }
                for i, (chunk, vector) in enumerate(zip(batch, vectors))
            ]
        )

    logger.info("Ingested %s: %d chunks", path.name, len(chunks))
    return len(chunks)


def main() -> None:
    ensure_index_exists()
    client = get_pinecone_client()
    index = client.Index(config.PINECONE_INDEX_NAME)

    pdf_dir = Path(config.KNOWLEDGE_BASE_DIR)
    pdf_paths = sorted(pdf_dir.glob("*.pdf"))
    if not pdf_paths:
        logger.warning("No PDFs found in %s - nothing to ingest.", pdf_dir)
        return

    total_chunks = 0
    for path in pdf_paths:
        total_chunks += ingest_pdf(index, path)

    logger.info("Done: %d file(s), %d chunk(s) total.", len(pdf_paths), total_chunks)


if __name__ == "__main__":
    main()
