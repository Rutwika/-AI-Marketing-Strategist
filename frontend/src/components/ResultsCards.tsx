import type { CustomerResult } from '../lib/types'

const SEGMENT_COLORS: Record<string, string> = {
  Champions: 'bg-emerald-100 text-emerald-800',
  'New Potential': 'bg-sky-100 text-sky-800',
  'At-Risk High-Value': 'bg-amber-100 text-amber-800',
  'High-Intent Window Shoppers': 'bg-violet-100 text-violet-800',
  'Bargain Hunters': 'bg-orange-100 text-orange-800',
  Hibernating: 'bg-slate-200 text-slate-700',
}

const CONFIDENCE_LABEL: Record<string, string> = {
  high: 'High confidence',
  medium: 'Medium confidence',
  low: 'Low confidence',
}

function Field({ label, value, full = false }: { label: string; value: string; full?: boolean }) {
  return (
    <div className={full ? 'col-span-2' : undefined}>
      <dt className="text-[11px] font-medium tracking-wide text-ink-muted uppercase">{label}</dt>
      <dd className="mt-0.5 text-sm text-ink">{value}</dd>
    </div>
  )
}

export function ResultsCards({ results }: { results: CustomerResult[] }) {
  return (
    <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-2">
      {results.map((r) => (
        <article
          key={r.customer_id}
          className="rounded-2xl border border-line bg-white p-5 shadow-sm"
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-[11px] font-medium tracking-wide text-ink-muted uppercase">
                Customer
              </p>
              <p className="text-lg font-semibold text-ink">{r.customer_id}</p>
            </div>
            <div className="flex flex-col items-end gap-1">
              <span
                className={`rounded-full px-3 py-1 text-xs font-semibold whitespace-nowrap ${
                  SEGMENT_COLORS[r.segment] ?? 'bg-slate-100 text-slate-700'
                }`}
              >
                {r.segment}
              </span>
              {!r.fits_custom_segment && (
                <span className="text-[10px] text-ink-muted" title="Closest default segment used">
                  default segment
                </span>
              )}
            </div>
          </div>

          <p className="mt-3 text-sm leading-relaxed text-ink-soft">{r.reason}</p>

          <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-3 border-t border-line pt-4">
            <Field label="Value tier" value={r.value_tier} />
            <Field label="Channel" value={r.channel} />
            <Field label="Action" value={r.action} full />
            <Field
              label="Offer"
              value={r.discount_pct > 0 ? `${r.offer} (${r.discount_pct}%)` : r.offer}
            />
            <Field label="Timing" value={r.timing} />
          </dl>

          <p className="mt-4 text-[11px] text-ink-muted">
            {CONFIDENCE_LABEL[r.confidence] ?? r.confidence}
          </p>
        </article>
      ))}
    </div>
  )
}
