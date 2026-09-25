"""Supabase client + auth helper for the FastAPI backend.

The backend uses the SERVICE key (full access, RLS bypassed) so it must do
its own per-user filtering on `runs`/`run_results` - see main.py. The
service key must never be sent to the frontend; only SUPABASE_URL and the
ANON key go there (frontend/.env.example).
"""

import logging
import os
from functools import lru_cache

from fastapi import HTTPException, status
from supabase import Client, create_client

logger = logging.getLogger("ai_marketing_strategist")


@lru_cache
def get_client() -> Client:
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not service_key:
        raise RuntimeError(
            "SUPABASE_URL / SUPABASE_SERVICE_KEY are not set. Copy backend/.env.example "
            "to backend/.env and fill in your Supabase project's values."
        )
    return create_client(url, service_key)


def get_user_id(authorization: str | None) -> str:
    """Verifies the bearer token from the Authorization header against
    Supabase Auth and returns the user's id. Raises 401 if missing/invalid."""

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")

    token = authorization.split(" ", 1)[1]
    # Deliberately outside the try/except below: a misconfigured client
    # (missing/bad env vars) is a server-side problem (500), not a bad
    # token (401) - conflating the two here previously hid real config
    # errors behind a misleading "Invalid or expired token" message.
    client = get_client()
    try:
        response = client.auth.get_user(token)
    except Exception as exc:  # supabase-py raises on an invalid/expired token
        logger.exception("Supabase token verification failed")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token") from exc

    if response is None or response.user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")

    return response.user.id
