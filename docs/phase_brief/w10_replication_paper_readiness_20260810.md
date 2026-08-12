# W10 — Replication / PAPER Readiness — 2026-08-10

**Scope:** quarantined independent-replication identity/PIT/license readiness plus PAPER-0 capturability/reconciliation engineering.  
**Explicit exclusions:** replication outcomes, provider access, credentials, broker orders, strategy-live authority, financial-alpha evidence.  
**Current verdict:** `KEEP_OPEN_LOW_PRIORITY / PAPER_READINESS_PARTIAL / FIRST_PAPER_ORDER_BLOCKED / REPLICATION_NOT_READY / PREBREAKOUT_NONBLOCKING`.

**Priority law:** W10 is an external/operational readiness lane only. It must never consume shared capacity needed by PREBREAKOUT stock-data evidence or Clock #1 custody.

## Delivered

### PAPER-0

- Added `ExecutionIntentV1` with exact authority fields required by `docs/architecture/paper_0_authority.md`.
- Intent hash and deterministic `client_order_id` derive from the full authority object; policy/TIF mutation outside `MOC_CLOSE_AUCTION_V1 + cls` fails closed.
- Added exact single-account `CIQSEC + SPT trading-item ↔ broker symbol + broker asset-id` execution-map custody with ambiguity rejection and content hash.
- Added `SessionCloseAuthorityV1`; no fixed-16:00 fallback exists. Only an externally verified actual close or verified regular full-session record is accepted.
- Added stale `rebalance_epoch` fencing and `FREEZE_NEW_RISK` buy blocking before a PAPER order dictionary can be built.
- Rebalancer now propagates an explicitly supplied `time_in_force`; legacy callers that omit TIF retain their historical behavior.
- Alpaca recovery parity now requires exact non-default TIF, so a recovered `day` order cannot satisfy a PAPER `cls` intent.
- Added canonical PAPER live-state projection including order lifecycle, open orders, partial-fill residuals, positions, cash, equity, and a state hash that commits residual/open risk.
- Added restart semantics: every restart begins frozen; exact account/rebalance/epoch/map/position/cash/equity/order-state reconciliation clears the freeze; mismatch preserves it.
- Added a read-only Alpaca reconciliation snapshot for account identity, positions, open orders, and recent order states. It makes no submit/cancel/replace/close call.
- Added exact broker-snapshot → canonical PAPER-state translation through broker asset-id + symbol mapping; unknown open orders fail closed.
- Admitted a real official-NYSE **completed-session readiness receipt** for 2026-08-07 as `VERIFIED_REGULAR_FULL_SESSION`, hash-bound to `data/paper0/readiness/session_close/nyse_regular_full_session_20260807.source.json`. This does not authorize a future order: the eventual PAPER date still requires its own fresh date-specific close receipt.
- Frozen the PAPER-0 account-activity decision: a separate fill-by-fill account-activity surface is **not required for the first PAPER operational-learning event** while broker account/positions/cash/equity/open-orders/recent-order state + cumulative filled quantity reconcile exactly. Bust/correction or exact fill/fee/venue attribution remains PAPER-1/deferred unless a discrepancy forces earlier promotion.
- Ran the real execution-map preflight. The CIQ side is frozen and clean at 99 unique CIQSEC/SPT/ticker rows, but no real broker account/asset mapping was admitted because PAPER credentials are absent from the current execution environment. No credential contents were read and no broker asset/order request was made.

### Independent replication readiness

- Added `research/replication_readiness_v1` metadata-only quarantine contract.
- Added write-once quarantine custody and explicit denial of replication outcomes/family-specific acquisition authority.
- Added initial WRDS/CRSP-Compustat-IBES candidate receipt at `data/replication_quarantine/readiness_v1/wrds_5table_readiness_20260810.json`.
- Frozen `WRDS_5TABLE_PERMANENT_IDENTITY_V1`: risky-security identity is CRSP PERMNO; PERMCO is company grouping only; current ticker/name/CUSIP fallback is forbidden; I/B/E/S ticker cannot become CRSP identity without a separately authorized date-effective crosswalk.
- Frozen `WRDS_5TABLE_PIT_VINTAGE_V1`: economic dates are not availability timestamps; same-session EOD market rows cannot be used before close; date-effective name/CCM links are mandatory; `fundq` current/restated values cannot be relabeled original-vintage without proof; I/B/E/S revision chronology cannot be collapsed to latest.
- Wrote immutable readiness v2 `data/replication_quarantine/readiness_v1/wrds_5table_readiness_20260810_v2.json`: identity and PIT readiness move to `FEASIBLE`, but overall readiness remains honestly `NOT_READY` because table-level entitlement/source evidence, license/retention evidence, and latency remain unresolved.
- Recorded `data/replication_quarantine/evidence_status/wrds_entitlement_license_retention_status_20260810.json`: no qualifying non-secret entitlement/license/retention evidence is present in local repo authority. No WRDS/provider access or credential/secret inspection occurred.

