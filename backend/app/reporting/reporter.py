"""Reporter - evidence and learning.

Produces Markdown and JSON reports strictly from persisted run data. Links every
conclusion to actual event/decision/evidence ids. Generates scenario-specific
training questions whose answer keys are derived from the simulation records.
"""
from __future__ import annotations

from typing import Any

from app.mitre.catalog import technique as mitre_technique


def _fmt_pct(component: dict[str, Any]) -> str:
    if component["na"]:
        return "N/A"
    return f"{component['value']:.1f} ({component['numerator']}/{component['denominator']})"


def build_training_questions(scenario: dict[str, Any], run_payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Derive 3 training questions whose answers come from the engine, not an LLM."""
    questions: list[dict[str, Any]] = []
    events = {e["step_key"]: e for e in run_payload["events"]}

    # Q1: which stage first contained (or failed to contain) the attack?
    contained = next(
        (e for e in run_payload["events"] if e["outcome"] in ("prevented", "detected")), None
    )
    if contained:
        answer = f"{contained['title']} ({contained['step_key']})"
    else:
        answer = "No stage contained the attack - the chain completed."
    questions.append(
        {
            "id": "Q1",
            "prompt": "At which simulated stage was the attack first prevented or detected?",
            "answer": answer,
            "derived_from": "earliest event with outcome prevented/detected",
        }
    )

    # Q2: which control, if enabled, blocks the final objective?
    final_step = scenario["steps"][-1]
    rec = scenario.get("recommended_control", {})
    rec_str = ", ".join(f"{k}={v}" for k, v in rec.items()) or "see scenario controls"
    questions.append(
        {
            "id": "Q2",
            "prompt": f"Which defensive control most directly changes the outcome of '{final_step['title']}'?",
            "answer": rec_str,
            "derived_from": "scenario recommended_control + prevent_if predicate",
        }
    )

    # Q3: how many adversary steps succeeded in this run?
    succeeded = [e for e in run_payload["events"] if e["outcome"] == "succeeded"]
    questions.append(
        {
            "id": "Q3",
            "prompt": "How many simulated adversary steps succeeded in this run?",
            "answer": str(len(succeeded)),
            "derived_from": "count of events with outcome=succeeded",
        }
    )
    return questions


def build_report_data(
    scenario: dict[str, Any],
    run_payload: dict[str, Any],
    comparison: dict[str, Any] | None,
) -> dict[str, Any]:
    metrics = run_payload["metrics"]
    failed_controls: list[dict[str, Any]] = []
    recommendations: list[dict[str, Any]] = []

    for ev in run_payload["events"]:
        if ev["outcome"] == "succeeded":
            step = next((s for s in scenario["steps"] if s["key"] == ev["step_key"]), {})
            blue = step.get("blue", {})
            ctrl = blue.get("control")
            failed_controls.append(
                {
                    "step_key": ev["step_key"],
                    "title": ev["title"],
                    "technique": ev.get("technique"),
                    "control": ctrl,
                    "reason": (
                        "No preventive control blocked this transition and no telemetry "
                        "triggered a detection under the current configuration."
                    ),
                }
            )
            if ctrl:
                allowed = scenario["controls"].get(ctrl, {}).get("values", [])
                strongest = allowed[-1] if allowed else "enabled"
                recommendations.append(
                    {
                        "control": ctrl,
                        "suggested_value": strongest,
                        "rationale": f"Enabling '{ctrl}' addresses the '{ev['title']}' stage.",
                        "evidence_step": ev["step_key"],
                    }
                )

    techniques = []
    seen = set()
    for ev in run_payload["events"]:
        t = ev.get("technique")
        if t and t not in seen:
            seen.add(t)
            info = mitre_technique(t)
            if info:
                techniques.append(info)

    return {
        "scenario": {
            "id": scenario["id"],
            "title": scenario["title"],
            "version": scenario["version"],
            "version_hash": scenario["version_hash"],
            "track": scenario["track"],
        },
        "run": {
            "run_id": run_payload["run_id"],
            "kind": run_payload["kind"],
            "seed": run_payload["seed"],
            "config": run_payload["config"],
            "event_hash": run_payload["event_hash"],
            "created_at": run_payload["created_at"],
        },
        "metrics": metrics,
        "events": run_payload["events"],
        "decisions": run_payload["decisions"],
        "failed_controls": failed_controls,
        "recommendations": recommendations,
        "techniques": techniques,
        "comparison": comparison,
        "training_questions": build_training_questions(scenario, run_payload),
        "limitations": [
            "The resilience score is a scenario-specific simulation metric, not a certified real-world security rating.",
            "All people, domains, identities and organizations are synthetic (.example).",
            "Technique mappings denote conceptual relevance, not proof of a real intrusion.",
            "Deterministic replay is reproducible; it is not a statistical experiment.",
        ],
    }


def render_markdown(data: dict[str, Any]) -> str:
    sc = data["scenario"]
    run = data["run"]
    m = data["metrics"]
    lines: list[str] = []
    lines.append(f"# SpecterRed X - Resilience Report")
    lines.append("")
    lines.append(f"**Scenario:** {sc['title']} (`{sc['id']}` v{sc['version']})  ")
    lines.append(f"**Track:** {sc['track']}  ")
    lines.append(f"**Run:** `{run['run_id']}` ({run['kind']}), seed `{run['seed']}`  ")
    lines.append(f"**Event hash:** `{run['event_hash'][:16]}...`  ")
    lines.append(f"**Generated:** {run['created_at']}")
    lines.append("")
    lines.append("> Synthetic simulation. The resilience score is a scenario-specific "
                 "simulation metric, not a certified real-world security rating.")
    lines.append("")

    lines.append("## Executive Summary")
    lines.append("")
    succeeded = [e for e in data["events"] if e["outcome"] == "succeeded"]
    contained = [e for e in data["events"] if e["outcome"] in ("prevented", "detected")]
    lines.append(
        f"The simulation executed {len(data['events'])} ordered steps. "
        f"{len(contained)} were prevented or detected; {len(succeeded)} adversary "
        f"step(s) succeeded. Overall resilience score: **{m['resilience_score']:.1f}/100**."
    )
    lines.append("")

    lines.append("## Resilience Score Components")
    lines.append("")
    lines.append("| Component | Weight | Score |")
    lines.append("|---|---|---|")
    for comp, w in m["weights"].items():
        lines.append(f"| {comp.replace('_',' ').title()} | {w:.2f} | {_fmt_pct(m['components'][comp])} |")
    lines.append(f"| **Resilience Score** |  | **{m['resilience_score']:.1f}** |")
    lines.append("")

    lines.append("## Event Timeline")
    lines.append("")
    lines.append("| # | Step | Technique | Outcome | Evidence |")
    lines.append("|---|---|---|---|---|")
    for ev in data["events"]:
        evid = ", ".join(ev.get("evidence_ids", [])) or "-"
        lines.append(
            f"| {ev['seq']} | {ev['title']} | {ev.get('technique') or '-'} | "
            f"**{ev['outcome']}** | {evid} |"
        )
    lines.append("")

    lines.append("## Agent Decisions")
    lines.append("")
    if data["decisions"]:
        for d in data["decisions"]:
            lines.append(
                f"- `{d['decision_id']}` (step `{d['step_key']}`, mode: {d['mode']}): "
                f"**{d['action']}** -> {d['outcome']}. Evidence: "
                f"{', '.join(d['input_evidence_ids']) or 'none'}. {d['explanation']}"
            )
    else:
        lines.append("_No agent decisions recorded._")
    lines.append("")

    if data["failed_controls"]:
        lines.append("## Failed / Missing Controls")
        lines.append("")
        for fc in data["failed_controls"]:
            lines.append(f"- **{fc['title']}** ({fc.get('technique') or 'n/a'}): {fc['reason']} "
                         f"Relevant control: `{fc.get('control') or 'n/a'}`.")
        lines.append("")

    if data["recommendations"]:
        lines.append("## Evidence-Supported Recommendations")
        lines.append("")
        for r in data["recommendations"]:
            lines.append(f"- Set `{r['control']}` = `{r['suggested_value']}` - {r['rationale']} "
                         f"(evidence step: `{r['evidence_step']}`)")
        lines.append("")

    if data.get("comparison"):
        c = data["comparison"]
        lines.append("## Counterfactual Comparison")
        lines.append("")
        lines.append(f"**Baseline:** `{c['baseline_run_id']}` -> **Replay:** `{c['replay_run_id']}`")
        lines.append("")
        if c["controls_changed"]:
            lines.append("Controls changed:")
            for cc in c["controls_changed"]:
                lines.append(f"- `{cc['control']}`: `{cc['from']}` -> `{cc['to']}`")
            lines.append("")
        lines.append(f"**Verdict:** {c['verdict']}")
        lines.append("")
        rs = c["metric_deltas"]["resilience_score"]
        lines.append(f"Resilience: {rs['baseline']:.1f} -> {rs['replay']:.1f} (Δ {rs['delta']:+.1f})")
        lines.append("")
        changed = [d for d in c["step_diffs"] if d["changed"]]
        if changed:
            lines.append("Steps whose outcome changed:")
            for d in changed:
                lines.append(f"- `{d['step_key']}` ({d['title']}): "
                             f"{d['baseline_outcome']} -> {d['replay_outcome']}")
            lines.append("")
        lines.append("Residual risks:")
        for rr in c["residual_risks"]:
            lines.append(f"- {rr}")
        lines.append("")
        lines.append(f"_Attribution: {c['attribution']['note']}_")
        lines.append("")

    if data["techniques"]:
        lines.append("## MITRE ATT&CK Mappings (conceptual)")
        lines.append("")
        for t in data["techniques"]:
            lines.append(f"- [{t['id']}]({t.get('url','')}) - {t['name']}")
        lines.append("")
        lines.append("_" + mitre_attribution() + "_")
        lines.append("")

    lines.append("## Training Questions")
    lines.append("")
    for q in data["training_questions"]:
        lines.append(f"- **{q['id']}. {q['prompt']}**  ")
        lines.append(f"  Answer: {q['answer']}  _(derived from: {q['derived_from']})_")
    lines.append("")

    lines.append("## Limitations")
    lines.append("")
    for lim in data["limitations"]:
        lines.append(f"- {lim}")
    lines.append("")
    return "\n".join(lines)


def mitre_attribution() -> str:
    from app.mitre.catalog import ATTRIBUTION

    return ATTRIBUTION
