# Terminal Zero / GodView Certified Portfolio OS

Status: Active product framing — GodView certified portfolio OS (paper)
Date: 2026-07-19
Product tip lineage: `490a234` (F1C-SHIP closed substrate)
Active gate: **GV-E0A-OPERABLE**
Authority: `docs/architecture/top_level_roadmap.md`, `PRD.md`, `docs/phase_brief/gv-e0a-operable-brief.md`

Terminal Zero is a local-first quantitative research console. The **authorized product pivot** is from a UOE discretionary cockpit framing to a **GodView certified portfolio OS** (paper accounting + independent certification). It is not a trading bot, not a broker, and not an alpha claim surface.

```text
PRODUCT_PIVOT = AUTHORIZED (UOE discretionary cockpit → GodView certified portfolio OS)
F1C_SHIP = CLOSED_SUBSTRATE
ACTIVE_GATE = GV-E0A-OPERABLE
SHIPPED_PRODUCT_SCORE = 39/100 (owner claim ceiling; no alpha)
FUNCTIONAL_STAGE = CERTIFIED_SINGLE_DECISION_OPERABLE
FORBIDDEN = providers, real prices, FS1 batch, PEAD, alpha claims, broker,
            compatibility dual-authority UI, historical-suite repair
```

## What is shipped substrate

On product tip lineage `490a234`, F1C-SHIP closed:

- permanent dual-fixture certified bundle (synthetic `OPEN` + `NO_POSITION`);
- product CI Windows/Linux parity.

That path is **closed substrate** (deterministic certification machinery). Dual-fixture demo is not the default operator UI.

## Active gate — GV-E0A-OPERABLE (implemented on `codex/gv-e0a-operable`)

```text
frozen MU G_supply evidence (4 files exact hashes)
→ explicit HOLD_FOR_EVIDENCE research decision / portfolio NO_POSITION
→ one active DecisionEnvelope
→ PortfolioBook + independent certification
→ atomic publication of current decision
→ one visible current decision
→ Streamlit default portfolio route
```

Operator publish path: `scripts/publish_gv_e0a_current.py`. Score remains **39/100** (stage-only progress; no alpha; no numeric uplift without rubric).

## Current Canon (start here)

- [docs/architecture/top_level_roadmap.md](docs/architecture/top_level_roadmap.md) — active architecture canon (E0A sole gate)
- [PRD.md](PRD.md) — active build authority + product requirements
- [docs/phase_brief/gv-e0a-operable-brief.md](docs/phase_brief/gv-e0a-operable-brief.md) — E0A EXECUTION_PACKET
- [docs/architecture/gv_fs0_certification_and_data_authority_contract.md](docs/architecture/gv_fs0_certification_and_data_authority_contract.md) — frozen certification contract
- [docs/architecture/godview_portfolio_first_operating_model.md](docs/architecture/godview_portfolio_first_operating_model.md) — portfolio-first operating model
- [docs/architecture/godview_endgame_vision.md](docs/architecture/godview_endgame_vision.md) — endgame vision
- [docs/context/planner_packet_current.md](docs/context/planner_packet_current.md) — compact planner entry truth

## Historical product framing (not active authority)

The earlier **Unified Opportunity Engine (UOE)** discretionary cockpit framing (supercycle gem discovery + GodView signal taxonomy + buying-range prompts) is **historical product lineage only**. Do not treat UOE as the active primary product.

Historical continuity links (superseded as active authority):

- [docs/architecture/unified_opportunity_engine.md](docs/architecture/unified_opportunity_engine.md) — historical UOE architecture
- [docs/architecture/godview_signal_taxonomy.md](docs/architecture/godview_signal_taxonomy.md) — signal family taxonomy (context, not E0A gate)
- [docs/architecture/dashboard_product_spec.md](docs/architecture/dashboard_product_spec.md) — historical dashboard state model
- [docs/prd.md](docs/prd.md) / [docs/spec.md](docs/spec.md) — lowercased historical pointers
- [PRODUCT_SPEC.md](PRODUCT_SPEC.md) — may retain historical UOE/PEAD sections; active header is GodView pivot

If a conflict appears, **active roadmap + PRD active authority block + E0A brief** win.

## Future stages (not next action)

```text
GV-E0A-OPERABLE  ← ACTIVE
GV-FS1           policy/benchmark paths (after E0A)
GV-FS2           authority/accounting hardening
GV-RA0           real-data admission (authorization required)
GV-P1            prospective policy evaluation
```

## Run (local)

```text
.venv\Scripts\python -m pytest
.venv\Scripts\python launch.py
# or
.venv\Scripts\streamlit run app.py
```

Use Python 3.12+ and the project `.venv`. No provider credentials are required or authorized for E0A.
