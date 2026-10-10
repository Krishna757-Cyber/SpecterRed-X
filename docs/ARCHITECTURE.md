# SpecterRed X — Architecture

A modular-monolith backend with a strict trust boundary: **agents propose, the engine/orchestrator decides and persists.** All diagrams below describe the implementation that actually exists in this repository.

## System architecture

```mermaid
flowchart TB
  subgraph Frontend["Frontend — React / Vite / TypeScript"]
    UI["Screens: Landing, Cyber Range, Replay, Arena, Dashboard, Scenario Library, Reports"]
    R3F["React Three Fiber 3D"]
    RF["React Flow 2D fallback"]
    APIClient["Typed API client (src/api.ts)"]
    UI --> R3F
    UI --> RF
    UI --> APIClient
  end

  subgraph Backend["Backend — FastAPI (modular monolith)"]
    Routes["api/routes.py — REST endpoints"]
    subgraph Sim["simulation/"]
      Engine["engine.py — deterministic authority"]
      Scen["scenarios.py — data-driven S1/S2/S3"]
      Pred["predicates.py — safe JSON DSL"]
    end
    subgraph Agents["agents/"]
      Red["red_agent.py (explanatory)"]
      Blue["blue_agent.py (policy)"]
    end
    Score["scoring/resilience.py"]
    subgraph Services["services/"]
      Runs["runs.py — orchestrator + persistence"]
      Cmp["comparison.py"]
      Rep["reports.py"]
      Dash["dashboard.py"]
    end
    Reporter["reporting/reporter.py"]
    Mitre["mitre/catalog.py (offline, validated)"]
    ORM["models/db.py — SQLAlchemy 2"]
  end

  DB[("SQLite — persistent history")]

  APIClient -- "HTTP /api" --> Routes
  Routes --> Runs
  Runs --> Engine
  Engine --> Scen
  Engine --> Pred
  Engine --> Red
  Engine --> Blue
  Runs --> Score
  Runs --> Cmp
  Routes --> Rep --> Reporter --> Mitre
  Routes --> Dash
  Runs --> ORM --> DB
```

## Database relationships

```mermaid
erDiagram
  SCENARIO ||--o{ RUN : "defines"
  RUN ||--o{ EVENT : "produces"
  RUN ||--o{ AGENT_DECISION : "produces"
  RUN ||--o{ COMPARISON : "baseline"
  RUN ||--o{ COMPARISON : "replay"
  RUN ||--o{ REPORT : "summarized by"
  COMPARISON ||--o{ REPORT : "attached to"

  SCENARIO {
    string id PK
    string version
    string version_hash
    json definition
  }
  RUN {
    string id PK
    string scenario_id FK
    string scenario_version_hash
    int seed
    string kind "baseline|replay"
    string baseline_run_id FK
    json initial_config
    json final_state
    json metrics
    string event_hash
    datetime created_at
  }
  EVENT {
    int id PK
    string run_id FK
    int seq
    string step_key
    json payload
  }
  AGENT_DECISION {
    int id PK
    string run_id FK
    int seq
    string decision_id
    json payload
  }
  COMPARISON {
    string id PK
    string baseline_run_id FK
    string replay_run_id FK
    json payload
  }
  REPORT {
    string id PK
    string run_id FK
    string comparison_id
    text markdown
    json data
  }
```

## Agent interaction (per scenario step)

```mermaid
sequenceDiagram
  participant O as Orchestrator (runs.py)
  participant E as Engine
  participant R as Red Agent
  participant B as Blue Agent
  participant DB as SQLite

  O->>E: run_simulation(scenario, config, seed)
  loop each ordered step
    E->>R: describe next predefined step
    R-->>E: objective + expected observables (no state change)
    E->>E: evaluate prevent_if (preventive controls)
    E->>E: emit telemetry ONLY where emit_if holds
    E->>B: evaluate(emitted telemetry only)
    B-->>E: decision (action, evidence ids, explanation) or monitor_only
    E->>E: apply/record outcome (prevented|detected|succeeded)
  end
  E-->>O: events + decisions + final_state + event_hash
  O->>O: compute resilience score
  O->>DB: persist Run + Events + Decisions
```

## Simulation state transitions

```mermaid
stateDiagram-v2
  [*] --> Attempted: prerequisites met
  [*] --> Unreached: prerequisites NOT met
  Unreached --> [*]: outcome = prevented (chain broken upstream)

  Attempted --> Prevented: prevent_if(controls) == true
  Attempted --> Evaluate: not prevented
  Evaluate --> Detected: Blue detect_if(emitted telemetry) == true
  Evaluate --> Succeeded: no detection → set state flags, advance adversary
  Prevented --> [*]
  Detected --> [*]: adversary state does NOT advance
  Succeeded --> [*]
```

## Counterfactual replay

```mermaid
flowchart LR
  B["Baseline Run (immutable)\nconfig0, seed, version_hash"] -->|"validate control_changes"| M{"merge changes\nonto config0"}
  M -->|"invalid value"| X["HTTP 400 reject"]
  M -->|"valid"| Rep["Replay Run\nsame version_hash + seed"]
  B --> C["build_comparison()"]
  Rep --> C
  C --> D["step diffs + metric deltas\n+ residual risks + attribution"]
  D --> R["Report (md + json)"]
```

## Trust boundaries

```mermaid
flowchart TB
  subgraph Untrusted["Proposals (no authority)"]
    RA["Red Agent — narrative only"]
    BA["Blue Agent — selects permitted action"]
    LLM["Optional LLM — narrative only"]
  end
  subgraph Authority["Simulation Authority"]
    ENG["Engine + Orchestrator\nONLY component that mutates state"]
  end
  subgraph Forbidden["Hard-blocked (AST-tested)"]
    F1["eval / exec"]
    F2["subprocess / os.system"]
    F3["socket / requests / urllib / httpx"]
  end
  RA --> ENG
  BA --> ENG
  LLM -. "narrative text only" .-> ENG
  ENG -. "never imports" .-x Forbidden
```

The forbidden-primitive boundary is enforced by `tests/test_simulation.py::test_no_prohibited_primitives_in_simulation_and_agents`, which parses the `simulation/`, `agents/`, and `scoring/` modules with Python's AST and fails if any banned call or import appears.
