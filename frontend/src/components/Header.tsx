import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function Header() {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()

  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        <Link to="/" className="font-semibold text-slate-900">
          AI Marketing Strategist
        </Link>
        <nav className="flex items-center gap-4 text-sm">
          {user ? (
            <>
              <Link to="/app" className="text-slate-600 hover:text-slate-900">
                Dashboard
              </Link>
              <span className="text-slate-400">{user.email}</span>
              <button
                onClick={async () => {
                  await signOut()
                  navigate('/')
                }}
                className="rounded-md border border-slate-300 px-3 py-1.5 text-slate-700 hover:bg-slate-50"
              >
                Log out
              </button>
            </>
          ) : (
            <Link
              to="/login"
              className="rounded-md bg-slate-900 px-3 py-1.5 text-white hover:bg-slate-700"
            >
              Log in
            </Link>
          )}
        </nav>
      </div>
    </header>
  )
}
