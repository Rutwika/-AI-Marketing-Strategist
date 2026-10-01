"""Gemini embeddings wrapper for RAG ingestion and retrieval.

Uses asymmetric task types (RETRIEVAL_DOCUMENT at ingest time, RETRIEVAL_QUERY
at query time) since gemini-embedding-001 is tuned for this distinction.
output_dimensionality is a per-call kwarg on this langchain-google-genai
version (not a constructor field) - verified against the installed 2.0.7.
"""

import os
from functools import lru_cache

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from rag import config


@lru_cache
def get_embeddings_client() -> GoogleGenerativeAIEmbeddings:
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY is not set. Copy backend/.env.example to backend/.env "
            "and add a key from https://aistudio.google.com/app/apikey."
        )
    return GoogleGenerativeAIEmbeddings(model=config.EMBEDDING_MODEL, google_api_key=api_key)


def embed_documents(texts: list[str]) -> list[list[float]]:
    return get_embeddings_client().embed_documents(
        texts, task_type="RETRIEVAL_DOCUMENT", output_dimensionality=config.EMBEDDING_DIMENSION
    )


def embed_query(text: str) -> list[float]:
    return get_embeddings_client().embed_query(
        text, task_type="RETRIEVAL_QUERY", output_dimensionality=config.EMBEDDING_DIMENSION
    )
