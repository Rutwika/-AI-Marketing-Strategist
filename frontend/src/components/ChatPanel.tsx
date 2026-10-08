import { useState } from 'react'
import { askChat, ApiError } from '../lib/api'
import type { AnalyzeResult, ChatResponse } from '../lib/types'

interface Message {
  question: string
  response?: ChatResponse
  error?: string
}

const ROUTE_LABEL: Record<ChatResponse['route'], string> = {
  table_qa: 'From this table',
  exa_rag: 'From the web',
}

export function ChatPanel({ table, accessToken }: { table: AnalyzeResult; accessToken: string }) {
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)

  async function submit() {
    const q = question.trim()
    if (!q || loading) return

    setQuestion('')
    setLoading(true)
    const index = messages.length
    setMessages((prev) => [...prev, { question: q }])

    try {
      const response = await askChat(q, table, accessToken)
      setMessages((prev) => prev.map((m, i) => (i === index ? { ...m, response } : m)))
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Something went wrong asking that question.'
      setMessages((prev) => prev.map((m, i) => (i === index ? { ...m, error: message } : m)))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mt-6 rounded-2xl border border-line bg-white p-5 shadow-sm">
      <p className="text-[11px] font-medium tracking-wide text-ink-muted uppercase">Ask about these results</p>

      {messages.length > 0 && (
        <div className="mt-3 flex flex-col gap-4">
          {messages.map((m, i) => (
            <div key={i}>
              <p className="text-sm font-medium text-ink">{m.question}</p>
              {m.response && (
                <div className="mt-1">
                  <p className="text-sm text-ink-soft">{m.response.answer}</p>
                  {m.response.warning && (
                    <p className="mt-1 text-xs text-amber-700">{m.response.warning}</p>
                  )}
                  <div className="mt-1 flex flex-wrap items-center gap-1.5">
                    <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-600">
                      {ROUTE_LABEL[m.response.route]}
                    </span>
                    {m.response.citations.map((c) => (
                      <span
                        key={c.document}
                        className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-600"
                        title={c.excerpt}
                      >
                        {c.document}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {m.error && <p className="mt-1 text-sm text-red-700">{m.error}</p>}
            </div>
          ))}
        </div>
      )}

      <form
        onSubmit={(e) => {
          e.preventDefault()
          submit()
        }}
        className="mt-4 flex gap-2"
      >
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="e.g. How many Champions? or What's a typical win-back discount?"
          maxLength={500}
          disabled={loading}
          className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-lime-deep focus:outline-none disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!question.trim() || loading}
          className="rounded-full bg-ink px-4 py-2 text-sm font-medium text-white hover:bg-ink-soft disabled:opacity-50"
        >
          {loading ? 'Asking…' : 'Ask'}
        </button>
      </form>
    </div>
  )
}
