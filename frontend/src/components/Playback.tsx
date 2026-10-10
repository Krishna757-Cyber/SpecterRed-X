import { Pause, Play, RotateCcw, SkipBack, SkipForward } from 'lucide-react'
import type { Playback } from '@/lib/usePlayback'
import type { SimEvent } from '@/types'
import { OUTCOME_META } from './OutcomeBadge'
import { clsx } from './clsx'

const SPEEDS = [0.5, 1, 2, 4]

export function PlaybackControls({ pb, events }: { pb: Playback; events: SimEvent[] }) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      <div className="flex items-center gap-1">
        <button className="btn btn-ghost px-2.5 py-2" onClick={pb.reset} aria-label="Reset to start" title="Reset">
          <RotateCcw size={16} />
        </button>
        <button className="btn btn-ghost px-2.5 py-2" onClick={pb.prev} aria-label="Previous step" title="Step back">
          <SkipBack size={16} />
        </button>
        <button
          className="btn btn-primary px-3 py-2"
          onClick={pb.toggle}
          aria-label={pb.playing ? 'Pause' : 'Play'}
          title={pb.playing ? 'Pause' : 'Play'}
        >
          {pb.playing ? <Pause size={16} /> : <Play size={16} />}
        </button>
        <button className="btn btn-ghost px-2.5 py-2" onClick={pb.next} aria-label="Next step" title="Step forward">
          <SkipForward size={16} />
        </button>
      </div>

      <div className="flex items-center gap-1 text-xs text-muted">
        {SPEEDS.map((s) => (
          <button
            key={s}
            onClick={() => pb.setSpeed(s)}
            className={clsx(
              'rounded-md px-2 py-1 font-mono',
              pb.speed === s ? 'bg-cyan/15 text-cyan' : 'hover:text-ink',
            )}
            aria-pressed={pb.speed === s}
          >
            {s}×
          </button>
        ))}
      </div>

      <div className="flex min-w-[200px] flex-1 items-center gap-3">
        <input
          type="range"
          min={0}
          max={Math.max(0, events.length - 1)}
          value={pb.step}
          onChange={(e) => pb.setStep(Number(e.target.value))}
          className="w-full accent-cyan"
          aria-label="Scrub timeline"
        />
        <span className="mono shrink-0 text-xs text-muted">
          {events.length ? pb.step + 1 : 0}/{events.length}
        </span>
      </div>
    </div>
  )
}

export function Timeline({
  events,
  current,
  onSelect,
  changedKeys,
}: {
  events: SimEvent[]
  current: number
  onSelect: (i: number) => void
  changedKeys?: Set<string>
}) {
  return (
    <ol className="flex gap-2 overflow-x-auto pb-2" aria-label="Event timeline">
      {events.map((ev, i) => {
        const m = OUTCOME_META[ev.outcome]
        const active = i === current
        const changed = changedKeys?.has(ev.step_key)
        return (
          <li key={ev.seq} className="shrink-0">
            <button
              onClick={() => onSelect(i)}
              className={clsx(
                'w-44 rounded-xl border p-3 text-left transition-all duration-150',
                active ? 'border-cyan bg-cyan/10 shadow-glow' : 'border-[var(--border-subtle)] hover:border-cyan/40',
              )}
              aria-current={active}
            >
              <div className="flex items-center justify-between">
                <span className="mono text-[10px] text-muted">#{ev.seq}</span>
                <span className="mono text-xs" style={{ color: m.color }} aria-hidden>
                  {m.glyph}
                </span>
              </div>
              <p className="mt-1 line-clamp-2 text-xs font-medium text-ink">{ev.title}</p>
              <div className="mt-1.5 flex items-center gap-1">
                <span className="mono text-[10px]" style={{ color: m.color }}>
                  {m.label}
                </span>
                {changed && (
                  <span className="chip ml-auto border-warning/40 bg-warning/10 px-1.5 py-0 text-[9px] text-warning">
                    changed
                  </span>
                )}
              </div>
            </button>
          </li>
        )
      })}
    </ol>
  )
}
