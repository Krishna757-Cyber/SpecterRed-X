// Typed API client. Uses the Vite dev proxy (/api -> backend) by default so the
// app works with CORS limited to the dev origin.
import type {
  Comparison,
  Dashboard,
  Health,
  MitreTechnique,
  ReplayResponse,
  Run,
  RunSummary,
  ScenarioDetail,
  ScenarioSummary,
} from './types'

const BASE = import.meta.env.VITE_API_BASE?.replace(/\/$/, '') || '/api'

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`
    try {
      const body = await res.json()
      if (body?.detail) detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
    } catch {
      /* ignore */
    }
    throw new ApiError(detail, res.status)
  }
  return res.json() as Promise<T>
}

export const api = {
  health: () => request<Health>('/health'),
  dashboard: () => request<Dashboard>('/dashboard'),
  scenarios: () => request<{ scenarios: ScenarioSummary[] }>('/scenarios').then((r) => r.scenarios),
  scenario: (id: string) => request<ScenarioDetail>(`/scenarios/${id}`),
  createRun: (scenario_id: string, config?: Record<string, string>, seed = 1337) =>
    request<Run>('/runs', { method: 'POST', body: JSON.stringify({ scenario_id, config, seed }) }),
  runs: () => request<{ runs: RunSummary[] }>('/runs').then((r) => r.runs),
  run: (id: string) => request<Run>(`/runs/${id}`),
  replay: (id: string, control_changes: Record<string, string>) =>
    request<ReplayResponse>(`/runs/${id}/replay`, {
      method: 'POST',
      body: JSON.stringify({ control_changes }),
    }),
  comparison: (id: string) => request<Comparison>(`/comparisons/${id}`),
  createReport: (runId: string, comparison_id?: string) =>
    request<{ report_id: string; run_id: string; comparison_id: string | null }>(
      `/runs/${runId}/report`,
      { method: 'POST', body: JSON.stringify({ comparison_id: comparison_id ?? null }) },
    ),
  mitre: () => request<{ available: boolean; techniques: MitreTechnique[] }>('/mitre'),
  reportUrl: (reportId: string, fmt: 'md' | 'json') => `${BASE}/reports/${reportId}.${fmt}`,
}
