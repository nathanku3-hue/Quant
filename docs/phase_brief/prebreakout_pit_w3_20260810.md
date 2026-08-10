# W3 Phase Brief — PREBREAKOUT PIT Authority

**Date:** 2026-08-10
**State:** `W3_MECHANICS_CLOSED / DATA_GATE_OPEN / B_MINUS_1_PIT_AUTHORITY_UNAVAILABLE`
**Owner boundary:** PIT source/identity/availability/corporate actions only

## Shipped in this slice

- New fail-closed W3 authority compiler: `research/prebreakout_pit_v1/authority.py`.
- Date-local risk-set contract: `PREBREAKOUT_US_PRIMARY_COMMON_DATE_LOCAL_V1`.
- Exact risky identity: `CIQSEC:IQ...` + numeric Trading Item + exact `SPT<trading_item>` alias.
- Date-local primary proof only: provider date-local primary or exact date-local unique qualifying listing; ambiguous primary state excludes deterministically.
- Availability law: candidate/action `observed_at <= available_at <= as_of`; source observed range cannot extend past the decision session; prospective receipt retrieval must be `<= as_of`; historical later retrieval is legal only with mechanically bound historical as-of semantics.
- Source-complete corporate-action row for every candidate; effective terminal/unresolved events exclude; no alternate-listing rescue.
- Hard rejection of current-survivor/current-primary projection and ticker/entity/PERMNO/alternate-listing fallback.
- Content-addressed authority packet with semantic reopen validation and zero Alpha/capital/outcome authority.
- Generic B-1 smoke proof bound to immutable W2 authority `PREBREAKOUT_W2_CONTRACT_v1`, `breakout_contract_sha256=94c8756e11d4e31cbf4d6ca4953b63c83306f4b357a42f0b70c94ae3fd261e71`, and exact source-derived B/B-1 sessions.
- MU/SNDK historical pre-W2 proof retained at statistical/promotion weight zero and explicitly removed from current authority.
- Frozen pre-capture acquisition manifest: `docs/architecture/prebreakout_pit_acquisition_manifest_v1.json` (`f3cac696...473dc3f`), including raw-byte-only W9 coordination and separate PREBREAKOUT/CRV1 admission semantics.
- Real provider capture executed later under explicit user authority: 346 date-local market/listing sessions, 1,894,207 rows, 5,919 companies / 6,018 exact listings, plus 12/12 filtered lifecycle parts covering the same 5,919-company union. Evidence=`docs/context/e2e_evidence/prebreakout_w3_real_data_capture_20260810.json`.
- MU/SNDK exact identities resolved generically from the captured bytes: MU=`CIQSEC:IQ289030 / 2630498`; SNDK=`CIQSEC:IQ1860586153 / 1929119896`. Frozen W2 mechanics yield 11/12 accepted breakout episodes respectively; all remain zero-weight traces.

## Current real blocker

W2 is now immutably frozen and bound:

```text
W2 authority version         = PREBREAKOUT_W2_CONTRACT_v1
methodology/breakout hash    = 94c8756e11d4e31cbf4d6ca4953b63c83306f4b357a42f0b70c94ae3fd261e71
B                            = strict close > prior 20-session high
accepted-episode cooldown    = 20 full observed sessions
B-1                          = immediately prior observed listing session
TTFLD window                 = B-20 ... B-1
```

Raw source custody is now complete for the captured fast-path corpus. The remaining blocker is **compilation**, not acquisition: the 346-session market/listing bytes and 12/12 lifecycle parts have not yet been compiled into exact date-local W3 authority packets with corporate-action state for each required B-1 date. AOV-109/current-primary custody is not a legal substitute.

Current gate state for both named smoke cases therefore remains `B_MINUS_1_PIT_AUTHORITY_UNAVAILABLE`. This is a blocker and never a pass. Current receipt=`docs/context/e2e_evidence/prebreakout_pit_w3_current_gate_20260810.json`; raw-capture evidence=`docs/context/e2e_evidence/prebreakout_w3_real_data_capture_20260810.json`.

Receipt `docs/context/e2e_evidence/prebreakout_pit_w3_mu_sndk_20260810.json` remains historical pre-W2 custody only; its `BREAKOUT_CONTRACT_UNBOUND` reason is not current authority and does not satisfy the W2 smoke obligation.

## Validation

Final validation: W3 focused=`17/17 PASS`; W2+W3 frozen-handshake=`24/24 PASS`; adjacent W2/W3 + W9 CIQ admission + historical identity/lifecycle=`40/40 PASS`; selected compile, JSON/hash/state reconciliation and `git diff --check` PASS. Coverage includes exact identity, all forbidden fallback flags, historical as-of requirement, availability, corporate-action completeness/effective/unresolved state, deterministic B-1 eligible/excluded/absent outcomes, active null/drifted W2-hash rejection, historical-only receipt classification, current B-1 unavailable blocker semantics, packet tamper, and wrong-date B-1 rejection.

## Next legal action

1. Stop new W3 abstraction/provider discovery. Build one deterministic hash manifest over both landed market directories plus all 12 filtered lifecycle parts.
2. Compile exact date-local primary state and complete exact-listing corporate-action state into W3 authority packets for the required development/lockbox dates; current Primary Issue remains forbidden.
3. Regenerate generic zero-weight MU/SNDK B-1 proofs across all retained W2 episodes. `PIT_ELIGIBLE_B_MINUS_1` requires a downstream immutable flag in `B-20..B-1`; canonical deterministic exclusion is valid; `DETERMINISTIC_UNAVAILABLE` remains a blocker.
4. Before Trial #1 is charged, fix the outcome-blind Trial-1 loader so provider-missing total-return rows follow the already-frozen `abstain score=0 / no imputation` policy instead of aborting the whole frame; do not change scientific windows/thresholds/model/control/folds/holdout/objective. Rehash the code bundle afterward.
5. Only after exact W3 + Trial-1 source/code manifests are frozen may W2 append real `TRIAL_OPEN #1`; W4/W5 may then run. W6 stays untouched until the surviving candidate is frozen.

Provider acquisition was performed in the later fast-path slice using the existing authenticated CIQ session. No W4 outcome access, Trial-1 charge, statistical development result, W6 lockbox read, prediction append, Parent/Child mutation, broker order, replication outcome, or capital action was performed.
