# PREBREAKOUT Fast-Path Handover — 2026-08-10

## Executive status

Owner stream: `PREBREAKOUT_DISCOVERY_v1` fast path
Branch: `codex/pit-source-authority-1`
Critical chain: `W3 data -> Trial-1 deterministic M0 -> W4 census/W5 development -> W6 one untouched lockbox -> frozen prospective tape -> shadow economics -> PAPER-0`
Off critical path: W7/VSB, W8 Sector Rotation, W9/CRV1, replication outcomes, ML/boosting, optimizer, additional search, Parent/Child redesign.
W2 frozen contract SHA-256: `94c8756e11d4e31cbf4d6ca4953b63c83306f4b357a42f0b70c94ae3fd261e71`
Trial budget state: **Trial #1 not opened; real material trials consumed = 0/8.**
Financial/capital authority: `financial_alpha_evidence=0`; `capital_authority=NONE`.

## What is complete

### 1. W3 mechanics

W3 PIT mechanics are frozen under `PREBREAKOUT_US_PRIMARY_COMMON_DATE_LOCAL_V1` in:

- `research/prebreakout_pit_v1/authority.py`
- `tests/prebreakout_pit_v1/test_authority.py`
- `docs/architecture/prebreakout_pit_authority_v1.md`
- `docs/architecture/prebreakout_pit_acquisition_manifest_v1.json`

Active W3 smoke proof requires the exact frozen W2 hash. `BREAKOUT_CONTRACT_UNBOUND` is historical receipt state only. Current upstream-unavailable state is `B_MINUS_1_PIT_AUTHORITY_UNAVAILABLE` until real B-1 authority is compiled.

Forbidden throughout: AOV-109 substitution, ticker/PERMNO/entity identity fallback, survivor/current-primary back-projection, alternate-listing rescue.

### 2. Full date-local market/listing corpus captured from live CIQ Pro

Capture entrypoint:

`python scripts/prebreakout_capture_ciq_historical_corpus.py ...`

It attaches to the existing authenticated CIQ Pro DevTools page on port `9230`; it does not sign in/out or navigate. The request uses Securities ProductQuery perspective `321247` and the proved date-qualified law:

- Major US Exchanges: field `406718`, value `-1,-4`
- funding/common-equity values: field `321268`, values `1,16`
- dated Close Price `324251` with date secondary `sk_557`, predicate `NotNa`
- exact identity: MI KEY/company + `SP_CIQ_ID` + exact SPT/Trading Item
- market: Close `324251`, Total Return `322797` / `1D`, Volume `324277`
- current Primary Issue is not requested

Physical custody is split across two restartable directories but forms one non-overlapping date spine:

- `data/prebreakout/raw/historical_corpus_20250324_20260807/` — 6 sessions, 2025-03-24..2025-03-31
- `data/prebreakout/raw/historical_corpus_20250401_20260807/` — 340 sessions, 2025-04-01..2026-08-07

Combined verified custody:

```text
sessions                 = 346
first_session             = 2025-03-24
last_session              = 2026-08-07
market/listing rows       = 1,894,207
union companies           = 5,919
union exact listings      = 6,018
missing close             = 0
missing volume            = 0
missing total_return_1d   = 177,820
```

The daily population changes naturally. Example retained parity date `2025-05-16` returns exactly `5,394` source securities / `5,329` entities, matching the earlier independent Lane-2 provider proof. Ambiguous multi-listing entities are retained and marked; they are never repaired from current-primary state.

CIQ close semantics were sanity-checked on a known split history (NFLX): pre/post effective-date close scale is already split-normalized while daily total return remains continuous. This supports using the provider close for frozen W2 B without inventing split factors.

### 3. MU/SNDK exact identity and algorithmic B traces resolved generically

From the full date-local corpus, not ticker fallback:

```text
MU
  CIQSEC = CIQSEC:IQ289030
  Trading Item = 2630498
  SPT = SPT2630498
  exact-listing history = 346 sessions
  W2 accepted B episodes = 11

SNDK
  CIQSEC = CIQSEC:IQ1860586153
  Trading Item = 1929119896
  SPT = SPT1929119896
  exact-listing history = 346 sessions
  W2 accepted B episodes = 12
```

All episodes were retained. Do not hand-select one famous breakout.

### 4. Full-union lifecycle/corporate-action source captured

Capture entrypoint:

`python scripts/prebreakout_capture_ciq_key_developments.py ...`

Provider source: Key Developments ProductQuery perspective `311682`, exact company Add-Companies filter plus server-side lifecycle event-type criterion.

Event type field: `322182` / `SPKD_TYPE_CATEGORY`; exact relevant lookup set is frozen in the script and includes M&A transaction announcement/cancellation/closing, delisting/listing-change, bankruptcy states, and stock-split/significant-stock-dividend events.

Canonical filtered lifecycle custody:

`data/prebreakout/raw/key_developments_lifecycle_20250324_20260807/`

Verified:

```text
parts                         = 12/12
requested entity rows         = 5,919
unique requested entities     = 5,919
market-union entity set equal = TRUE
duplicate requested IDs       = 0
normalized lifecycle rows     = 176,353
```

Global Blue anchor is present exactly:

- 2025-02-18 — M&A Transaction Announcement
- 2025-02-20 — Delisting announcement
- 2025-07-02 — M&A Transaction Closing
- 2025-08-29 — Delisting/Form 15

An earlier broad/unfiltered partial exists at `data/prebreakout/raw/key_developments_20250324_20260807/`. It is quarantined/non-authoritative; do not use it. The filtered lifecycle directory above is the intended source.

## Immediate next action

**Compile the real W3 date-local authority bundle from the captured market/listing + filtered lifecycle bytes. Do not charge Trial #1 yet.**

