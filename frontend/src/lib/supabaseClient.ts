import { createClient } from '@supabase/supabase-js'

const url = import.meta.env.VITE_SUPABASE_URL
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!url || !anonKey) {
  // Loud but non-fatal: lets the app boot (e.g. before Phase 2 credentials
  // exist) while making misconfiguration obvious in the console.
  console.warn(
    'VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY are not set. Copy frontend/.env.example to ' +
      'frontend/.env and fill in your Supabase project values before using login.',
  )
}

export const supabase = createClient(url ?? '', anonKey ?? '')
