"""Dashboard aggregation - all values derived from persisted runs."""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.db import Report, Run


def build_dashboard(db: Session) -> dict[str, Any]:
    runs = db.scalars(select(Run).order_by(Run.created_at.desc())).all()
    total = len(runs)

    if total == 0:
        return {
            "empty": True,
            "message": "No simulations have been run yet. Start a scenario to populate the dashboard.",
            "total_runs": 0,
            "baseline_runs": 0,
            "replay_runs": 0,
            "avg_resilience": None,
            "latest_resilience": None,
            "detection_coverage": None,
            "containment_coverage": None,
            "recent_runs": [],
            "recent_reports": [],
            "intelligence_core_state": "idle",
        }

    scores = [r.metrics.get("resilience_score", 0.0) for r in runs]
    avg = round(sum(scores) / len(scores), 2)

    latest = runs[0]
    latest_comp = latest.metrics.get("components", {})

    def _coverage(name: str) -> float | None:
        vals = []
        for r in runs:
            c = r.metrics.get("components", {}).get(name)
            if c and not c["na"]:
                vals.append(c["value"])
        return round(sum(vals) / len(vals), 2) if vals else None

    # Intelligence core state follows the latest run's result.
    final_state = latest.final_state or {}
    if any(k.startswith("account") and v for k, v in final_state.items()) or final_state.get("funds_transferred"):
        core = "threat_active"  # adversary achieved objective
    elif latest.metrics.get("resilience_score", 0) >= 70:
        core = "contained"
    else:
        core = "evaluating"

    recent_reports = db.scalars(select(Report).order_by(Report.created_at.desc()).limit(5)).all()

    return {
        "empty": False,
        "total_runs": total,
        "baseline_runs": sum(1 for r in runs if r.kind == "baseline"),
        "replay_runs": sum(1 for r in runs if r.kind == "replay"),
        "avg_resilience": avg,
        "latest_resilience": latest.metrics.get("resilience_score"),
        "detection_coverage": _coverage("detection"),
        "containment_coverage": _coverage("containment"),
        "recent_runs": [
            {
                "run_id": r.id,
                "scenario_id": r.scenario_id,
                "kind": r.kind,
                "resilience_score": r.metrics.get("resilience_score"),
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in runs[:8]
        ],
        "recent_reports": [
            {"report_id": rep.id, "run_id": rep.run_id, "created_at": rep.created_at.isoformat() if rep.created_at else None}
            for rep in recent_reports
        ],
        "intelligence_core_state": core,
    }
