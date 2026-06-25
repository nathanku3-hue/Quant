# V2 PEAD D1 Repair Brief

Status: D1 repaired/rebuilt and parent closure evidence reconciled; untracked local ownership remains explicit; D2 is separate
Date: 2026-06-18
RoundID: `ROUND-20260618-V2-D1-REPAIR`
ScopeID: `V2_D1_SUE_FORMULA_LIQUIDITY_ATOMIC_REPAIR`
Owner: Data + Docs/Ops

## Parent closure reconciliation

- Authoritative full D1 repair evidence is published at `docs/saw_reports/saw_v2_d1_repair_20260618.md`.
- Thin parent-closure reconciliation evidence is published at `docs/saw_reports/saw_v2_d1_parent_closure_reconciliation_20260618.md`.
- Read-only verification confirms the Parquet SHA256 matches the manifest SHA256 `81b2689b48943373f58586ddc382fb609dbce022cde93d4d502333cae5541855`.
- `scripts/pead_d1_sue_builder.py`, `tests/test_pead_d1_sue.py`, this brief, and both D1 SAW reports are untracked local D1-owned files; evidence closure is reconciled, but clean tracked-repo closure is not claimed.
- This closure-only pass did not change or execute D1 code/data, run D1 tests, access providers, run D2/Ken French work, launch/wire the dashboard, execute strategy code, stage files, or commit.

## Objective

Repair the bounded PEAD D1 SUE builder and artifact without widening into D2 returns, benchmark acquisition, provider validation, strategy interpretation, or UI work.

## Delivered scope

- `scripts/pead_d1_sue_builder.py` uses raw numeric `epspxq`; it does not divide by `ajexq`. The legacy `adj_eps` column name remains for compatibility.
- Duplicate `(gvkey, rdq)` identities are resolved before exact t-4 lag and rolling calculations so removed rows cannot contaminate stateful features.
- Exact t-4 continuity remains required.
- Raw `sue_price_scaled` remains available; `sue_price_scaled_clipped` applies RDQ cross-sectional clipping at `+/-5` standard deviations.
- `cshoq_lag1` is measured in millions. `liquidity_pass = prccq_lag1 * cshoq_lag1 > 50` is a flag only and does not alter `valid_sue`.
- Parquet and manifest publication use temp-to-replace writes.
- Rebuilt `data/processed/pead_d1_sue_signal.parquet`: 346,511 rows, 233,586 valid SUE rows, 13,216 GVKEYs, RDQ 2015-01-02 through 2026-06-16, SHA256 `81b2689b48943373f58586ddc382fb609dbce022cde93d4d502333cae5541855`.
- Manifest quality metrics are part of the artifact contract: raw `abs(sue_price_scaled) > 5` is 441 / 233,586 valid rows (0.1888%), below the 0.5% fail-closed threshold; 1,992 valid rows have clipped values; 204,227 valid rows pass the liquidity flag.
- The manifest records the current-vintage limitation: Compustat fundamentals may include restatement hindsight, so strict filing-vintage PIT EPS is not established by D1.
- Empty processed-output paths fail before touching existing Parquet or manifest outputs.
- Early RDQ deduplication removed 1,447 contaminated lag-valid events from the pre-reconciliation count of 235,033.

## Acceptance criteria

- [x] `epspxq` is numeric and used directly; `ajexq` is not applied.
- [x] `(gvkey, rdq)` deduplication occurs before lag and rolling transforms.
- [x] Exact t-4 continuity is enforced.
- [x] Raw and clipped SUE columns coexist.
- [x] Liquidity units and strict `> 50` threshold are explicit, and the flag is independent of `valid_sue`.
- [x] Parquet and manifest writes are atomic temp-to-replace operations.
- [x] Rebuilt artifact and manifest agree on the recorded SHA256.
- [x] Duplicate-RDQ counterexample coverage prevents stage-order regression.
- [x] Quality gate enforces raw `abs(SUE) > 5` share below 0.5% of valid rows and records metrics in the manifest.
- [x] Empty processed-output paths preserve the prior output bundle.
- [x] Current-vintage Compustat/restatement-hindsight limitation is explicit in the manifest and docs.

## Ship-Fast Decision Gate

What is done: D1 formula, stage order, clipping, liquidity flag, atomic publication, tests, and rebuilt artifact.

What is blocked: D2 return/IID/event-window work, Ken French patch, and provider validation.

User order interpreted as: execute only the bounded D1 repair before starting a separate D2 round.

Recommended next step: separate D2 repair starting with `gvkey+iid` returns before any daily ADV selection.

Why this is correct: return continuity must be computed within one security identity before any daily representative-IID choice can occur.

Alternatives considered: one-batch D1-D2 repair was rejected because it would mix a proven D1 artifact repair with unresolved D2 identity and event-window contracts.

Decision needed from user: no new D1 decision; the next execution packet is the separately bounded D2 repair.

Scope limit: no D2 edits or builds, Ken French acquisition, provider access, strategy interpretation, UI, alerts, ranking, promotion, or broker paths.

Stop rule: stop D2 execution if returns are not first computed by `(gvkey, iid)` or if the event-window range cannot cover the longest planned horizon.

## Rollback

Restore the prior D1 builder and artifact/manifest pair together. Never mix a builder, Parquet artifact, or manifest from different D1 versions.

## Next action

**Separate D2 repair starting with `gvkey+iid` returns before any daily ADV selection.**