## Acceptance status

| Check | Status | Evidence |
|---|---|---|
| Intent binds account/rebalance/policy/seal/map/instrument/side/qty/policy/TIF/epoch | PASS | `tests/test_paper0_authority.py` |
| Authority mutation changes identity or fails closed | PASS | `tests/test_paper0_authority.py` |
| `MOC_CLOSE_AUCTION_V1 → market + cls` survives rebalancer boundary | PASS (local fake) | `tests/test_paper0_authority.py` |
| Recovery with wrong TIF is rejected | PASS (local fake) | `tests/test_paper0_authority.py` |
| accepted → partial → open residual → fill projection | PASS | `tests/test_paper0_authority.py` |
| accepted → partial → canceled residual projection | PASS | `tests/test_paper0_authority.py` |
| restart starts frozen and exact mismatch preserves freeze | PASS | `tests/test_paper0_authority.py` |
| broker account/position/open/recent-order capturability | PASS (local fake) | `tests/test_paper0_authority.py` |
| replication outcomes inaccessible in readiness contract | PASS | `tests/test_replication_readiness_v1.py` |
| quarantine storage is write-once and path constrained | PASS | `tests/test_replication_readiness_v1.py` |
| real frozen execution map for first PAPER rebalance | BLOCKED | CIQ 99-row source is frozen; current runtime has no PAPER credentials, so no real broker account/asset IDs could be admitted without inventing them |
| verified exchange/session-close readiness receipt | PASS | real official-NYSE 2026-08-07 regular-full-session receipt admitted; every future PAPER order still requires a date-specific receipt |
| narrow account-activity/fill surface for PAPER-0 | NOT REQUIRED | decision receipt defers fill-by-fill activity to PAPER-1 unless discrepancy/bust/correction/exact fill attribution requires it |
| replication permanent-identity contract | PASS | `WRDS_5TABLE_PERMANENT_IDENTITY_V1`, SHA-256 bound in readiness v2 |
| replication PIT/vintage contract | PASS | `WRDS_5TABLE_PIT_VINTAGE_V1`, SHA-256 bound in readiness v2 |
| non-secret WRDS entitlement evidence | BLOCKED EXTERNAL | existing exact-table request remains evidence-missing; local repo has no qualifying attributable evidence |
| license / retention evidence | BLOCKED EXTERNAL | no qualifying attributable license/retention evidence landed; no status promotion made |
| family-specific replication acquisition | FORBIDDEN | remains `NOT_AUTHORIZED`; no replication preregistration exists |

## Validation

Focused local validation remains broker-order/provider-output free:

```text
python -m pytest tests/test_paper0_authority.py tests/test_replication_readiness_v1.py tests/test_execution_controls.py -q
→ 89 passed
```

This evidence-only continuation did not change execution code.

## Custody / ownership note

The canonical `docs/decision log.md` and `docs/lessonss.md` were already modified by other active lanes when W10 began. W10 did not overwrite or append to those shared dirty surfaces. This brief and the W10 architecture note carry the lane-local decision/lesson record until the shared-doc owner reconciles them.

## Next W10 action

1. **Do not schedule W10 ahead of PREBREAKOUT.** Resume only on independent/external capacity.
2. In an environment where existing PAPER credentials are already supplied, run one bounded read-only account + assets lookup and freeze the real 99-row `PaperExecutionMapV1`; do not submit/cancel/replace an order and keep `FREEZE_NEW_RISK=true`.
3. Obtain or formally decline the exact non-secret WRDS entitlement + license/retention evidence requested in `V2_D0_2`; only qualifying hash-bound evidence may advance those readiness statuses.
4. Leave replication outcomes inaccessible and family-specific acquisition `NOT_AUTHORIZED` until a future family-specific replication preregistration exists.
