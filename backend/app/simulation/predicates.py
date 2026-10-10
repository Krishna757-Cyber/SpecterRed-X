"""A small, safe JSON predicate DSL.

The engine evaluates scenario rules through this evaluator ONLY. There is no
``eval``/``exec`` and no dynamic code generation anywhere in this module.

Supported predicate forms (all are plain dicts)::

    {"const": true}                      -> literal boolean
    {"control": "mfa_mode", "in": [..]}  -> config[control] in list
    {"control": "x", "eq": "enabled"}    -> config[control] == value
    {"signal": "mfa_fatigue_alert"}      -> signal present in emitted set
    {"flag": "prevented"}                -> truthy flag in context
    {"all": [p1, p2, ...]}               -> logical AND
    {"any": [p1, p2, ...]}               -> logical OR
    {"not": p}                           -> logical NOT

Evaluation context::

    {"controls": {name: value}, "signals": set[str], "flags": {name: bool}}
"""
from __future__ import annotations

from typing import Any, Mapping


class PredicateError(ValueError):
    """Raised when a predicate is malformed."""


def evaluate(predicate: Mapping[str, Any] | None, context: Mapping[str, Any]) -> bool:
    """Evaluate ``predicate`` against ``context`` and return a bool.

    A ``None`` predicate evaluates to ``False`` (no rule => does not fire).
    """
    if predicate is None:
        return False
    if not isinstance(predicate, Mapping):
        raise PredicateError(f"predicate must be an object, got {type(predicate)!r}")

    controls: Mapping[str, Any] = context.get("controls", {})
    signals = context.get("signals", set())
    flags: Mapping[str, Any] = context.get("flags", {})

    # Exactly one top-level key is expected.
    if "const" in predicate:
        return bool(predicate["const"])

    if "control" in predicate:
        name = predicate["control"]
        value = controls.get(name)
        if "in" in predicate:
            allowed = predicate["in"]
            if not isinstance(allowed, (list, tuple)):
                raise PredicateError("'in' must be a list")
            return value in allowed
        if "eq" in predicate:
            return value == predicate["eq"]
        raise PredicateError("'control' predicate needs 'in' or 'eq'")

    if "signal" in predicate:
        return predicate["signal"] in signals

    if "flag" in predicate:
        return bool(flags.get(predicate["flag"], False))

    if "all" in predicate:
        parts = predicate["all"]
        if not isinstance(parts, (list, tuple)):
            raise PredicateError("'all' must be a list")
        return all(evaluate(p, context) for p in parts)

    if "any" in predicate:
        parts = predicate["any"]
        if not isinstance(parts, (list, tuple)):
            raise PredicateError("'any' must be a list")
        return any(evaluate(p, context) for p in parts)

    if "not" in predicate:
        return not evaluate(predicate["not"], context)

    raise PredicateError(f"unrecognized predicate: {predicate!r}")
