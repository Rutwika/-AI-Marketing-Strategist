"""Single source of truth for RAG env vars/constants, so ingest.py and
retrieval.py never drift apart on index name, embedding model, or dimension.
"""

import os

from dotenv import load_dotenv

# main.py already calls this before importing chain.py (-> rag.retrieval ->
# rag.config), but standalone scripts (ingest.py, verify_retrieval.py) import
# this module directly - load here too so .env is picked up either way.
# Idempotent and harmless to call more than once.
load_dotenv()

PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "marketing-segment-research")
PINECONE_CLOUD = os.environ.get("PINECONE_CLOUD", "aws")
PINECONE_REGION = os.environ.get("PINECONE_REGION", "us-east-1")

EMBEDDING_MODEL = os.environ.get("PINECONE_EMBEDDING_MODEL", "models/gemini-embedding-001")
EMBEDDING_DIMENSION = int(os.environ.get("PINECONE_EMBEDDING_DIMENSION", "768"))

RAG_TOP_K = int(os.environ.get("RAG_TOP_K", "3"))

CHUNK_SIZE = 400
CHUNK_OVERLAP = 40

KNOWLEDGE_BASE_DIR = os.path.join(os.path.dirname(__file__), "knowledge_base")
