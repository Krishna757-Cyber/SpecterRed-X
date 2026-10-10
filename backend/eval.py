"""`make eval` entrypoint - runs every scenario baseline + recommended replay and
writes REAL results to docs/evaluation_report.json. No fabricated numbers.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.scoring.resilience import compute_scores  # noqa: E402
from app.services.comparison import build_comparison  # noqa: E402
from app.simulation import scenarios as scen  # noqa: E402
from app.simulation.engine import run_simulation  # noqa: E402


def _payload(result, scenario) -> dict:
    metrics = compute_scores(scenario, result.events_as_dicts(), result.decisions_as_dicts())
    return {
        "run_id": f"eval_{result.scenario_id}_{result.event_hash[:8]}",
        "config": result.config,
        "events": result.events_as_dicts(),
        "decisions": result.decisions_as_dicts(),
        "metrics": metrics,
        "event_hash": result.event_hash,
    }


def main() -> int:
    report = {"generated_by": "eval.py", "scenarios": []}
    for sid in ("S1", "S2", "S3"):
        scenario = scen.get_scenario(sid)
        base = run_simulation(sid, scen.default_config(sid))
        rec = scenario["recommended_control"]
        replay = run_simulation(sid, {**scen.default_config(sid), **rec})

        base_p = _payload(base, scenario)
        replay_p = _payload(replay, scenario)
        base_p["run_id"] = f"{sid}-baseline"
        replay_p["run_id"] = f"{sid}-replay"
        comparison = build_comparison(scenario, base_p, replay_p)

        # Reproducibility check: run baseline twice, hashes must match.
        base2 = run_simulation(sid, scen.default_config(sid))
        reproducible = base.event_hash == base2.event_hash

        report["scenarios"].append(
            {
                "id": sid,
                "title": scenario["title"],
                "version_hash": scenario["version_hash"],
                "reproducible": reproducible,
                "baseline": {
                    "config": base_p["config"],
                    "resilience_score": base_p["metrics"]["resilience_score"],
                    "components": base_p["metrics"]["components"],
                    "outcomes": [e["outcome"] for e in base_p["events"]],
                    "event_hash": base.event_hash,
                },
                "replay": {
                    "control_changes": rec,
                    "config": replay_p["config"],
                    "resilience_score": replay_p["metrics"]["resilience_score"],
                    "components": replay_p["metrics"]["components"],
                    "outcomes": [e["outcome"] for e in replay_p["events"]],
                    "event_hash": replay.event_hash,
                },
                "delta": round(
                    replay_p["metrics"]["resilience_score"]
                    - base_p["metrics"]["resilience_score"],
                    2,
                ),
                "improved": comparison["improved"],
                "changed_steps": comparison["changed_step_keys"],
                "verdict": comparison["verdict"],
            }
        )

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs")
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "evaluation_report.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Wrote {out_path}")
    for s in report["scenarios"]:
        print(
            f"  {s['id']}: baseline={s['baseline']['resilience_score']:.1f} "
            f"replay={s['replay']['resilience_score']:.1f} "
            f"delta={s['delta']:+.1f} reproducible={s['reproducible']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
