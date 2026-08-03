# Dashboard Redesign Migration Plan

Status: `ACTIVE — FINAL PLANNING ROUND`
Date: 2026-08-03
Active gate: `GV-DASHBOARD-ALL-CAPITAL-PIT-1`
Canonical contract: `docs/architecture/dashboard_all_capital_pit_contract.md`

## Migration law

Place real product content before broad extraction. Build lower authority layers only as needed to operate the real read-only episode. Do not split `dashboard.py` into speculative frameworks and do not ship disconnected contracts as product progress.

## Ordered migration

### 0. Bank current shadow baseline

Run the focused real-MU/same-evidence tests and commit exactly the current five code/test paths. No documentation, unrelated files, release ceremony, or tag.

### 1. Freeze minimum contracts

Add exact five-field PIT identity, evidence/digest contracts, explicit target intent/unit/normalization, strict extension envelopes, and immutable proposal.

### 2. Adapt verified real sources

Map the active MU-operated workspace/proposal object, independent MU-shadow object, and certified-book cash. Do not invent JSON/Parquet sources, market identity, or cash yield.

### 3. Add governance command authority

Introduce typed proposal submission and a handler that decides exact identity acceptance/rejection. Adapters, dashboard, event store, and projector do not make this decision.

### 4. Add ordered event authority

Adapt existing custody or introduce the minimum event-store protocol for stream/sequence ordering, digest chaining, duplicate/gap rejection, canonical reads, and idempotence. Do not create a second competing durable authority.

### 5. Add deterministic projections

Purely fold valid events into read-only proposal/episode models. Restrict Slice 1 statuses to its event vocabulary. Order rows by event sequence then record ID.

### 6. Ship six-page read-only product surface

Create Command Center, make it default, preserve Discovery & Analysis, and render the real three-row PIT episode through `dashboard.py`. Move full event/replay details to Operations & Replay.

### 7. Stop Slice 1

Prove zero selection, target composition, optimizer/risk math, preview, authorization, book mutation, certification change, and deletion.

### 8. Add selection/composition in Slice 2

Add reject-all, one base target, compatible delta/overlay legs, target collision handling, and replayable selection events.

### 9. Add preview/authority in Slice 3

Add deterministic target resolution, costs/limits/multi-model risk, immutable preview, stale-bound authorization, application, certification, and exact replay.

### 10. Place, extract, and delete after proof

Relocate useful content, extract only exercised boundaries, then delete verified displaced paths after import/caller, behavior, regression, and rollback proof.

## Repository-grounded migration facts

- `views/command_center.py` is new.
- `operated_portfolio_app.py` is the existing standalone app path.
- operated MU comes from the prospective workspace/proposal object path.
- shadow MU comes from `core/gv_v2_mu_nvda_shadow_decision.py`.
- cash comes from the certified workspace/book.

## Stop rules

Stop and report rather than filling assumptions when exact book head, market snapshot, evidence digest, cash yield, lifecycle source, or event authority cannot be mapped from repository truth.
