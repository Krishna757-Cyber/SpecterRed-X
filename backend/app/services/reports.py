"""Report service - builds + persists Markdown/JSON reports from run data."""
from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.db import Comparison, Report
from app.reporting.reporter import build_report_data, render_markdown
from app.services.runs import run_payload
from app.simulation import scenarios as scen


def create_report(db: Session, run_id: str, comparison_id: str | None) -> dict:
    payload = run_payload(db, run_id)
    scenario = scen.get_scenario(payload["scenario_id"])
    if scenario is None:
        raise ValueError(f"scenario for run {run_id} not found")

    comparison = None
    if comparison_id:
        comp = db.get(Comparison, comparison_id)
        comparison = comp.payload if comp else None
    else:
        # Auto-attach a comparison if this run is a replay or has one.
        from app.models.db import Comparison as C
        from sqlalchemy import select, or_

        comp = db.scalar(
            select(C).where(or_(C.replay_run_id == run_id, C.baseline_run_id == run_id))
        )
        if comp:
            comparison = comp.payload
            comparison_id = comp.id

    data = build_report_data(scenario, payload, comparison)
    markdown = render_markdown(data)

    report = Report(
        id=f"rep_{uuid.uuid4().hex[:12]}",
        run_id=run_id,
        comparison_id=comparison_id,
        markdown=markdown,
        data=data,
    )
    db.add(report)
    db.commit()
    return {"report_id": report.id, "run_id": run_id, "comparison_id": comparison_id}


def get_report(db: Session, report_id: str) -> Report | None:
    return db.get(Report, report_id)
