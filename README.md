# SpecterRed X

**Attack. Adapt. Defend. Prove Resilience.**

An AI-powered cyber-defense flight simulator that turns controlled security failures into measurable resilience — against phishing, executive impersonation, and voice-clone fraud.

> **Honesty first.** SpecterRed X runs a *deterministic simulation* of a fictional organization under a scam/impersonation attack. The resilience score is a **scenario-specific simulation metric, not a certified real-world security rating**. All people, domains, and organizations are synthetic (`.example`). A MITRE ATT&CK technique mapping denotes *conceptual relevance*, not proof of a real intrusion.

---

## Official track & problem

**ForgeHacks Online 2026 — AI + Cybersecurity.**

> "Build an AI-powered solution that helps people recognize, prevent, verify, or respond to scams, impersonation, and fraud enabled by AI or modern technologies."

SpecterRed X addresses this with a safe, repeatable training environment: observe a baseline attack run, inspect the evidence behind a defensive failure, change one security control, replay the *same* scenario, and compare the outcomes with evidence-backed reporting.

## Target users

- Security awareness & blue-team trainers who need safe, repeatable scam/impersonation drills.
- Finance, IT help-desk, and SOC teams practicing verification workflows (callback verification, dual approval, phishing-resistant MFA).
- Hackathon judges and educators who want to *see* why a control changed an outcome, backed by real records.

---

## The Counterfactual Defense Twin (signature innovation)

The core loop is **Simulate → Observe → Verify → Defend → Replay → Compare → Learn**:

1. **Simulate** a fictional org under attack with the current control configuration.
2. **Observe** the ordered events, telemetry, and Blue-Agent decisions in a 3D cyber range.
3. **Verify** the evidence behind each defensive failure (real event + decision records).
4. **Defend** by changing one or more allowed security controls.
5. **Replay** the *same* scenario version, initial snapshot, and seed — the baseline stays immutable.
6. **Compare** event-by-event: which outcomes changed, per-metric deltas, residual risks.
7. **Learn** from an evidence-backed report with scenario-derived training questions.

Example: a synthetic executive invoice request is accepted without independent verification (baseline). Enable `payment_callback_verification` and replay — the simulated payment transition is now blocked because the required independent verification is missing. The app shows the actual event and control records behind that change.

---

## Features (actually implemented)

- **Deterministic simulation engine** — pure, seeded, data-driven; the sole authority over simulated state. Identical inputs produce identical normalized event hashes.
- **Three fraud/impersonation scenarios** — S1 Phishing → Account Takeover, S2 Executive Invoice Impersonation (BEC), S3 Help-Desk Voice-Clone Impersonation.
- **Four explainable agents** — Red (adversarial reasoner), Blue (defensive reasoner), Orchestrator (simulation authority + persistence), Reporter (evidence & learning).
- **Counterfactual replay** with an immutable baseline, honest comparison (it says so when a change does *not* help), and single-control attribution.
- **Resilience scoring** (0–100) with documented weights and zero-denominator renormalization.
- **Persistent history** (SQLite) that survives restarts.
- **Markdown + JSON reports** built strictly from persisted records, with validated MITRE ATT&CK context.
- **Holographic Cyberverse UI** — procedural 3D cyber range (React Three Fiber) with event-driven playback, plus a Counterfactual Replay workspace, Red vs Blue arena, dashboard, scenario library, and reports.
- **Graceful fallbacks** — automatic React Flow 2D network view when WebGL is unavailable, on Low/2D quality, or if the 3D canvas throws. The full core workflow works without WebGL.
- **Offline by default** — no paid API key or internet connection required. Optional LLM assists narrative only.

---

## Technology stack

| Layer | Tech |
|---|---|
| Backend | Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2, SQLite, Pytest |
| Frontend | React 18, TypeScript (strict), Vite, Tailwind CSS, React Router, React Three Fiber + Three.js + Drei, React Flow, Recharts, Lucide |
| Data | Validated MITRE ATT&CK Enterprise subset (committed for offline use) |

---

## Architecture (summary)

A modular monolith backend with a strict trust boundary: agents propose, the engine/orchestrator decides and persists. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for Mermaid diagrams.

```
frontend (React/Vite)  ──HTTP──▶  FastAPI
                                    ├─ simulation/   deterministic engine + scenarios + predicate DSL
                                    ├─ agents/       red + blue reasoners (explanatory, no state mutation)
                                    ├─ scoring/      resilience score
                                    ├─ services/     orchestration, comparison, reports, dashboard
                                    ├─ reporting/    markdown/json reporter
                                    ├─ mitre/        validated ATT&CK catalog (offline)
                                    └─ models/       SQLAlchemy ORM + SQLite
```

---

## Setup & installation

**Prerequisites:** Python 3.11+, Node 18+ (tested on Node 24), npm.

### Backend

```bash
cd backend
python -m venv .venv
# Windows (Git Bash): .venv/Scripts/python.exe -m pip install -r requirements.txt
# macOS/Linux:        .venv/bin/pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

---

## Run instructions

Start the backend (port 8000):

```bash
cd backend
# Windows (Git Bash):
PYTHONPATH=. .venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
# macOS/Linux:
PYTHONPATH=. .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Start the frontend (port 5173, proxies `/api` → backend):

```bash
cd frontend
npm run dev
```

Open http://localhost:5173. Click **Start Simulation** to launch S1 and open the Cyber Range on real events.

