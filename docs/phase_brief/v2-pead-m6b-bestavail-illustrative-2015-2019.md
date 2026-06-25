# V2 PEAD M6b Best-Available Illustrative 2015-2019

## Mode

`EXECUTION_PACKET`

## Round

- `RoundID`: `ROUND-20260625-V2-PEAD-M6B-BESTAVAIL-OPTION1`
- `DataGate ScopeID`: `V2_PEAD_M6B_DATA_GATE_BESTAVAIL_POLICY_READ_ONLY`
- `Run ScopeID`: `V2_PEAD_M6B_RUN_BESTAVAIL_ILLUSTRATIVE_2015_2019_STANDALONE`

## Owner decision locked

Option 1 is selected: read-only validation plus a standalone flagged diagnostic curve. Option 2 is rejected because a reusable best-available input adapter would erode the firewall between best-available B and future strict A data.

## Required sequence

1. `M6b-DATA-GATE`: read-only audit and owner policy decision only. It emits no curve and no daily-return parquet.
2. `M6b-RUN-BESTAVAIL`: standalone 2015-2019 illustrative diagnostic only. It must remain isolated from strict M6b and alpha paths.

## Data gate result

The policy gate accepts best-available local data only with hard flags:

- restated/current-vintage Compustat EPS via local D1/fundq-derived artifact,
- local Compustat return proxy via local D2A/secd-derived artifact,
- no delisting adjustment,
- single-source/provider-limited Compustat basis,
- coverage capped to 2015-2019 for B claims.

Gate artifact:

```text
docs/context/e2e_evidence/pead_m6b_data_gate_bestavail_policy_20260625.json
```

The gate sets:

```text
curve_emitted = false
daily_return_parquet_emitted = false
m6b_strict_readiness = false
usable_for_alpha_inference = false
```

## Standalone run artifact names

The standalone diagnostic is isolated under these names:

```text
docs/context/e2e_evidence/pead_m6b_bestavail_illustrative_2015_2019.json
data/processed/pead_m6b_bestavail_illustrative_2015_2019_daily_returns.parquet
```

These names are intentionally separate from strict M6 paths.

## Required claim ceiling

Every output, chart, table, and report must carry all eight flags:

```text
illustrative_only
restated_vintage
no_delisting
survivorship_biased
coverage_2015_2019
provider_limited
not_alpha
not_tradable_claim
```

The output also carries:

```text
no_delisting_adjustment = true
m6b_strict_readiness = false
usable_for_alpha_inference = false
```

## Boundary

No provider ingestion, no strict M6b readiness flag change, no M6a evidence flag change, no dashboard alpha path, no ranking/scoring, no alerts/recommendations, no live/paper route, and no broker/order path are authorized.

## Value statement

B is a half-real end-to-end sanity check of the M6a.1 sparse engine only. It does not materially advance the alpha question. Alpha/tradable conclusions remain deferred to strict Path A with separately authorized data.

## Implementation paths

- `scripts/pead_m6b_bestavail_illustrative_2015_2019.py`
- `tests/test_pead_m6b_bestavail_illustrative_2015_2019.py`
- `docs/context/e2e_evidence/pead_m6b_data_gate_bestavail_policy_20260625.json`

## Repair note - 2026-06-25

Reviewer A/C terminal-window BLOCK and Reviewer B generation/commit concerns were repaired in one ordered round:

1. B selection now filters events before the engine so `entry_idx + holding_period_sessions - 1 <= max_return_idx` inside the 2015-2019 return calendar.
2. `--commit-bestavail-run` now runs the data gate first, stages B JSON/parquet, then performs rollback-protected public replacement of the run package.

Formula:

```text
full_window_eligible_event := searchsorted(return_calendar, decision_date, side="right") <= len(return_calendar) - holding_period_sessions
```

Repaired evidence:

```text
selected_events_after_signal_filter = 27941
selected_events_with_incomplete_60_session_window = 0
daily_rows = 975
daily_range = 2016-01-15..2019-11-27
parquet_sha256 = 10bba1fb7189af3c629a28e9ef39d674db80fe9816bbf4a13254384ea1eda01e
```

## Validation note

- Direct data-gate CLI passed and wrote `docs/context/e2e_evidence/pead_m6b_data_gate_bestavail_policy_20260625.json`.
- Direct `--commit-bestavail-run` passed and wrote `docs/context/e2e_evidence/pead_m6b_bestavail_illustrative_2015_2019.json` plus `data/processed/pead_m6b_bestavail_illustrative_2015_2019_daily_returns.parquet`.
- B focused pytest passed 5/5.
- M6 sparse-engine pytest passed 12/12.
- Compile passed for `scripts/pead_m6b_bestavail_illustrative_2015_2019.py`.
- Combined two-file pytest command was blocked by the tool safety filter; the same files passed separately.
