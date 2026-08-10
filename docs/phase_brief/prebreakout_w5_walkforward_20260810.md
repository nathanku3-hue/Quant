# PREBREAKOUT W5 Walk-Forward — Execution Brief

Date: 2026-08-10
Status: `MECHANICS_CLOSED / SUPERSEDED_FOR_NEXT_ACTION_BY prebreakout_w5_trial1_m0_20260810.md`
Mode: `EXECUTION_PACKET`
Scope: `W5_DEVELOPMENT_WALK_FORWARD_MECHANICS_ONLY`

Current continuation: Trial-1 M0 is frozen **uncharged** in `docs/phase_brief/prebreakout_w5_trial1_m0_20260810.md`. This mechanics brief remains the reusable W5 leakage/custody contract; it does not authorize development execution or label inspection.
Family: `PREBREAKOUT_DISCOVERY_v1`
Authority: `DEVELOPMENT_ONLY / FINANCIAL_ALPHA_EVIDENCE_0 / CAPITAL_AUTHORITY_NONE`
Untouched evaluator: `CLOSED_TO_W5`
Prospective clock: `NOT_STARTED_BY_W5`

## Chosen scope

**Chosen Scope:** Implement the provider-blind W5 development walk-forward seam: explicit rolling/expanding training, an exact charged temporal-fold plan (fixture proof uses four OOS folds), primary-horizon embargo, deterministic security-level cross-sectional holdout, persistent W2 Trial/Search-Ledger custody, exact source/PIT bindings, and zero-statistical-weight trace rows.

**Why Now:** W2, W3, and W4 now expose compatible mechanical authority surfaces. W5 can bind to them without opening W6 and can fail closed on temporal leakage, uncharged variants, source-manifest drift, PIT identity drift, holdout contamination, and smoke-row statistical contamination.

**Why Not Alternatives:** W1 Clock #1 remains separately custodied. W2 owns breakout/TTFLD/horizon/falsifier/search constitution. W3 owns date-local PIT identity/availability/corporate-action authority. W4 owns the discovery Atlas census. W6 owns untouched/lockbox evaluation. W7 VSB remains confirmation-only. W8/W9/W10 remain independent lanes.

**Out-of-Boundary Items:** provider acquisition; real CIQ data writes; new discovery outcome opening; W6 lockbox access; prospective prediction-ledger start; VSB retuning; Sector Rotation; CRV1 horizon/risk-set changes; Parent/Child mutation; PAPER broker orders; replication outcomes; any financial-alpha or capital claim.

**Stop Rules:** Stop if W5 requires an untouched/prospective outcome surface, an uncharged material variant, a ticker-specific branch, survivor/current-membership fallback, source-manifest substitution, or edits to Clock #1/VSB/Parent-Child/Sector Rotation/PAPER/replication authority.

**Demo Target:** deterministic fixture proof of four chronological temporal OOS folds, rolling and expanding semantics, 20-session primary-horizon embargo, cross-sectional holdout exclusion from fit/tuning, trace-only zero-weight scoring, persistent charge-before-label custody, exact source/PIT binding, and scorer isolation from OOS labels.

## Upstream contract state consumed by W5

W5 now binds directly to W2 `research/prebreakout_discovery_v1/preregistration.py` and W2's persistent `ledger.py`; it does not maintain a parallel scientific or search-budget constitution.

Frozen W2 identities currently consumed by W5:

- W2 authority version: `PREBREAKOUT_W2_CONTRACT_v1`;
- methodology contract SHA-256: `94c8756e11d4e31cbf4d6ca4953b63c83306f4b357a42f0b70c94ae3fd261e71`;
- breakout contract SHA-256: `94c8756e11d4e31cbf4d6ca4953b63c83306f4b357a42f0b70c94ae3fd261e71`;
- canonical handoff: `docs/context/prebreakout_w2_binding_current.md`;
- family: `PREBREAKOUT_DISCOVERY_v1`;
- risk set: `PREBREAKOUT_US_PRIMARY_COMMON_DATE_LOCAL_V1`;
- primary label: `PREBREAKOUT_RIGHT_TAIL_20D_TOP5_V1`;
- secondary label: `PREBREAKOUT_RIGHT_TAIL_10D_TOP5_V1`;
- algorithmic breakout B: strict close greater than the immediately prior 20-session high, with 20-session episode cooldown;
- primary horizon: `20` sessions; secondary horizon: `10` sessions;
- TTFLD legitimate window: `B-20` through `B-1`, with misses receiving zero effective lead;
- search family: `PREBREAKOUT_SEARCH_v1`;
- trial ledger: `PREBREAKOUT_V1_TRIAL_LEDGER`;
- hard material-trial budget: `8`, charged at `TRIAL_OPEN` before result inspection;
- smoke acceptance weight: `0`, with special-case branching forbidden;
- financial-alpha evidence: `0`; capital authority: `NONE`.

