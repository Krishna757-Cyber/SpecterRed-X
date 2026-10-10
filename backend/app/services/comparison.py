"""Counterfactual comparison - honest, event-based diff of baseline vs replay.

Compares two SimulationResult-derived run payloads step-by-step and reports:
 - which steps changed outcome,
 - which controls changed,
 - per-metric deltas,
 - evidence references,
 - residual risks,
 - whether the replay actually improved the result (honest, may be "no").
"""
from __future__ import annotations

from typing import Any


def _controls_changed(baseline_cfg: dict[str, str], replay_cfg: dict[str, str]) -> list[dict[str, str]]:
    changed = []
    for name in sorted(set(baseline_cfg) | set(replay_cfg)):
        b = baseline_cfg.get(name)
        r = replay_cfg.get(name)
        if b != r:
            changed.append({"control": name, "from": b, "to": r})
    return changed


def _residual_risks(scenario: dict[str, Any], replay_events: list[dict[str, Any]]) -> list[str]:
    """Steps that still succeeded in the replay are residual risks."""
    risks = []
    for ev in replay_events:
        if ev["outcome"] == "succeeded":
            risks.append(
                f"Step '{ev['title']}' ({ev['step_key']}) still succeeded - "
                f"adversary objective achieved at this stage."
            )
    if not risks:
        risks.append("No simulated adversary step succeeded in the replay under these controls.")
    return risks


def build_comparison(
    scenario: dict[str, Any],
    baseline: dict[str, Any],
    replay: dict[str, Any],
) -> dict[str, Any]:
    """``baseline``/``replay`` are run payloads: {config, events, decisions, metrics, ...}."""
    b_events = {e["step_key"]: e for e in baseline["events"]}
    r_events = {e["step_key"]: e for e in replay["events"]}

    step_diffs: list[dict[str, Any]] = []
    changed_step_keys: list[str] = []
    changed_assets: set[str] = set()
    for step in scenario["steps"]:
        key = step["key"]
        be = b_events.get(key)
        re = r_events.get(key)
        if be is None or re is None:
            continue
        changed = be["outcome"] != re["outcome"]
        if changed:
            changed_step_keys.append(key)
            changed_assets.update(step.get("affects_assets", []))
        step_diffs.append(
            {
                "step_key": key,
                "title": step["title"],
                "technique": step.get("technique"),
                "baseline_outcome": be["outcome"],
                "replay_outcome": re["outcome"],
                "changed": changed,
                "baseline_evidence": be.get("evidence_ids", []),
                "replay_evidence": re.get("evidence_ids", []),
                "affects_assets": step.get("affects_assets", []),
            }
        )

    # Per-metric deltas.
    b_metrics = baseline["metrics"]
    r_metrics = replay["metrics"]
    metric_deltas: dict[str, Any] = {
        "resilience_score": {
            "baseline": b_metrics["resilience_score"],
            "replay": r_metrics["resilience_score"],
            "delta": round(r_metrics["resilience_score"] - b_metrics["resilience_score"], 2),
        }
    }
    for comp in b_metrics["components"]:
        bc = b_metrics["components"][comp]
        rc = r_metrics["components"][comp]
        metric_deltas[comp] = {
            "baseline": None if bc["na"] else bc["value"],
            "replay": None if rc["na"] else rc["value"],
            "baseline_na": bc["na"],
            "replay_na": rc["na"],
            "delta": None if (bc["na"] or rc["na"]) else round(rc["value"] - bc["value"], 2),
        }

    controls_changed = _controls_changed(baseline["config"], replay["config"])
    improved = r_metrics["resilience_score"] > b_metrics["resilience_score"]
    regressed = r_metrics["resilience_score"] < b_metrics["resilience_score"]

    if improved:
        verdict = (
            f"The replay improved the resilience score by "
            f"{metric_deltas['resilience_score']['delta']} points."
        )
    elif regressed:
        verdict = (
            f"The replay REDUCED the resilience score by "
            f"{abs(metric_deltas['resilience_score']['delta'])} points. "
            f"The selected control change did not help this scenario."
        )
    else:
        verdict = (
            "The replay produced no change in the resilience score. The selected "
            "control did not affect the modeled outcome for this scenario."
        )

    attribution: dict[str, Any]
    if len(controls_changed) <= 1:
        attribution = {
            "available": True,
            "note": "A single control was changed, so the outcome delta is attributable to it.",
        }
    else:
        attribution = {
            "available": False,
            "note": (
                "Multiple controls changed simultaneously. Per-control attribution is "
                "not computed in this comparison; replay each change independently to "
                "attribute individual contributions."
            ),
        }

    return {
        "scenario_id": scenario["id"],
        "scenario_version_hash": scenario["version_hash"],
        "baseline_run_id": baseline["run_id"],
        "replay_run_id": replay["run_id"],
        "controls_changed": controls_changed,
        "changed_step_keys": changed_step_keys,
        "changed_assets": sorted(changed_assets),
        "step_diffs": step_diffs,
        "metric_deltas": metric_deltas,
        "improved": improved,
        "regressed": regressed,
        "verdict": verdict,
        "residual_risks": _residual_risks(scenario, replay["events"]),
        "attribution": attribution,
        "limitations": [
            "This is a deterministic simulation metric, not a certified real-world security rating.",
            "Deterministic replay is reproducible, not a statistical experiment.",
            "A technique mapping denotes conceptual relevance, not proof of a real intrusion.",
        ],
    }
