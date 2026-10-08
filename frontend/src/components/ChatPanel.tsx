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

function ChatBubbleIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="h-6 w-6">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M8 10h.01M12 10h.01M16 10h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 0 1-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
      />
    </svg>
  )
}

function CloseIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="h-6 w-6">
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
    </svg>
  )
}

export function ChatPanel({ table, accessToken }: { table: AnalyzeResult; accessToken: string }) {
  const [open, setOpen] = useState(false)
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
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      {open && (
        <div className="mb-3 flex max-h-[70vh] w-[360px] max-w-[calc(100vw-3rem)] flex-col rounded-2xl border border-line bg-white shadow-xl">
          <div className="flex items-center justify-between border-b border-line px-4 py-3">
            <p className="text-sm font-semibold text-ink">Ask about these results</p>
            <button
              onClick={() => setOpen(false)}
              aria-label="Close chat"
              className="text-ink-muted hover:text-ink"
            >
              <CloseIcon />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto px-4 py-3">
            {messages.length === 0 ? (
              <p className="text-sm text-ink-muted">
                Ask a question about this table (e.g. "How many Champions?"), or about general
                marketing practice (e.g. "What's a typical win-back discount?").
              </p>
            ) : (
              <div className="flex flex-col gap-4">
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
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault()
              submit()
            }}
            className="flex gap-2 border-t border-line p-3"
          >
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask a question…"
              maxLength={500}
              disabled={loading}
              autoFocus
              className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-lime-deep focus:outline-none disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={!question.trim() || loading}
              className="rounded-full bg-ink px-4 py-2 text-sm font-medium text-white hover:bg-ink-soft disabled:opacity-50"
            >
              {loading ? '…' : 'Ask'}
            </button>
          </form>
        </div>
      )}

      <button
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? 'Close chat' : 'Ask about these results'}
        className="flex h-14 w-14 items-center justify-center rounded-full bg-ink text-white shadow-lg hover:bg-ink-soft"
      >
        {open ? <CloseIcon /> : <ChatBubbleIcon />}
      </button>
    </div>
  )
}
