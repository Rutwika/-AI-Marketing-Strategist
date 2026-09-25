import { Link } from 'react-router-dom'

const STEPS = [
  { title: 'Upload your customer CSV', detail: 'Any columns, 1–20 rows. No fixed schema required.' },
  {
    title: 'Optionally describe your segments',
    detail: 'e.g. "VIP: 5+ orders and $500+ lifetime spend." Leave blank to use our default playbook.',
  },
  {
    title: 'Get recommendations',
    detail: 'A segment, a plain-language reason, and a next-best action for every customer.',
  },
]

export function Main() {
  return (
    <div className="mx-auto max-w-2xl px-4 py-16">
      <h1 className="text-3xl font-semibold text-ink">How it works</h1>
      <ol className="mt-8 flex flex-col gap-6">
        {STEPS.map((step, i) => (
          <li key={step.title} className="flex gap-4">
            <span className="flex h-8 w-8 flex-none items-center justify-center rounded-full bg-lime text-sm font-bold text-ink">
              {i + 1}
            </span>
            <div>
              <p className="font-medium text-ink">{step.title}</p>
              <p className="text-sm text-slate-600">{step.detail}</p>
            </div>
          </li>
        ))}
      </ol>

      <div className="mt-10 flex flex-wrap items-center gap-4">
        <Link
          to="/app/analyze"
          className="rounded-full bg-ink px-6 py-3 font-medium text-white hover:bg-ink-soft"
        >
          Upload a CSV
        </Link>
        <a
          href="/sample-customers.csv"
          download
          className="text-sm font-medium text-slate-600 underline hover:text-ink"
        >
          Download a sample CSV
        </a>
      </div>
    </div>
  )
}
