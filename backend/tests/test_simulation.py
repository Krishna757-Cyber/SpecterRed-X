"""Core workflow tests for the SpecterRed X simulation backend."""
from __future__ import annotations

import ast
import os

import pytest

from app.scoring.resilience import compute_scores
from app.simulation import scenarios as scen
from app.simulation.engine import run_simulation
from app.simulation.predicates import PredicateError, evaluate


# --------------------------------------------------------------------------- #
# Scenario definitions & initialization
# --------------------------------------------------------------------------- #
def test_three_scenarios_present():
    ids = {s["id"] for s in scen.all_scenarios()}
    assert ids == {"S1", "S2", "S3"}


def test_default_config_valid():
    for s in scen.all_scenarios():
        cfg = scen.default_config(s["id"])
        assert set(cfg) == set(s["controls"])


def test_scenario_version_hash_stable():
    a = scen.get_scenario("S1")["version_hash"]
    b = scen.get_scenario("S1")["version_hash"]
    assert a == b and len(a) == 64


# --------------------------------------------------------------------------- #
# Predicate DSL
# --------------------------------------------------------------------------- #
def test_predicate_control_in():
    ctx = {"controls": {"mfa_mode": "push"}, "signals": set(), "flags": {}}
    assert evaluate({"control": "mfa_mode", "in": ["push", "phishing_resistant"]}, ctx)
    assert not evaluate({"control": "mfa_mode", "in": ["none"]}, ctx)


def test_predicate_logical():
    ctx = {"controls": {"a": "enabled"}, "signals": {"sig"}, "flags": {"f": True}}
    assert evaluate({"all": [{"control": "a", "eq": "enabled"}, {"signal": "sig"}]}, ctx)
    assert evaluate({"any": [{"const": False}, {"flag": "f"}]}, ctx)
    assert evaluate({"not": {"const": False}}, ctx)


def test_predicate_malformed_raises():
    with pytest.raises(PredicateError):
        evaluate({"bogus": 1}, {"controls": {}, "signals": set(), "flags": {}})


# --------------------------------------------------------------------------- #
# Engine: invalid transitions / control validation
# --------------------------------------------------------------------------- #
def test_invalid_control_rejected():
    with pytest.raises(ValueError):
        run_simulation("S1", {"mfa_mode": "banana"})


def test_unknown_control_rejected():
    with pytest.raises(ValueError):
        run_simulation("S1", {"nonexistent_control": "enabled"})


def test_unknown_scenario_rejected():
    with pytest.raises(ValueError):
        run_simulation("S99", {})


# --------------------------------------------------------------------------- #
# Determinism / reproducibility
# --------------------------------------------------------------------------- #
def test_determinism_identical_hash():
    r1 = run_simulation("S1", scen.default_config("S1"), seed=1337)
    r2 = run_simulation("S1", scen.default_config("S1"), seed=1337)
    assert r1.event_hash == r2.event_hash


def test_different_config_changes_hash():
    base = run_simulation("S1", scen.default_config("S1"))
    changed = run_simulation("S1", {**scen.default_config("S1"), "session_risk_policy": "enabled"})
    assert base.event_hash != changed.event_hash


# --------------------------------------------------------------------------- #
# Blue agent only sees emitted telemetry (no magic signals)
# --------------------------------------------------------------------------- #
def test_blue_only_sees_emitted_telemetry():
    # With all telemetry controls disabled, no detection evidence should exist.
    r = run_simulation("S1", scen.default_config("S1"))
    for ev in r.events:
        if ev.detected:
            # a detected event MUST have emitted signals backing it
            assert ev.emitted_signals, f"step {ev.step_key} detected with no evidence"


# --------------------------------------------------------------------------- #
# Replay changes only the outcomes explained by changed controls
# --------------------------------------------------------------------------- #
def test_recommended_control_improves_or_changes_outcome():
    scenario = scen.get_scenario("S1")
    base = run_simulation("S1", scen.default_config("S1"))
    rec = scenario["recommended_control"]
    replay = run_simulation("S1", {**scen.default_config("S1"), **rec})

    base_metrics = compute_scores(scenario, base.events_as_dicts(), base.decisions_as_dicts())
    replay_metrics = compute_scores(scenario, replay.events_as_dicts(), replay.decisions_as_dicts())
    # Enabling session_risk_policy must change at least one step outcome.
    base_outcomes = {e.step_key: e.outcome for e in base.events}
    replay_outcomes = {e.step_key: e.outcome for e in replay.events}
    assert base_outcomes != replay_outcomes
    assert replay_metrics["resilience_score"] >= base_metrics["resilience_score"]


