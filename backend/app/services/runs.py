"""Run service - the orchestration + persistence authority.

Creates baseline runs, replays (preserving the immutable baseline), builds
comparisons, and assembles run payloads from persisted records. This is the only
place that writes Run/Event/AgentDecision/Comparison rows.
"""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.db import AgentDecision, Comparison, Event, Run
from app.scoring.resilience import compute_scores
from app.services.comparison import build_comparison
from app.simulation import scenarios as scen
from app.simulation.engine import run_simulation


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _persist_run(
    db: Session,
    *,
    scenario: dict[str, Any],
    config: dict[str, str],
    seed: int,
    kind: str,
    baseline_run_id: str | None,
) -> Run:
    result = run_simulation(scenario["id"], config, seed=seed)
    metrics = compute_scores(scenario, result.events_as_dicts(), result.decisions_as_dicts())

    run = Run(
        id=_new_id("run"),
        scenario_id=scenario["id"],
        scenario_version_hash=result.scenario_version_hash,
        seed=seed,
        kind=kind,
        baseline_run_id=baseline_run_id,
        initial_config=result.config,
        final_state=result.final_state,
        status="completed",
        metrics=metrics,
        event_hash=result.event_hash,
    )
    db.add(run)
    db.flush()  # assign run.id for FKs

    for ev in result.events:
        db.add(Event(run_id=run.id, seq=ev.seq, step_key=ev.step_key, payload=ev.to_dict()))
    for dec in result.decisions:
        db.add(
            AgentDecision(
                run_id=run.id, seq=dec.seq, decision_id=dec.decision_id, payload=dec.to_dict()
            )
        )
    db.commit()
    return run


def create_run(db: Session, scenario_id: str, config: dict[str, str] | None, seed: int = 1337) -> Run:
    scenario = scen.get_scenario(scenario_id)
    if scenario is None:
        raise ValueError(f"unknown scenario {scenario_id!r}")
    cfg = scen.validate_config(scenario_id, config or {})
    return _persist_run(
        db, scenario=scenario, config=cfg, seed=seed, kind="baseline", baseline_run_id=None
    )


def replay_run(db: Session, baseline_run_id: str, control_changes: dict[str, str]) -> dict[str, Any]:
    """Replay a baseline with ``control_changes`` applied. Baseline stays immutable."""
    baseline = db.get(Run, baseline_run_id)
    if baseline is None:
        raise ValueError(f"unknown baseline run {baseline_run_id!r}")

    scenario = scen.get_scenario(baseline.scenario_id)
    if scenario is None:
        raise ValueError(f"scenario {baseline.scenario_id!r} not found")

    # Validate control changes against allowed values; merge onto baseline config.
    new_cfg = dict(baseline.initial_config)
    for name, value in (control_changes or {}).items():
        if name not in scenario["controls"]:
            raise ValueError(f"unknown control {name!r} for scenario {scenario['id']}")
        allowed = scenario["controls"][name]["values"]
        if value not in allowed:
            raise ValueError(f"invalid value {value!r} for control {name!r}; allowed: {allowed}")
        new_cfg[name] = value

    # Same scenario version, same initial snapshot basis, same seed.
    replay = _persist_run(
        db,
        scenario=scenario,
        config=new_cfg,
        seed=baseline.seed,
        kind="replay",
        baseline_run_id=baseline.id,
    )

    baseline_payload = run_payload(db, baseline.id)
    replay_payload = run_payload(db, replay.id)
    comparison = build_comparison(scenario, baseline_payload, replay_payload)

    comp_id = _new_id("cmp")
    comparison["id"] = comp_id
    db.add(
        Comparison(
            id=comp_id,
            baseline_run_id=baseline.id,
            replay_run_id=replay.id,
            payload=comparison,
        )
    )
    db.commit()

    return {"replay_run": _run_summary(replay), "comparison": comparison}


def run_payload(db: Session, run_id: str) -> dict[str, Any]:
    run = db.get(Run, run_id)
    if run is None:
        raise ValueError(f"unknown run {run_id!r}")
    events = [e.payload for e in sorted(run.events, key=lambda x: x.seq)]
    decisions = [d.payload for d in sorted(run.decisions, key=lambda x: x.seq)]
    return {
        "run_id": run.id,
        "scenario_id": run.scenario_id,
        "scenario_version_hash": run.scenario_version_hash,
        "seed": run.seed,
        "kind": run.kind,
        "baseline_run_id": run.baseline_run_id,
        "config": run.initial_config,
        "final_state": run.final_state,
        "status": run.status,
        "metrics": run.metrics,
        "event_hash": run.event_hash,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "events": events,
        "decisions": decisions,
    }


def _run_summary(run: Run) -> dict[str, Any]:
    return {
        "run_id": run.id,
        "scenario_id": run.scenario_id,
        "kind": run.kind,
        "baseline_run_id": run.baseline_run_id,
        "status": run.status,
        "seed": run.seed,
        "config": run.initial_config,
        "resilience_score": run.metrics.get("resilience_score"),
        "event_hash": run.event_hash,
        "created_at": run.created_at.isoformat() if run.created_at else None,
    }


def list_runs(db: Session) -> list[dict[str, Any]]:
    runs = db.scalars(select(Run).order_by(Run.created_at.desc())).all()
    return [_run_summary(r) for r in runs]


def get_comparison(db: Session, comparison_id: str) -> dict[str, Any] | None:
    comp = db.get(Comparison, comparison_id)
    return comp.payload if comp else None
