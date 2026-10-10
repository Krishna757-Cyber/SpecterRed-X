# SpecterRed X — Assumptions & Decisions

Recorded per the build brief. Dates are absolute. "The brief" = the SpecterRed X master build prompt.

## Environment & dates

- Build date: **2026-10-10**.
- Platform: Windows 11, Python 3.11.9, Node 24.19.0, npm 11.16.0.
- The repository was **empty** at start (no prior implementation to preserve); git was initialized here.

## Implementation decisions

- **Modular monolith** backend (FastAPI) rather than microservices, per the two-hour constraint and the brief's explicit guidance.
- **Synchronous** simulation execution with persisted events + frontend playback (no SSE), per the brief.
- **No Alembic**: the repo did not previously use it; the schema is created at startup with a `schema_info` version row. Reproducible initialization re-seeds scenario definitions idempotently (keyed on `version_hash`).
- **SQLite** file DB at `backend/specterred.db` (overridable via `SPECTERRED_DB_URL`). History survives restarts; verified by test and by live restart.
- **Seed** is threaded through a per-run `random.Random(seed)` even though current scenario rules are fully deterministic, so future stochastic rules remain reproducible. The seed is included in the event hash inputs.
- **Event identity** uses run-scoped sequence numbers (`seq`) and deterministic evidence ids (`EV-<seq>-<signal>`), never wall-clock timestamps or random ids. Creation timestamps are stored separately for user-facing history and excluded from the reproducibility hash.
- **Containment semantics:** a `detected` step is treated as contained — the adversary's state does not advance past a detected step. This makes detection meaningfully change downstream outcomes in replay.
- **Baseline score of 0.0** for all three scenarios with defaults is expected and honest: with every control disabled, each modeled step succeeds and no telemetry is observable, so Detection/Prevention/Containment are all 0 and Evidence Coverage is N/A (no containment decisions). The counterfactual replay is what demonstrates improvement.

## MITRE ATT&CK

- Network access **was available** during the build. The validator downloaded the official Enterprise ATT&CK STIX dataset from `mitre-attack/attack-stix-data` and validated all nine candidate technique IDs. All nine validated and are committed to `backend/app/data/mitre_validated.json` for offline use.
- `T1656` (Impersonation) validated but is **marked deprecated** in the current upstream dataset. It is retained because it remains the clearest conceptual label for executive/voice impersonation, and is flagged `deprecated: true` in the committed data. If stricter correctness is desired, it can be dropped without affecting the engine.
- The UI and reports state that a technique mapping means **conceptual relevance, not proof of a real intrusion.**

## Offline-mode assumptions

- The entire core demo (simulate → observe → verify → defend → replay → compare → report) runs with **no internet and no API key**.
- Fonts are self-hosted via `@fontsource` (Inter, JetBrains Mono) so typography works offline.
- The 3D range is fully procedural; it loads **no external model files**.

## Optional LLM integration

- Off by default. Enabled only when all of `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` are set.
- Scope is **narrative only**. The LLM never controls the engine, determines ground truth, invents evidence, or executes anything. Current build ships the deterministic path; the config surface and honest mode labeling (`Deterministic policy` vs `LLM-assisted narrative`) are implemented and the health endpoint reports the active mode.

## Missing integrations / simplifications

- Payments, email, and voice are **abstract events only** — no real payment, email, or audio integrations (by design and for safety).
- **False positives** are not modeled in the current scenarios (detection reflects true positives). Documented in `docs/METRICS.md`.
- **Per-control attribution** across multiple simultaneous control changes is not auto-decomposed; the comparison reports attribution as unavailable and advises independent replays. (This is explicitly on the brief's cut list.)
- No API authentication (single-user local dev tool). Noted in the README security section; do not expose publicly without adding auth.

## Features deliberately deferred (per cut list)

- Tier-2 scenarios (excessive privileges, lateral movement, cloud misconfig, exfiltration).
- Training Center + adaptive learning UI (answer keys are computed in the Reporter, but the dedicated screen is deferred).
- ATT&CK search screen and a settings screen.
- Decorative bloom / heavier post-processing on the 3D scene.

None of the "never cut" items were cut: persistent history, deterministic replay, baseline immutability, honest event-based comparison, core-workflow tests, working API↔UI integration, README, and demo script are all present.
