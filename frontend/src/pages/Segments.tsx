import { Link } from 'react-router-dom'

const SEGMENTS = [
  {
    name: 'Champions',
    color: 'bg-emerald-100 text-emerald-800',
    signal: 'Long relationship, frequent orders, high spend, still buying.',
    description: 'Your most loyal, highest-value customers.',
    approach: 'No discounts - early access, VIP perks, referral asks.',
  },
  {
    name: 'New Potential',
    color: 'bg-sky-100 text-sky-800',
    signal: 'Recent first purchase, only one or two orders so far.',
    description: 'Just joined and freshly engaged.',
    approach: 'Welcome/nurture email, cross-sell an adjacent category.',
  },
  {
    name: 'At-Risk High-Value',
    color: 'bg-amber-100 text-amber-800',
    signal: 'Used to order often and spend a lot - recency and engagement have dropped.',
    description: 'Valuable customers who have gone quiet.',
    approach: 'Priority win-back via SMS or a personal email, strongest allowed offer.',
  },
  {
    name: 'High-Intent Window Shoppers',
    color: 'bg-violet-100 text-violet-800',
    signal: "No purchase yet, but actively browsing or abandoned a cart.",
    description: "Haven't bought, but clearly interested.",
    approach: 'Cart/browse reminder within 24 hours, reviews or social proof.',
  },
  {
    name: 'Bargain Hunters',
    color: 'bg-orange-100 text-orange-800',
    signal: 'Orders often, but almost always with a coupon - low spend per order.',
    description: 'Frequent buyers who need a discount to convert.',
    approach: 'Clearance and overstock promos only - no full-price offers.',
  },
  {
    name: 'Hibernating',
    color: 'bg-slate-200 text-slate-700',
    signal: 'Low recency, frequency and spend across the board.',
    description: 'Effectively inactive.',
    approach: 'One low-cost re-engagement email - no paid channels.',
  },
]

export function Segments() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-16">
      <h1 className="text-3xl font-semibold text-ink">The 6 segments, at a glance</h1>
      <p className="mt-3 max-w-2xl text-sm text-slate-600">
        Every uploaded customer is assigned the closest of these six segments (or one of your own
        custom segments, if you describe them). Each one comes with its own recommended approach,
        grounded in the research behind Roma's playbook.
      </p>

      <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2">
        {SEGMENTS.map((s) => (
          <div key={s.name} className="rounded-2xl border border-line bg-white p-5 shadow-sm">
            <span className={`rounded-full px-3 py-1 text-xs font-semibold ${s.color}`}>{s.name}</span>
            <p className="mt-3 text-sm font-medium text-ink">{s.description}</p>
            <p className="mt-1 text-xs text-ink-muted">{s.signal}</p>
            <p className="mt-3 border-t border-line pt-3 text-xs text-ink-soft">
              <span className="font-medium text-ink">Typical approach: </span>
              {s.approach}
            </p>
          </div>
        ))}
      </div>

      <div className="mt-10 rounded-xl border border-slate-200 bg-slate-50 p-6">
        <p className="font-medium text-ink">Want to see all six in action?</p>
        <p className="mt-1 text-sm text-slate-600">
          This sample has 2 customers per segment, written so each one clearly matches - upload it
          to see every segment assigned, with its research-grounded sources, in one run.
        </p>
        <div className="mt-4 flex flex-wrap items-center gap-4">
          <a
            href="/segment-samples.csv"
            download
            className="rounded-full bg-ink px-5 py-2.5 text-sm font-medium text-white hover:bg-ink-soft"
          >
            Download sample (12 customers, all 6 segments)
          </a>
          <Link to="/app/analyze" className="text-sm font-medium text-slate-600 underline hover:text-ink">
            Go to upload →
          </Link>
        </div>
      </div>
    </div>
  )
}
