# Terminal Zero / GodView Certified Portfolio OS

Status: Active product framing — GodView certified portfolio OS (paper)
Date: 2026-07-19
Product tip: E0A operable banked (`accef5c` lineage); F1C-SHIP closed substrate earlier
Active work: **E0A-R1** merge-safety repair (hard cap) → then **E0B-DV1** sole product gate
Authority: `docs/architecture/top_level_roadmap.md`, `PRD.md`, `docs/phase_brief/gv-e0a-r1-merge-safety-brief.md`

Terminal Zero is a local-first quantitative research console. The **authorized product pivot** is from a UOE discretionary cockpit framing to a **GodView certified portfolio OS** (paper accounting + independent certification). It is not a trading bot, not a broker, and not an alpha claim surface.

```text
PRODUCT_PIVOT = AUTHORIZED (UOE discretionary cockpit → GodView certified portfolio OS)
F1C_SHIP = CLOSED_SUBSTRATE
E0A_OPERABLE = BANKED_SUBSTRATE (plumbing only; NOT decision value / NOT alpha)
ACTIVE_REPAIR = E0A-R1 (merge-safety tax; close after clean-main smoke)
ACTIVE_PRODUCT_GATE_AFTER_REPAIR = E0B-DV1
FUNCTIONAL_STAGE = CERTIFIED_SINGLE_DECISION_OPERABLE (stage-only)
CONJUNCTIVE_ENDGAME_MATURITY ≈ 9/100 (decision value near zero)
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

## Active work — E0A-R1 (repair tax)

Hard-capped merge-safety only. See [gv-e0a-r1-merge-safety-brief.md](docs/phase_brief/gv-e0a-r1-merge-safety-brief.md).

```text
single authority + proven-provenance custody refs + no dual-authority default
+ clean main + fresh-checkout smoke → STOP → open E0B-DV1
```

**Provenance rule:** prove intended origin before tracking a missing authority file; otherwise amend/remove the reference. Never promote accidental dirty-root bytes.

## Current Canon (start here)

- [docs/architecture/top_level_roadmap.md](docs/architecture/top_level_roadmap.md) — active architecture canon
- [docs/phase_brief/gv-e0a-r1-merge-safety-brief.md](docs/phase_brief/gv-e0a-r1-merge-safety-brief.md) — E0A-R1 hard cap
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

If a conflict appears, **active roadmap + E0A-R1 brief** win until E0B opens.

## Sequence after E0A-R1

```text
E0A-R1          ← ACTIVE REPAIR (merge-safety)
E0B-DV1         one complete decision-value slice (causal improvement required)
E0B-DV2         replication (heterogeneous cases, null value, adversarial, multi-operator)
E0B-SHIP        bounded decision-value release
then only       providers / prospective economics / portfolio expansion eligibility
```

## Run (local)

```text
.venv\Scripts\python -m pytest
.venv\Scripts\python launch.py
# or
.venv\Scripts\streamlit run app.py
```

Use Python 3.12+ and the project `.venv`. No provider credentials are required or authorized for E0A.
