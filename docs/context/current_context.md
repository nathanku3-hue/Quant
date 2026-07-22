## Active Addendum — GV-ALPHA0_ACTIVE (2026-07-23)

- **Train:** **GV-ALPHA0_ACTIVE** — end-to-end Alpha product by 2026-07-30 intent.
- **Main:** PR #8 merged at `2c7f32c` (substrate `29cfeff`). B0B banked as **source family one**.
- **Metrics:** score **39**; stage **CERTIFIED_SINGLE_DECISION_OPERABLE**; observed **0**.
- **Hard rules:** ADMITTED never auto-ADVANCE; formal comparison deferred after Alpha; case promote is result-last fail-closed (not rollback atomicity).
- **B0A:** CLOSED/BANKED unchanged.
- **Next (no stop):** exact authorized source family two → 3–5 facts + operator capture + certified result as one vertical → later reconciliation/export/dogfood on the same train.

## What Was Done
- B0B official SEC accession `0000723125-26-000015` admitted; claim INSUFFICIENT; HOLD → paper NO_POSITION.
- R2 rebuild-from-raw; R2.1 auth-object set + parity pins; ALPHA0 strict JSON/byte locators/atomic promote.
- Stale worker direction toward B0B-closure/comparison revoked.

## What Is Locked
- `GV-ALPHA0_ACTIVE` is sole active product train language.
- Source family one = B0B MU package; independent_source_count=1 until family two banks.
- No live capital, no score uplift, no formal human comparison gate for Alpha.

## What Is Next
```text
authorize + bank independent source family two (exact objects)
→ extract 3–5 case-specific facts
→ operator decision capture
→ certified paper NO_POSITION result
→ (later) reconciliation / export / fresh-clone / dogfood
```

## First Command
`.venv\Scripts\python -m pytest -q tests/gv_fs0_product/test_v2_b0b_official_source_intake.py`
