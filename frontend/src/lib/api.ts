import type { AnalyzeResult, RunRecord } from './types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function parseErrorMessage(response: Response): Promise<string> {
  try {
    const body = await response.json()
    if (typeof body.detail === 'string') return body.detail
  } catch {
    // response wasn't JSON - fall through to the status text
  }
  return response.statusText || `Request failed with status ${response.status}`
}

export async function analyzeCsv(
  file: File,
  customSegments: string,
  accessToken: string,
): Promise<AnalyzeResult> {
  const form = new FormData()
  form.append('file', file)
  if (customSegments.trim()) form.append('custom_segments', customSegments.trim())

  const response = await fetch(`${API_BASE_URL}/api/analyze`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${accessToken}` },
    body: form,
  })

  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorMessage(response))
  }
  return response.json()
}

export async function listRuns(accessToken: string): Promise<RunRecord[]> {
  const response = await fetch(`${API_BASE_URL}/api/runs`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  })
  if (!response.ok) throw new ApiError(response.status, await parseErrorMessage(response))
  return response.json()
}

export async function getRun(id: string, accessToken: string): Promise<RunRecord> {
  const response = await fetch(`${API_BASE_URL}/api/runs/${id}`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  })
  if (!response.ok) throw new ApiError(response.status, await parseErrorMessage(response))
  return response.json()
}
