"""API routes - all endpoints required by the spec."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.mitre.catalog import all_techniques, is_available
from app.models.db import SessionLocal
from app.schemas.api import CreateRunRequest, HealthResponse, ReplayRequest, ReportRequest
from app.services import dashboard as dash
from app.services import reports as report_svc
from app.services import runs as run_svc
from app.simulation import scenarios as scen

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/health", response_model=HealthResponse)
def health():
    s = get_settings()
    return HealthResponse(
        status="ok",
        app=s.app_name,
        schema_version=s.schema_version,
        llm_enabled=s.llm_enabled,
        llm_mode="LLM-assisted narrative" if s.llm_enabled else "Deterministic policy",
        mitre_available=is_available(),
        webgl_note="Core workflow (simulate/replay/compare/report) works without WebGL.",
    )


@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    return dash.build_dashboard(db)


@router.get("/scenarios")
def list_scenarios():
    out = []
    for sc in scen.all_scenarios():
        out.append(
            {
                "id": sc["id"],
                "title": sc["title"],
                "track": sc["track"],
                "description": sc["description"],
                "difficulty": sc["difficulty"],
                "duration_min": sc["duration_min"],
                "defensive_concepts": sc["defensive_concepts"],
                "controls": sc["controls"],
                "recommended_control": sc.get("recommended_control", {}),
                "version": sc["version"],
                "version_hash": sc["version_hash"],
                "step_count": len(sc["steps"]),
            }
        )
    return {"scenarios": out}


@router.get("/scenarios/{scenario_id}")
def get_scenario(scenario_id: str):
    sc = scen.get_scenario(scenario_id)
    if sc is None:
        raise HTTPException(status_code=404, detail=f"scenario {scenario_id} not found")
    return sc


@router.post("/runs", status_code=201)
def create_run(req: CreateRunRequest, db: Session = Depends(get_db)):
    try:
        run = run_svc.create_run(db, req.scenario_id, req.config, seed=req.seed)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return run_svc.run_payload(db, run.id)


@router.get("/runs")
def list_runs(db: Session = Depends(get_db)):
    return {"runs": run_svc.list_runs(db)}


@router.get("/runs/{run_id}")
def get_run(run_id: str, db: Session = Depends(get_db)):
    try:
        return run_svc.run_payload(db, run_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/runs/{run_id}/events")
def get_run_events(run_id: str, db: Session = Depends(get_db)):
    try:
        payload = run_svc.run_payload(db, run_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"run_id": run_id, "events": payload["events"]}


@router.get("/runs/{run_id}/decisions")
def get_run_decisions(run_id: str, db: Session = Depends(get_db)):
    try:
        payload = run_svc.run_payload(db, run_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"run_id": run_id, "decisions": payload["decisions"]}


@router.post("/runs/{run_id}/replay")
def replay(run_id: str, req: ReplayRequest, db: Session = Depends(get_db)):
    try:
        return run_svc.replay_run(db, run_id, req.control_changes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/comparisons/{comparison_id}")
def get_comparison(comparison_id: str, db: Session = Depends(get_db)):
    comp = run_svc.get_comparison(db, comparison_id)
    if comp is None:
        raise HTTPException(status_code=404, detail=f"comparison {comparison_id} not found")
    return comp


@router.post("/runs/{run_id}/report", status_code=201)
def create_report(run_id: str, req: ReportRequest, db: Session = Depends(get_db)):
    try:
        return report_svc.create_report(db, run_id, req.comparison_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/reports/{report_id}.md", response_class=PlainTextResponse)
def get_report_md(report_id: str, db: Session = Depends(get_db)):
    rep = report_svc.get_report(db, report_id)
    if rep is None:
        raise HTTPException(status_code=404, detail=f"report {report_id} not found")
    return PlainTextResponse(
        rep.markdown,
        headers={"Content-Disposition": f'attachment; filename="{report_id}.md"'},
    )


@router.get("/reports/{report_id}.json")
def get_report_json(report_id: str, db: Session = Depends(get_db)):
    rep = report_svc.get_report(db, report_id)
    if rep is None:
        raise HTTPException(status_code=404, detail=f"report {report_id} not found")
    return JSONResponse(
        rep.data,
        headers={"Content-Disposition": f'attachment; filename="{report_id}.json"'},
    )


@router.get("/mitre")
def list_mitre():
    return {"available": is_available(), "techniques": all_techniques()}
