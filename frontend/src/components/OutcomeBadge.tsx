import { clsx } from './clsx'
import type { Outcome } from '@/types'

// Outcome never relies on color alone: each carries an icon glyph + label.
export const OUTCOME_META: Record<Outcome, { label: string; glyph: string; color: string; cls: string }> = {
  succeeded: { label: 'Succeeded', glyph: '✕', color: 'var(--agent-red)', cls: 'text-red-agent border-red-agent/40 bg-red-agent/10' },
  detected: { label: 'Detected', glyph: '◎', color: 'var(--agent-blue)', cls: 'text-blue-agent border-blue-agent/40 bg-blue-agent/10' },
  prevented: { label: 'Prevented', glyph: '✓', color: 'var(--semantic-success)', cls: 'text-success border-success/40 bg-success/10' },
}

export function OutcomeBadge({ outcome, className }: { outcome: Outcome; className?: string }) {
  const m = OUTCOME_META[outcome]
  return (
    <span className={clsx('chip font-mono', m.cls, className)} title={m.label}>
      <span aria-hidden>{m.glyph}</span>
      {m.label}
    </span>
  )
}
