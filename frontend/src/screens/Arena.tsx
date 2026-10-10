import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ChevronDown, ChevronUp, ShieldAlert, ShieldCheck } from 'lucide-react'
import { api } from '@/api'
import { useAsync } from '@/lib/useAsync'
import { usePlayback } from '@/lib/usePlayback'
import { cacheRun, getCachedRun, useCurrentRunId } from '@/lib/store'
import { PlaybackControls, Timeline } from '@/components/Playback'
import { OutcomeBadge } from '@/components/OutcomeBadge'
import { EmptyState, ErrorState, Panel, Spinner } from '@/components/ui'
import type { Run, ScenarioDetail } from '@/types'

export default function Arena() {
  const [runId] = useCurrentRunId()
  const [expanded, setExpanded] = useState(true)

  const runState = useAsync<Run | null>(async () => {
    if (!runId) return null
    const cached = getCachedRun(runId)
    if (cached) return cached
    const r = await api.run(runId)
    cacheRun(r)
    return r
  }, [runId])

  const run = runState.data
  const scenState = useAsync<ScenarioDetail | null>(
    async () => (run ? api.scenario(run.scenario_id) : null),
    [run?.scenario_id],
  )

  const events = run?.events ?? []
  const pb = usePlayback(events.length)
  const ev = events[pb.step] ?? null

  const [stepMeta, setStepMeta] = useState<ScenarioDetail['steps'][number] | null>(null)
  useEffect(() => {
    if (ev && scenState.data) {
      setStepMeta(scenState.data.steps.find((s) => s.key === ev.step_key) ?? null)
    }
  }, [ev, scenState.data])

  if (!runId) {
    return (
      <EmptyState
        title="No active simulation"
        hint="Start a scenario to watch the Red and Blue agents reason over real events."
        action={<Link to="/scenarios" className="btn btn-primary mt-2">Choose a scenario</Link>}
      />
    )
  }
  if (runState.loading || scenState.loading) return <div className="grid min-h-[50vh] place-items-center"><Spinner /></div>
  if (runState.error) return <ErrorState message={runState.error} onRetry={runState.reload} />
  if (!run || !scenState.data) return <ErrorState message="Run not found." />

  const decision = run.decisions.find((d) => ev && d.step_key === ev.step_key) ?? null

  return (
    <div className="space-y-4">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-ink">Red vs Blue Arena</h1>
          <p className="text-sm text-muted">{scenState.data.title} · run <span className="mono text-cyan">{run.run_id}</span></p>
        </div>
        <span className="chip border-[var(--border-subtle)]">
          Step <span className="mono ml-1 text-cyan">{events.length ? pb.step + 1 : 0}/{events.length}</span>
        </span>
      </header>

      {/* center status */}
      <Panel>
        <PlaybackControls pb={pb} events={events} />
      </Panel>

      {/* split screen */}
      <div className="grid gap-4 lg:grid-cols-2">
        {/* RED */}
        <section className="panel border-red-agent/30 p-5 shadow-glow-red" aria-label="Red agent">
          <h2 className="flex items-center gap-2 text-sm font-bold text-red-agent">
            <ShieldAlert size={16} /> Red Agent — Adversarial Reasoner
          </h2>
          {ev ? (
            <div className="mt-4 space-y-3 text-sm">
              <Field label="Current step" value={ev.title} />
              <Field label="Simulated objective" value={ev.objective} multiline />
              {ev.technique && (
                <div>
                  <p className="text-xs text-muted">Technique (conceptual)</p>
                  <span className="mono mt-1 inline-block rounded bg-red-agent/10 px-2 py-0.5 text-xs text-red-agent">
                    {ev.technique}
                  </span>
                </div>
              )}
              <div>
                <p className="text-xs text-muted">Expected observables (ground truth)</p>
                <ul className="mt-1 flex flex-wrap gap-1.5">
                  {(stepMeta?.expected_observables ?? ev.expected_observables).map((o) => (
                    <li key={o} className="mono chip border-red-agent/30 bg-red-agent/5 text-[10px] text-red-agent">{o}</li>
                  ))}
                </ul>
              </div>
            </div>
          ) : (
            <p className="mt-4 text-sm text-muted">Press play to begin.</p>
          )}
        </section>

        {/* BLUE */}
        <section className="panel border-blue-agent/30 p-5 shadow-glow-blue" aria-label="Blue agent">
          <h2 className="flex items-center gap-2 text-sm font-bold text-blue-agent">
            <ShieldCheck size={16} /> Blue Agent — Defensive Reasoner
          </h2>
          {ev ? (
            <div className="mt-4 space-y-3 text-sm">
              <div>
                <p className="text-xs text-muted">Observed evidence (emitted telemetry only)</p>
                {ev.emitted_signals.length ? (
                  <ul className="mt-1 space-y-1">
                    {ev.evidence_ids.map((id, i) => (
                      <li key={id} className="mono rounded bg-blue-agent/10 px-2 py-1 text-[11px] text-blue-agent">
                        {id} · {ev.emitted_signals[i]}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-1 text-xs italic text-muted">No telemetry observable under current controls — nothing to act on.</p>
                )}
              </div>
              {decision ? (
                <>
                  <Field label="Defensive decision" value={decision.action} />
                  <Field label="Applied control" value={decision.control || '—'} />
                  <div>
                    <p className="text-xs text-muted">Decision outcome</p>
                    <div className="mt-1 flex items-center gap-2">
                      <OutcomeBadge outcome={ev.outcome} />
                      <span className="mono text-[10px] text-muted">{decision.decision_id} · {decision.mode}</span>
                    </div>
                  </div>
                  <Field label="Explanation" value={decision.explanation} multiline />
                </>
              ) : (
                <p className="text-xs italic text-muted">No decision recorded for this step.</p>
              )}
            </div>
          ) : (
            <p className="mt-4 text-sm text-muted">Awaiting events…</p>
          )}
        </section>
      </div>

      {/* bottom: timeline + decision history */}
      <Panel
        title="Event & decision history"
        right={
          <button className="btn btn-ghost text-xs" onClick={() => setExpanded((e) => !e)}>
            {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />} {expanded ? 'Collapse' : 'Expand'}
          </button>
        }
      >
        <Timeline events={events} current={pb.step} onSelect={pb.setStep} />
        {expanded && (
          <div className="mt-4 space-y-2">
            {run.decisions.map((d) => (
              <div key={d.decision_id} className="flex items-start gap-3 rounded-lg border border-[var(--border-subtle)] bg-surface/40 p-2.5 text-xs">
                <span className="mono shrink-0 text-blue-agent">{d.decision_id}</span>
                <div>
                  <p className="text-ink">{d.action} <span className="text-muted">on</span> {d.step_key}</p>
                  <p className="text-muted">{d.explanation}</p>
                  {d.input_evidence_ids.length > 0 && (
                    <p className="mono mt-0.5 text-[10px] text-muted">evidence: {d.input_evidence_ids.join(', ')}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </Panel>
    </div>
  )
}

function Field({ label, value, multiline }: { label: string; value: string; multiline?: boolean }) {
  return (
    <div>
      <p className="text-xs text-muted">{label}</p>
      <p className={`mt-0.5 text-ink ${multiline ? 'text-xs leading-relaxed' : 'text-sm font-medium'}`}>{value}</p>
    </div>
  )
}
