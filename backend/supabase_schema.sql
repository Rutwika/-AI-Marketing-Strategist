-- AI Marketing Strategist - Week 1 schema (docs/TRD.md > "Data storage & security")
-- Run this once in the Supabase project's SQL editor (Phase 2).

create table if not exists public.runs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  file_name text not null,
  row_count integer not null,
  custom_segments text,
  created_at timestamptz not null default now()
);

create table if not exists public.run_results (
  id uuid primary key default gen_random_uuid(),
  run_id uuid not null references public.runs (id) on delete cascade,
  customer_id text not null,
  segment text not null,
  value_tier text not null,
  reason text not null,
  channel text not null,
  action text not null,
  offer text not null,
  discount_pct integer not null,
  confidence text not null
);

alter table public.runs enable row level security;
alter table public.run_results enable row level security;

-- A user can only see/insert their own runs. The backend uses the service
-- key (bypasses RLS) so these policies matter mainly if the frontend ever
-- queries Supabase directly.
create policy "Users can view their own runs" on public.runs
  for select using (auth.uid() = user_id);

create policy "Users can insert their own runs" on public.runs
  for insert with check (auth.uid() = user_id);

create policy "Users can view results for their own runs" on public.run_results
  for select using (
    exists (select 1 from public.runs where runs.id = run_results.run_id and runs.user_id = auth.uid())
  );
