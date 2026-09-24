import type { CustomerResult } from '../lib/types'

const SEGMENT_COLORS: Record<string, string> = {
  Champions: 'bg-emerald-100 text-emerald-800',
  'New Potential': 'bg-sky-100 text-sky-800',
  'At-Risk High-Value': 'bg-amber-100 text-amber-800',
  'High-Intent Window Shoppers': 'bg-violet-100 text-violet-800',
  'Bargain Hunters': 'bg-orange-100 text-orange-800',
  Hibernating: 'bg-slate-200 text-slate-700',
}

export function ResultsTable({ results }: { results: CustomerResult[] }) {
  return (
    <div className="mt-6 overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50 text-left text-xs font-medium uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-4 py-3">Customer</th>
            <th className="px-4 py-3">Segment</th>
            <th className="px-4 py-3">Value</th>
            <th className="px-4 py-3">Reason</th>
            <th className="px-4 py-3">Channel</th>
            <th className="px-4 py-3">Action</th>
            <th className="px-4 py-3">Offer</th>
            <th className="px-4 py-3">Timing</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {results.map((r) => (
            <tr key={r.customer_id}>
              <td className="px-4 py-3 font-medium text-slate-900">{r.customer_id}</td>
              <td className="px-4 py-3">
                <span
                  className={`whitespace-nowrap rounded-full px-2.5 py-1 text-xs font-medium ${
                    SEGMENT_COLORS[r.segment] ?? 'bg-slate-100 text-slate-700'
                  }`}
                >
                  {r.segment}
                </span>
                {!r.fits_custom_segment && (
                  <span className="ml-1 text-[10px] text-slate-400" title="Closest default segment used">
                    (default)
                  </span>
                )}
              </td>
              <td className="px-4 py-3 text-slate-600">{r.value_tier}</td>
              <td className="max-w-xs px-4 py-3 text-slate-600">{r.reason}</td>
              <td className="px-4 py-3 text-slate-600">{r.channel}</td>
              <td className="max-w-xs px-4 py-3 text-slate-600">{r.action}</td>
              <td className="px-4 py-3 text-slate-600">
                {r.offer}
                {r.discount_pct > 0 && (
                  <span className="ml-1 text-xs text-slate-400">({r.discount_pct}%)</span>
                )}
              </td>
              <td className="px-4 py-3 whitespace-nowrap text-slate-500">{r.timing}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
