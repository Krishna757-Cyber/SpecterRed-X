// Lightweight global store for the "current run" shared across screens, backed
// by sessionStorage so a page refresh keeps the active run. No external dep.
import { useEffect, useState } from 'react'
import type { Run } from '@/types'

const KEY = 'specterred.currentRunId'

let currentRunId: string | null = sessionStorage.getItem(KEY)
const listeners = new Set<() => void>()

export function setCurrentRunId(id: string | null) {
  currentRunId = id
  if (id) sessionStorage.setItem(KEY, id)
  else sessionStorage.removeItem(KEY)
  listeners.forEach((l) => l())
}

export function getCurrentRunId(): string | null {
  return currentRunId
}

export function useCurrentRunId(): [string | null, (id: string | null) => void] {
  const [id, setId] = useState<string | null>(currentRunId)
  useEffect(() => {
    const l = () => setId(currentRunId)
    listeners.add(l)
    return () => {
      listeners.delete(l)
    }
  }, [])
  return [id, setCurrentRunId]
}

// Small cache so navigating between screens doesn't refetch the same run.
const runCache = new Map<string, Run>()
export function cacheRun(run: Run) {
  runCache.set(run.run_id, run)
}
export function getCachedRun(id: string): Run | undefined {
  return runCache.get(id)
}
