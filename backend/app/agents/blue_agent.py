"""Blue Agent - Defensive Reasoner.

The Blue Agent evaluates ONLY the synthetic telemetry actually emitted for a
step (passed in via ``context['signals']``). It applies the documented detection
policy (``step['blue']['detect_if']``) and, when it fires, selects the permitted
simulated defensive action. Every decision cites real evidence ids.

A missing detection signal can NOT appear here: the engine only passes emitted
signals, and the predicate can only reference those. The agent never invents
evidence and never mutates state.
"""
from __future__ import annotations

from typing import Any

from app.simulation.predicates import evaluate

MODE_DETERMINISTIC = "Deterministic policy"


def blue_decide(
    step: dict[str, Any],
    seq: int,
    emitted_signals: list[str],
    evidence_ids: list[str],
    context: dict[str, Any],
) -> tuple[Any, bool]:
    """Return ``(DecisionRecord | None, detected: bool)``.

    Imported lazily inside the engine to avoid a circular import at module load.
    """
    from app.simulation.engine import DecisionRecord  # local import avoids cycle

    blue = step.get("blue")
    if not blue:
        return None, False

    detected = evaluate(blue.get("detect_if"), context)

    if detected:
        action = blue["action"]
        outcome = "contained"
        explanation = blue["explain"]
    else:
        action = "monitor_only"
        outcome = "no_action"
        if emitted_signals:
            explanation = (
                "Telemetry present but did not match a documented detection rule; "
                "continued monitoring."
            )
        else:
            explanation = (
                "No telemetry was observable for this step under the current "
                "controls; the Blue Agent had no evidence to act on."
            )

    decision = DecisionRecord(
        decision_id=f"DEC-{seq:03d}",
        seq=seq,
        step_key=step["key"],
        agent="blue",
        input_evidence_ids=list(evidence_ids),
        action=action,
        outcome=outcome,
        control=blue.get("control", ""),
        mode=MODE_DETERMINISTIC,
        explanation=explanation,
    )
    return decision, detected
