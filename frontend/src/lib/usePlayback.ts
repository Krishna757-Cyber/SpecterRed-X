// Shared playback hook: steps through a run's ordered events with play/pause/
// speed/scrub. The 3D scene, timeline and arena all subscribe to the same step.
import { useEffect, useRef, useState } from 'react'

export interface Playback {
  step: number // 0-based index into events (−1 = before first)
  playing: boolean
  speed: number
  setStep: (s: number) => void
  play: () => void
  pause: () => void
  toggle: () => void
  next: () => void
  prev: () => void
  reset: () => void
  setSpeed: (s: number) => void
}

// (import fix below — React does not export useCallback as a named default here)
export function usePlayback(count: number): Playback {
  const [step, setStepRaw] = useState(0)
  const [playing, setPlaying] = useState(false)
  const [speed, setSpeed] = useState(1)
  const timer = useRef<number | null>(null)

  const clamp = (s: number) => Math.max(0, Math.min(count - 1, s))
  const setStep = (s: number) => setStepRaw(clamp(s))

  useEffect(() => {
    if (!playing) return
    if (step >= count - 1) {
      setPlaying(false)
      return
    }
    timer.current = window.setTimeout(() => setStepRaw((s) => clamp(s + 1)), 1400 / speed)
    return () => {
      if (timer.current) window.clearTimeout(timer.current)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [playing, step, speed, count])

  // Reset to start when the run (count) changes.
  useEffect(() => {
    setStepRaw(0)
    setPlaying(false)
  }, [count])

  return {
    step,
    playing,
    speed,
    setStep,
    play: () => setPlaying(true),
    pause: () => setPlaying(false),
    toggle: () => setPlaying((p) => !p),
    next: () => setStep(step + 1),
    prev: () => setStep(step - 1),
    reset: () => {
      setStepRaw(0)
      setPlaying(false)
    },
    setSpeed,
  }
}
