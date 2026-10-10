# SpecterRed X — Metrics

All displayed metrics are derived from **persisted simulation records** (events + agent decisions). Nothing is hard-coded in the frontend.

## Resilience Score

```
Resilience Score (0–100) =
    0.30 · Detection
  + 0.25 · Containment
  + 0.20 · Prevention
  + 0.15 · Response Efficiency
  + 0.10 · Evidence Coverage
```

Each component is normalized to 0–100 **before** combining.

## Component definitions

### Detection — weight 0.30
`detected / expected-detectable events`

- Denominator: events whose scenario step is marked `detectable` **and** that were actually reachable/attempted (an unreached step contributes nothing).
- Numerator: of those, the events the Blue Agent `detected` (i.e. emitted telemetry matched a documented detection rule).

### Containment — weight 0.25
`achieved / applicable containment objectives`

- Denominator: reachable steps whose scenario definition sets `containment_objective: true`.
- Numerator: of those, steps whose outcome is `prevented` or `detected`.

### Prevention — weight 0.20
`blocked / preventable transitions`

- Denominator: reachable steps marked `preventable: true`.
- Numerator: of those, steps whose outcome is `prevented` (a preventive control blocked the transition).

### Response Efficiency — weight 0.15
```
clamp(1 − (steps_to_contain − optimal_steps) / (budget_steps − optimal_steps), 0, 1) × 100
```

- `steps_to_contain` = sequence number of the earliest step that contained the attack and after which the adversary did not succeed again.
- `optimal_steps` and `budget_steps` come from the scenario's `scoring` block.
- If the attack was **never** contained, Response Efficiency = 0 (not N/A): failing to contain is a real, worst-case result, not missing data.

### Evidence Coverage — weight 0.10
`containment decisions with ≥1 cited evidence id / containment decisions`

- Only decisions that took a containment action are counted. `monitor_only` decisions are not required to cite evidence and are excluded from the denominator.

## Normalization

Each component value is a percentage in [0, 100]. Division results are rounded to 2 decimals. The overall score is the weighted sum using the (possibly renormalized) effective weights, rounded to 2 decimals.

## Zero-denominator behavior

If a component's denominator is **0**, that component is marked **N/A** (`na: true`, `value: 0.0`) and its weight is **redistributed proportionally** across the remaining non-N/A components. Concretely:

```
effective_weight[k] = weight[k] / sum(weight over non-N/A components)
overall = Σ (component_value[k] × effective_weight[k])  for non-N/A k
```

This guarantees:
- No division by zero.
- Missing data is never silently counted as success (a 0/0 component does not contribute a 0 that drags the score down, nor a 100 that inflates it — it simply drops out and the others are reweighted).

If *every* component is N/A (e.g. an empty event list), the overall score is `0.0` and all components report N/A.

## Replay comparison rules

- A replay re-runs the **same scenario version hash + seed** with validated control changes merged onto the baseline config.
- Per-step diff: a step is `changed` when `baseline_outcome != replay_outcome`.
- Per-metric deltas: `replay − baseline`; if either side is N/A the delta is reported as `null`.
- `improved` / `regressed` are based strictly on the overall resilience-score delta. A non-positive delta is reported honestly ("the selected control did not help this scenario").
- **Attribution:** when exactly one control changed, the outcome delta is attributable to it. When multiple controls change simultaneously, attribution is reported as *unavailable* and the UI advises replaying each change independently. We never invent causality.

## Recorded evaluation results

Produced by `backend/eval.py` → `docs/evaluation_report.json` (deterministic; identical inputs reproduce identical event hashes). Baseline uses all controls at their defaults (disabled / `none`); replay applies each scenario's single recommended control.

| Scenario | Baseline | Replay (recommended control) | Δ | Reproducible |
|---|---|---|---|---|
| S1 — Phishing → Account Takeover | 0.0 | 48.33 (`session_risk_policy=enabled`) | +48.33 | ✓ |
| S2 — Executive Invoice Impersonation | 0.0 | 34.17 (`payment_callback_verification=enabled`) | +34.17 | ✓ |
| S3 — Help-Desk Voice-Clone | 0.0 | 70.0 (`helpdesk_identity_verification=enabled`) | +70.0 | ✓ |

> These are **synthetic simulation outcomes**, not real-world measurements. A baseline of 0.0 reflects that with all defenses disabled, every modeled adversary step succeeds and no telemetry is observable — exactly the point the counterfactual replay then improves on.

## Limitations & edge cases

- **False positives are not modeled** in the current scenarios; detection reflects true-positive telemetry only. This is a known simplification.
- **Missing telemetry** is handled explicitly: if a telemetry control is disabled, the signal is not emitted and the Blue Agent has nothing to act on (it records `monitor_only` with an explanation). It never "magically" sees an un-emitted signal.
- **Incompatible comparisons:** comparisons are only meaningful between a baseline and a replay of the *same* scenario version hash. The replay endpoint enforces this by construction (a replay always derives from one baseline).
- The score is **scenario-specific** and should not be compared across different scenarios as if it were a universal rating.
