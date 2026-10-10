// Shared types mirroring the backend payloads.

export interface ControlSpec {
  values: string[]
  default: string
}

export interface ScenarioSummary {
  id: string
  title: string
  track: string
  description: string
  difficulty: string
  duration_min: number
  defensive_concepts: string[]
  controls: Record<string, ControlSpec>
  recommended_control: Record<string, string>
  version: string
  version_hash: string
  step_count: number
}

export interface Asset {
  id: string
  label: string
  kind: 'service' | 'identity' | 'data' | 'control'
  zone: string
  pos: [number, number, number]
}

export interface ScenarioDetail extends ScenarioSummary {
  assets: Asset[]
  steps: ScenarioStep[]
  scoring: { optimal_steps: number; budget_steps: number }
}

export interface ScenarioStep {
  key: string
  actor: string
  title: string
  technique: string | null
  objective: string
  expected_observables: string[]
  affects_assets: string[]
}

export type Outcome = 'succeeded' | 'prevented' | 'detected'

export interface SimEvent {
  seq: number
  step_key: string
  actor: string
  title: string
  technique: string | null
  objective: string
  prevented: boolean
  allowed: boolean
  detected: boolean
  expected_observables: string[]
  emitted_signals: string[]
  evidence_ids: string[]
  affects_assets: string[]
  state_after: Record<string, boolean>
  outcome: Outcome
  narrative: string
}

export interface Decision {
  decision_id: string
  seq: number
  step_key: string
  agent: string
  input_evidence_ids: string[]
  action: string
  outcome: string
  control: string
  mode: string
  explanation: string
}

export interface MetricComponent {
  value: number
  numerator: number
  denominator: number
  na: boolean
}

export interface Metrics {
  resilience_score: number
  components: Record<string, MetricComponent>
  weights: Record<string, number>
  effective_weights: Record<string, number>
}

export interface Run {
  run_id: string
  scenario_id: string
  scenario_version_hash: string
  seed: number
  kind: 'baseline' | 'replay'
  baseline_run_id: string | null
  config: Record<string, string>
  final_state: Record<string, boolean>
  status: string
  metrics: Metrics
  event_hash: string
  created_at: string | null
  events: SimEvent[]
  decisions: Decision[]
}

export interface RunSummary {
  run_id: string
  scenario_id: string
  kind: 'baseline' | 'replay'
  baseline_run_id: string | null
  status: string
  seed: number
  config: Record<string, string>
  resilience_score: number
  event_hash: string
  created_at: string | null
}

export interface StepDiff {
  step_key: string
  title: string
  technique: string | null
  baseline_outcome: Outcome
  replay_outcome: Outcome
  changed: boolean
  baseline_evidence: string[]
  replay_evidence: string[]
  affects_assets: string[]
}

export interface Comparison {
  id: string
  scenario_id: string
  scenario_version_hash: string
  baseline_run_id: string
  replay_run_id: string
  controls_changed: { control: string; from: string; to: string }[]
  changed_step_keys: string[]
  changed_assets: string[]
  step_diffs: StepDiff[]
  metric_deltas: Record<
    string,
    { baseline: number | null; replay: number | null; delta: number | null; baseline_na?: boolean; replay_na?: boolean }
  >
  improved: boolean
  regressed: boolean
  verdict: string
  residual_risks: string[]
  attribution: { available: boolean; note: string }
  limitations: string[]
}

export interface ReplayResponse {
  replay_run: RunSummary
  comparison: Comparison
}

export interface Dashboard {
  empty: boolean
  message?: string
  total_runs: number
  baseline_runs: number
  replay_runs: number
  avg_resilience: number | null
  latest_resilience: number | null
  detection_coverage: number | null
  containment_coverage: number | null
  recent_runs: {
    run_id: string
    scenario_id: string
    kind: string
    resilience_score: number
    created_at: string | null
  }[]
  recent_reports: { report_id: string; run_id: string; created_at: string | null }[]
  intelligence_core_state: 'idle' | 'threat_active' | 'evaluating' | 'contained'
}

export interface Health {
  status: string
  app: string
  schema_version: number
  llm_enabled: boolean
  llm_mode: string
  mitre_available: boolean
  webgl_note: string
}

export interface MitreTechnique {
  id: string
  name: string
  url: string
  deprecated: boolean
  description?: string
}
