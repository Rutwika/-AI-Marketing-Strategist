"""FastAPI app for AI Marketing Strategist (Week 1 MVP).

Routes (docs/TRD.md > "API endpoints"):
  GET  /api/health          - no auth
  POST /api/analyze         - CSV upload (+ optional custom segments) -> AnalyzeResult
  GET  /api/runs            - the caller's past runs
  GET  /api/runs/{run_id}   - one saved run, with its results
"""

import io
import logging
import os
from datetime import datetime, timezone

import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

import chain
import rules
from schemas import AnalyzeResult, CustomerResult, RunRecord, SummaryBlock
from supabase_client import get_client, get_user_id

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

# Column names (case-insensitive) that count as an existing customer identifier.
_ID_LIKE_COLUMNS = {"customer_id", "customerid", "id", "email", "customer", "user_id", "account_id"}


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


def _save_run(user_id: str, file_name: str, row_count: int, custom_segments: str | None, result: AnalyzeResult) -> None:
    """Best-effort save to Supabase. A storage failure must not lose the
    marketer's already-computed results, so this only logs on error."""

    try:
        client = get_client()
        run = (
            client.table("runs")
            .insert(
                {
                    "user_id": user_id,
                    "file_name": file_name,
                    "row_count": row_count,
                    "custom_segments": custom_segments,
                }
            )
            .execute()
        )
        run_id = run.data[0]["id"]
        rows = [
            {
                "run_id": run_id,
                "customer_id": r.customer_id,
                "segment": r.segment,
                "value_tier": r.value_tier,
                "reason": r.reason,
                "channel": r.channel,
                "action": r.action,
                "offer": r.offer,
                "discount_pct": r.discount_pct,
                "confidence": r.confidence,
            }
            for r in result.results
        ]
        if rows:
            client.table("run_results").insert(rows).execute()
    except Exception:
        logger.exception("Failed to save run to Supabase (results are still returned to the user).")


@app.get("/api/health")
def health():
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}


@app.post("/api/analyze", response_model=AnalyzeResult)
async def analyze(
    file: UploadFile = File(...),
    custom_segments: str | None = Form(default=None),
    authorization: str | None = Header(default=None),
):
    user_id = get_user_id(authorization)

    if custom_segments and len(custom_segments) > 1000:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "custom_segments must be 1000 characters or fewer.")

    df, csv_text = await _read_and_validate_csv(file)
    input_ids = df["customer_id"].astype(str).tolist()

    last_violations: list[str] = []
    for attempt in range(2):
        try:
            result = chain.analyze(csv_text, custom_segments)
        except Exception as exc:
            logger.exception("Gemini call failed (attempt %s)", attempt + 1)
            if attempt == 1:
                raise HTTPException(status.HTTP_502_BAD_GATEWAY, "The AI model failed to respond. Please try again.") from exc
            continue

        violations = rules.check_guardrails(input_ids, result)
        if not violations:
            _save_run(user_id, file.filename or "upload.csv", len(df), custom_segments, result)
            return result

        last_violations = violations
        logger.warning("Guardrail check failed on attempt %s: %s", attempt + 1, violations)

    raise HTTPException(
        status.HTTP_502_BAD_GATEWAY,
        f"The AI model's output didn't pass our business-rule checks after a retry: {'; '.join(last_violations)}",
    )


@app.get("/api/runs", response_model=list[RunRecord])
def list_runs(authorization: str | None = Header(default=None)):
    user_id = get_user_id(authorization)
    client = get_client()
    rows = (
        client.table("runs")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return [
        RunRecord(
            id=row["id"],
            file_name=row["file_name"],
            row_count=row["row_count"],
            custom_segments=row.get("custom_segments"),
            created_at=row["created_at"],
        )
        for row in rows.data
    ]


@app.get("/api/runs/{run_id}", response_model=RunRecord)
def get_run(run_id: str, authorization: str | None = Header(default=None)):
    user_id = get_user_id(authorization)
    client = get_client()

    run_resp = client.table("runs").select("*").eq("id", run_id).eq("user_id", user_id).execute()
    if not run_resp.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Run not found.")
    run = run_resp.data[0]

    results_resp = client.table("run_results").select("*").eq("run_id", run_id).execute()
    results = [
        CustomerResult(
            customer_id=r["customer_id"],
            segment=r["segment"],
            value_tier=r["value_tier"],
            fits_custom_segment=bool(run.get("custom_segments")),
            reason=r["reason"],
            channel=r["channel"],
            action=r["action"],
            offer=r["offer"],
            discount_pct=r["discount_pct"],
            timing=r.get("timing", ""),
            confidence=r["confidence"],
        )
        for r in results_resp.data
    ]
    segments: dict[str, int] = {}
    for r in results:
        segments[r.segment] = segments.get(r.segment, 0) + 1

    return RunRecord(
        id=run["id"],
        file_name=run["file_name"],
        row_count=run["row_count"],
        custom_segments=run.get("custom_segments"),
        created_at=run["created_at"],
        result=AnalyzeResult(summary=SummaryBlock(total_customers=len(results), segments=segments), results=results),
    )
