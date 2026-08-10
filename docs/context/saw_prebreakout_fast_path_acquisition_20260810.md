# SAW — PREBREAKOUT Fast-Path W3 Acquisition — 2026-08-10

SAW Verdict: BLOCK

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: inherited-user-fast-path | Domains: PREBREAKOUT,PIT,CIQ_ACQUISITION,DATA_CUSTODY

RoundID: `PREBREAKOUT_FAST_PATH_W3_ACQUISITION_20260810`

ScopeID: `PREBREAKOUT_FULL_DATE_LOCAL_MARKET_LISTING_AND_LIFECYCLE_CAPTURE`

## Scope

Owned round scope: add restartable attach-only Capital IQ Pro capture entrypoints for the full PREBREAKOUT date-local listing/market corpus and filtered lifecycle events, execute the real historical acquisition, verify exact market/lifecycle entity coverage, and prepare handover. No Trial-1 charge, discovery-label open, W6 lockbox read, prospective outcome read, broker order, capital action, or other-family search was authorized.

Owned code/docs:

- `scripts/prebreakout_capture_ciq_historical_corpus.py`
- `scripts/prebreakout_capture_ciq_key_developments.py`
- `docs/handover/prebreakout_fast_path_handover_20260810.md`
- this SAW report

Upstream W3 mechanics consumed without widening:

- `research/prebreakout_pit_v1/authority.py`
- `docs/architecture/prebreakout_pit_authority_v1.md`
- `docs/architecture/prebreakout_pit_acquisition_manifest_v1.json`

## Acceptance checks

- `CHK-01`: historical market/listing capture uses exact Securities ProductQuery date-local law, no current-primary/ticker/PERMNO/entity fallback, and preserves ambiguous listings — PASS.
- `CHK-02`: combined market corpus is non-overlapping and spans 346 provider sessions from 2025-03-24 through 2026-08-07 — PASS.
- `CHK-03`: lifecycle capture uses provider Key Developments with server-side lifecycle event-type criterion; requested entity union exactly equals the 5,919-company market union — PASS.
- `CHK-04`: MU/SNDK exact CIQSEC + Trading Item identities are resolved from captured provider bytes and frozen W2 B mechanics can operate generically — PASS.
- `CHK-05`: W3 regression, acquisition-script compile, and scoped Git whitespace checks pass — PASS.
- `CHK-06`: mandatory independent Reviewer A/B/C passes — NOT RUN / UNAVAILABLE on current DevSpace surface; terminal SAW must remain BLOCK.

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| Blocking | Repository-mandated independent Reviewer A/B/C evidence is unavailable | Run independent strategy/regression, runtime/resilience, and data-integrity/performance review against the committed acquisition bytes and handover | review lane | OPEN |
| Material | Real corpus contains 177,820 missing `SP_TOTAL_RETURN` cells while Close/Volume are complete; current Trial-1 loader rejects any NaN although frozen policy says invalid history should abstain at score zero | Before Trial #1 charge, make outcome-blind Trial-1 execution match its frozen abstention policy without changing scientific windows/thresholds/model/control/folds/holdout/objective; recompute code-bundle hash | next PREBREAKOUT worker | OPEN |
| Advisory | Large provider bytes are local data custody, not Git payload | Build one deterministic hash manifest over both market directories + 12 lifecycle parts before Trial-1 source manifest | next PREBREAKOUT worker | OPEN |

## Implementer evidence

Real provider custody verification:

```text
market sessions                  = 346
market rows                      = 1,894,207
market union entities            = 5,919
market union exact listings      = 6,018
first session                    = 2025-03-24
last session                     = 2026-08-07
lifecycle parts                  = 12
lifecycle requested entities     = 5,919
lifecycle unique entities        = 5,919
lifecycle entity set == market   = TRUE
lifecycle duplicate requests     = 0
filtered lifecycle rows          = 176,353
```

Global Blue lifecycle anchor is present at `2025-07-02 / M&A: Transaction Closing`, with the related 2025 announcement/delisting records.

MU exact identity: `CIQSEC:IQ289030 / Trading Item 2630498 / SPT2630498`.

SNDK exact identity: `CIQSEC:IQ1860586153 / Trading Item 1929119896 / SPT1929119896`.

Validation:

- `PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python.exe -m pytest tests/prebreakout_pit_v1 -q` -> `17 passed`.
- `py_compile` for W3 authority + both acquisition scripts -> PASS.
- scoped `git diff --check` -> PASS.
- exact lifecycle requested-entity set equality to market union -> PASS.

## Scope split summary

in-scope complete: attach-only CIQ capture code, 346-session date-local listing/market custody, 12/12 filtered lifecycle parts, exact entity-set reconciliation, generic MU/SNDK identity resolution, handover.

in-scope open: compile the captured bytes into real per-date W3 authority and B-1 proofs; fix Trial-1 missing-return abstention mechanics before the first real charge.

inherited/out-of-scope: W1 Clock custody, W2 scientific law, W4 result-bearing census, W5 development result, W6 untouched evaluation, W7/VSB, W8 Sector, W9/CRV1, replication outcomes, PAPER broker execution.

## Document Changes Showing

- `scripts/prebreakout_capture_ciq_historical_corpus.py` — restartable date-local Securities ProductQuery capture — reviewer status: independent A/B/C pending.
- `scripts/prebreakout_capture_ciq_key_developments.py` — restartable filtered Key Developments lifecycle capture — reviewer status: independent A/B/C pending.
- `docs/handover/prebreakout_fast_path_handover_20260810.md` — exact next-worker custody and critical-path handoff — reviewer status: independent A/B/C pending.

Open Risks:

1. Independent Reviewer A/B/C closure is unavailable; SAW cannot be PASS.
2. Trial-1 total-return missingness execution mismatch must be corrected before charge.
3. Real W3 authority compilation from the landed data is still the next data gate; provider capture alone is not a PIT pass.

Next action: Compile one hash-bound market+lifecycle corpus manifest, make Trial-1 missing-return handling conform to frozen abstention policy before charge, then compile real W3 authority/B-1 proofs; do not open Trial #1 until those exact source and code manifests are frozen.

ClosurePacket: RoundID=PREBREAKOUT_FAST_PATH_W3_ACQUISITION_20260810; ScopeID=PREBREAKOUT_FULL_DATE_LOCAL_MARKET_LISTING_AND_LIFECYCLE_CAPTURE; ChecksTotal=6; ChecksPassed=5; ChecksFailed=1; Verdict=BLOCK; OpenRisks=Independent_Reviewer_A_B_C_unavailable,Trial1_missing_return_abstention_mismatch,W3_authority_compile_open; NextAction=Hash_manifest_then_fix_abstention_then_compile_W3_before_Trial1_open

ClosureValidation: PASS

SAWBlockValidation: PASS
