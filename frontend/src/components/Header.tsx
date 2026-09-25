import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function Header() {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()

  return (
    <header className="bg-ink">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link to="/" className="font-display text-3xl font-black text-brand-blue">
          Roma
        </Link>
        <nav className="flex items-center gap-5 text-sm">
          {user ? (
            <>
              <Link to="/app" className="text-white/70 hover:text-white">
                Dashboard
              </Link>
              <span className="hidden text-white/40 sm:inline">{user.email}</span>
              <button
                onClick={async () => {
                  await signOut()
                  navigate('/')
                }}
                className="rounded-full border border-white/25 px-4 py-1.5 font-medium text-white hover:bg-white/10"
              >
                Log out
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="text-white/70 hover:text-white">
                Sign in
              </Link>
              <Link
                to="/login"
                className="rounded-full bg-lime px-4 py-1.5 font-semibold text-ink hover:bg-lime-deep"
              >
                Get started
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  )
}
