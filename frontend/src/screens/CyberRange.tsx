import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Camera, Crosshair, Layers, Shield } from 'lucide-react'
import { api } from '@/api'
import { useAsync } from '@/lib/useAsync'
import { usePlayback } from '@/lib/usePlayback'
import { cacheRun, getCachedRun, useCurrentRunId } from '@/lib/store'
import { NetworkView } from '@/components/NetworkView'
import { PlaybackControls, Timeline } from '@/components/Playback'
import { OUTCOME_META, OutcomeBadge } from '@/components/OutcomeBadge'
import { EmptyState, ErrorState, Panel, Spinner } from '@/components/ui'
import type { Asset, Run, ScenarioDetail } from '@/types'

export default function CyberRange() {
  const [runId] = useCurrentRunId()
  const [selectedAsset, setSelectedAsset] = useState<string | null>(null)

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
  const currentEvent = events[pb.step] ?? null

  // Auto-select the asset the current event touches.
  useEffect(() => {
    if (currentEvent?.affects_assets?.length) {
      setSelectedAsset(currentEvent.affects_assets[0])
    }
  }, [currentEvent])

  const assets = useMemo(() => scenState.data?.assets ?? [], [scenState.data])
  const assetById = useMemo(() => {
    const m = new Map<string, Asset>()
    assets.forEach((a) => m.set(a.id, a))
    return m
  }, [assets])

  if (!runId) {
    return (
      <EmptyState
        title="No active simulation"
        hint="Start a scenario to populate the Cyber Range with real backend events."
        action={
          <Link to="/scenarios" className="btn btn-primary mt-2">
            Choose a scenario
          </Link>
        }
      />
    )
  }

  if (runState.loading || scenState.loading) return <div className="grid min-h-[50vh] place-items-center"><Spinner label="Loading run…" /></div>
  if (runState.error) return <ErrorState message={runState.error} onRetry={runState.reload} />
  if (!run || !scenState.data) return <ErrorState message="Run or scenario not found." />

  const scenario = scenState.data
  const inspected = selectedAsset ? assetById.get(selectedAsset) : null
  const decisions = run.decisions.filter((d) => currentEvent && d.step_key === currentEvent.step_key)

  return (
    <div className="space-y-4">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-ink">3D Cyber Range</h1>
          <p className="text-sm text-muted">
            {scenario.title} · run <span className="mono text-cyan">{run.run_id}</span> ·{' '}
            <span className="mono">{run.kind}</span>
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="chip border-[var(--border-subtle)]">
            Resilience <span className="mono ml-1 text-cyan">{run.metrics.resilience_score.toFixed(1)}</span>
          </span>
          <Link to="/replay" className="btn btn-ghost text-xs">
            <Shield size={14} /> Change a control & replay
          </Link>
        </div>
      </header>

      <div className="grid gap-4 lg:grid-cols-[1fr_340px]">
        {/* 3D / 2D canvas */}
        <div className="panel relative h-[460px] overflow-hidden p-0 sm:h-[520px]">
          <div className="absolute left-3 top-3 z-10 flex items-center gap-2">
            <span className="chip border-[var(--border-subtle)] bg-obsidian/60 text-[10px]">
              <Layers size={11} /> {scenario.track}
            </span>
          </div>
          {currentEvent && (
            <div className="absolute right-3 top-3 z-10">
              <OutcomeBadge outcome={currentEvent.outcome} />
            </div>
          )}
          <NetworkView
            assets={assets}
            event={currentEvent}
            selectedAsset={selectedAsset}
            onSelectAsset={setSelectedAsset}
          />
        </div>

        {/* Inspector column */}
        <div className="space-y-4">
          <Panel title="Event Inspector" subtitle={currentEvent ? `Step ${currentEvent.seq} of ${events.length}` : undefined}>
            {currentEvent ? (
              <div className="space-y-3 text-sm">
                <p className="font-semibold text-ink">{currentEvent.title}</p>
                <p className="text-xs leading-relaxed text-muted">{currentEvent.narrative}</p>
                {currentEvent.technique && (
                  <div className="flex items-center gap-2 text-xs">
                    <span className="text-muted">Technique</span>
                    <span className="mono rounded bg-violet/10 px-1.5 py-0.5 text-intel">{currentEvent.technique}</span>
                  </div>
                )}
                <div>
                  <p className="text-xs text-muted">Evidence observed</p>
                  {currentEvent.evidence_ids.length ? (
                    <ul className="mt-1 space-y-1">
                      {currentEvent.evidence_ids.map((id) => (
                        <li key={id} className="mono rounded bg-surface/60 px-2 py-1 text-[11px] text-blue-agent">
                          {id}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="mt-1 text-xs italic text-muted">No telemetry observable under current controls.</p>
                  )}
                </div>
              </div>
            ) : (
              <p className="text-sm text-muted">Press play to step through the run.</p>
            )}
          </Panel>

          <Panel title="Asset Inspector">
            {inspected ? (
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <Crosshair size={14} className="text-cyan" />
                  <span className="font-semibold text-ink">{inspected.label}</span>
                </div>
                <dl className="grid grid-cols-2 gap-y-1.5 text-xs">
                  <dt className="text-muted">Asset ID</dt>
                  <dd className="mono text-ink">{inspected.id}</dd>
                  <dt className="text-muted">Kind</dt>
                  <dd className="text-ink">{inspected.kind}</dd>
                  <dt className="text-muted">Zone</dt>
                  <dd className="text-ink">{inspected.zone}</dd>
                </dl>
                {currentEvent?.affects_assets.includes(inspected.id) && (
                  <p className="chip mt-1 w-full justify-center" style={{ color: OUTCOME_META[currentEvent.outcome].color }}>
                    Touched by current event
                  </p>
                )}
              </div>
            ) : (
              <p className="text-sm text-muted">Select a node in the network to inspect it.</p>
            )}
          </Panel>

          {decisions.length > 0 && (
            <Panel title="Blue Agent Decision">
              {decisions.map((d) => (
                <div key={d.decision_id} className="space-y-1 text-xs">
                  <p className="mono text-blue-agent">{d.decision_id} · {d.action}</p>
                  <p className="text-muted">{d.explanation}</p>
                  <p className="mono text-[10px] text-muted">mode: {d.mode}</p>
                </div>
              ))}
            </Panel>
          )}
        </div>
      </div>

      {/* Playback + timeline */}
      <Panel
        title="Playback"
        right={
          <button className="btn btn-ghost text-xs" onClick={pb.reset}>
            <Camera size={13} /> Reset
          </button>
        }
      >
        <PlaybackControls pb={pb} events={events} />
        <div className="mt-4">
          <Timeline events={events} current={pb.step} onSelect={pb.setStep} />
        </div>
      </Panel>
    </div>
  )
}
