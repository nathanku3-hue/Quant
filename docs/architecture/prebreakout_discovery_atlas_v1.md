# PREBREAKOUT Discovery Atlas v1 — W4 Contract

## 2026-08-10 real-corpus implementation update

The first real Trial-1 run exposed several corpus mechanics that are now part of the executable W4 contract without changing W2 scientific law:

- B/B-1/TTFLD adjacency is measured on the **exact listing-local observed-session ordinal**, not assumed from the global provider session spine. This handles legitimate listing gaps without turning them into false B-1 failures.
- The 60-session feature warmup may contribute legitimate prehistory flags to early development winner episodes, but warmup rows do not enter W4 false-winner/control decision counts.
- `INCOMPLETE_HORIZON` is an explicit outcome state. Such rows remain visible for custody but are excluded from matured winner, false-winner, and ordinary-control denominators; no imputation or false nonwinner conversion is permitted.
- Trial-1's full same-session ordinary-control law is preserved exactly while avoiding real-data Cartesian explosion: each exact control group is retained as a complete `matched_control_count` plus hash of the full sorted control identity set. No controls are sampled or dropped.
- Real W3 authority may be supplied lazily/date-by-date from the hash-bound W3 authority manifest rather than retaining all 226 full packets in memory simultaneously. Each date still undergoes packet verification and exact population/status equality checks.
- Nullable pandas scalars such as `pd.NA` are normalized as missing outcome values instead of being coerced through Python truthiness.

Current real-run status: W3 is complete; Trial #1 is charged `1/8`; Trial-1 flags were frozen before label materialization; W5 completed with median recall lift `0.71570953472408605`; the final real W4 Atlas artifact is still not materialized. Finish W4 only and do not consume W6. Current handover=`docs/handover/prebreakout_trial1_w4_handover_20260810.md`.

**Date:** 2026-08-10
**Family:** `PREBREAKOUT_DISCOVERY_v1`
**State:** `MECHANICS_CLOSED / BYTES_FROZEN / DORMANT_UNTIL_REAL_DISCOVERY_DATA`
**Authority:** `DISCOVERY_ONLY / EXTERNAL_FROZEN_FLAGS_ONLY / FINANCIAL_ALPHA_EVIDENCE_0 / CAPITAL_AUTHORITY_NONE`

## Purpose

W4 is the full discovery census between frozen methodology/PIT/candidate custody and later development/evaluation. It must enumerate the complete diagnostic populations needed to understand where a **previously frozen candidate flag** succeeds and fails without acquiring provider data, opening outcomes, developing the flag, tuning a model, or computing promotion metrics itself.

W4 is **not a flag-development surface**. A real Atlas run consumes externally supplied flags from a separately owned, already charged candidate whose prediction/flag bytes were frozen before the discovery labels became available.

The canonical implementation is isolated at:

- `research/prebreakout_atlas_v1/atlas.py`
- `research/prebreakout_atlas_v1/__init__.py`
- `tests/prebreakout_atlas_v1/test_atlas.py`

The separate package is intentional. W2 and W5 may both evolve under `research/prebreakout_discovery_v1/`; W4 consumes a frozen W2 hash-bound methodology object instead of importing or owning those implementation surfaces.

## Upstream authority binding

### W2 methodology

W4 consumes `PrebreakoutMethodologyBinding`, populated from the frozen W2 preregistration snapshot and cryptographically bound to it. Current immutable upstream binding is:

```text
W2 authority version             = PREBREAKOUT_W2_CONTRACT_v1
methodology_contract_sha256      = 94c8756e11d4e31cbf4d6ca4953b63c83306f4b357a42f0b70c94ae3fd261e71
breakout_contract_sha256         = 94c8756e11d4e31cbf4d6ca4953b63c83306f4b357a42f0b70c94ae3fd261e71
W4 methodology binding_sha256    = 080aba6676202e68d14aff405049a2422d231dd7b8335f3be32f376b049205ad
```

The methodology and breakout hashes are intentionally identical for W2 v1 because B/B-1 is part of the single frozen scientific contract. Construction recomputes W2's contract hash from the supplied snapshot and rejects any snapshot/hash mismatch. Canonical handoff=`docs/context/prebreakout_w2_binding_current.md`. The binding covers:

- family ID;
- methodology contract SHA-256;
- breakout contract SHA-256;
- date-local risk-set spec ID;
- primary label spec ID;
- algorithmic breakout-B spec ID;
- TTFLD spec ID;
- primary horizon;
- lead lookback;
- minimum legitimate lead;
- search-family ID; and
- maximum material-trial budget.

W4 has no fallback/default that can redefine those scientific values. A binding change changes the W4 report identity.

### W3 PIT authority

A real Atlas run requires exact W2/W3 family and risk-set alignment plus one verified W3 date-local PIT authority packet for every decision date in the Atlas grid. For each date, W4 requires exact equality between the grid and W3 authority population by:

```text
CIQSEC:IQ... + numeric trading_item_id
```

Eligibility/exclusion status and deterministic exclusion reason must match W3 exactly. The date-local grid must equal the full W3 authority population; silent row dropping, current-survivor projection, alternate-listing repair, ticker/entity/PERMNO fallback, or synthetic survivor backfill is forbidden.

