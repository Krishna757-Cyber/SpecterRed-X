// Quality preference (High / Low / 2D) persisted to localStorage, plus a small
// reduced-motion hook. Used by the 3D routes and the quality selector.
import { useEffect, useState } from 'react'

export type Quality = 'high' | 'low' | '2d'
const KEY = 'specterred.quality'

export function getQuality(): Quality {
  const v = localStorage.getItem(KEY)
  return v === 'high' || v === 'low' || v === '2d' ? v : 'high'
}

export function useQuality(): [Quality, (q: Quality) => void] {
  const [quality, setQualityState] = useState<Quality>(getQuality)
  useEffect(() => {
    const handler = () => setQualityState(getQuality())
    window.addEventListener('specterred-quality', handler)
    return () => window.removeEventListener('specterred-quality', handler)
  }, [])
  const setQuality = (q: Quality) => {
    localStorage.setItem(KEY, q)
    setQualityState(q)
    window.dispatchEvent(new Event('specterred-quality'))
  }
  return [quality, setQuality]
}

export function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(
    () => window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false,
  )
  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)')
    const handler = () => setReduced(mq.matches)
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [])
  return reduced
}

export function webglAvailable(): boolean {
  try {
    const canvas = document.createElement('canvas')
    return !!(
      window.WebGLRenderingContext &&
      (canvas.getContext('webgl') || canvas.getContext('experimental-webgl'))
    )
  } catch {
    return false
  }
}
