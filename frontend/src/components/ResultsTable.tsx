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

interface ColumnDef {
  key: string
  label: string
  cellClassName: string
  hasValue: (r: CustomerResult) => boolean
  render: (r: CustomerResult) => React.ReactNode
}

const COLUMN_DEFS: ColumnDef[] = [
  {
    key: 'customer_id',
    label: 'Customer',
    cellClassName: 'px-4 py-3 font-semibold whitespace-nowrap text-ink',
    hasValue: (r) => Boolean(r.customer_id),
    render: (r) => r.customer_id,
  },
  {
    key: 'segment',
    label: 'Segment',
    cellClassName: 'px-4 py-3 whitespace-nowrap',
    hasValue: (r) => Boolean(r.segment),
    render: (r) => (
      <>
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
      </>
    ),
  },
  {
    key: 'value_tier',
    label: 'Value tier',
    cellClassName: 'px-4 py-3 whitespace-nowrap text-ink-soft',
    hasValue: (r) => Boolean(r.value_tier),
    render: (r) => r.value_tier,
  },
  {
    key: 'reason',
    label: 'Reason',
    cellClassName: 'min-w-[260px] px-4 py-3 text-ink-soft',
    hasValue: (r) => Boolean(r.reason),
    render: (r) => r.reason,
  },
  {
    key: 'channel',
    label: 'Channel',
    cellClassName: 'px-4 py-3 whitespace-nowrap text-ink-soft',
    hasValue: (r) => Boolean(r.channel),
    render: (r) => r.channel,
  },
  {
    key: 'action',
    label: 'Action',
    cellClassName: 'min-w-[180px] px-4 py-3 text-ink-soft',
    hasValue: (r) => Boolean(r.action),
    render: (r) => r.action,
  },
  {
    key: 'offer',
    label: 'Offer',
    cellClassName: 'min-w-[160px] px-4 py-3 text-ink-soft',
    hasValue: (r) => Boolean(r.offer) || r.discount_pct > 0,
    render: (r) => (r.discount_pct > 0 ? `${r.offer} (${r.discount_pct}%)` : r.offer),
  },
  {
    key: 'timing',
    label: 'Timing',
    cellClassName: 'px-4 py-3 whitespace-nowrap text-ink-soft',
    hasValue: (r) => Boolean(r.timing),
    render: (r) => r.timing,
  },
  {
    key: 'confidence',
    label: 'Confidence',
    cellClassName: 'px-4 py-3 whitespace-nowrap text-ink-soft',
    hasValue: (r) => Boolean(r.confidence),
    render: (r) => CONFIDENCE_LABEL[r.confidence] ?? r.confidence,
  },
  {
    key: 'sources',
    label: 'Sources',
    cellClassName: 'min-w-[280px] px-4 py-3',
    hasValue: (r) => r.sources.length > 0,
    render: (r) =>
      r.sources.length === 0 ? (
        <span className="text-ink-muted">—</span>
      ) : (
        <ul className="space-y-2">
          {r.sources.map((s) => (
            <li key={s.document}>
              <span className="block text-[10px] font-medium text-slate-600" title={s.document}>
                {s.document}
              </span>
              {s.excerpt && (
                <span className="block text-xs leading-snug text-ink-muted italic">“{s.excerpt}”</span>
              )}
            </li>
          ))}
        </ul>
      ),
  },
]

export function ResultsTable({ results }: { results: CustomerResult[] }) {
  const columns = COLUMN_DEFS.filter((col) => results.some(col.hasValue))

  return (
    <div className="mt-6 max-h-[70vh] overflow-auto rounded-2xl border border-line bg-white shadow-sm">
      <table className="w-full min-w-[1400px] border-collapse text-left text-sm">
        <thead className="sticky top-0 z-10">
          <tr className="border-b border-line bg-slate-50">
            {columns.map((col) => (
              <th
                key={col.key}
                className="bg-slate-50 px-4 py-3 text-[11px] font-medium tracking-wide text-ink-muted uppercase whitespace-nowrap"
              >
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {results.map((r) => (
            <tr key={r.customer_id} className="align-top hover:bg-slate-50/60">
              {columns.map((col) => (
                <td key={col.key} className={col.cellClassName}>
                  {col.render(r)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
