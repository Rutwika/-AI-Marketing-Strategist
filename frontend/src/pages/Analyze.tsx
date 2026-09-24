import { useRef, useState } from 'react'
import { analyzeCsv, ApiError } from '../lib/api'
import { useAuth } from '../context/AuthContext'
import type { AnalyzeResult } from '../lib/types'
import { ResultsTable } from '../components/ResultsTable'

const MAX_ROWS = 20

type Status = 'idle' | 'loading' | 'success' | 'error'

export function Analyze() {
  const { session } = useAuth()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [file, setFile] = useState<File | null>(null)
  const [customSegments, setCustomSegments] = useState('')
  const [status, setStatus] = useState<Status>('idle')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [result, setResult] = useState<AnalyzeResult | null>(null)

  function validateFile(candidate: File): string | null {
    if (!candidate.name.toLowerCase().endsWith('.csv')) {
      return 'Please choose a .csv file.'
    }
    if (candidate.size === 0) {
      return 'That file is empty.'
    }
    if (candidate.size > 1_000_000) {
      return 'File is larger than 1 MB.'
    }
    return null
  }

  async function countDataRows(candidate: File): Promise<number> {
    const text = await candidate.text()
    const lines = text.split(/\r\n|\n/).filter((line) => line.trim().length > 0)
    return Math.max(0, lines.length - 1) // minus header
  }

  function onFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const candidate = e.target.files?.[0] ?? null
    setErrorMessage(null)
    setStatus('idle')
    setResult(null)

    if (!candidate) {
      setFile(null)
      return
    }
    const basicError = validateFile(candidate)
    if (basicError) {
      setErrorMessage(basicError)
      setFile(null)
      return
    }
    setFile(candidate)
  }

  async function runAnalysis() {
    if (!file || !session) return

    setStatus('loading')
    setErrorMessage(null)

    try {
      const rowCount = await countDataRows(file)
      if (rowCount === 0) {
        setStatus('error')
        setErrorMessage('The CSV has no data rows.')
        return
      }
      if (rowCount > MAX_ROWS) {
        setStatus('error')
        setErrorMessage(`Please upload ${MAX_ROWS} rows or fewer (found ${rowCount}).`)
        return
      }

      const data = await analyzeCsv(file, customSegments, session.access_token)
      setResult(data)
      setStatus('success')
    } catch (err) {
      setStatus('error')
      setErrorMessage(
        err instanceof ApiError
          ? err.message
          : 'Something went wrong talking to the AI model. Please try again.',
      )
    }
  }

  function reset() {
    setFile(null)
    setCustomSegments('')
    setStatus('idle')
    setErrorMessage(null)
    setResult(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  function downloadResultsCsv() {
    if (!result) return
    const header = [
      'customer_id',
      'segment',
      'value_tier',
      'reason',
      'channel',
      'action',
      'offer',
      'discount_pct',
      'timing',
      'confidence',
    ]
    const rows = result.results.map((r) =>
      header.map((key) => `"${String(r[key as keyof typeof r]).replaceAll('"', '""')}"`).join(','),
    )
    const csv = [header.join(','), ...rows].join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'segment-results.csv'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-12">
      <h1 className="text-3xl font-semibold text-slate-900">Analyze customers</h1>

      {status !== 'success' && (
        <div className="mt-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <label className="flex flex-col gap-1 text-sm font-medium text-slate-700">
            Customer CSV (max {MAX_ROWS} rows)
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              onChange={onFileChange}
              className="mt-1 rounded-md border border-slate-300 px-3 py-2 text-sm file:mr-3 file:rounded-md file:border-0 file:bg-slate-900 file:px-3 file:py-1.5 file:text-white"
            />
          </label>

          <label className="mt-4 flex flex-col gap-1 text-sm font-medium text-slate-700">
            Your segment definitions (optional)
            <textarea
              value={customSegments}
              onChange={(e) => setCustomSegments(e.target.value)}
              maxLength={1000}
              rows={3}
              placeholder='e.g. "VIP: 5+ orders and $500+ lifetime spend"'
              className="rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
            />
          </label>

          <div className="mt-4 rounded-md bg-slate-50 px-4 py-3 text-xs text-slate-600">
            <p className="font-medium text-slate-700">Business rules applied to every recommendation</p>
            <ul className="mt-1 list-disc pl-4">
              <li>Never a discount above 20%</li>
              <li>Champions never get a discount</li>
              <li>Cheapest channel first (email/push before SMS, paid social as a last resort)</li>
            </ul>
          </div>

          {status === 'error' && errorMessage && (
            <div className="mt-4 flex items-center justify-between rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
              <span>{errorMessage}</span>
              {file && (
                <button onClick={runAnalysis} className="font-medium underline">
                  Retry
                </button>
              )}
            </div>
          )}

          <button
            onClick={runAnalysis}
            disabled={!file || status === 'loading'}
            className="mt-6 rounded-lg bg-slate-900 px-6 py-3 font-medium text-white hover:bg-slate-700 disabled:opacity-50"
          >
            {status === 'loading' ? 'Analyzing… (up to ~30s)' : 'Analyze'}
          </button>
        </div>
      )}

      {status === 'success' && result && (
        <div className="mt-8">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex flex-wrap gap-2">
              {Object.entries(result.summary.segments).map(([segment, count]) => (
                <span
                  key={segment}
                  className="rounded-full bg-slate-100 px-3 py-1 text-sm font-medium text-slate-700"
                >
                  {segment}: {count}
                </span>
              ))}
            </div>
            <div className="flex gap-3">
              <button
                onClick={downloadResultsCsv}
                className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
              >
                Download results as CSV
              </button>
              <button
                onClick={reset}
                className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
              >
                Run another file
              </button>
            </div>
          </div>

          <ResultsTable results={result.results} />
        </div>
      )}
    </div>
  )
}
