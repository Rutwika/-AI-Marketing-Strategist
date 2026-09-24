import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const EXAMPLE = {
  customer_id: 'C002',
  segment: 'At-Risk High-Value',
  reason: 'Bought regularly until March, no purchases or email opens since.',
  channel: 'sms',
  offer: '15% off next order',
}

export function Landing() {
  const { user } = useAuth()

  return (
    <div className="mx-auto max-w-3xl px-4 py-16 text-center">
      <h1 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
        Turn messy customer data into segments and next best actions — no SQL.
      </h1>
      <p className="mx-auto mt-4 max-w-xl text-lg text-slate-600">
        Upload a customer CSV. Get a segment, a plain-language reason, and a next-best action for
        every row — in under 30 seconds.
      </p>
      <Link
        to={user ? '/app' : '/login'}
        className="mt-8 inline-block rounded-lg bg-slate-900 px-6 py-3 font-medium text-white hover:bg-slate-700"
      >
        Get started
      </Link>

      <div className="mt-16 rounded-xl border border-slate-200 bg-white p-6 text-left shadow-sm">
        <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
          Example result
        </p>
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <span className="rounded-full bg-amber-100 px-3 py-1 text-sm font-medium text-amber-800">
            {EXAMPLE.segment}
          </span>
          <span className="text-sm text-slate-500">customer {EXAMPLE.customer_id}</span>
        </div>
        <p className="mt-3 text-sm text-slate-700">{EXAMPLE.reason}</p>
        <p className="mt-2 text-sm text-slate-500">
          Recommended: <span className="font-medium text-slate-700">{EXAMPLE.channel}</span> ·{' '}
          {EXAMPLE.offer}
        </p>
      </div>
    </div>
  )
}
