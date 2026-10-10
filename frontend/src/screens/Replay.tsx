import { useEffect, useMemo, useState } from 'react'
import { Download, GitCompareArrows, Repeat } from 'lucide-react'
import { api } from '@/api'
import { useAsync } from '@/lib/useAsync'
import { cacheRun, getCachedRun, setCurrentRunId, useCurrentRunId } from '@/lib/store'
import { NetworkView } from '@/components/NetworkView'
import { OutcomeBadge } from '@/components/OutcomeBadge'
import { EmptyState, ErrorState, Panel, Spinner } from '@/components/ui'
import type { Comparison, Run, RunSummary, ScenarioDetail } from '@/types'

type Mode = 'baseline' | 'replay' | 'diff'

export default function Replay() {
  const [currentRunId] = useCurrentRunId()
  const runsState = useAsync<RunSummary[]>(() => api.runs(), [])
  const baselineOnly = useMemo(
    () => (runsState.data ?? []).filter((r) => r.kind === 'baseline'),
    [runsState.data],
  )

  const [baselineId, setBaselineId] = useState<string | null>(null)

  // Default the baseline selector to the current run (if it is a baseline) or the newest baseline.
  useEffect(() => {
    if (baselineId || baselineOnly.length === 0) return
    const preferred = baselineOnly.find((r) => r.run_id === currentRunId) ?? baselineOnly[0]
    setBaselineId(preferred.run_id)
  }, [baselineOnly, currentRunId, baselineId])

  const baselineState = useAsync<Run | null>(async () => {
    if (!baselineId) return null
    const cached = getCachedRun(baselineId)
    if (cached) return cached
    const r = await api.run(baselineId)
    cacheRun(r)
    return r
  }, [baselineId])

  const baseline = baselineState.data
  const scenState = useAsync<ScenarioDetail | null>(
    async () => (baseline ? api.scenario(baseline.scenario_id) : null),
    [baseline?.scenario_id],
  )

  const [changes, setChanges] = useState<Record<string, string>>({})
  const [replayRun, setReplayRun] = useState<Run | null>(null)
  const [comparison, setComparison] = useState<Comparison | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [mode, setMode] = useState<Mode>('baseline')
  const [reportId, setReportId] = useState<string | null>(null)
  const [stepIdx, setStepIdx] = useState(0)

  // Reset the workspace when the baseline changes.
  useEffect(() => {
    setChanges({})
    setReplayRun(null)
    setComparison(null)
    setReportId(null)
    setMode('baseline')
    setStepIdx(0)
  }, [baselineId])

  async function doReplay() {
    if (!baselineId || Object.keys(changes).length === 0) return
    setBusy(true)
    setError(null)
    try {
      const resp = await api.replay(baselineId, changes)
      const full = await api.run(resp.replay_run.run_id)
      cacheRun(full)
      setReplayRun(full)
      setComparison(resp.comparison)
      setMode('diff')
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(false)
    }
  }

  async function makeReport() {
    if (!replayRun || !comparison) return
    setBusy(true)
    try {
      const r = await api.createReport(replayRun.run_id, comparison.id)
      setReportId(r.report_id)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(false)
    }
  }

  if (runsState.loading) return <div className="grid min-h-[50vh] place-items-center"><Spinner /></div>
  if (runsState.error) return <ErrorState message={runsState.error} onRetry={runsState.reload} />
  if (baselineOnly.length === 0) {
    return (
      <EmptyState
        title="No baseline runs yet"
        hint="Start a scenario first — then return here to change a control and replay it."
        action={<a href="/scenarios" className="btn btn-primary mt-2">Choose a scenario</a>}
      />
    )
  }

  const scenario = scenState.data
  const activeRun = mode === 'replay' || mode === 'diff' ? replayRun ?? baseline : baseline
  const activeEvents = activeRun?.events ?? []
  const currentEvent = activeEvents[Math.min(stepIdx, activeEvents.length - 1)] ?? null

  return (
    <div className="space-y-4">
      <header>
        <h1 className="text-xl font-bold text-ink">Counterfactual Replay</h1>
        <p className="text-sm text-muted">
          Baseline vs replay of the same deterministic scenario. Change a control, replay, and compare
          evidence-backed outcomes.
        </p>
      </header>

      <div className="grid gap-4 lg:grid-cols-[360px_1fr]">
        {/* LEFT: controls */}
        <div className="space-y-4">
          <Panel title="Baseline run">
            <select
              className="w-full rounded-lg border border-[var(--border-subtle)] bg-surface px-3 py-2 text-sm text-ink"
              value={baselineId ?? ''}
              onChange={(e) => setBaselineId(e.target.value)}
              aria-label="Select baseline run"
            >
              {baselineOnly.map((r) => (
                <option key={r.run_id} value={r.run_id}>
                  {r.scenario_id} · {r.run_id.slice(0, 12)} · score {r.resilience_score.toFixed(0)}
                </option>
              ))}
            </select>
            {baseline && (
              <p className="mt-2 text-xs text-muted">
                Immutable baseline hash <span className="mono text-cyan">{baseline.event_hash.slice(0, 12)}…</span>
              </p>
            )}
          </Panel>

          <Panel title="Defensive controls" subtitle="Change one or more, then replay">
            {!scenario ? (
              <Spinner />
            ) : (
              <div className="space-y-3">
                {Object.entries(scenario.controls).map(([name, spec]) => {
                  const base = baseline?.config[name] ?? spec.default
                  const value = changes[name] ?? base
                  const recommended = scenario.recommended_control[name]
                  return (
                    <div key={name}>
                      <label className="flex items-center justify-between text-xs">
                        <span className="text-ink">{name}</span>
                        {recommended && (
                          <button
                            className="mono text-[10px] text-cyan hover:underline"
                            onClick={() => setChanges((c) => ({ ...c, [name]: recommended }))}
                          >
                            recommend: {recommended}
                          </button>
                        )}
                      </label>
                      <select
                        className="mt-1 w-full rounded-lg border border-[var(--border-subtle)] bg-surface px-2.5 py-1.5 text-sm text-ink"
                        value={value}
                        onChange={(e) => setChanges((c) => ({ ...c, [name]: e.target.value }))}
                      >
                        {spec.values.map((v) => (
                          <option key={v} value={v}>
                            {v}
                            {v === base ? ' (baseline)' : ''}
                          </option>
                        ))}
                      </select>
                    </div>
                  )
                })}
                <button
                  className="btn btn-primary w-full"
                  onClick={doReplay}
                  disabled={busy || Object.keys(changes).length === 0}
                >
                  <Repeat size={15} /> {busy ? 'Replaying…' : 'Replay scenario'}
                </button>
                {Object.keys(changes).length === 0 && (
                  <p className="text-center text-[11px] text-muted">Change at least one control to enable replay.</p>
                )}
              </div>
            )}
          </Panel>

          {error && <ErrorState message={error} />}
        </div>

        {/* RIGHT: comparison */}
        <div className="space-y-4">
          {/* score cards */}
          <div className="grid gap-3 sm:grid-cols-3">
            <ScoreCard label="Baseline" value={baseline?.metrics.resilience_score ?? null} />
            <ScoreCard label="Replay" value={replayRun?.metrics.resilience_score ?? null} accent="var(--brand-cyan)" />
            <DeltaCard comparison={comparison} />
          </div>

          {/* 3D with mode switch */}
          <Panel
            title="Network view"
            right={
              <div className="flex gap-1">
                {(['baseline', 'replay', 'diff'] as Mode[]).map((m) => (
                  <button
                    key={m}
                    disabled={m !== 'baseline' && !replayRun}
                    onClick={() => setMode(m)}
                    className={`rounded-md px-2.5 py-1 text-xs capitalize ${
                      mode === m ? 'bg-cyan/15 text-cyan' : 'text-muted hover:text-ink'
                    } disabled:opacity-40`}
                  >
                    {m}
                  </button>
                ))}
              </div>
            }
          >
            <div className="relative h-[300px] overflow-hidden rounded-xl">
              <NetworkView
                assets={scenario?.assets ?? []}
                event={currentEvent}
                selectedAsset={mode === 'diff' ? comparison?.changed_assets[0] ?? null : null}
                onSelectAsset={() => {}}
              />
              {currentEvent && (
                <div className="absolute right-2 top-2">
                  <OutcomeBadge outcome={currentEvent.outcome} />
                </div>
              )}
            </div>
            <input
              type="range"
              min={0}
              max={Math.max(0, activeEvents.length - 1)}
              value={stepIdx}
              onChange={(e) => setStepIdx(Number(e.target.value))}
              className="mt-3 w-full accent-cyan"
              aria-label="Scrub events"
            />
          </Panel>

          {/* step diff table */}
          {comparison && (
            <Panel title="Event-level comparison" subtitle={comparison.verdict}>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead className="text-left text-muted">
                    <tr>
                      <th className="pb-2">#</th>
                      <th className="pb-2">Step</th>
                      <th className="pb-2">Baseline</th>
                      <th className="pb-2">Replay</th>
                      <th className="pb-2">Changed</th>
                    </tr>
                  </thead>
                  <tbody>
                    {comparison.step_diffs.map((d, i) => (
                      <tr key={d.step_key} className={`border-t border-[var(--border-subtle)] ${d.changed ? 'bg-warning/5' : ''}`}>
                        <td className="py-2 mono text-muted">{i + 1}</td>
                        <td className="py-2 text-ink">{d.title}</td>
                        <td className="py-2"><OutcomeBadge outcome={d.baseline_outcome} /></td>
                        <td className="py-2"><OutcomeBadge outcome={d.replay_outcome} /></td>
                        <td className="py-2">{d.changed ? <span className="text-warning">● yes</span> : <span className="text-muted">—</span>}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                <div>
                  <p className="text-xs font-semibold text-ink">Controls changed</p>
                  <ul className="mt-1 space-y-1 text-xs text-muted">
                    {comparison.controls_changed.map((c) => (
                      <li key={c.control} className="mono">
                        {c.control}: {c.from} → <span className="text-cyan">{c.to}</span>
                      </li>
                    ))}
                  </ul>
                  <p className="mt-2 text-[11px] italic text-muted">{comparison.attribution.note}</p>
                </div>
                <div>
                  <p className="text-xs font-semibold text-ink">Residual risks</p>
                  <ul className="mt-1 space-y-1 text-xs text-muted">
                    {comparison.residual_risks.map((r, i) => (
                      <li key={i}>• {r}</li>
                    ))}
                  </ul>
                </div>
              </div>

              <MetricDeltas comparison={comparison} />

              <div className="mt-4 flex flex-wrap items-center gap-2">
                {!reportId ? (
                  <button className="btn btn-primary text-xs" onClick={makeReport} disabled={busy}>
                    <GitCompareArrows size={14} /> Generate report
                  </button>
                ) : (
                  <>
                    <a className="btn btn-ghost text-xs" href={api.reportUrl(reportId, 'md')} target="_blank" rel="noreferrer">
                      <Download size={14} /> Markdown
                    </a>
                    <a className="btn btn-ghost text-xs" href={api.reportUrl(reportId, 'json')} target="_blank" rel="noreferrer">
                      <Download size={14} /> JSON
                    </a>
                    <span className="mono text-[11px] text-success">report {reportId}</span>
                  </>
                )}
                {replayRun && (
                  <button
                    className="btn btn-ghost text-xs"
                    onClick={() => {
                      setCurrentRunId(replayRun.run_id)
                    }}
                  >
                    Set replay as active run
                  </button>
                )}
              </div>

              <ul className="mt-4 space-y-1 border-t border-[var(--border-subtle)] pt-3 text-[11px] text-muted">
                {comparison.limitations.map((l, i) => (
                  <li key={i}>• {l}</li>
                ))}
              </ul>
            </Panel>
          )}
        </div>
      </div>
    </div>
  )
}

function ScoreCard({ label, value, accent }: { label: string; value: number | null; accent?: string }) {
  return (
    <div className="panel p-4">
      <p className="text-xs uppercase tracking-wider text-muted">{label}</p>
      <p className="mt-1 text-3xl font-bold" style={accent ? { color: accent } : { color: 'var(--text-primary)' }}>
        {value === null ? '—' : value.toFixed(1)}
      </p>
      <p className="text-[11px] text-muted">resilience / 100</p>
    </div>
  )
}

function DeltaCard({ comparison }: { comparison: Comparison | null }) {
  const delta = comparison?.metric_deltas.resilience_score.delta ?? null
  const color = delta === null ? 'var(--text-secondary)' : delta > 0 ? 'var(--semantic-success)' : delta < 0 ? 'var(--agent-red)' : 'var(--semantic-warning)'
  return (
    <div className="panel p-4">
      <p className="text-xs uppercase tracking-wider text-muted">Change</p>
      <p className="mt-1 text-3xl font-bold" style={{ color }}>
        {delta === null ? '—' : `${delta > 0 ? '+' : ''}${delta.toFixed(1)}`}
      </p>
      <p className="text-[11px] text-muted">
        {delta === null ? 'run a replay' : delta > 0 ? 'improved' : delta < 0 ? 'regressed' : 'no change'}
      </p>
    </div>
  )
}

function MetricDeltas({ comparison }: { comparison: Comparison }) {
  const comps = Object.entries(comparison.metric_deltas).filter(([k]) => k !== 'resilience_score')
  return (
    <div className="mt-4">
      <p className="text-xs font-semibold text-ink">Per-metric deltas</p>
      <div className="mt-2 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {comps.map(([name, d]) => (
          <div key={name} className="rounded-lg border border-[var(--border-subtle)] bg-surface/40 p-2.5">
            <p className="text-[11px] capitalize text-muted">{name.replace(/_/g, ' ')}</p>
            <p className="mono text-xs text-ink">
              {d.baseline === null ? 'N/A' : d.baseline.toFixed(0)} →{' '}
              <span className="text-cyan">{d.replay === null ? 'N/A' : d.replay.toFixed(0)}</span>
              {d.delta !== null && (
                <span className={d.delta > 0 ? 'text-success' : d.delta < 0 ? 'text-red-agent' : 'text-muted'}>
                  {' '}
                  ({d.delta > 0 ? '+' : ''}
                  {d.delta.toFixed(0)})
                </span>
              )}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
