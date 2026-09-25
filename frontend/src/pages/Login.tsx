import { useState, type FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function Login() {
  const { user, signIn, signUp } = useAuth()
  const navigate = useNavigate()
  const [mode, setMode] = useState<'signin' | 'signup'>('signin')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [info, setInfo] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  if (user) return <Navigate to="/app" replace />

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setInfo(null)
    setSubmitting(true)

    if (mode === 'signin') {
      const { error } = await signIn(email, password)
      setSubmitting(false)
      if (error) {
        setError(error)
        return
      }
      navigate('/app')
      return
    }

    const { error, confirmedImmediately } = await signUp(email, password)
    setSubmitting(false)
    if (error) {
      setError(error)
      return
    }
    if (confirmedImmediately) {
      // This project doesn't require email confirmation - the sign-up
      // already returned an active session, so go straight in.
      navigate('/app')
      return
    }
    setInfo('Account created. Check your inbox to confirm your email, then log in.')
    setMode('signin')
  }

  return (
    <div className="mx-auto max-w-sm px-4 py-16">
      <h1 className="text-2xl font-semibold text-ink">
        {mode === 'signin' ? 'Log in' : 'Create an account'}
      </h1>

      <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
        <label className="flex flex-col gap-1 text-sm font-medium text-slate-700">
          Email
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="rounded-md border border-slate-300 px-3 py-2 text-ink focus:border-lime-deep focus:outline-none"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm font-medium text-slate-700">
          Password
          <input
            type="password"
            required
            minLength={6}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="rounded-md border border-slate-300 px-3 py-2 text-ink focus:border-lime-deep focus:outline-none"
          />
        </label>

        {error && <p className="text-sm text-red-600">{error}</p>}
        {info && <p className="text-sm text-emerald-600">{info}</p>}

        <button
          type="submit"
          disabled={submitting}
          className="mt-2 rounded-full bg-ink px-4 py-2 font-medium text-white hover:bg-ink-soft disabled:opacity-50"
        >
          {submitting ? 'Please wait…' : mode === 'signin' ? 'Log in' : 'Sign up'}
        </button>
      </form>

      <button
        onClick={() => {
          setMode(mode === 'signin' ? 'signup' : 'signin')
          setError(null)
          setInfo(null)
        }}
        className="mt-4 text-sm text-slate-500 hover:text-ink"
      >
        {mode === 'signin' ? "Don't have an account? Sign up" : 'Already have an account? Log in'}
      </button>
    </div>
  )
}
