# SpecterRed X — Hackathon Submission

## Project title
**SpecterRed X — Autonomous Cyber Defense Flight Simulator**

## Short description
SpecterRed X turns controlled, synthetic security failures into measurable resilience. It runs a deterministic simulation of a fictional organization under a scam/impersonation attack, lets you observe the evidence behind a defensive failure, change one security control, replay the exact same scenario, and compare the outcomes — then exports an evidence-backed report. Its signature innovation is the **Counterfactual Defense Twin**.

## Official track
**ForgeHacks Online 2026 — AI + Cybersecurity.**

## Problem statement
"Build an AI-powered solution that helps people recognize, prevent, verify, or respond to scams, impersonation, and fraud enabled by AI or modern technologies."

AI-enabled phishing, executive impersonation (BEC), fraudulent payment requests, and voice-clone account-recovery attacks are hard to practice against safely. There is no safe range to *fail*, inspect why, fix one control, and prove the fix worked.

## Target users
Security-awareness and blue-team trainers; finance, IT help-desk, and SOC teams practicing verification workflows; educators and hackathon judges who want to see *why* a control changed an outcome, backed by real records.

## Technical approach
- **Deterministic simulation engine** (Python) is the sole authority over simulated state — pure, seeded, data-driven, with a safe JSON predicate DSL (no `eval`/`exec`, no subprocess, no network).
- **Four explainable agents:** Red (adversarial reasoner), Blue (defensive policy reasoner), Orchestrator (authority + persistence), Reporter (evidence & learning).
- **Counterfactual replay:** same scenario version + seed + initial snapshot; the baseline is immutable; the comparison is computed from persisted records and is honest when a change does not help.
- **Resilience score** (0–100) with documented weights and zero-denominator renormalization.
- **FastAPI + SQLAlchemy + SQLite** persistence; **React + TypeScript + React Three Fiber** holographic UI with an automatic React Flow 2D fallback.
- **Offline-first:** no paid API key required. Validated MITRE ATT&CK subset committed for offline conceptual mapping.

## Real-world impact
Teams can rehearse the exact decisions that stop real fraud — callback verification before a payment, phishing-resistant MFA, help-desk identity proofing — and get a reproducible, evidence-backed before/after that shows which control mattered and what residual risk remains. It is a safe teaching instrument, explicitly labeled as a simulation rather than a real-world guarantee.

## What is real vs. synthetic (integrity)
- Real: the engine, persistence, scoring, replay, comparison, reports, and the three scenarios' logic. Evaluation numbers in `docs/evaluation_report.json` are produced by running the engine.
- Synthetic: all people, organizations, and `.example` domains; all messages are placeholders (e.g. "[synthetic message: urgent payment request]").
- Not claimed: no real-world security guarantee, no customers/certifications, no "first in the world," no LLM running unless explicitly configured.

## Screenshot checklist
Capture at 1440×900 (light-on-dark):
1. **Landing** — hero "Attack. Adapt. Defend. Prove Resilience." with the 3D network globe.
2. **3D Cyber Range** — S1 mid-playback, Event Inspector showing a technique + evidence, outcome badge visible.
3. **Counterfactual Replay** — baseline 0.0 vs replay score, +Δ card, event-level comparison table with changed rows highlighted.
4. **Red vs Blue Arena** — split red/blue panels with the Blue decision + evidence ids.
5. **Dashboard** — resilience bar chart + intelligence core state + recent runs/reports.
6. **Reports** — rendered Markdown report with the metric table and MITRE section; show the .md/.json download buttons.
7. **2D fallback** — Cyber Range with quality set to "2D" (React Flow network) to prove the no-WebGL path.

## Repository
https://github.com/Krishna757-Cyber/SpecterRed-X

## Links
- Setup & usage: `README.md`
- Architecture (Mermaid): `docs/ARCHITECTURE.md`
- Metrics: `docs/METRICS.md`
- Assumptions: `docs/ASSUMPTIONS.md`
- Demo script: `docs/DEMO_SCRIPT.md`
- Evaluation results: `docs/evaluation_report.json`
