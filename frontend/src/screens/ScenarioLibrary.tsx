import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Clock, Gauge, Play, ShieldCheck, X } from 'lucide-react'
import { api } from '@/api'
import { useAsync } from '@/lib/useAsync'
import { cacheRun, setCurrentRunId } from '@/lib/store'
import { ErrorState, Panel, Spinner } from '@/components/ui'
import type { ScenarioDetail, ScenarioSummary } from '@/types'

const DIFFICULTY_COLOR: Record<string, string> = {
  Intermediate: 'var(--brand-cyan)',
  Advanced: 'var(--agent-red)',
  Beginner: 'var(--semantic-success)',
}

export default function ScenarioLibrary() {
  const { data, loading, error, reload } = useAsync<ScenarioSummary[]>(() => api.scenarios(), [])
  const [detailId, setDetailId] = useState<string | null>(null)
  const [starting, setStarting] = useState<string | null>(null)
  const [startError, setStartError] = useState<string | null>(null)
  const navigate = useNavigate()

  async function start(id: string) {
    setStarting(id)
    setStartError(null)
    try {
      const run = await api.createRun(id)
      cacheRun(run)
      setCurrentRunId(run.run_id)
      navigate('/range')
    } catch (e) {
      setStartError(e instanceof Error ? e.message : String(e))
      setStarting(null)
    }
  }

  if (loading) return <div className="grid min-h-[50vh] place-items-center"><Spinner /></div>
  if (error) return <ErrorState message={error} onRetry={reload} />
  if (!data) return null

  return (
    <div className="space-y-4">
      <header>
        <h1 className="text-xl font-bold text-ink">Scenario Library</h1>
        <p className="text-sm text-muted">
          Three fictional scam, impersonation, and fraud scenarios. All identities and{' '}
          <span className="mono">.example</span> domains are synthetic.
        </p>
      </header>

      {startError && <ErrorState message={startError} />}

      <div className="grid gap-4 lg:grid-cols-3">
        {data.map((s) => (
          <div key={s.id} className="panel flex flex-col p-5 transition-transform duration-250 hover:-translate-y-0.5">
            <div className="flex items-center justify-between">
              <span className="mono text-xs text-cyan">{s.id}</span>
              <span className="chip border-[var(--border-subtle)] text-[10px]" style={{ color: DIFFICULTY_COLOR[s.difficulty] ?? 'var(--text-secondary)' }}>
                <Gauge size={11} /> {s.difficulty}
              </span>
            </div>
            <h2 className="mt-2 text-base font-semibold text-ink">{s.title}</h2>
            <p className="mt-1 text-xs uppercase tracking-wider text-muted">{s.track}</p>
            <p className="mt-3 line-clamp-4 flex-1 text-sm text-muted">{s.description}</p>

            <div className="mt-3 flex flex-wrap gap-1.5">
              {s.defensive_concepts.slice(0, 3).map((c) => (
                <span key={c} className="chip border-[var(--border-subtle)] text-[10px] text-muted">
                  <ShieldCheck size={10} /> {c}
                </span>
              ))}
            </div>

            <div className="mt-3 flex items-center gap-3 text-xs text-muted">
              <span className="flex items-center gap-1"><Clock size={12} /> ~{s.duration_min} min</span>
              <span>{s.step_count} steps</span>
            </div>

            <div className="mt-4 flex gap-2">
              <button className="btn btn-primary flex-1 text-sm" onClick={() => start(s.id)} disabled={starting === s.id}>
                <Play size={14} /> {starting === s.id ? 'Starting…' : 'Start'}
              </button>
              <button className="btn btn-ghost text-sm" onClick={() => setDetailId(s.id)}>
                Details
              </button>
            </div>
          </div>
        ))}
      </div>

      {detailId && <DetailDrawer id={detailId} onClose={() => setDetailId(null)} onStart={start} />}
    </div>
  )
}

function DetailDrawer({ id, onClose, onStart }: { id: string; onClose: () => void; onStart: (id: string) => void }) {
  const { data, loading } = useAsync<ScenarioDetail>(() => api.scenario(id), [id])
  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/50" onClick={onClose}>
      <div
        className="h-full w-full max-w-md overflow-y-auto border-l border-[var(--border-subtle)] bg-navy p-6 animate-fade-in"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-label="Scenario details"
      >
        <div className="flex items-start justify-between">
          <h2 className="text-lg font-bold text-ink">{data?.title ?? id}</h2>
          <button className="btn btn-ghost px-2 py-1" onClick={onClose} aria-label="Close"><X size={16} /></button>
        </div>
        {loading || !data ? (
          <div className="mt-6"><Spinner /></div>
        ) : (
          <div className="mt-4 space-y-4">
            <p className="text-sm text-muted">{data.description}</p>

            <Panel title="Defensive controls">
              <ul className="space-y-2 text-xs">
                {Object.entries(data.controls).map(([name, spec]) => (
                  <li key={name} className="flex items-center justify-between">
                    <span className="mono text-ink">{name}</span>
                    <span className="mono text-muted">{spec.values.join(' · ')}</span>
                  </li>
                ))}
              </ul>
            </Panel>

            <Panel title="Attack chain">
              <ol className="space-y-2 text-xs">
                {data.steps.map((st, i) => (
                  <li key={st.key} className="flex gap-2">
                    <span className="mono text-cyan">{i + 1}</span>
                    <div>
                      <p className="text-ink">{st.title}</p>
                      {st.technique && <span className="mono text-[10px] text-intel">{st.technique}</span>}
                    </div>
                  </li>
                ))}
              </ol>
            </Panel>

            <button className="btn btn-primary w-full" onClick={() => onStart(id)}>
              <Play size={15} /> Start this scenario
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
