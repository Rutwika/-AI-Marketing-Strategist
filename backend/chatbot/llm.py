"""Shared Gemini client for all chatbot nodes, mirroring chain.py's
build_chain()/rag's get_embeddings_client() "fail loudly if misconfigured"
pattern, but as a single lru_cache singleton since every node in this graph
uses the same model/temperature (unlike chain.py, which only has one call).
"""

import os
from functools import lru_cache

from langchain_google_genai import ChatGoogleGenerativeAI

from chatbot import config


@lru_cache
def get_chat_llm() -> ChatGoogleGenerativeAI:
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY is not set. Copy backend/.env.example to backend/.env "
            "and add a key from https://aistudio.google.com/app/apikey."
        )
    return ChatGoogleGenerativeAI(
        model=config.CHAT_GEMINI_MODEL, temperature=config.CHAT_TEMPERATURE, google_api_key=api_key
    )
