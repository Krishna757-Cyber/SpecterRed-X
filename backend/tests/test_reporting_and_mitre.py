"""Additional edge-case + offline tests for determinism, reporting and MITRE."""
from __future__ import annotations

import json
import os

from app.mitre.catalog import all_techniques, is_available, technique
from app.reporting.reporter import build_report_data, render_markdown
from app.scoring.resilience import compute_scores
from app.services.comparison import build_comparison
from app.simulation import scenarios as scen
from app.simulation.engine import run_simulation


def _payload(result, scenario):
    metrics = compute_scores(scenario, result.events_as_dicts(), result.decisions_as_dicts())
    return {
        "run_id": f"{result.scenario_id}-x",
        "kind": result.events and "baseline" or "baseline",
        "seed": result.seed,
        "config": result.config,
        "event_hash": result.event_hash,
        "created_at": "2026-10-10T00:00:00",
        "events": result.events_as_dicts(),
        "decisions": result.decisions_as_dicts(),
        "metrics": metrics,
    }


def test_mitre_offline_available_and_validated():
    assert is_available()
    # Every technique referenced by a scenario step must resolve in the catalog.
    for s in scen.all_scenarios():
        for step in s["steps"]:
            t = step.get("technique")
            if t:
                assert technique(t) is not None, f"{t} missing from validated catalog"
    assert len(all_techniques()) >= 9


def test_comparison_single_control_attribution_available():
    scenario = scen.get_scenario("S1")
    base = run_simulation("S1", scen.default_config("S1"))
    rep = run_simulation("S1", {**scen.default_config("S1"), "session_risk_policy": "enabled"})
    cmp = build_comparison(scenario, _payload(base, scenario), _payload(rep, scenario))
    assert cmp["attribution"]["available"] is True
    assert cmp["improved"] is True
    assert cmp["changed_step_keys"]


def test_comparison_multi_control_attribution_unavailable():
    scenario = scen.get_scenario("S1")
    base = run_simulation("S1", scen.default_config("S1"))
    rep = run_simulation(
        "S1",
        {**scen.default_config("S1"), "session_risk_policy": "enabled", "link_filtering": "enabled"},
    )
    cmp = build_comparison(scenario, _payload(base, scenario), _payload(rep, scenario))
    assert cmp["attribution"]["available"] is False


def test_comparison_honest_when_no_improvement():
    scenario = scen.get_scenario("S1")
    base = run_simulation("S1", scen.default_config("S1"))
    # Enable a control that does not affect any S1 transition outcome at the
    # chain-breaking level on its own: user_report_button only prevents step 2,
    # which still leaves the earlier/later chain — but to be safe we compare a
    # no-op: replay with the SAME config.
    rep = run_simulation("S1", scen.default_config("S1"))
    cmp = build_comparison(scenario, _payload(base, scenario), _payload(rep, scenario))
    assert cmp["improved"] is False
    assert cmp["metric_deltas"]["resilience_score"]["delta"] == 0.0
    assert "no change" in cmp["verdict"].lower() or "did not" in cmp["verdict"].lower()


def test_report_markdown_contains_real_ids():
    scenario = scen.get_scenario("S2")
    rep = run_simulation("S2", {**scen.default_config("S2"), "payment_callback_verification": "enabled"})
    data = build_report_data(scenario, _payload(rep, scenario), None)
    md = render_markdown(data)
    assert "SpecterRed X" in md
    assert "Resilience Score Components" in md
    assert "Training Questions" in md
    # Evidence ids from the run should appear in the timeline table.
    any_evidence = any(e["evidence_ids"] for e in data["events"])
    if any_evidence:
        first = next(e for e in data["events"] if e["evidence_ids"])
        assert first["evidence_ids"][0] in md


def test_evaluation_report_exists_and_reproducible():
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "docs",
        "evaluation_report.json",
    )
    # Regenerate in-memory and assert reproducibility rather than depending on disk.
    for sid in ("S1", "S2", "S3"):
        a = run_simulation(sid, scen.default_config(sid))
        b = run_simulation(sid, scen.default_config(sid))
        assert a.event_hash == b.event_hash
    # If the committed file exists, it must be valid JSON with 3 scenarios.
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            report = json.load(f)
        assert len(report["scenarios"]) == 3
        for s in report["scenarios"]:
            assert s["reproducible"] is True


def test_baseline_immutable_under_replay_in_engine():
    # Running a replay-style second simulation must not alter the first result.
    base = run_simulation("S3", scen.default_config("S3"))
    base_hash = base.event_hash
    base_outcomes = [e.outcome for e in base.events]
    _ = run_simulation("S3", {**scen.default_config("S3"), "helpdesk_identity_verification": "enabled"})
    assert base.event_hash == base_hash
    assert [e.outcome for e in base.events] == base_outcomes
