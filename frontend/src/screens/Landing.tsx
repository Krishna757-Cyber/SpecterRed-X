import { Suspense, lazy } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  ArrowRight,
  Boxes,
  FileCheck2,
  GitCompareArrows,
  Github,
  Repeat,
  Shield,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'
import { usePrefersReducedMotion, webglAvailable } from '@/lib/quality'
import { api } from '@/api'
import { setCurrentRunId, cacheRun } from '@/lib/store'
import { useState } from 'react'

const LandingGlobe = lazy(() => import('@/components/LandingGlobe').then((m) => ({ default: m.LandingGlobe })))

export default function Landing() {
  const reducedMotion = usePrefersReducedMotion()
  const navigate = useNavigate()
  const [starting, setStarting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function startSimulation() {
    setStarting(true)
    setError(null)
    try {
      // Launch the flagship S1 baseline and open the Cyber Range on real events.
      const run = await api.createRun('S1')
      cacheRun(run)
      setCurrentRunId(run.run_id)
      navigate('/range')
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
      setStarting(false)
    }
  }

  return (
    <div>
      {/* HERO */}
      <section className="relative overflow-hidden border-b border-[var(--border-subtle)]">
        <div className="mx-auto grid max-w-[1600px] items-center gap-8 px-4 py-16 lg:grid-cols-2 lg:py-24">
          <div className="animate-fade-in">
            <span className="chip border-cyan/40 bg-cyan/10 text-cyan">
              <Sparkles size={13} /> ForgeHacks 2026 · AI + Cybersecurity
            </span>
            <h1 className="mt-5 text-4xl font-bold leading-tight tracking-tight text-ink sm:text-5xl lg:text-6xl">
              Attack. Adapt. Defend.
              <span className="block bg-gradient-to-r from-cyan via-intel to-violet bg-clip-text text-transparent">
                Prove Resilience.
              </span>
            </h1>
            <p className="mt-5 max-w-xl text-base text-muted sm:text-lg">
              An AI-powered cyber-defense flight simulator that turns controlled security failures
              into measurable resilience — against phishing, executive impersonation, and voice-clone
              fraud.
            </p>

            <div className="mt-7 flex flex-wrap gap-3">
              <button className="btn btn-primary" onClick={startSimulation} disabled={starting}>
                {starting ? 'Launching…' : 'Start Simulation'}
                <ArrowRight size={16} />
              </button>
              <Link to="/range" className="btn btn-ghost">
                <Boxes size={16} /> Explore Cyber Range
              </Link>
            </div>
            {error && (
              <p className="mt-3 text-sm text-red-agent" role="alert">
                Could not reach the backend: {error}. Start it with{' '}
                <code className="mono">uvicorn app.main:app</code>.
              </p>
            )}
          </div>

          <div className="relative h-[320px] sm:h-[420px] lg:h-[480px]">
            {webglAvailable() ? (
              <Suspense fallback={<GlobePlaceholder />}>
                <LandingGlobe reducedMotion={reducedMotion} />
              </Suspense>
            ) : (
              <GlobePlaceholder />
            )}
            <div className="pointer-events-none absolute bottom-2 left-1/2 flex -translate-x-1/2 gap-4 text-xs text-muted">
              <span className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full" style={{ background: 'var(--agent-red)' }} /> Adversarial
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full" style={{ background: 'var(--agent-blue)' }} /> Defensive
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* COUNTERFACTUAL DEFENSE TWIN */}
      <section className="mx-auto max-w-[1600px] px-4 py-14">
        <div className="panel p-8">
          <span className="chip border-intel/40 bg-intel/10 text-intel">
            <GitCompareArrows size={13} /> Signature Innovation
          </span>
          <h2 className="mt-4 text-2xl font-bold text-ink sm:text-3xl">The Counterfactual Defense Twin</h2>
          <p className="mt-3 max-w-3xl text-muted">
            Observe a baseline run of a fictional organization under attack. Inspect the evidence
            behind a defensive failure. Change one security control. Replay the <em>same</em>{' '}
            deterministic scenario. Then compare — step by step — which outcomes actually changed and
            why.
          </p>
          <div className="mt-6 grid gap-3 text-sm sm:grid-cols-3 lg:grid-cols-7">
            {['Simulate', 'Observe', 'Verify', 'Defend', 'Replay', 'Compare', 'Learn'].map((s, i) => (
              <div
                key={s}
                className="flex items-center justify-center gap-2 rounded-xl border border-[var(--border-subtle)] bg-surface/40 px-3 py-3 font-medium text-ink"
              >
                <span className="mono text-xs text-cyan">{i + 1}</span>
                {s}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* BEFORE / AFTER */}
      <section className="mx-auto max-w-[1600px] px-4 pb-14">
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="panel border-red-agent/30 p-6">
            <h3 className="flex items-center gap-2 text-sm font-semibold text-red-agent">
              <Shield size={16} /> Before — control disabled
            </h3>
            <p className="mt-3 text-sm text-muted">
              A synthetic executive invoice request is <span className="text-red-agent">accepted</span>{' '}
              without independent verification. The fraudulent payment transition succeeds.
            </p>
          </div>
          <div className="panel border-success/30 p-6">
            <h3 className="flex items-center gap-2 text-sm font-semibold text-success">
              <ShieldCheck size={16} /> After — callback verification enabled
            </h3>
            <p className="mt-3 text-sm text-muted">
              The same replayed payment transition is <span className="text-success">blocked</span>{' '}
              because the required independent verification is missing. The engine shows the exact
              event and control records.
            </p>
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section className="mx-auto max-w-[1600px] px-4 pb-14">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Feature icon={Boxes} title="3D Cyber Range" body="A procedural holographic network with event-driven playback tied to persisted simulation data." />
          <Feature icon={Repeat} title="Deterministic Replay" body="Seeded, reproducible runs. Identical inputs produce identical normalized event hashes." />
          <Feature icon={GitCompareArrows} title="Evidence-Based Comparison" body="Honest, step-level diffs with per-metric deltas — and it tells you when a change did not help." />
          <Feature icon={FileCheck2} title="Exportable Reports" body="Markdown + JSON reports built strictly from real run records, with MITRE ATT&CK context." />
        </div>
      </section>

      {/* ARCHITECTURE + SAFETY */}
      <section className="mx-auto max-w-[1600px] px-4 pb-16">
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="panel p-6">
            <h3 className="text-sm font-semibold text-ink">Architecture & Safety</h3>
            <ul className="mt-3 space-y-2 text-sm text-muted">
              <li>• Deterministic policy engine is the sole authority over simulated state.</li>
              <li>• No <code className="mono">eval</code>/<code className="mono">exec</code>, no subprocess, no network access in simulation or agents.</li>
              <li>• Synthetic targets only — fictional identities and <code className="mono">.example</code> domains.</li>
              <li>• Core demo runs fully offline, without any paid API key.</li>
              <li>• Optional LLM assists narrative only; it never determines ground truth.</li>
            </ul>
          </div>
          <div className="panel p-6">
            <h3 className="text-sm font-semibold text-ink">Honest by design</h3>
            <p className="mt-3 text-sm text-muted">
              The resilience score is a scenario-specific <strong>simulation metric</strong>, not a
              certified real-world security rating. A technique mapping denotes conceptual relevance,
              not proof of a real intrusion. Deterministic replay is reproducible — it is not a
              statistical experiment.
            </p>
            <div className="mt-4 flex gap-3">
              <Link to="/scenarios" className="btn btn-ghost text-xs">
                View Scenarios
              </Link>
              <a className="btn btn-ghost text-xs" href="https://attack.mitre.org/" target="_blank" rel="noreferrer">
                <Github size={14} /> MITRE ATT&CK
              </a>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}

function Feature({ icon: Icon, title, body }: { icon: typeof Boxes; title: string; body: string }) {
  return (
    <div className="panel p-5 transition-transform duration-250 hover:-translate-y-0.5">
      <div className="grid h-10 w-10 place-items-center rounded-xl bg-cyan/10 text-cyan">
        <Icon size={18} />
      </div>
      <h3 className="mt-3 text-sm font-semibold text-ink">{title}</h3>
      <p className="mt-1.5 text-xs leading-relaxed text-muted">{body}</p>
    </div>
  )
}

function GlobePlaceholder() {
  return (
    <div className="grid h-full place-items-center rounded-panel border border-[var(--border-subtle)] bg-surface/30">
      <div className="text-center text-muted">
        <Boxes className="mx-auto mb-2 text-cyan" />
        <p className="text-xs">Holographic network preview</p>
      </div>
    </div>
  )
}
