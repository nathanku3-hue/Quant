# Terminal Zero / GodView Certified Portfolio OS

Status: Active product framing — GodView certified portfolio OS (paper)
Date: 2026-07-27
Product tip: Alpha merged on **main@48a43b9**; current multi-source case remains OPERABLE; score 39 / observed 0
Active work: **ONE_CASE_EVIDENCE_GAP_TRIAGE_MACHINERY**; Commit A pre-human only; no score uplift
Authority: `docs/architecture/top_level_roadmap.md`, `PRD.md`

Terminal Zero is a local-first quantitative research console. The **authorized product pivot** is from a UOE discretionary cockpit framing to a **GodView certified portfolio OS** (paper accounting + independent certification). It is not a trading bot, not a broker, and not an alpha claim surface.

```text
PRODUCT_PIVOT = AUTHORIZED (UOE discretionary cockpit → GodView certified portfolio OS)
F1C_SHIP = CLOSED_SUBSTRATE
E0A_OPERABLE = BANKED_SUBSTRATE (plumbing only; NOT decision value / NOT alpha)
ACTIVE_PRODUCT = ONE_CASE_EVIDENCE_GAP_TRIAGE_MACHINERY (current Alpha authority unchanged)
FUNCTIONAL_STAGE = CERTIFIED_MULTI_SOURCE_CASE_OPERABLE
SHIPPED_PRODUCT_SCORE = 39/100 (FROZEN)
OBSERVED_COMPARISON_COUNT = 0
CURRENT_DECISION = DECISION_V2_ALPHA0_CLOSE_MU_G_SUPPLY_1 → paper NO_POSITION
ALPHA_ENTRY = python launch_alpha.py  (broker-free Case Workspace)
FORBIDDEN = providers, real prices, FS1 batch, PEAD, alpha claims, broker,
            compatibility dual-authority UI, dirty-root authority auto-canonization
```

## Governing sequence

```text
truth substrate → demonstrated decision value → replication → prospective economics → live capital
```

## What is banked substrate (not product intelligence)

**F1C-SHIP** (lineage `490a234`): permanent dual-fixture certified bundle + product CI. Closed substrate.

**E0A operable:** frozen E0 custody → `HOLD_FOR_EVIDENCE` → paper `NO_POSITION` → cert → current publish → one UI.  
Proves custody/cert/publish plumbing. Does **not** prove better decisions, portfolio outcomes, or alpha.

Default UI: one current certified decision only. F1C dual-role bundle is evidence-only (never default fallback).

Operator publish path: `scripts/publish_gv_e0a_current.py`.

## Active work — one-case evidence-gap triage Commit A

See [gv-one-case-decision-delta-brief.md](docs/phase_brief/gv-one-case-decision-delta-brief.md).

```text
answer-free projection from nine allowlisted hash-bound inputs
→ post-hosted-green session binding
→ separately signed verified-human identity evidence
→ equal maximum budgets + one-shot seal/blinding/replay
→ local green → one push → hosted Windows/Linux green
→ STOP before human exposure
```

`OBSERVATION_CLASS = EVIDENCE_GAP_TRIAGE_ONLY`. This slice does not test the full physical-supply → economics → business → shareholder → price-envelope chain and cannot establish investment value, portfolio value, or alpha. Commit A contains no comparison UI, current-decision publication, stage/count promotion, provider work, or human result.

## Current Canon (start here)

- [docs/architecture/top_level_roadmap.md](docs/architecture/top_level_roadmap.md) — active architecture canon
- [docs/phase_brief/gv-one-case-decision-delta-brief.md](docs/phase_brief/gv-one-case-decision-delta-brief.md) — active Commit A approval contract
- [PRD.md](PRD.md) — product requirements (header may lag; roadmap wins on gate status)
- [docs/architecture/gv_fs0_certification_and_data_authority_contract.md](docs/architecture/gv_fs0_certification_and_data_authority_contract.md) — frozen certification contract
- [docs/architecture/godview_portfolio_first_operating_model.md](docs/architecture/godview_portfolio_first_operating_model.md) — portfolio-first operating model
- [docs/architecture/godview_endgame_vision.md](docs/architecture/godview_endgame_vision.md) — endgame vision
- [docs/context/planner_packet_current.md](docs/context/planner_packet_current.md) — compact planner entry truth

## Historical product framing (not active authority)

The earlier **Unified Opportunity Engine (UOE)** discretionary cockpit framing is **historical only**.

Historical continuity links (superseded as active authority — do not auto-canonize from dirty root):

- [docs/architecture/unified_opportunity_engine.md](docs/architecture/unified_opportunity_engine.md)
- [docs/architecture/godview_signal_taxonomy.md](docs/architecture/godview_signal_taxonomy.md)
- [docs/architecture/dashboard_product_spec.md](docs/architecture/dashboard_product_spec.md) — historical dashboard state model (historical continuity only)
- [docs/prd.md](docs/prd.md) / [docs/spec.md](docs/spec.md)
- [PRODUCT_SPEC.md](PRODUCT_SPEC.md)
- [docs/phase_brief/gv-e0a-operable-brief.md](docs/phase_brief/gv-e0a-operable-brief.md) — E0A implementation brief (banked)

If a conflict appears, **active roadmap + one-case evidence-gap-triage brief** win.

## Active sequence

```text
Commit A        pre-human EVIDENCE_GAP_TRIAGE_ONLY machinery
hosted proof    exact Windows/Linux green candidate
human preflight two eligible separately verified humans; no exposure yet
one-shot run    one terminal sign-independent observation
Commit B        immutable result import and publication only
then            one full original E0 vertical only if disposition is IMPROVED
```

## Run (local)

```text
.venv\Scripts\python -m pytest
.venv\Scripts\python launch.py
# or
.venv\Scripts\streamlit run app.py
```

Use Python 3.12+ and the project `.venv`. No provider credentials are required or authorized for E0A.
