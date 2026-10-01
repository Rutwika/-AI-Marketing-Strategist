Drop the research PDFs here, then run `python -m rag.ingest` from `backend/`
(with the venv active) to chunk, embed, and upsert them into Pinecone.

The PDFs themselves are gitignored (see the repo root `.gitignore`) - only
this README is tracked, so the folder exists in a fresh checkout.