## External flag / Trial-1 dependency

### W4 consumes the flag; it never develops it

The `flagged` field is an upstream result, not an Atlas transform. Before a real W4 run, the caller must supply a frozen candidate identity plus immutable flag custody proving that the exact date/security flags were produced before the relevant discovery labels were opened.

W4 must not fit a model, choose features or thresholds, search candidate variants, infer a flag from winner labels, use W5 fitted outputs as a prerequisite for the first discovery census, or modify a candidate after Atlas outcomes are visible.

Any later fitted W5 candidate is a separate charged candidate/version and can be censused only from its own already-frozen flags.

### Trial-1 bootstrap law

The first real candidate supplied to W4 is **Trial-1: a fully deterministic pre-fit rule**. **No real `TRIAL_OPEN #1` currently exists.** Before W2 may issue it, both the exact Trial-1 data/source manifest (including W3 PIT/source bindings) and the exact Trial-1 implementation manifest must already be frozen. Only then may W2 charge Trial-1, binding the corresponding source/code identities before the first result-bearing Atlas label join.

Its rule, transforms, thresholds, implementation bytes, source/PIT binding, and flag-generation procedure must remain frozen from that open onward.

Trial-1 exists specifically to break the circular dependency:

```text
frozen deterministic rule
→ externally frozen date/security flags
→ W4 true / missed / false winner + control census
→ later W5 development may learn from discovery
```

not:

```text
W5 fitted model
→ first flags
→ W4 discovery
```

W4 does not define Trial-1's scientific rule. W2/search custody owns its candidate definition and charge; W3 owns its legitimate PIT inputs; W4 receives only the frozen flag projection and candidate custody references.

## Atlas input law

Every date/security input row contains:

```text
decision_session_date
decision_session_ordinal
security_id                    # canonical CIQSEC:IQ...
trading_item_id                # canonical numeric CIQ trading item
pit_authority_sha256
pit_risk_set_spec_id
eligibility_status             # ELIGIBLE or EXCLUDED
exclusion_reason               # required iff EXCLUDED
flagged                        # exact frozen PREBREAKOUT flag for this date
winner_label                   # already-open discovery label only
outcome_status                 # MATURED_OPEN only
effective_episode_id
breakout_session_date          # winners only
breakout_session_ordinal       # winners only
b_minus_1_session_date         # winners only
b_minus_1_session_ordinal      # winners only
<preregistered match columns>
```

Excluded rows cannot be flagged. Nonwinners cannot carry breakout/B-1 fields. Winner rows must carry exact B and B-1 date/session identities. W4 does not derive B from market data and does not open or generate the winner label.

## Census units

### 1. True-winner / missed-winner census

The statistical unit is one `effective_episode_id + security_id + trading_item_id` winner episode, not one daily row. This prevents repeated daily observations from manufacturing multiple winner successes or misses.

Each winner episode must contain exactly one row at the frozen B-1 date/session. W4 scans only eligible rows inside the W2-frozen lead window from `B - lead_lookback_sessions` through the latest legitimate lead session. Under the current W2 law, `min_legitimate_lead_sessions=1`, so that latest admissible session is exactly B-1.

Classification is deterministic:

- `TRUE_WINNER`: B-1 is PIT-eligible and at least one eligible frozen flag exists inside the legal prebreakout window;
- `MISSED_WINNER`: B-1 is PIT-eligible but no legal flag exists by B-1;
- `EXCLUDED_WINNER`: the exact B-1 row is deterministically PIT-excluded.

A flag at B or later never rescues a miss. W4 records the first legitimate flag date/session but does not calculate aggregate TTFLD statistics; W6 owns untouched TTFLD scoring.

### 2. False-winner census

`FALSE_WINNER` is a full date-local decision row that is:

- PIT-eligible;
- frozen flag = true; and
- frozen winner label = false.

False-winner rows are not collapsed by a W4-specific heuristic. W6 owns effective-episode and dependence-aware evaluation semantics.

### 3. Ordinary control pool

`ORDINARY_CONTROL_POOL` is the complete set of date-local rows that are:

- PIT-eligible;
- frozen flag = false; and
- frozen winner label = false.

No controls are sampled, cherry-picked, or chosen by ticker.

### 4. Deterministic exclusion census

All excluded rows remain visible as `EXCLUDED_WINNER` or `EXCLUDED_NONWINNER`, carry their W3 reason, and receive statistical weight zero. W4 never repairs exclusions by fallback.

### 5. Matched-control census

W4 does not tune the control definition. `MatchedControlContract` supplies a preregistered `control_definition_id`, exact matching columns, the bound W2 methodology hash, and—on real runs—both an upstream-verified search-charge receipt SHA-256 and the immutable Trial-Ledger snapshot SHA-256 because W2 marks `control_definition` as a charged search field. W4 binds those custody artifacts but does not reimplement or mutate the upstream ledger verifier.

For every positive-weight true winner, missed winner, and false winner case, W4 emits **all** positive-weight ordinary controls with:

