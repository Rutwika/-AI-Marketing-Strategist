import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const EXAMPLE = {
  customer_id: 'C002',
  segment: 'At-Risk High-Value',
  reason: 'Bought regularly until March, no purchases or email opens since.',
  channel: 'SMS',
  offer: '15% off next order',
}

const FEATURES = [
  {
    n: '01',
    title: 'Upload, not integrate',
    body: 'Any columns, any naming, 1–20 rows. No schema mapping, no data team.',
  },
  {
    n: '02',
    title: 'A segment for every customer',
    body: 'Champions, At-Risk High-Value, Bargain Hunters and more — with a plain-language reason.',
  },
  {
    n: '03',
    title: 'An action, not just an insight',
    body: 'Channel, offer and timing for each customer, kept inside your discount policy.',
  },
]

export function Landing() {
  const { user } = useAuth()
  const ctaTarget = user ? '/app' : '/login'

  return (
    <div>
      <section className="mx-auto max-w-6xl px-6 pt-10 sm:pt-14">
        <div className="grid grid-cols-1 items-center gap-12 rounded-[32px] bg-lime px-8 py-14 sm:px-14 sm:py-16 lg:grid-cols-2">
          <div>
            <p className="font-sans text-xs font-semibold tracking-[0.18em] text-ink/60 uppercase">
              AI marketing strategist
            </p>
            <h1 className="mt-4 font-display text-5xl leading-[1.05] font-bold text-ink sm:text-6xl">
              Segments that convert, without the SQL.
            </h1>
            <p className="mt-5 max-w-md text-lg text-ink/70">
              Upload a customer CSV. Roma reads it, segments every customer, and hands you a
              next-best action — in under a minute.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-4">
              <Link
                to={ctaTarget}
                className="rounded-full bg-ink px-6 py-3 font-semibold text-white hover:bg-ink-soft"
              >
                Get started →
              </Link>
              <span className="text-sm text-ink/60">No SQL. No fixed schema. Just a CSV.</span>
            </div>
          </div>

          <div className="relative flex justify-center py-4">
            <div className="w-full max-w-sm -rotate-2 rounded-2xl border border-ink/10 bg-white p-6 shadow-xl">
              <p className="text-xs font-medium tracking-wide text-ink-muted uppercase">
                Example result
              </p>
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <span className="rounded-full bg-lime-pale px-3 py-1 text-sm font-semibold text-ink">
                  {EXAMPLE.segment}
                </span>
                <span className="text-sm text-ink-muted">customer {EXAMPLE.customer_id}</span>
              </div>
              <p className="mt-3 text-sm text-ink-soft">{EXAMPLE.reason}</p>
              <div className="mt-4 flex items-center justify-between border-t border-line pt-3 text-sm">
                <span className="text-ink-muted">
                  Recommended: <span className="font-semibold text-ink">{EXAMPLE.channel}</span>
                </span>
                <span className="font-semibold text-ink">{EXAMPLE.offer}</span>
              </div>
            </div>
            <div className="absolute top-8 -right-2 hidden rotate-3 rounded-xl border border-ink/10 bg-ink px-4 py-2 text-sm font-semibold text-lime shadow-lg sm:block">
              13 customers → 6 segments
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 py-16 sm:py-20">
        <div className="grid grid-cols-1 gap-10 sm:grid-cols-3">
          {FEATURES.map((f) => (
            <div key={f.n}>
              <p className="font-display text-3xl font-bold text-lime-deep">{f.n}</p>
              <h3 className="mt-2 text-lg font-semibold text-ink">{f.title}</h3>
              <p className="mt-2 text-sm text-ink-muted">{f.body}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
