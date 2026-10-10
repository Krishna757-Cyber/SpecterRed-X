"""Red Agent - Adversarial Scenario Reasoner.

The Red Agent is explanatory only. It selects the next *predefined* scenario
step and describes the simulated adversarial objective, expected observables and
the (conceptual) MITRE ATT&CK mapping. It cannot execute real attacks, generate
executable actions, or mutate simulated state - that authority belongs solely to
the engine/orchestrator.
"""
from __future__ import annotations

from typing import Any


def red_describe(step: dict[str, Any], attempted: bool) -> str:
    """Return a short, factual narrative for the red step.

    ``attempted`` is False when prerequisites were not met (the chain was broken
    upstream), in which case the adversary never reached this step.
    """
    if not attempted:
        return (
            f"Adversary could not attempt '{step['title']}' - a prerequisite "
            f"stage was prevented or contained earlier in the chain."
        )
    technique = step.get("technique")
    tech = f" (maps conceptually to {technique})" if technique else ""
    return f"Red objective{tech}: {step['objective']}"


def red_expected_observables(step: dict[str, Any]) -> list[str]:
    """Ground-truth signals a defender *could* observe for this step."""
    return list(step.get("expected_observables", []))
