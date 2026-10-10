"""API + persistence tests using FastAPI TestClient and a temp SQLite DB."""
from __future__ import annotations

import importlib
import os
import tempfile

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch, tmp_path):
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("SPECTERRED_DB_URL", f"sqlite:///{db_file.as_posix()}")

    # Reload config + db modules so they pick up the temp DB URL.
    import app.core.config as config

    config.get_settings.cache_clear()
    import app.models.db as db

    importlib.reload(db)
    import app.services.runs as runs

    importlib.reload(runs)
    import app.services.reports as reports

    importlib.reload(reports)
    import app.services.dashboard as dashboard

    importlib.reload(dashboard)
    import app.api.routes as routes

    importlib.reload(routes)
    import app.main as main

    importlib.reload(main)

    with TestClient(main.app) as c:
        yield c, db


def test_health(client):
    c, _ = client
    r = c.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["llm_enabled"] is False
    assert body["llm_mode"] == "Deterministic policy"


def test_list_scenarios(client):
    c, _ = client
    r = c.get("/scenarios")
    assert r.status_code == 200
    assert len(r.json()["scenarios"]) == 3


def test_full_workflow_create_replay_compare_report(client):
    c, _ = client

    # 1. Create a baseline run (all defenses off by default)
    r = c.post("/runs", json={"scenario_id": "S1"})
    assert r.status_code == 201, r.text
    baseline = r.json()
    baseline_id = baseline["run_id"]
    assert baseline["kind"] == "baseline"
    assert len(baseline["events"]) == 5

    # 2. Events + decisions endpoints
    assert c.get(f"/runs/{baseline_id}/events").json()["events"]
    assert c.get(f"/runs/{baseline_id}/decisions").status_code == 200

    # 3. Replay with the recommended control change
    r = c.post(f"/runs/{baseline_id}/replay", json={"control_changes": {"session_risk_policy": "enabled"}})
    assert r.status_code == 200, r.text
    replay_resp = r.json()
    comparison = replay_resp["comparison"]
    replay_id = replay_resp["replay_run"]["run_id"]
    assert replay_id != baseline_id

    # 4. Baseline immutability: baseline event_hash unchanged after replay
    baseline_after = c.get(f"/runs/{baseline_id}").json()
    assert baseline_after["event_hash"] == baseline["event_hash"]
    assert baseline_after["kind"] == "baseline"

    # 5. Comparison shows changed steps + metric deltas
    assert comparison["changed_step_keys"], "expected at least one changed step"
    assert "resilience_score" in comparison["metric_deltas"]

    # 6. Fetch comparison by id
    assert c.get(f"/comparisons/{comparison['id']}").status_code == 200

    # 7. Report generation (md + json)
    r = c.post(f"/runs/{replay_id}/report", json={"comparison_id": comparison["id"]})
    assert r.status_code == 201, r.text
    report_id = r.json()["report_id"]

    md = c.get(f"/reports/{report_id}.md")
    assert md.status_code == 200
    assert "SpecterRed X" in md.text
    assert "attachment" in md.headers.get("content-disposition", "")

    js = c.get(f"/reports/{report_id}.json")
    assert js.status_code == 200
    assert js.json()["run"]["run_id"] == replay_id


def test_invalid_replay_control_rejected(client):
    c, _ = client
    baseline = c.post("/runs", json={"scenario_id": "S1"}).json()
    r = c.post(f"/runs/{baseline['run_id']}/replay", json={"control_changes": {"mfa_mode": "banana"}})
    assert r.status_code == 400


def test_invalid_scenario_rejected(client):
    c, _ = client
    r = c.post("/runs", json={"scenario_id": "DOES_NOT_EXIST"})
    assert r.status_code == 400


def test_persistence_across_restart(client, monkeypatch):
    c, db = client
    baseline = c.post("/runs", json={"scenario_id": "S2"}).json()
    run_id = baseline["run_id"]

    # Simulate a restart: new session against the same DB file.
    import app.services.runs as runs

    with db.SessionLocal() as session:
        payload = runs.run_payload(session, run_id)
    assert payload["run_id"] == run_id
    assert len(payload["events"]) == 4


def test_dashboard_empty_then_populated(client):
    c, _ = client
    empty = c.get("/dashboard").json()
    assert empty["empty"] is True
    c.post("/runs", json={"scenario_id": "S1"})
    populated = c.get("/dashboard").json()
    assert populated["empty"] is False
    assert populated["total_runs"] >= 1
