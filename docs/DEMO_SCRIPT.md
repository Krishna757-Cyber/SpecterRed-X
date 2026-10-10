# SpecterRed X — 3-Minute Demo Script

Use a **real running app** with **real simulation data**. Start both servers first:

```bash
cd backend && PYTHONPATH=. .venv/Scripts/python.exe -m uvicorn app.main:app --port 8000
cd frontend && npm run dev
```

Open http://localhost:5173. For a clean demo, delete `backend/specterred.db` before starting so the Dashboard begins empty (optional).

---

### 0:00–0:20 — The problem
**Say:** "AI-enabled phishing, executive impersonation, and voice-clone fraud are hard to practice against safely. SpecterRed X is a flight simulator for cyber defense: it lets you fail safely, inspect the evidence, fix one control, and prove the fix worked."
**On screen:** Landing page. Point at the headline "Attack. Adapt. Defend. Prove Resilience." and the red/blue activity globe.

### 0:20–0:45 — Enter the Cyberverse, pick S1
**Click:** **Start Simulation** (hero button).
**Expected:** A real baseline run of **S1 — Phishing → Account Takeover** is created and the **3D Cyber Range** opens with 5 real events. The resilience chip reads **0.0** (all defenses off).
**Say:** "This is a synthetic organization — fictional identities, `.example` domains. The score is a simulation metric, not a real-world rating."

### 0:45–1:15 — Show real Red and Blue decisions
**Click:** the **Play** button in Playback (or step with the forward button).
**Expected:** The 3D nodes light up per step; the Event Inspector updates with each step's title, the conceptual MITRE technique (e.g. `T1566.002`), and the evidence observed.
**Click:** **Red vs Blue** in the nav.
**Expected:** Split screen — left (red) shows the adversarial objective + expected observables; right (blue) shows observed evidence and the decision. With defenses off, the Blue Agent honestly shows **"No telemetry observable under current controls — nothing to act on,"** and most steps are **Succeeded**.
**Say:** "Notice the Blue Agent only sees telemetry the scenario actually emits. Nothing is faked."

### 1:15–1:45 — Inspect the defensive failure and its evidence
**Click:** **Counterfactual Replay** in the nav.
**Expected:** The baseline run is preselected; its **immutable** event hash is shown. The baseline resilience score card reads **0.0**.
**Say:** "Here's the failure: with no risk-based session policy, the stolen session establishes and a hidden mailbox-forwarding rule persists access. Let's change exactly one control."

### 1:45–2:15 — Change a control and replay
**Click:** the **"recommend: enabled"** shortcut next to `session_risk_policy` (sets it to enabled).
**Click:** **Replay scenario**.
**Expected:** A new replay run is created against the **same scenario version and seed**; the view switches to **Diff** mode. Replay score card reads **48.3**, the **Change** card reads **+48.3 (improved)**.
**Say:** "Same scenario, same seed — the only difference is one control."

### 2:15–2:40 — Compare real results, components, and event differences
**On screen:** scroll to **Event-level comparison**.
**Expected:** The table shows per-step **Baseline → Replay** outcome badges; changed rows (credential capture, MFA fatigue, session established, mailbox rule) are highlighted and marked "yes". Below: **Controls changed** (`session_risk_policy: disabled → enabled`), **Residual risks**, and **Per-metric deltas** (Detection/Containment/Prevention rising).
**Say:** "Attribution is clean because exactly one control changed. The comparison is computed from persisted records — and if a change didn't help, the app says so."

### 2:40–3:00 — Download the report, explain training value
**Click:** **Generate report**, then **Markdown** (and mention **JSON**).
**Expected:** A report built strictly from real run data downloads — executive summary, score components, event timeline with evidence ids, agent decisions, failed controls, evidence-supported recommendations, the counterfactual comparison, validated MITRE mappings, training questions, and limitations.
**Say:** "That's the loop — Simulate, Observe, Verify, Defend, Replay, Compare, Learn — with evidence behind every claim. Everything you saw ran offline, with no paid API, and the full workflow also works with WebGL disabled via the 2D view."

---

## Backup / robustness talking points
- **No WebGL?** Set the quality selector (top-right) to **2D** — the Cyber Range switches to a React Flow network and the entire workflow still works.
- **Reduced motion?** The app respects `prefers-reduced-motion`; animations are disabled.
- **Determinism:** running the same baseline twice yields the same normalized event hash (shown in `docs/evaluation_report.json`, `reproducible: true`).
- **Try S2/S3:** Scenario Library → Start. For S2, the recommended control is `payment_callback_verification=enabled` (baseline 0.0 → replay 34.2). For S3, `helpdesk_identity_verification=enabled` (0.0 → 70.0).
