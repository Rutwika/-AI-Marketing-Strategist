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
  high: 'High',
  medium: 'Medium',
  low: 'Low',
}

const COLUMNS = [
  'Customer',
  'Segment',
  'Value tier',
  'Reason',
  'Channel',
  'Action',
  'Offer',
  'Timing',
  'Confidence',
  'Sources',
]

export function ResultsTable({ results }: { results: CustomerResult[] }) {
  return (
    <div className="mt-6 overflow-x-auto rounded-2xl border border-line bg-white shadow-sm">
      <table className="w-full min-w-[1400px] border-collapse text-left text-sm">
        <thead>
          <tr className="border-b border-line bg-slate-50">
            {COLUMNS.map((col) => (
              <th
                key={col}
                className="px-4 py-3 text-[11px] font-medium tracking-wide text-ink-muted uppercase whitespace-nowrap"
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {results.map((r) => (
            <tr key={r.customer_id} className="align-top hover:bg-slate-50/60">
              <td className="px-4 py-3 font-semibold whitespace-nowrap text-ink">{r.customer_id}</td>
              <td className="px-4 py-3 whitespace-nowrap">
                <span
                  className={`rounded-full px-3 py-1 text-xs font-semibold whitespace-nowrap ${
                    SEGMENT_COLORS[r.segment] ?? 'bg-slate-100 text-slate-700'
                  }`}
                >
                  {r.segment}
                </span>
                {!r.fits_custom_segment && (
                  <div className="mt-1 text-[10px] text-ink-muted" title="Closest default segment used">
                    default segment
                  </div>
                )}
              </td>
              <td className="px-4 py-3 whitespace-nowrap text-ink-soft">{r.value_tier}</td>
              <td className="min-w-[260px] px-4 py-3 text-ink-soft">{r.reason}</td>
              <td className="px-4 py-3 whitespace-nowrap text-ink-soft">{r.channel}</td>
              <td className="min-w-[180px] px-4 py-3 text-ink-soft">{r.action}</td>
              <td className="min-w-[160px] px-4 py-3 text-ink-soft">
                {r.discount_pct > 0 ? `${r.offer} (${r.discount_pct}%)` : r.offer}
              </td>
              <td className="px-4 py-3 whitespace-nowrap text-ink-soft">{r.timing}</td>
              <td className="px-4 py-3 whitespace-nowrap text-ink-soft">
                {CONFIDENCE_LABEL[r.confidence] ?? r.confidence}
              </td>
              <td className="min-w-[280px] px-4 py-3">
                {r.sources.length === 0 ? (
                  <span className="text-ink-muted">—</span>
                ) : (
                  <ul className="space-y-2">
                    {r.sources.map((s) => (
                      <li key={s.document}>
                        <span className="block text-[10px] font-medium text-slate-600" title={s.document}>
                          {s.document}
                        </span>
                        {s.excerpt && (
                          <span className="block text-xs leading-snug text-ink-muted italic">
                            “{s.excerpt}”
                          </span>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
