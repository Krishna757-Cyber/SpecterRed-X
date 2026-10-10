import { useEffect, useMemo, useState } from 'react'
import { Download, FileText, Sparkles } from 'lucide-react'
import { api } from '@/api'
import { useAsync } from '@/lib/useAsync'
import { EmptyState, ErrorState, Panel, Spinner } from '@/components/ui'
import { Markdown } from '@/components/Markdown'
import type { RunSummary } from '@/types'

export default function Reports() {
  const runsState = useAsync<RunSummary[]>(() => api.runs(), [])
  const [selectedRun, setSelectedRun] = useState<string | null>(null)
  const [reportId, setReportId] = useState<string | null>(null)
  const [markdown, setMarkdown] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const runs = useMemo(() => runsState.data ?? [], [runsState.data])

  useEffect(() => {
    if (!selectedRun && runs.length) setSelectedRun(runs[0].run_id)
  }, [runs, selectedRun])

  async function generate(runId: string) {
    setBusy(true)
    setError(null)
    setMarkdown(null)
    try {
      const r = await api.createReport(runId)
      setReportId(r.report_id)
      const md = await fetch(api.reportUrl(r.report_id, 'md')).then((res) => res.text())
      setMarkdown(md)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(false)
    }
  }

  if (runsState.loading) return <div className="grid min-h-[50vh] place-items-center"><Spinner /></div>
  if (runsState.error) return <ErrorState message={runsState.error} onRetry={runsState.reload} />

  if (runs.length === 0) {
    return (
      <EmptyState
        title="No runs to report on"
        hint="Start a scenario and optionally replay it, then generate an evidence-backed report here."
        action={<a href="/scenarios" className="btn btn-primary mt-2">Choose a scenario</a>}
      />
    )
  }

  return (
    <div className="space-y-4">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-xl font-bold text-ink"><FileText size={18} className="text-cyan" /> Reports</h1>
          <p className="text-sm text-muted">Generated strictly from persisted run data — Markdown & JSON.</p>
        </div>
      </header>

      <div className="grid gap-4 lg:grid-cols-[300px_1fr]">
        <Panel title="Runs">
          <ul className="space-y-1">
            {runs.map((r) => (
              <li key={r.run_id}>
                <button
                  onClick={() => setSelectedRun(r.run_id)}
                  className={`w-full rounded-lg border px-3 py-2 text-left text-xs transition-colors ${
                    selectedRun === r.run_id ? 'border-cyan bg-cyan/10' : 'border-[var(--border-subtle)] hover:border-cyan/40'
                  }`}
                >
                  <span className="mono text-cyan">{r.run_id}</span>
                  <span className="mt-0.5 block text-muted">{r.scenario_id} · {r.kind} · {r.resilience_score.toFixed(1)}</span>
                </button>
              </li>
            ))}
          </ul>
        </Panel>

        <Panel
          title="Report preview"
          right={
            selectedRun && (
              <div className="flex gap-2">
                <button className="btn btn-primary text-xs" onClick={() => generate(selectedRun)} disabled={busy}>
                  <Sparkles size={13} /> {busy ? 'Generating…' : markdown ? 'Regenerate' : 'Generate'}
                </button>
                {reportId && (
                  <>
                    <a className="btn btn-ghost text-xs" href={api.reportUrl(reportId, 'md')} target="_blank" rel="noreferrer"><Download size={13} /> .md</a>
                    <a className="btn btn-ghost text-xs" href={api.reportUrl(reportId, 'json')} target="_blank" rel="noreferrer"><Download size={13} /> .json</a>
                  </>
                )}
              </div>
            )
          }
        >
          {error && <ErrorState message={error} />}
          {!markdown && !busy && !error && (
            <p className="py-10 text-center text-sm text-muted">Select a run and generate a report to preview it here.</p>
          )}
          {busy && <div className="py-10"><Spinner label="Building report…" /></div>}
          {markdown && (
            <div className="max-h-[70vh] overflow-y-auto rounded-xl border border-[var(--border-subtle)] bg-obsidian/40 p-5">
              <Markdown source={markdown} />
            </div>
          )}
        </Panel>
      </div>
    </div>
  )
}