def test_s2_callback_blocks_payment():
    base = run_simulation("S2", scen.default_config("S2"))
    replay = run_simulation("S2", {**scen.default_config("S2"), "payment_callback_verification": "enabled"})
    base_pay = next(e for e in base.events if e.step_key == "urgent_payment_request")
    replay_pay = next(e for e in replay.events if e.step_key == "urgent_payment_request")
    assert base_pay.outcome == "succeeded"
    assert replay_pay.outcome in ("prevented", "detected")


def test_s3_identity_verification_changes_outcome():
    base = run_simulation("S3", scen.default_config("S3"))
    replay = run_simulation("S3", {**scen.default_config("S3"), "helpdesk_identity_verification": "enabled"})
    base_reset = next(e for e in base.events if e.step_key == "mfa_reset")
    replay_reset = next(e for e in replay.events if e.step_key == "mfa_reset")
    assert base_reset.outcome == "succeeded"
    assert replay_reset.outcome != "succeeded"


# --------------------------------------------------------------------------- #
# Scoring + zero denominators
# --------------------------------------------------------------------------- #
def test_scores_in_range():
    for sid in ("S1", "S2", "S3"):
        scenario = scen.get_scenario(sid)
        r = run_simulation(sid, scen.default_config(sid))
        m = compute_scores(scenario, r.events_as_dicts(), r.decisions_as_dicts())
        assert 0 <= m["resilience_score"] <= 100
        for comp in m["components"].values():
            assert comp["na"] or (0 <= comp["value"] <= 100)


def test_zero_denominator_marks_na_not_zero_division():
    scenario = scen.get_scenario("S1")
    # No decisions and no events -> components should be N/A, not crash.
    m = compute_scores(scenario, [], [])
    assert m["components"]["detection"]["na"] is True
    assert isinstance(m["resilience_score"], float)


# --------------------------------------------------------------------------- #
# Full-defense run should score higher than no-defense run
# --------------------------------------------------------------------------- #
def test_full_defense_beats_no_defense():
    for sid in ("S1", "S2", "S3"):
        scenario = scen.get_scenario(sid)
        no_def = run_simulation(sid, scen.default_config(sid))
        full = {name: spec["values"][-1] for name, spec in scenario["controls"].items()}
        full_run = run_simulation(sid, full)
        m_no = compute_scores(scenario, no_def.events_as_dicts(), no_def.decisions_as_dicts())
        m_full = compute_scores(scenario, full_run.events_as_dicts(), full_run.decisions_as_dicts())
        assert m_full["resilience_score"] >= m_no["resilience_score"]


# --------------------------------------------------------------------------- #
# No LLM config -> deterministic mode
# --------------------------------------------------------------------------- #
def test_no_llm_falls_back_to_deterministic(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    r = run_simulation("S1", scen.default_config("S1"))
    for d in r.decisions:
        assert d.mode == "Deterministic policy"


# --------------------------------------------------------------------------- #
# Sandbox boundaries: no prohibited execution/network primitives in sim/agents
# --------------------------------------------------------------------------- #
def test_no_prohibited_primitives_in_simulation_and_agents():
    roots = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "app", "simulation"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "app", "agents"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "app", "scoring"),
    ]
    banned_calls = {"eval", "exec", "system", "popen"}
    banned_imports = {"subprocess", "socket", "requests", "urllib", "httpx", "http"}
    for root in roots:
        for dirpath, _, files in os.walk(root):
            for fn in files:
                if not fn.endswith(".py"):
                    continue
                path = os.path.join(dirpath, fn)
                with open(path, encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=path)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                        assert node.func.id not in banned_calls, f"{node.func.id} in {path}"
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            top = alias.name.split(".")[0]
                            assert top not in banned_imports, f"import {top} in {path}"
                    if isinstance(node, ast.ImportFrom):
                        top = (node.module or "").split(".")[0]
                        assert top not in banned_imports, f"from {top} in {path}"
