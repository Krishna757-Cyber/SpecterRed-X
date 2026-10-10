import { clsx } from './clsx'
import type { Dashboard } from '@/types'

// A small SVG "intelligence core" whose state follows actual run status.
// No decorative timers: it is driven purely by the dashboard's computed state.
const STATE_META: Record<
  Dashboard['intelligence_core_state'],
  { label: string; color: string; desc: string }
> = {
  idle: { label: 'Idle', color: '#A8B3C7', desc: 'No active simulation' },
  threat_active: { label: 'Threat active', color: '#FF304F', desc: 'Adversary achieved an objective in the latest run' },
  evaluating: { label: 'Evaluating', color: '#9B7CFF', desc: 'Blue Agent partially contained the latest run' },
  contained: { label: 'Contained', color: '#29D391', desc: 'Latest run reached a strong resilience score' },
}

export function IntelligenceCore({ state }: { state: Dashboard['intelligence_core_state'] }) {
  const m = STATE_META[state]
  return (
    <div className="flex flex-col items-center gap-3 py-2">
      <svg width="150" height="150" viewBox="0 0 150 150" aria-hidden>
        <defs>
          <radialGradient id="core-grad">
            <stop offset="0%" stopColor={m.color} stopOpacity="0.9" />
            <stop offset="70%" stopColor={m.color} stopOpacity="0.15" />
            <stop offset="100%" stopColor={m.color} stopOpacity="0" />
          </radialGradient>
        </defs>
        <circle cx="75" cy="75" r="60" fill="none" stroke={m.color} strokeOpacity="0.15" strokeWidth="1" />
        <circle
          cx="75"
          cy="75"
          r="48"
          fill="none"
          stroke={m.color}
          strokeOpacity="0.3"
          strokeWidth="1.5"
          strokeDasharray="4 6"
          className={state !== 'idle' ? 'animate-pulse-ring' : ''}
        />
        <circle cx="75" cy="75" r="40" fill="url(#core-grad)" />
        <circle cx="75" cy="75" r="18" fill={m.color} fillOpacity="0.85" />
        <circle cx="75" cy="75" r="18" fill="none" stroke={m.color} strokeWidth="2" />
      </svg>
      <div className="text-center">
        <p className="flex items-center justify-center gap-2 text-sm font-semibold" style={{ color: m.color }}>
          <span className={clsx('inline-block h-2 w-2 rounded-full')} style={{ background: m.color }} aria-hidden />
          {m.label}
        </p>
        <p className="mt-1 max-w-[220px] text-xs text-muted">{m.desc}</p>
      </div>
    </div>
  )
}