- the same decision session; and
- exact equality on every preregistered match column.

There is no W4 `N controls` hyperparameter. If no exact preregistered control exists, the case is retained in `cases_without_exact_matched_control`; it is not silently dropped or rematched under a looser rule.

## MU / SNDK smoke law

Named smoke examples enter W4 only through generic W3 `BMinusOneEligibilityProof` objects. The proof may contain `display_symbol` for human traceability, but `display_symbol_used_for_logic` must be false and W4 never branches on symbol literals.

A resolved smoke identity is the canonical CIQSEC + Trading Item key from W3. Every Atlas row for that identity receives:

```text
statistical_weight = 0
promotion_denominator_weight = 0
```

The W4 smoke trace records W3 proof status/reason, B/B-1 reference, identity, number of Atlas input rows, and whether any eligible flag existed by B-1. Post-B-1 flags do not change that field.

Thus MU/SNDK can prove engineering behavior without changing any discovery acceptance denominator, search objective, or untouched evaluation result.

## Real-run gates

A non-fixture W4 run fails closed unless all of the following are true:

1. W2 methodology binding and W3 family/risk-set ID agree exactly.
2. `MatchedControlContract` binds the same W2 methodology hash.
3. Trial-1 (or a later separately charged candidate) is already charged and its externally supplied flag bytes are frozen before discovery-label availability; for Trial-1 specifically, the exact data/source manifest and Trial-1 implementation manifest must have been frozen **before** its `TRIAL_OPEN`. The first real run must use the deterministic pre-fit Trial-1 rule, not a fitted W5 model.
4. Both a non-null control-definition search-charge receipt SHA-256 and its Trial-Ledger snapshot SHA-256 are present.
5. Every decision date has one verified W3 PIT authority packet.
6. The Atlas grid equals the complete date-local W3 authority population for every date.
7. Every input label is already explicitly `MATURED_OPEN` under legitimate discovery authority supplied by the caller.

The Atlas performs no provider acquisition and no label-open operation itself.

## Fixture mode

`fixture=True` is permitted only for deterministic mechanical tests. Fixture mode:

- carries `authority_class=MECHANICAL_FIXTURE_ZERO_EVIDENCE`;
- forbids supplying real W3 authority packets;
- still enforces canonical identity, exclusion, B/B-1, effective-episode, matching, and smoke-weight mechanics; and
- can never be cited as PIT, OOS, prospective, replication, or financial-alpha evidence.

## W5 / W6 boundary

W4 produces discovery populations and trace fields only.

W5 owns rolling/expanding development, temporal OOS folds, cross-sectional holdout, charged search, fit/tuning, and development objective calculation.

W6 owns prediction-before-label custody, lockbox opening, Precision, Recall, Lift, PR-AUC, TTFLD statistics, catastrophic false winners, effective episodes, right-tail wealth, and incumbent `I` versus `I+X` comparison.

W4 intentionally computes none of those promotion metrics.

## Forbidden operations

W4 never performs:

- provider capture/query;
- outcome opening;
- Clock #1/A2 access;
- model fitting or retuning;
- search-budget charging itself;
- W6 lockbox evaluation;
- Parent/Child mutation;
- VSB tuning;
- Sector Rotation or CRV1 mutation;
- replication outcome access;
- broker/PAPER orders; or
- capital allocation.

`financial_alpha_evidence=0` and `capital_authority=NONE` remain hard report fields.

## Validation — 2026-08-10

Focused W4 fixture suite on final W2 single-seal handoff bytes:

```text
tests/prebreakout_atlas_v1/test_atlas.py: 14/14 PASS
```

Full current PREBREAKOUT mechanical/custody matrix:

```text
PREBREAKOUT discovery package     26
W3 PIT authority                  17
W4 Atlas                          14
W6 untouched evaluator            12
------------------------------------
TOTAL                              69 PASS
```

The 26-test discovery package includes W2 contract/breakout, W2 Trial/Search-Ledger mechanics, W5 walk-forward, and the uncharged Trial-1 M0 candidate/source-manifest gate. No result-bearing trial or label surface is opened by this matrix.
```

Coverage includes cryptographic W2 snapshot/hash binding, W2↔W3 risk-set drift rejection, one-count-per-effective-winner-episode, exact B-1 requirement, no post-B-1 rescue, true/missed/excluded winners, false winners, exhaustive exact matched controls, canonical CIQ identity, exclusion fail-closed behavior, paired real-run charge-receipt + Trial-Ledger snapshot custody, MU/SNDK zero-weight smoke traces, and report tamper detection.

No real discovery Atlas outcome census was executed in this W4 implementation slice.

## Dormancy / reopen law

W4 mechanics are closed after this freeze. Do not add more Atlas plumbing, matching variants, metrics, candidate logic, or data adapters while dormant.

Reopen W4 only for the **first real Atlas run**, and only when all four programme gates are simultaneously true:

```text
W2 binding exact
+ W3 full date-local PIT authority present
+ Trial-1 and control definition charged with frozen external flags
+ discovery labels legitimately open
```

Until then, the frozen W4 bytes remain untouched.
