"""Verified MITRE ATT&CK catalog (offline).

Technique data is loaded from ``app/data/mitre_validated.json``, which was built
by validating candidate IDs against the official
``mitre-attack/attack-stix-data`` Enterprise dataset. Only validated IDs are
served. A technique mapping here denotes CONCEPTUAL RELEVANCE to the modeled
behavior - it is NOT proof that a real intrusion occurred.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any

ATTRIBUTION = (
    "This project uses the MITRE ATT&CK(R) knowledge base. "
    "(C) 2024 The MITRE Corporation. ATT&CK is a registered trademark of The MITRE "
    "Corporation. Technique data from mitre-attack/attack-stix-data. Mappings denote "
    "conceptual relevance only, not evidence of a real intrusion."
)

_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "mitre_validated.json")


@lru_cache
def _load() -> dict[str, Any]:
    if not os.path.exists(_DATA_PATH):
        return {"validated": {}, "missing": []}
    with open(_DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def technique(tid: str) -> dict[str, Any] | None:
    """Return validated technique info or None if the ID failed validation."""
    return _load().get("validated", {}).get(tid)


def all_techniques() -> list[dict[str, Any]]:
    return list(_load().get("validated", {}).values())


def is_available() -> bool:
    return bool(_load().get("validated"))
