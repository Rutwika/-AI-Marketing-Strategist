# Roma — AI Marketing Strategist (Week 1 MVP)

Upload a customer CSV, get back a segment, a plain-language reason, and a next-best action
(channel + message + offer) for every customer — no SQL, no fixed schema. Built for Week 1 of the
My Real Product program. Full spec: [`docs/PRD.md`](docs/PRD.md) · [`docs/TRD.md`](docs/TRD.md).

## Stack

React (Vite + Tailwind) → FastAPI → LangChain + Gemini, with Supabase for auth and saved runs.
See `docs/TRD.md` for the full architecture.

## Local setup

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
copy .env.example .env          # then fill in GOOGLE_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY
uvicorn main:app --reload --port 8000
```

Run the tests with `pytest` from inside `backend/`.

Supabase setup: create a free project at [supabase.com](https://supabase.com), then run
[`backend/supabase_schema.sql`](backend/supabase_schema.sql) in its SQL editor to create the
`runs` and `run_results` tables.

Gemini key: create a free key at [Google AI Studio](https://aistudio.google.com/app/apikey).

### Frontend

```bash
cd frontend
npm install
copy .env.example .env          # then fill in VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY
npm run dev
```

Opens at `http://localhost:5173` and expects the backend at `http://localhost:8000`
(`VITE_API_BASE_URL`).

## Sample data

[`sample_data/customers_sample.csv`](sample_data/customers_sample.csv) — 13 synthetic customers
covering all six default segments. Also served by the frontend at `/sample-customers.csv`.
`customers_alt_columns.csv` and `customers_messy.csv` are extra test files (different column
names, and blank/inconsistent data) used to check the model copes with real-world messiness.

## Status

Week 1 of 4 (MVP). Roadmap: Week 2 adds RAG over a company knowledge base, Week 3 adds
multi-step agents, Week 4 focuses on reliability. See `docs/PRD.md` > Roadmap.
