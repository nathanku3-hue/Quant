# GV-FS0 Protocol V1.1 — Verifier Input/Output Compatibility

Status: Active compatibility amendment (does not rewrite frozen V1 schema bytes)
Date: 2026-07-18
Mode: `EXECUTION_PACKET`
Protocol ID: `GV_FS0_PROTOCOL_V1` (semantics)
Compatibility ID: `GV_FS0_PROTOCOL_V1_1_VERIFIER_IO`
Authority: frozen V1 contract `docs/architecture/gv_fs0_certification_and_data_authority_contract.md` §10–§11; freeze commit `c007895`

## Why V1.1 exists

Frozen V1 already defines `gv_fs0_verifier_input_v1` with:

```text
schema_version
protocol
decision
source_prices
source_intents
```

The independent reconstruction engine shipped at freeze still required legacy:

```text
prices
events
```

A schema-valid V1 verifier input was therefore rejected (`SCHEMA_KEYS_INVALID` / unknown `source_*`). That blocked F1A product certification, which must feed the frozen verifier only original fixture/decision projections — never primary generated events.

V1.1 repairs **only** verifier engine I/O compatibility. It does **not** redesign ranks, slots, ownership, certification, publication, or UI.

## Normative V1.1 rules

1. The isolated reconstruction engine accepts **only** `schema_version = gv_fs0_verifier_input_v1`.
2. Root keys must be exactly `schema_version`, `protocol`, `decision`, `source_prices`, `source_intents`.
3. Presence of legacy `prices` or `events` is fail-closed with `LEGACY_VERIFIER_INPUT_PROHIBITED`.
4. `source_prices` use `close_price` + `price_timestamp` + `source_sequence` (V1 projection).
5. `source_intents` are original economic intents only. The engine maps them to independent reconstruction events; it never consumes primary ledgers, snapshots, certifications, components, or bundles.
6. OPEN requires exactly one `EXECUTION_INTENT`, one `EXPLICIT_FEE` (same session as execution), one `DIVIDEND_DECLARATION`, one `DIVIDEND_PAYMENT_INSTRUCTION`, and at least one `VALUATION_INSTRUCTION`.
7. NO_POSITION requires only `VALUATION_INSTRUCTION` intents (zero execution/fee/dividend intents).
8. Engine identity remains process-only: `sys.executable -I -X utf8 validation/gv_fs0_reconstruction.py --input <file>`.
9. Reconstruction result schema version is `GV_FS0_RECONSTRUCTION_RESULT_V1_1` with `protocol_compat_version = GV_FS0_PROTOCOL_V1_1_VERIFIER_IO`. Economic comparison fields remain under `economic_payload` for independent hash comparison. Formal controller wrapping into attempt records still follows frozen `gv_fs0_verifier_result_v1` at product certification time.
10. Frozen V1 JSON schemas, tables, registries, vectors, and freeze manifest under `contracts/gv_fs0/v1/` remain **byte-immutable**. This amendment changes the reconstruction engine and tests only.

## Explicit non-goals

- No same-version edit of frozen V1 contract artifact bytes.
- No F1A PortfolioBook / certification / Streamlit implementation in this amendment.
- No providers, real data, FS1, or legacy replay authority.

## Evidence

```text
tests/test_gv_fs0_reconstruction_isolation.py  # V1 input golden economics + legacy reject
python -c "import glob,pytest,sys; sys.exit(pytest.main(['-q',*glob.glob('tests/test_gv_fs0_*.py')]))"
```

## Next

Resume F1A on the product branch: Decision → Book → Snapshots → two verifier attempts with schema-valid `gv_fs0_verifier_input_v1` → Certification → final adapter injection.
