"""Deterministic simulation engine.

This module is the SOLE authority that mutates simulated state. It is pure and
seeded: given the same scenario version, initial config and seed it produces an
identical normalized event sequence (and therefore an identical event hash).

No ``eval``/``exec``, no ``subprocess``/``os.system``, no network calls. Scenario
rules are interpreted through the safe predicate DSL only.

The engine implements the required event lifecycle per step:
    1. Red Agent selects the predefined step.
    2. Engine evaluates preventive controls (prevent_if).
    3. Engine decides prevented vs allowed.
    4. Telemetry is emitted ONLY where its emit_if predicate holds.
    5. Blue Agent evaluates ONLY emitted telemetry.
    6. Blue Agent proposes a permitted action from documented policy.
    7. Engine validates & records the decision.
    8. Engine records event, evidence refs, decision and resulting state.
    9. Next step proceeds per the scenario definition.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

from app.agents.blue_agent import blue_decide
from app.agents.red_agent import red_describe
from app.core.hashing import stable_hash
from app.simulation import scenarios as scen
from app.simulation.predicates import evaluate


@dataclass
class EventRecord:
    seq: int
    step_key: str
    actor: str
    title: str
    technique: str | None
    objective: str
    prevented: bool
    allowed: bool
    detected: bool
    expected_observables: list[str]
    emitted_signals: list[str]
    evidence_ids: list[str]
    affects_assets: list[str]
    state_after: dict[str, bool]
    outcome: str  # "prevented" | "detected" | "succeeded"
    narrative: str

    def to_hashable(self) -> dict[str, Any]:
        """Projection used for the reproducibility hash (no timestamps / db ids)."""
        return {
            "seq": self.seq,
            "step_key": self.step_key,
            "actor": self.actor,
            "technique": self.technique,
            "prevented": self.prevented,
            "allowed": self.allowed,
            "detected": self.detected,
            "emitted_signals": sorted(self.emitted_signals),
            "evidence_ids": self.evidence_ids,
            "outcome": self.outcome,
            "state_after": dict(sorted(self.state_after.items())),
        }

    def to_dict(self) -> dict[str, Any]:
        d = self.to_hashable()
        d.update(
            {
                "title": self.title,
                "objective": self.objective,
                "expected_observables": self.expected_observables,
                "affects_assets": self.affects_assets,
                "narrative": self.narrative,
            }
        )
        return d


@dataclass
class DecisionRecord:
    decision_id: str
    seq: int
    step_key: str
    agent: str  # "blue"
    input_evidence_ids: list[str]
    action: str
    outcome: str
    control: str
    mode: str  # "Deterministic policy" | "LLM-assisted narrative"
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "seq": self.seq,
            "step_key": self.step_key,
            "agent": self.agent,
            "input_evidence_ids": self.input_evidence_ids,
            "action": self.action,
            "outcome": self.outcome,
            "control": self.control,
            "mode": self.mode,
            "explanation": self.explanation,
        }


@dataclass
class SimulationResult:
    scenario_id: str
    scenario_version: str
    scenario_version_hash: str
    seed: int
    config: dict[str, str]
    events: list[EventRecord] = field(default_factory=list)
    decisions: list[DecisionRecord] = field(default_factory=list)
    final_state: dict[str, bool] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    event_hash: str = ""

    def events_as_dicts(self) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self.events]

    def decisions_as_dicts(self) -> list[dict[str, Any]]:
        return [d.to_dict() for d in self.decisions]


def _evidence_id(seq: int, signal: str) -> str:
    """Run-scoped, deterministic evidence id (no wall clock, no random)."""
    return f"EV-{seq:03d}-{signal}"


def run_simulation(scenario_id: str, config: dict[str, str], seed: int = 1337) -> SimulationResult:
    """Execute a scenario deterministically against ``config``.

    ``seed`` is threaded through a local ``random.Random`` so the engine is
    reproducible even if future scenario logic uses randomness. The current
    rules are fully deterministic; the seed is still recorded and hashed-around.
    """
    scenario = scen.get_scenario(scenario_id)
    if scenario is None:
        raise ValueError(f"unknown scenario {scenario_id!r}")

    cfg = scen.validate_config(scenario_id, config)
    rng = random.Random(seed)  # noqa: F841 - reserved for future stochastic rules

    state: dict[str, bool] = {}
    result = SimulationResult(
        scenario_id=scenario_id,
        scenario_version=scenario["version"],
        scenario_version_hash=scenario["version_hash"],
        seed=seed,
        config=cfg,
    )

    seq = 0
    for step in scenario["steps"]:
        seq += 1

        # requires: all prerequisite flags must be set, else the chain stops here.
        requires = step.get("requires", [])
        prerequisites_met = all(state.get(flag, False) for flag in requires)

        ctx_controls = {"controls": cfg, "signals": set(), "flags": {}}

        if not prerequisites_met:
            # The attack chain was broken earlier; this step cannot be attempted.
            prevented = True
            allowed = False
            emitted: list[str] = []
            detected = False
            outcome = "prevented"
            evidence_ids: list[str] = []
            decision = None
            narrative = red_describe(step, attempted=False)
        else:
            # 2-3. Preventive control evaluation.
            prevent = evaluate(step.get("prevent_if"), ctx_controls) if step.get("preventable") else False
            prevented = bool(prevent)
            allowed = not prevented

            # 4. Telemetry emission (only where emit_if holds).
            emitted = []
            evidence_ids = []
            for tele in step.get("telemetry", []):
                if evaluate(tele.get("emit_if"), ctx_controls):
                    emitted.append(tele["signal"])
                    evidence_ids.append(_evidence_id(seq, tele["signal"]))

            # 5-7. Blue agent sees ONLY emitted telemetry.
            flags = {"prevented": prevented, "detected": False}
            blue_ctx = {"controls": cfg, "signals": set(emitted), "flags": flags}
            decision, detected = blue_decide(
                step, seq, emitted, evidence_ids, blue_ctx
            )

            # 8. Determine outcome and apply state transition.
            if prevented:
                outcome = "prevented"
            elif detected:
                outcome = "detected"
            else:
                outcome = "succeeded"
                # Only an un-prevented, un-detected step advances the adversary state.
                for flag in step.get("sets_flags", []):
                    state[flag] = True
            # If detected, we treat the step as contained: adversary state does NOT advance.
            narrative = red_describe(step, attempted=True)

        event = EventRecord(
            seq=seq,
            step_key=step["key"],
            actor=step["actor"],
            title=step["title"],
            technique=step.get("technique"),
            objective=step["objective"],
            prevented=prevented,
            allowed=allowed,
            detected=detected,
            expected_observables=step.get("expected_observables", []),
            emitted_signals=emitted,
            evidence_ids=evidence_ids,
            affects_assets=step.get("affects_assets", []),
            state_after=dict(state),
            outcome=outcome,
            narrative=narrative,
        )
        result.events.append(event)
        if decision is not None:
            result.decisions.append(decision)

    result.final_state = dict(state)

    # Reproducibility hash over normalized events + scenario version + seed + config.
    result.event_hash = stable_hash(
        {
            "scenario_version_hash": scenario["version_hash"],
            "seed": seed,
            "config": dict(sorted(cfg.items())),
            "events": [e.to_hashable() for e in result.events],
        }
    )
    return result
