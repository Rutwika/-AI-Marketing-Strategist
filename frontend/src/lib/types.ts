// Mirrors backend/schemas.py so the two stay in sync by hand until there's
// a shared schema generator.

export type Segment =
  | 'Champions'
  | 'New Potential'
  | 'At-Risk High-Value'
  | 'High-Intent Window Shoppers'
  | 'Bargain Hunters'
  | 'Hibernating'

export type ValueTier = 'High' | 'Medium' | 'Low'
export type Channel = 'email' | 'sms' | 'push' | 'paid_social' | 'none'
export type Confidence = 'high' | 'medium' | 'low'

export interface CustomerResult {
  customer_id: string
  segment: Segment
  value_tier: ValueTier
  fits_custom_segment: boolean
  reason: string
  channel: Channel
  action: string
  offer: string
  discount_pct: number
  timing: string
  confidence: Confidence
}

export interface AnalyzeResult {
  summary: {
    total_customers: number
    segments: Record<string, number>
  }
  results: CustomerResult[]
}

export interface RunRecord {
  id: string
  file_name: string
  row_count: number
  custom_segments: string | null
  created_at: string
  result?: AnalyzeResult | null
}