W3 currently names the same family and exact date-local risk-set ID. W3 remains the authority for canonical `CIQSEC:IQ...` + numeric Trading Item identity, availability cutoffs, corporate actions, and no current-survivor/current-primary/ticker/entity/PERMNO fallback.

W4 consumes W2/W3 and owns the discovery census. W5 does not reconstruct Atlas classifications or B-1 smoke proofs.

## W5 input projection

W5 consumes already-admitted **development-only** feature and label projections. It performs no provider query and no Atlas label opening.

Feature rows are exact-key rows with:

```text
decision_date
security_id                 # exact CIQSEC:IQ<digits>
trading_item_id             # exact numeric Trading Item ID
statistical_weight          # >0 development; 0 trace-only smoke
source_manifest_sha256      # one exact charged development-source manifest
pit_authority_sha256        # exactly one W3 authority packet hash per decision date
pit_risk_set_spec_id        # exact W2/W3 date-local risk-set ID
<W2-ledger-charged feature representation columns>
```

Development labels are a separate exact-key projection with:

```text
decision_date
security_id
target_label                # binary primary development label
label_available_date        # strictly after decision_date
```

Feature and label key sets must match exactly. W5 does not silently drop unlabeled rows, repair identities, substitute current membership, or convert deterministic W3 exclusions into eligible rows.

## Persistent search custody

W2's append-only Trial/Search Ledger is the single W5 material-search authority.

A valid W5 run requires an existing, still-open W2 `TRIAL_OPEN` whose payload binds:

- `trial_id` and `implementation_id`;
- immutable `variant_sha256`;
- W5 `training_window_spec_id`;
- W5 `cross_sectional_holdout_spec_id`;
- W5 `temporal_fold_plan_id`;
- exact `source_manifest_sha256`;
- W2 family/search-family/ledger-scope/budget identities;
- discovery-only outcome access with untouched-lockbox and prospective access explicitly forbidden.

W5 verifies the full W2 hash chain before reading development label values. An absent, duplicate, mismatched, tampered, over-budget, or already-closed trial fails closed. The feature projection's single source-manifest hash must equal the charged W2 variant's source-manifest hash.

**Current real-search state is `0/8`; no real `TRIAL_OPEN #1` exists.** Fixture/unit-test opens are mechanics-only and carry zero real search authority. Before W2 may issue real Trial-1 open, the exact data/source manifest and the exact Trial-1 implementation manifest must both be frozen. W5 must reject any attempt to treat a candidate as charged merely because a provisional rule, source list, or implementation draft exists.

The exact feature representation, model, training-window variant, holdout definition, and temporal-fold plan remain material charged variants. W5 supplies no silent scientific defaults. The development objective ID is explicit, and W5 rejects Sharpe/CAGR-named primary search objectives; economic wealth metrics remain secondary under the methodology freeze.

## Temporal law

- `WalkForwardMode` is explicit: `EXPANDING` or `ROLLING`.
- Fold count is explicit in the charged plan. The fixture proof uses `4`; W5 fails closed when admitted history cannot support the requested plan rather than silently reducing the fold count.
- Every fold is ordered `train -> embargo -> temporal OOS`.
- `embargo_sessions >= 20` because W2's primary horizon is 20 sessions.
- Every training label must satisfy `label_available_date < fold.oos_start_date`; otherwise the fold blocks before scorer invocation.
- Expanding mode holds the development start fixed and expands only through the pre-embargo training cut.
- Rolling mode uses the explicit charged fixed training window.
- Temporal OOS windows cannot overlap.

## Cross-sectional holdout law

- Assignment is deterministic from `cross_sectional_holdout_spec_id + holdout_seed + canonical CIQSEC security_id` through a hash bucket.
- No ticker, named company, outcome, old sector map, or later membership enters assignment.
- Positive-weight holdout securities are excluded from every training frame and from the W5 search objective.
- They are still scored on temporal OOS dates so prediction bytes exist.
- Their labels are never joined by W5's tuning path.
- W5 fails if the charged holdout is infeasible rather than moving securities between strata.

## Smoke / MU-SNDK consequence

W5 contains no literal MU/SNDK branch. W3/W4 own the generic B-1 eligibility/exclusion proof and named smoke tracing. Any W4 smoke trace reaching W5 uses `statistical_weight=0`:

