"""Pinecone client/index singletons, mirroring supabase_client.py's
get_client() lru_cache pattern."""

from functools import lru_cache

from pinecone import Index, Pinecone

from rag import config


@lru_cache
def get_pinecone_client() -> Pinecone:
    if not config.PINECONE_API_KEY:
        raise RuntimeError(
            "PINECONE_API_KEY is not set. Copy backend/.env.example to backend/.env "
            "and add a key from https://app.pinecone.io."
        )
    return Pinecone(api_key=config.PINECONE_API_KEY)


@lru_cache
def get_index() -> Index:
    """Returns a handle to the configured index. Does not create it - if the
    index doesn't exist yet, run `python -m rag.ingest` first. Raising here
    (instead of silently returning an unusable handle) makes a misconfigured
    deploy fail loudly in logs rather than quietly returning zero context."""

    client = get_pinecone_client()
    if config.PINECONE_INDEX_NAME not in client.list_indexes().names():
        raise RuntimeError(
            f"Pinecone index {config.PINECONE_INDEX_NAME!r} does not exist. "
            "Run `python -m rag.ingest` from backend/ to create and populate it."
        )
    return client.Index(config.PINECONE_INDEX_NAME)
