import { Gauge } from 'lucide-react'
import { useQuality, type Quality } from '@/lib/quality'

const OPTIONS: { value: Quality; label: string }[] = [
  { value: 'high', label: 'High 3D' },
  { value: 'low', label: 'Low 3D' },
  { value: '2d', label: '2D' },
]

export function QualitySelector() {
  const [quality, setQuality] = useQuality()
  return (
    <label className="flex items-center gap-2 text-xs text-muted">
      <Gauge size={14} aria-hidden />
      <span className="sr-only">Rendering quality</span>
      <select
        value={quality}
        onChange={(e) => setQuality(e.target.value as Quality)}
        className="rounded-lg border border-[var(--border-subtle)] bg-surface px-2 py-1 text-xs text-ink focus:outline-none"
        aria-label="Rendering quality"
      >
        {OPTIONS.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </label>
  )
}
