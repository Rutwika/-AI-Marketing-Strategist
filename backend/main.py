"""FastAPI app for AI Marketing Strategist (Week 1 MVP).

No accounts: every endpoint is open, nothing is persisted between requests.

Routes (docs/TRD.md > "API endpoints"; docs/TRD_chatbot.md for /api/chat):
  GET  /api/health          - health check
  POST /api/analyze         - CSV upload (+ optional custom segments) -> AnalyzeResult
  POST /api/chat            - question + in-memory table -> routed, cited answer
"""

import io
import logging
import os
from datetime import datetime, timezone

import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool

load_dotenv()

import chain
import rules
from chatbot.graph import run_chat
from schemas import AnalyzeResult, ChatRequest, ChatResponse

logger = logging.getLogger("ai_marketing_strategist")

app = FastAPI(title="AI Marketing Strategist API")

_origins = [o.strip() for o in os.environ.get("FRONTEND_ORIGIN", "http://localhost:5173").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_FILE_BYTES = 1_000_000  # < 1 MB, per the TRD
MIN_ROWS = 1
MAX_ROWS = 20

# Column names (case-insensitive) that count as an existing customer identifier,
# in priority order - a list, not a set, so "customer_id" is always preferred
# over a looser match like "email" when a CSV has both.
_ID_LIKE_COLUMNS = ["customer_id", "customerid", "id", "customer", "user_id", "account_id", "email"]


def _normalize_customer_id_column(df: pd.DataFrame) -> pd.DataFrame:
    """Guarantees a `customer_id` column exists so the model has something
    stable to copy into each result, and so rules.check_guardrails can match
    every output row back to an input row - even when the uploaded CSV has
    no obvious id column (the PRD allows "any columns")."""

    lower_map = {c.lower(): c for c in df.columns}
    match = next((lower_map[c] for c in _ID_LIKE_COLUMNS if c in lower_map), None)

    df = df.copy()
    if match is not None:
        if match != "customer_id":
            # Defensive: even with the priority order above, guard against a
            # rename colliding with a pre-existing "customer_id" column.
            df = df.drop(columns=["customer_id"], errors="ignore")
            df = df.rename(columns={match: "customer_id"})
    else:
        df.insert(0, "customer_id", [f"row_{i + 1}" for i in range(len(df))])

    # customer_id first, for a stable, legible CSV sent to the model.
    cols = ["customer_id"] + [c for c in df.columns if c != "customer_id"]
    return df[cols]


async def _read_and_validate_csv(file: UploadFile) -> tuple[pd.DataFrame, str]:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Please upload a .csv file.")

    raw = await file.read()
    if len(raw) == 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "The uploaded file is empty.")
    if len(raw) > MAX_FILE_BYTES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "File is larger than 1 MB.")

    try:
        df = pd.read_csv(io.BytesIO(raw))
    except Exception as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Could not parse CSV: {exc}") from exc

    if len(df) < MIN_ROWS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "The CSV has no data rows.")
    if len(df) > MAX_ROWS:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Please upload {MAX_ROWS} rows or fewer (got {len(df)}).",
        )

    df = _normalize_customer_id_column(df)
    clean_csv_text = df.to_csv(index=False)
    return df, clean_csv_text


@app.get("/api/health")
def health():
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}


@app.post("/api/analyze", response_model=AnalyzeResult)
async def analyze(
    file: UploadFile = File(...),
    custom_segments: str | None = Form(default=None),
):
    if custom_segments and len(custom_segments) > 1000:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "custom_segments must be 1000 characters or fewer.")

    df, csv_text = await _read_and_validate_csv(file)
    input_ids = df["customer_id"].astype(str).tolist()

    last_violations: list[str] = []
    for attempt in range(2):
        try:
            result = await run_in_threadpool(chain.analyze, csv_text, custom_segments)
        except Exception as exc:
            logger.exception("Gemini call failed (attempt %s)", attempt + 1)
            if attempt == 1:
                raise HTTPException(status.HTTP_502_BAD_GATEWAY, "The AI model failed to respond. Please try again.") from exc
            continue

        violations = rules.check_guardrails(input_ids, result)
        if not violations:
            return result

        last_violations = violations
        logger.warning("Guardrail check failed on attempt %s: %s", attempt + 1, violations)

    raise HTTPException(
        status.HTTP_502_BAD_GATEWAY,
        f"The AI model's output didn't pass our business-rule checks after a retry: {'; '.join(last_violations)}",
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(body: ChatRequest):
    if len(body.table.results) > MAX_ROWS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Table has more than {MAX_ROWS} rows.")

    try:
        return await run_in_threadpool(run_chat, body.question, body.table)
    except Exception as exc:
        logger.exception("Chat graph failed to run.")
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "The chatbot failed to respond. Please try again.") from exc
