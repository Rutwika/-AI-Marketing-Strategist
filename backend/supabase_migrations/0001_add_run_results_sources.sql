-- Adds RAG citation support to an existing live project. Run once by hand in
-- the Supabase SQL editor. A fresh project created from supabase_schema.sql
-- already includes this column.

alter table public.run_results
  add column if not exists sources jsonb not null default '[]'::jsonb;