Suggested sequence:

1. Build one deterministic corpus manifest across both market directories and all 12 lifecycle parts; hash-bind exact files/receipts and the 346-session spine.
2. Compile per-date primary state from exact date-local uniqueness:
   - one qualifying listing for company -> `PRIMARY_DATE_LOCAL / UNIQUE_DATE_LOCAL_QUALIFYING_LISTING`
   - multiple qualifying listings -> `AMBIGUOUS_DATE_LOCAL / DATE_LOCAL_AMBIGUOUS_MULTIPLE`
   - never use current Primary Issue.
3. Compile corporate-action state per exact CIQSEC + Trading Item and date. Use event availability/date semantics fail-closed. A known terminal event effective on/before the decision session must become `EFFECTIVE_TERMINAL`; known future-effective terminal events may be `PENDING_TERMINAL`; unresolved mapping/state must not be silently `CLEAR`.
4. Materialize/verify `PrebreakoutPITAuthority` packets for the required development + lockbox decision dates.
5. Regenerate zero-weight MU/SNDK B-1 proofs for all retained W2 episodes. `DETERMINISTIC_UNAVAILABLE` is a blocker, never a pass.

## Important integration issue before Trial #1 charge

The real corpus has `177,820` provider-missing `SP_TOTAL_RETURN` cells while Close and Volume are complete. This is a real full-population missingness state, not a reason to remove names.

Frozen Trial-1 documentation says invalid/insufficient market history should **abstain with score 0 / no imputation**. But current `research/prebreakout_discovery_v1/trial1_m0.py::_normalize_market_history()` rejects any non-numeric/NaN total-return row for the entire input frame.

Therefore, before building the charge-bearing Trial-1 code manifest, change only the outcome-blind implementation needed to make the executable behavior match the already-frozen abstention policy. Do not alter windows, thresholds, model law, control law, folds, holdout, or objective. Recompute the Trial-1 code-bundle hash after this mechanical fix. This is legal because Trial #1 is still uncharged and no Trial-1 development labels have been inspected.

## Trial-1/W4/W5/W6 custody state

Existing Trial-1 candidate is already frozen deterministic/pre-fit/market-only in `research/prebreakout_discovery_v1/trial1_m0.py` and `docs/phase_brief/prebreakout_w5_trial1_m0_20260810.md`.

Do not spend Trials 2–8 unless Trial #1 fails for an interpretable mechanism reason.

Intended single-corpus partition after W3 compilation:

```text
60 sessions  feature warmup
226 sessions W5 development decision spine
20 sessions  post-development label embargo / no-lockbox overlap
20 sessions  W6 untouched lockbox decisions
20 sessions  lockbox label-maturity tail
-----------------------------------------------
346 sessions total
```

The exact date mapping must be frozen from the provider session spine before labels are opened.

Only after the real W3 bundle, development-label custody hash, W4 episode custody hash, decision-spine hash and source-receipt bundle hash exist:

1. build exact Trial-1 source manifest;
2. recompute/freeze Trial-1 code manifest;
3. append exactly one real W2 `TRIAL_OPEN` (cost 1/8);
4. run W4 census + W5 development;
5. if the candidate survives, freeze immediately — no tweak;
6. write W6 predictions first, then consume exactly one untouched lockbox once.

## Development/lockbox survival law

Primary evidence remains right-tail, not CAGR/Sharpe.

Required signs:

- PIT/custody violations = 0
- Recall/Lift beats breadth-matched baseline
- median effective TTFLD > 0
- catastrophic false-winner rate improves versus frozen control
- I+X incremental net utility > 0
- Precision@K, PR-AUC, right-tail wealth capture and effective episodes are first-class
- CAGR/Sharpe/MDD are diagnostics only

MU/SNDK remain visible zero-weight engineering smoke only.

## PAPER lane

PAPER-0 mechanics are already substantially implemented elsewhere. Keep this parallel and non-blocking to PREBREAKOUT alpha evidence.

Remaining practical PAPER items from current repo truth:

1. real read-only CIQSEC/SPT -> Alpaca PAPER account/asset execution-map receipt, using already-supplied PAPER credentials if available;
2. date-specific verified session-close receipt for the eventual PAPER order date.

Do not submit broker orders during this research handoff. `FREEZE_NEW_RISK` remains the safety default until reconciliation and authority gates pass.

## Git / workspace custody

Use canonical worktree:

`E:/code/quant/.worktrees/devspace-053ca7a4f582fb3e`

Branch:

`codex/pit-source-authority-1`

The working tree contains many concurrent dirty/untracked files from other streams. Do **not** revert or wholesale-stage them. Shared current-truth files contain interleaved edits. The isolated PREBREAKOUT/W3 commit intentionally avoids staging unrelated stream files.

Large provider data under `data/prebreakout/` is local acquisition custody and is intentionally not part of the Git commit.

## Stop rules

- Do not requery A2.
- Do not use AOV-109 as PREBREAKOUT authority.
- Do not use ticker/entity/PERMNO fallback.
- Do not back-project current survivor/current-primary state.
- Do not open Trial #1 before exact data + code manifests are frozen.
- Do not inspect W6 lockbox before predictions are frozen.
- Do not retune after Trial #1 survives.
- Do not put W7/W8/W9/replication/ML/additional search back on the critical path.
- Do not create broker orders from this handoff.

## First worker checkpoint

A new worker should first verify:

```text
market sessions = 346
market union entities = 5,919
lifecycle parts = 12
lifecycle requested union = same 5,919 entities
Trial #1 real ledger opens = 0
W2 hash = 94c8756e11d4e31cbf4d6ca4953b63c83306f4b357a42f0b70c94ae3fd261e71
```

If any of those differ, stop and reconcile custody before proceeding.