> With `make` available you can also use `make backend-install`, `make backend`, `make frontend-install`, `make frontend`, `make test`, `make eval`.

---

## Environment variables

Copy `.env.example`. **Everything is optional — the core demo runs with none set.**

| Variable | Purpose | Default |
|---|---|---|
| `SPECTERRED_DB_URL` | SQLite URL for persistent history | `sqlite:///./backend/specterred.db` |
| `SPECTERRED_CORS_ORIGINS` | Comma-separated allowed origins | `http://localhost:5173,http://127.0.0.1:5173` |
| `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL` | Optional LLM narrative assist (all three required to enable) | empty → deterministic only |
| `VITE_API_BASE` | Frontend → backend base URL | `/api` (Vite proxy) |

Never commit real secrets. Model keys are server-side only and never exposed to the frontend or logs.

---

## Test commands

```bash
cd backend
PYTHONPATH=. .venv/Scripts/python.exe -m pytest -q      # backend unit + API tests
PYTHONPATH=. .venv/Scripts/python.exe eval.py           # writes docs/evaluation_report.json (real results)
```

```bash
cd frontend
npm run typecheck   # tsc --noEmit (strict)
npm run lint        # eslint, max-warnings 0
npm run build       # production build
```

See the **Verification** section below for the latest recorded results.

---

## Scenarios

| ID | Title | Track | Key control that flips the outcome |
|---|---|---|---|
| S1 | Phishing → Account Takeover | Credential phishing / impersonation | `session_risk_policy`, `mfa_mode`, `mailbox_rule_alerting` |
| S2 | Executive Invoice Impersonation (BEC) | Payment fraud | `payment_callback_verification`, `dual_approval`, `vendor_change_policy` |
| S3 | Help-Desk Voice-Clone Impersonation | Account-recovery abuse | `helpdesk_identity_verification`, `callback_verification`, `privileged_action_approval` |

All assets, identities, and `.example` domains are fictional. S3 is text-based — no voice cloning, audio, or real calling.

---

## Deterministic vs optional LLM components

- **Deterministic policy (default):** the engine, control evaluation, telemetry emission, Blue-Agent decisions, scoring, and comparison are all deterministic and seeded. This is the ground truth.
- **LLM-assisted narrative (optional, off by default):** when `LLM_BASE_URL`/`LLM_API_KEY`/`LLM_MODEL` are set, an LLM may *only* improve narrative explanations. It never controls the engine, invents evidence, determines ground truth, or executes commands. Decisions are labeled with their mode.

---

## Replay methodology

A replay re-runs the **same scenario version hash**, the **same seed**, and the baseline's initial configuration snapshot with the requested control changes merged in. Control changes are validated against each control's allowed values; invalid changes are rejected (HTTP 400). A new run is persisted and the baseline is never mutated. The comparison is computed from the two persisted runs. Reproducibility is enforced by a stable hash over normalized events (excluding timestamps and db ids). See [docs/METRICS.md](docs/METRICS.md).

---

## Metric definitions (summary)

```
Resilience = 0.30·Detection + 0.25·Containment + 0.20·Prevention
           + 0.15·Response Efficiency + 0.10·Evidence Coverage
```

Each component is normalized to 0–100. If a denominator is zero the component is marked **N/A** and its weight is redistributed across the remaining components — missing data is never counted as success and never divides by zero. Full definitions and edge cases in [docs/METRICS.md](docs/METRICS.md).

---

## Safety boundaries

This is a defensive training simulator. Enforced:

- Synthetic targets, fictional identities, `.example` domains only.
- **No** `eval`/`exec`, **no** `subprocess`/`os.system`, **no** network calls in simulation or agent code (enforced by an automated AST test).
- No exploit execution, real-target scanning, credential collection, real email/payment operations, or model-generated executable actions.
- Strict input validation, parameterized DB access (SQLAlchemy ORM), safe serialization, environment-based secrets.
- Core demo works fully offline.

---

## Known limitations

- Synthetic simulation results do **not** prove real-world security. The score is scenario-specific.
- Per-control attribution is computed only when a single control changes; multi-control replays report that attribution is unavailable (replay each change independently to attribute).
- MITRE mapping `T1656` (Impersonation) is present but marked deprecated in the upstream dataset; it is retained for conceptual clarity and labeled as such.
- The 3D scene is procedural and illustrative; packet animation is tied to the selected persisted event, not an independent fabricated attack.
- No authentication on the local API (single-user local dev tool). Do not expose it publicly without adding auth.

---

## Screenshots

See `docs/SUBMISSION.md` for the capture checklist. Key screens: Landing (holographic globe), 3D Cyber Range with playback, Counterfactual Replay comparison, Red vs Blue arena, Dashboard, Reports.

## Demo video

See [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) for the exact 3-minute walkthrough and clicks.

---

## Future roadmap

- Tier-2 scenarios (excessive privileges, lateral movement, cloud misconfig, data-exfiltration detection).
- Per-control attribution across simultaneous changes (automated independent replays).
- Training Center with adaptive difficulty and persisted attempts.
- ATT&CK search screen and settings persistence.

---

## Attribution

This project uses the MITRE ATT&CK® knowledge base. © The MITRE Corporation. ATT&CK is a registered trademark of The MITRE Corporation. Technique data from `mitre-attack/attack-stix-data`. Mappings denote conceptual relevance only.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
