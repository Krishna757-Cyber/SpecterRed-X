"""Canonical JSON serialization and stable hashing for reproducibility.

Event hashes MUST exclude nondeterministic metadata (db ids, wall-clock
timestamps). We serialize with sorted keys and no whitespace, then sha256.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(obj: Any) -> str:
    """Deterministic JSON string: sorted keys, compact separators."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_hash(obj: Any) -> str:
    """sha256 hex digest of the canonical JSON of ``obj``."""
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()
