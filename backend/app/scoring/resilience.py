"""Resilience scoring.

Resilience Score (0-100) =
    0.30 * Detection
  + 0.25 * Containment
  + 0.20 * Prevention
  + 0.15 * Response Efficiency
  + 0.10 * Evidence Coverage

Each component is normalized to 0-100 before combining. If a component's
denominator is zero it is marked N/A and its weight is redistributed across the
remaining components (never counted as success, never divides by zero).

All inputs are derived from persisted simulation records (events + decisions).
See docs/METRICS.md for definitions and edge cases.
"""
from __future__ import annotations

from typing import Any

WEIGHTS = {
    "detection": 0.30,
    "containment": 0.25,
    "prevention": 0.20,
    "response_efficiency": 0.15,
    "evidence_coverage": 0.10,
}


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def compute_scores(
    scenario: dict[str, Any],
    events: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute component scores + overall resilience score.

    Returns a dict with per-component ``{value, numerator, denominator, na}`` and
    the overall ``resilience_score`` plus the effective (renormalized) weights.
    """
    step_by_key = {s["key"]: s for s in scenario["steps"]}

    # --- Detection: detected / expected-detectable events ------------------
    det_num = 0
    det_den = 0
    for ev in events:
        step = step_by_key.get(ev["step_key"], {})
        if step.get("detectable"):
            # Only count steps that were actually attempted (reachable).
            if ev["outcome"] != "prevented" or ev["allowed"]:
                det_den += 1
                if ev["detected"]:
                    det_num += 1

    # --- Prevention: blocked / preventable transitions ---------------------
    prev_num = 0
    prev_den = 0
    for ev in events:
        step = step_by_key.get(ev["step_key"], {})
        if step.get("preventable"):
            # A step is a preventable transition only if it was reachable
            # (prerequisites met). Unreached steps are not counted.
            reachable = _was_reachable(ev, events, step_by_key)
            if reachable:
                prev_den += 1
                if ev["prevented"]:
                    prev_num += 1

    # --- Containment: achieved / applicable containment objectives ---------
    cont_num = 0
    cont_den = 0
    for ev in events:
        step = step_by_key.get(ev["step_key"], {})
        if step.get("containment_objective"):
            reachable = _was_reachable(ev, events, step_by_key)
            if reachable:
                cont_den += 1
                if ev["outcome"] in ("prevented", "detected"):
                    cont_num += 1

    # --- Response Efficiency ----------------------------------------------
    scoring = scenario.get("scoring", {})
    optimal = scoring.get("optimal_steps", 1)
    budget = scoring.get("budget_steps", len(scenario["steps"]))
    steps_to_contain = _steps_to_contain(events)
    if steps_to_contain is None:
        resp_eff = 0.0
        resp_na = False  # never contained => worst efficiency, not N/A
        resp_num = 0
        resp_den = 1
    else:
        denom = max(budget - optimal, 1)
        resp_eff = _clamp(1 - (steps_to_contain - optimal) / denom, 0, 1) * 100
        resp_na = False
        resp_num = steps_to_contain
        resp_den = budget

    # --- Evidence Coverage: decisions-with-required-evidence / decisions ---
    # "Required evidence" = a decision that took a containment action must cite
    # at least one evidence id. monitor_only decisions are not required to.
    ev_num = 0
    ev_den = 0
    for d in decisions:
        if d["outcome"] == "contained":
            ev_den += 1
            if d["input_evidence_ids"]:
                ev_num += 1

    components: dict[str, dict[str, Any]] = {
        "detection": _component(det_num, det_den),
        "containment": _component(cont_num, cont_den),
        "prevention": _component(prev_num, prev_den),
        "response_efficiency": {
            "value": round(resp_eff, 2),
            "numerator": resp_num,
            "denominator": resp_den,
            "na": resp_na,
        },
        "evidence_coverage": _component(ev_num, ev_den),
    }

    # Renormalize weights over non-N/A components.
    active = {k: WEIGHTS[k] for k, c in components.items() if not c["na"]}
    total_w = sum(active.values()) or 1.0
    eff_weights = {k: w / total_w for k, w in active.items()}

    overall = 0.0
    for k, w in eff_weights.items():
        overall += components[k]["value"] * w

    return {
        "resilience_score": round(overall, 2),
        "components": components,
        "weights": WEIGHTS,
        "effective_weights": {k: round(v, 4) for k, v in eff_weights.items()},
    }


def _component(num: int, den: int) -> dict[str, Any]:
    if den == 0:
        return {"value": 0.0, "numerator": num, "denominator": 0, "na": True}
    return {"value": round(100.0 * num / den, 2), "numerator": num, "denominator": den, "na": False}


def _was_reachable(ev: dict[str, Any], events: list[dict[str, Any]], step_by_key: dict[str, Any]) -> bool:
    """A step is reachable if all its ``requires`` flags were satisfied.

    We reconstruct reachability from the preceding event state. If the step has
    no requires it is always reachable. For steps with requires, we check the
    state_after of the previous event.
    """
    step = step_by_key.get(ev["step_key"], {})
    requires = step.get("requires", [])
    if not requires:
        return True
    idx = next((i for i, e in enumerate(events) if e["seq"] == ev["seq"]), None)
    if idx is None or idx == 0:
        return all(False for _ in requires)
    prev_state = events[idx - 1]["state_after"]
    return all(prev_state.get(flag, False) for flag in requires)


def _steps_to_contain(events: list[dict[str, Any]]) -> int | None:
    """Sequence number (1-based) of the first step that contained the attack.

    Containment = the earliest step whose outcome is prevented or detected, as
    long as the adversary does not later succeed at reaching its final objective.
    Returns None if the attack chain completed uncontained (the last reachable
    step succeeded).
    """
    contained_seq = None
    for ev in events:
        if ev["outcome"] in ("prevented", "detected"):
            contained_seq = ev["seq"]
            break

    if contained_seq is None:
        return None

    # If any step AFTER the first containment still succeeded, the attack was
    # not actually stopped there - fall through to the next containment.
    for ev in events:
        if ev["seq"] > contained_seq and ev["outcome"] == "succeeded":
            # Look for a later containment that holds.
            later = [
                e["seq"]
                for e in events
                if e["seq"] > ev["seq"] and e["outcome"] in ("prevented", "detected")
            ]
            if later:
                contained_seq = later[0]
            else:
                return None
    return contained_seq
