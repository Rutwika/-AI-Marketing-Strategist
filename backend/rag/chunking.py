"""PDF loading and word-window chunking. Pure functions (chunk_text has no
I/O) so they're unit-testable without any credentials - see
backend/tests/test_chunking.py.
"""

from pathlib import Path

from pypdf import PdfReader


def load_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 40) -> list[str]:
    """Splits text into overlapping word-window chunks for retrieval."""

    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(len(words), start + chunk_size)
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = end - overlap
    return chunks
