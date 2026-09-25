# Deployment Log — 2026-09-25

Retrospective on the Week 1 build and first deployment of Roma (AI Marketing Strategist): what was built, what broke, and how each issue was resolved. Written for reference ahead of future deployments.

## What got built

A full-stack app: React (Vite + Tailwind) frontend → FastAPI backend → LangChain + Gemini for AI segmentation → Supabase for auth/storage, per the PRD/TRD. A marketing manager uploads a customer CSV and gets back, for every customer, a segment, a plain-language reason, and a next-best action — with business-rule guardrails, unit tests, and a bold editorial UI ("Roma": Playfair Display + Work Sans, lime/blue palette).

## Gemini API

- **Model churn**: `gemini-2.0-flash` (originally spec'd) → deprecated (404). `gemini-3.8-flash` → worked, but its free tier is tiny: hit the **5/minute** limit almost immediately during testing, then the **20/day** limit from testing alone. Tried `gemini-3.8-flash-lite` (doesn't exist) and `gemini-2.5-flash-lite` (deprecated for new users) before landing on **`gemini-3.5-flash-lite`**, which worked and has its own separate quota bucket.
- Verified against 3 different CSVs (clean, different column names, messy/blank data) — zero business-rule violations each time.
- On Render, the API key itself turned out to be corrupted from a copy/paste into the dashboard — caused a low-level gRPC credential error (`Illegal header value`) that manifested as the request hanging for 150+ seconds rather than failing cleanly. See Render section.

## Supabase

- Initially landed on the organizations page in the dashboard with no visible "New project" option — needed to create an organization first.
- Ran the schema SQL (`backend/supabase_schema.sql`) via the dashboard's SQL Editor; it silently didn't create the tables (never fully root-caused — possibly a missed click, possibly a UI issue). Rather than keep debugging blind, applied the schema directly via a Postgres connection using the database password — worked immediately.
- Minor library quirk: the Python `gotrue` client's `delete_user()` returned `403 User not allowed` even with the service-role key; a raw REST call with the same key worked fine. Routed around it, never fully explained.

## GitHub

- No `git` on PATH, but found GitHub Desktop's bundled copy (`...\AppData\Local\GitHubDesktop\app-3.6.6\resources\app\git\cmd\git.exe`) and used that instead of installing a second copy.
- Pushing failed: `Cannot prompt because user interactivity has been disabled` — GitHub Desktop's stored login wasn't reusable by the standalone `git.exe`. Fixed with a Personal Access Token, used inline in the push URL each time (never saved to git config).

## Render (backend) — most of the real debugging happened here

1. **Build failure**: `pydantic-core` failed to compile — Render defaulted to Python 3.14, which has no prebuilt wheel yet for the pinned version. Fixed by pinning `PYTHON_VERSION=3.13.15` in `render.yaml`.
2. **401 "Invalid or expired token"**: a mistake in our own code — `get_user_id()` caught *every* exception (including Supabase client misconfiguration) and reported it all as a generic 401, hiding the real problem. Fixed the error handling to separate "server misconfigured" (500) from "bad token" (401), and added logging.
3. That fix revealed the real issue: `SUPABASE_SERVICE_KEY` had gotten corrupted when pasted into Render's environment variable field (`SupabaseException: Invalid API key`). Took two attempts to get a clean paste in.
4. **Server crashing mid-request**: a genuine architecture bug — `/api/analyze` was `async def` but called Gemini/Supabase *synchronously*, which blocks FastAPI's single event loop for the whole request. That blocked Render's own health-check pings too, so Render concluded the service was dead and killed/restarted it mid-request. Fixed by running the blocking calls in a thread pool (`starlette.concurrency.run_in_threadpool`).
5. After that fix, requests stopped crashing the server but still hung 150+ seconds — traced through Render's logs to the same corruption pattern, this time on `GOOGLE_API_KEY`. Re-pasted, fixed.
6. One more 502 that was a false alarm — caught a request mid-deploy during a redeploy; resolved itself once the deploy finished.
7. **Final result**: verified live with a real signup → analyze → save → retrieve flow, all 200s.

## Vercel (frontend)

- Comparatively smooth — root directory set to `frontend`, three env vars added, deployed successfully.
- Finding the live URL after deploy wasn't obvious from the deploy confirmation flow — check the post-deploy screen or the project dashboard's overview page.
- Open at time of writing: point Render's `FRONTEND_ORIGIN` at the live Vercel URL for CORS, then run one final live check end to end.

## Code bugs found and fixed (via testing, not inspection)

- **`customer_id` column collision**: the sample CSV (which has both a `customer_id` and an `email` column) could get mismatched because the column-matching logic used an unordered Python `set`. Found via a live 500 error; fixed with an ordered priority list plus a regression test (`test_prefers_existing_customer_id_over_email_without_collision`).
- **Misleading signup UX**: the login page always said "check your inbox to confirm your email," even when Supabase had already auto-confirmed the account instantly (email confirmation is off for this project). Fixed to detect an immediate session on sign-up and skip straight into the app instead.
- **Results table** was a cramped 8-column table requiring horizontal scroll and truncating longer text — replaced with a per-customer card layout.

## Key takeaway

Roughly half of this session's debugging time came from environment-variable values getting silently corrupted when pasted into Render's dashboard (hit this twice, for two different secrets) — and the true cause was masked at first by our own overly broad exception handling, which reported everything as a generic 401. The fix that actually moved things forward each time was reading the **full Python traceback in Render's logs**, not trusting the HTTP status code alone. Worth checking logs first on any future deployment issue, rather than re-guessing at env var values.
