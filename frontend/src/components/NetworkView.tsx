// Chooses 3D (High/Low) vs 2D (React Flow) based on quality preference + WebGL
// availability, with an error boundary that falls back to 2D on canvas failure.
import { Suspense, lazy } from 'react'
import type { Asset, SimEvent } from '@/types'
import { useQuality, usePrefersReducedMotion, webglAvailable } from '@/lib/quality'
import { CanvasErrorBoundary } from './CanvasErrorBoundary'
import { CyberRange2D } from './CyberRange2D'
import { Spinner } from './ui'

const CyberRange3D = lazy(() => import('./CyberRange3D').then((m) => ({ default: m.CyberRange3D })))

export function NetworkView(props: {
  assets: Asset[]
  event: SimEvent | null
  selectedAsset: string | null
  onSelectAsset: (id: string) => void
}) {
  const [quality] = useQuality()
  const reducedMotion = usePrefersReducedMotion()
  const canWebgl = webglAvailable()
  const use2d = quality === '2d' || !canWebgl

  const twoD = <CyberRange2D {...props} />

  if (use2d) {
    return (
      <div className="h-full w-full">
        {twoD}
        {!canWebgl && (
          <p className="absolute bottom-2 left-2 chip border-warning/40 bg-warning/10 text-[10px] text-warning">
            WebGL unavailable - 2D view
          </p>
        )}
      </div>
    )
  }

  return (
    <CanvasErrorBoundary fallback={twoD}>
      <Suspense fallback={<div className="grid h-full place-items-center"><Spinner label="Loading 3D range…" /></div>}>
        <CyberRange3D {...props} quality={quality} reducedMotion={reducedMotion} />
      </Suspense>
    </CanvasErrorBoundary>
  )
}
