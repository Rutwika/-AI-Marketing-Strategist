"""Exa client singleton, mirroring rag/pinecone_client.py's lru_cache pattern."""

from functools import lru_cache

from exa_py import Exa

from chatbot import config


@lru_cache
def get_exa_client() -> Exa:
    if not config.EXA_API_KEY:
        raise RuntimeError(
            "EXA_API_KEY is not set. Copy backend/.env.example to backend/.env "
            "and add a key from https://exa.ai."
        )
    return Exa(api_key=config.EXA_API_KEY)
