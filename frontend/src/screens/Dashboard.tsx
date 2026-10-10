import { Link } from 'react-router-dom'
import { Activity, FileText, Play, ShieldCheck } from 'lucide-react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { api } from '@/api'
import { useAsync } from '@/lib/useAsync'
import { EmptyState, ErrorState, Panel, Spinner, Stat } from '@/components/ui'
import { IntelligenceCore } from '@/components/IntelligenceCore'
import type { Dashboard as DashboardData } from '@/types'

export default function Dashboard() {
  const { data, loading, error, reload } = useAsync<DashboardData>(() => api.dashboard(), [])

  if (loading) return <div className="grid min-h-[50vh] place-items-center"><Spinner /></div>
  if (error) return <ErrorState message={error} onRetry={reload} />
  if (!data) return null

  if (data.empty) {
    return (
      <div className="space-y-4">
        <Header />
        <EmptyState
          title="No simulations yet"
          hint={data.message}
          action={<Link to="/scenarios" className="btn btn-primary mt-2"><Play size={15} /> Start your first simulation</Link>}
        />
      </div>
    )
  }

  const chartData = [...data.recent_runs]
    .reverse()
    .map((r) => ({ name: r.run_id.slice(4, 10), score: r.resilience_score, kind: r.kind }))

  return (
    <div className="space-y-4">
      <Header />

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Total runs" value={data.total_runs} sub={`${data.baseline_runs} baseline · ${data.replay_runs} replay`} />
        <Stat label="Avg resilience" value={data.avg_resilience?.toFixed(1) ?? '—'} sub="across all runs" accent="var(--brand-cyan)" />
        <Stat label="Detection coverage" value={data.detection_coverage !== null ? `${data.detection_coverage.toFixed(0)}%` : 'N/A'} sub="mean, applicable runs" accent="var(--agent-blue)" />
        <Stat label="Containment" value={data.containment_coverage !== null ? `${data.containment_coverage.toFixed(0)}%` : 'N/A'} sub="mean, applicable runs" accent="var(--semantic-success)" />
      </div>

      <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
        <Panel title="Resilience by run" subtitle="Derived from persisted simulation records">
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: -20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1b2740" />
                <XAxis dataKey="name" tick={{ fill: '#A8B3C7', fontSize: 11 }} />
                <YAxis domain={[0, 100]} tick={{ fill: '#A8B3C7', fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ background: '#0D1220', border: '1px solid rgba(150,175,210,0.18)', borderRadius: 12, color: '#F4F7FC' }}
                  cursor={{ fill: 'rgba(0,217,255,0.06)' }}
                />
                <Bar dataKey="score" radius={[4, 4, 0, 0]}>
                  {chartData.map((d, i) => (
                    <Cell key={i} fill={d.kind === 'replay' ? '#00D9FF' : '#7047FF'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-2 flex gap-4 text-[11px] text-muted">
            <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-violet" /> baseline</span>
            <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-cyan" /> replay</span>
          </div>
        </Panel>

        <Panel title="Intelligence core" subtitle="Follows the latest run state">
          <IntelligenceCore state={data.intelligence_core_state} />
        </Panel>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="Recent simulations" right={<Link to="/scenarios" className="btn btn-ghost text-xs"><Play size={13} /> New run</Link>}>
          <ul className="divide-y divide-[var(--border-subtle)]">
            {data.recent_runs.map((r) => (
              <li key={r.run_id} className="flex items-center justify-between py-2.5 text-sm">
                <div>
                  <span className="mono text-xs text-cyan">{r.run_id}</span>
                  <span className="ml-2 text-xs text-muted">{r.scenario_id} · {r.kind}</span>
                </div>
                <span className="mono text-sm text-ink">{r.resilience_score.toFixed(1)}</span>
              </li>
            ))}
          </ul>
        </Panel>

        <Panel title="Recent reports" right={<Link to="/reports" className="btn btn-ghost text-xs"><FileText size={13} /> All reports</Link>}>
          {data.recent_reports.length ? (
            <ul className="divide-y divide-[var(--border-subtle)]">
              {data.recent_reports.map((rep) => (
                <li key={rep.report_id} className="flex items-center justify-between py-2.5 text-sm">
                  <span className="mono text-xs text-ink">{rep.report_id}</span>
                  <div className="flex gap-2">
                    <a className="text-xs text-cyan hover:underline" href={api.reportUrl(rep.report_id, 'md')} target="_blank" rel="noreferrer">.md</a>
                    <a className="text-xs text-cyan hover:underline" href={api.reportUrl(rep.report_id, 'json')} target="_blank" rel="noreferrer">.json</a>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="py-6 text-center text-sm text-muted">No reports generated yet.</p>
          )}
        </Panel>
      </div>
    </div>
  )
}

function Header() {
  return (
    <header className="flex items-center justify-between">
      <div>
        <h1 className="flex items-center gap-2 text-xl font-bold text-ink">
          <Activity size={18} className="text-cyan" /> Dashboard
        </h1>
        <p className="text-sm text-muted">Resilience across your simulated fraud-defense runs.</p>
      </div>
      <Link to="/replay" className="btn btn-ghost text-xs">
        <ShieldCheck size={14} /> Counterfactual replay
      </Link>
    </header>
  )
}
