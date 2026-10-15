import type { CustomerResult } from '../lib/types'
import { SEGMENT_INFO } from '../lib/segments'

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
    cellClassName: 'min-w-[220px] px-4 py-3',
    hasValue: (r) => Boolean(r.segment),
    render: (r) => {
      const info = SEGMENT_INFO[r.segment]
      return (
        <>
          <span
            className={`rounded-full px-3 py-1 text-xs font-semibold whitespace-nowrap ${
              info?.color ?? 'bg-slate-100 text-slate-700'
            }`}
          >
            {r.segment}
          </span>
          {info && (
            <p className="mt-1.5 text-xs leading-snug text-ink-muted">
              {info.description} {info.signal}
            </p>
          )}
          {!r.fits_custom_segment && (
            <div className="mt-1 text-[10px] text-ink-muted" title="Closest default segment used">
              default segment
            </div>
          )}
        </>
      )
    },
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
    render: (r) => (
      <>
        <p>{r.reason}</p>
        {r.sources.map((s) => (
          <p key={s.document} className="mt-1.5 text-xs text-ink-muted italic" title={s.excerpt}>
            Source: {s.document}
          </p>
        ))}
      </>
    ),
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