- it may be scored and retained in `zero_weight_trace_predictions`;
- it is excluded from every fit;
- its label is never joined into the W5 objective;
- changing its label cannot change the W5 run output/hash.

This preserves the user's rule: MU/SNDK can demonstrate the mechanism, but have zero statistical weight. W5 does not manufacture their B-1 eligibility, flag, exclusion, or miss result.

## Prediction-before-development-label boundary

For each development fold, the scorer receives:

- matured training rows with training labels; and
- OOS rows containing only decision key, Trading Item ID, and charged feature columns.

The scorer never receives `target_label`, `label_available_date`, `statistical_weight`, source-manifest hash, PIT-authority hash, or risk-set authority ID for OOS scoring. W5 hashes all fold predictions before joining any temporal-development OOS label.

Only positive-weight, non-holdout temporal OOS rows enter the development objective. Cross-sectional holdout labels and zero-weight trace labels are never joined.

This is a **development leakage guard**, not W6 authority. It does not claim a truly untouched label store, lockbox evaluation, prospective evidence, or prediction-before-label custody for W6.

## Implementation

W5-owned paths in this round:

- `research/prebreakout_discovery_v1/contracts.py`
  - W2-bound W5 split contract;
  - rolling/expanding validation;
  - exact primary-horizon/embargo binding;
  - charged-plan and W2 identity checks.
- `research/prebreakout_discovery_v1/walk_forward.py`
  - temporal fold construction;
  - deterministic cross-sectional holdout;
  - exact source/PIT/identity validation;
  - persistent W2 Trial-Ledger verification;
  - fit/tune/holdout/trace isolation;
  - prediction sealing before temporal-development label join.
- `research/prebreakout_discovery_v1/__init__.py`
  - narrow public W5 surface.
- `tests/prebreakout_discovery_v1/test_walk_forward.py`
  - deterministic W2-bound W5 acceptance matrix.
- this brief and the W5 SAW evidence report.

Concurrent W2/W3/W4 files were inspected as authorities but are not claimed as W5-owned changes.

## Acceptance status

| Check | Requirement | Current result |
|---|---|---|
| W5-01 | expanding plan yields exact requested 4 non-overlapping temporal OOS folds with W2 20-session horizon embargo | PASS fixture |
| W5-02 | rolling plan keeps fixed training history and insufficient temporal coverage fails closed | PASS fixture |
| W5-03 | holdout never enters fit/search objective; holdout remains predicted | PASS fixture |
| W5-04 | zero-weight traces never enter fit/objective and remain prediction-traceable | PASS fixture |
| W5-05 | poisoning holdout/trace labels cannot change the W5 run | PASS fixture |
| W5-06 | immature training labels block before scorer invocation | PASS fixture |
| W5-07 | persistent W2 `TRIAL_OPEN` must bind candidate, split plan, and exact source manifest before label-value read | PASS fixture |
| W5-08 | already-closed trial, W2 contract drift, noncanonical CIQSEC/Trading Item, and wrong PIT risk-set ID fail closed | PASS fixture |
| W5-09 | W5 code/tests compile under repository Python | PASS |
| W5-10 | current PREBREAKOUT discovery package regression (W2/W5 plus W4 shim) | PASS: 19 tests after final source-binding changes |
| W5-11 | W3 + dedicated W4 fixture authority/mechanics regression | PASS: 26 tests after final source-binding changes |
| W5-12 | real W3-authorized source manifest + real W4 development-label projection executed | OPEN — intentionally not opened/run in this mechanics round |

## Remaining integration boundary

Before any result-bearing W5 run:

1. Freeze the exact Trial-1 data/source manifest and exact Trial-1 implementation manifest first. Only then may W2 issue `TRIAL_OPEN #1`, binding the corresponding exact source-manifest and code identities. No real material trial is currently open or consumed.
2. W3 must supply the date-local PIT authority packets for every admitted decision date under the aligned risk-set law.
3. W4 must supply the full discovery-development census/label projection under W2's frozen label contract, with smoke traces at zero statistical weight.
4. The charged source manifest must project those W3/W4-bound inputs into W5's exact schema; W5 will reject source/PIT drift rather than repair it.
5. W6 remains separate and closed to W5. No W5 tuning decision may consume a W6 lockbox or prospective outcome.

## Claim boundary

This round proves **walk-forward/search/source-custody mechanics, not Alpha**. No real PREBREAKOUT development result was calculated. No Clock #1 outcome was opened. No VSB parameter changed. No Sector Rotation/CRV1/PAPER/replication outcome surface was accessed. No broker order was created. `financial_alpha_evidence=0`; capital authority remains `NONE`.
