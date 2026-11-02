import { Link } from 'react-router-dom'

export function Header() {
  return (
    <header className="bg-ink">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link to="/" className="font-display text-3xl font-black text-brand-blue">
          Roma
        </Link>
        <nav className="flex items-center gap-5 text-sm">
          <Link to="/app" className="text-white/70 hover:text-white">
            Dashboard
          </Link>
          <Link to="/app/segments" className="text-white/70 hover:text-white">
            Segments
          </Link>
          <Link
            to="/app/analyze"
            className="rounded-full bg-lime px-4 py-1.5 font-semibold text-ink hover:bg-lime-deep"
          >
            Get started
          </Link>
        </nav>
      </div>
    </header>
  )
}
