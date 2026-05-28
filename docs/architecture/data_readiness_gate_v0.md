# Data Readiness Gate v0 — Narrow Implementation Brief

Status: implementation-ready brief
Date: 2026-05-26
Primary objective: turn Terminal Zero boot from “Streamlit starts” into “trusted local research data is safe.”

## 1. First implementation question

The first implementation question is:

> What is the minimal route-required dataset contract for Portfolio & Allocation strict boot?

Answer: Portfolio & Allocation strict boot should be split into route subcontracts. The gate should not try to certify every possible dashboard behavior at once.

## 2. Minimal Portfolio & Allocation route contract

### Route ID

```text
portfolio_allocation.strict.v0
```

### Global route invariants

```text
read_only = true
provider_calls_allowed = false
canonical_writes_allowed = false
broker_calls_allowed = false
live_overlay_allowed = false
scan_refresh_allowed = false
replay_rebuild_allowed = false
automatic_repair_allowed = false
allowed_boot_write = runtime/boot_status_current.json
```

### Subroute A — current optimizer/allocation readiness

This subroute certifies that the current optimizer universe and current allocation controls can use local data safely.

Required for strict trusted output:

| Input | Minimal path/contract | Class | Strict behavior |
| --- | --- | --- | --- |
| Historical dashboard package | `load_unified_data(mode="historical", top_n=2000, start_year=2000, universe_mode="top_liquid")` | derived from canonical | FAIL if prices or returns are empty, slot-swapped, duplicate-dated, duplicate-columned, nonfinite in selected route, or unreadable. |
| Price source | `data/processed/prices_tri.parquet` preferred; fallback `data/processed/prices.parquet` plus `data/processed/yahoo_patch.parquet` if route policy allows | canonical / governed local patch | FAIL if no valid local price source exists. |
| Returns | Loader-returned returns frame, usually from `total_ret` | canonical / derived from canonical | FAIL on price/return slot corruption or impossible return distribution in selected assets. |
| Ticker map | `data/processed/tickers.parquet` and loader-returned `ticker_map` | canonical | FAIL if any selected nonzero-weight asset or open position cannot map ticker ↔ permno. |
| Selected/current assets | derived from `build_optimizer_universe(...)`, selected assets, open lifecycle holds, or durable replay selection | route state | FAIL if strict output needs an asset with missing history, stale endpoint, or missing mapping. |
| Price endpoint freshness | `build_price_endpoint_freshness(prices_wide)` | derived check | FAIL if any selected nonzero-weight asset fails endpoint parity under policy. Planning WARN. |
| Scan payload | `data/last_scan_state.json` | cache/evidence, not canonical market data | Required only when building optimizer universe from today’s scan. Missing/legacy scan means strict current-optimizer output is unavailable; do not refresh during boot. |
| Position memory / lifecycle state | `data/portfolio_lifecycle_log.jsonl`, `data/portfolio_positions.json` | evidence/derived operational state | Validate only if used. Missing is WARN unless open-position route depends on it. |
| Sector map | `data/static/sector_map.parquet` | governed static | Required only when sector cap or sector display is trusted. Otherwise WARN/optional. |
| Fundamentals payload | loader-returned `fundamentals_wide` | canonical/derived depending source | Required only because current dashboard gates the Portfolio Builder on `fundamentals_wide is not None`. The gate should record this as a page-render dependency, not an optimizer-math dependency. |

Strict rule: no stale selected asset may be repaired with live overlay during boot. If the route would need `repair_stale_price_endpoints_with_live_overlay`, strict boot fails with:

```text
selected asset stale; provider/live overlay refresh not authorized during boot
```

### Phase-close classification

Strict missing local governed artifacts are a data-readiness block, not a code
regression. When the strict data gate fails because required local artifacts are
missing, `scripts/boot_preflight.py` must report the failure as:

```text
CodeReady = PASS_WITH_DATA_QUARANTINE
DataReadyStrict = BLOCKED_MISSING_LOCAL_ARTIFACTS
BootReady = BLOCKED_DATA_READY_STRICT
```

`CodeReady` only means the boot-control code and GitHub proof may be clean. It
does not authorize safe boot, research trust, replay trust, dashboard promotion,
or provider repair. `BootReady` remains blocked until the governed local
artifacts are present and the strict data-readiness gate passes.
This quarantine applies only when all strict blockers are governed local artifact
absence; schema, corruption, unreadable, duplicate, slot-swap, or return-bound
defects remain `CodeReady = BLOCKED_DATA_CONTRACT`.

### Subroute B — daily replay / YTD / replay allocation snapshot readiness

This subroute certifies the replay-facing Portfolio & Allocation surfaces.

Required for strict trusted output:

| Input | Minimal path/contract | Class | Strict behavior |
| --- | --- | --- | --- |
| PIT universe | `data/processed/universe_r3000_daily.parquet` | canonical PIT | FAIL if missing, empty, malformed, outside requested replay window, or duplicate `(date, permno)` in checked window. |
| Price source | `data/processed/prices_tri.parquet` preferred; fallback `prices.parquet` + `yahoo_patch.parquet` only if policy allows | canonical | FAIL if missing or unable to cover requested replay dates/assets. |
| Return source | `total_ret` from price source/loader | canonical/derived | FAIL on malformed, nonfinite required values, slot corruption, or absurd returns. |
| Ticker map | `data/processed/tickers.parquet` | canonical | FAIL if any selected allocation/replay asset cannot map. |
| Replay selection | `PortfolioReplaySelection` equivalent: method, max_weight, risk_free_rate, replay_assets, latest_price_date, signature | route state | v0 should require a durable request/selection input for strict replay certification. If only Streamlit session state knows it, boot cannot certify replay output globally. |
| Replay controls | method, max_weight, risk_free_rate, Rule100 candidate frame if Rule100 | route state/evidence | FAIL if nonfinite, missing, or signature-mismatched. |
| Replay dates | YTD/horizon dates derived from local price index | derived | FAIL if no replay dates or requested window outside local data/PIT coverage. |
| Saved replay artifact | `data/runtime_cache/strategy_replay/*.selected_method_replay.parquet` + `.manifest.json` | cache/evidence-only | Strict FAIL only if the dashboard would reuse it and identity/signature/window/row-count/schema checks fail. Missing is WARN unless strict replay output requires saved-artifact-only mode. |
| Lifecycle annotations | `data/portfolio_lifecycle_log.jsonl` | evidence/derived | WARN if absent; FAIL if present but malformed and displayed as trusted replay evidence. |
| Buy/sell decisions | `data/portfolio_lifecycle_buy_sell_log.jsonl` | evidence/derived | WARN if absent; FAIL if present but malformed and displayed as trusted replay evidence. |
| Rule100 history | `data/processed/rule100_softmax_v1_history.csv` | derived/evidence | Required only when method is Rule of 100. FAIL if selected method is Rule of 100 and required columns are missing. |

Strict replay rule: v0 should not rebuild a replay. It may probe the selected saved artifact or declare replay output not certified. Transitional in-memory replay build belongs to dashboard runtime, not boot certification.

### Durable certification addendum — 2026-05-28

The strict gate may now move selected endpoint and replay checks from `WARN` to
`PASS` only through durable registry certificates:

```text
data/registry/portfolio_selected_endpoint_certification_v0.json
data/registry/portfolio_replay_selection_certification_v0.json
```

Both certificates must be repo-relative, non-session-state, not expired,
`route_id = portfolio_allocation.strict.v0`, and
`review_scope_id = ROUND-20260527-DATA-READINESS-CERTIFICATION`. They must set
`provider_calls_allowed=false`, `repair_during_boot_allowed=false`, and
`rebuild_during_boot_allowed=false`, and every referenced artifact must exist
with matching `sha256` and optional `size_bytes`.

`data/processed/yahoo_patch.parquet` remains governed optional evidence. Missing
`yahoo_patch` is still a strict `WARN` unless the selected endpoint certificate
contains an explicit `yahoo_patch_policy` with
`patch_required=false` and `no_patch_certified=true`. Boot must not infer that a
missing patch is harmless and must not repair or rebuild the patch.

These certificates are proof of local data/replay-selection readiness only. They
do not promote strategy results, validate alpha, authorize recommendations,
write runtime status, call providers, or regenerate replay artifacts.

### Subroute C — benchmark/YTD display readiness

Required only when benchmark-relative performance is displayed as trusted.

| Input | Minimal path/contract | Class | Strict behavior |
| --- | --- | --- | --- |
| SPY/QQQ local benchmark columns | local price package or approved benchmark source | canonical/derived | WARN if absent for planning; FAIL if trusted benchmark return is displayed. |
| Live benchmark overlay | local anchored overlay only if pre-existing and explicitly display-only | cache-only/display-only | No provider call in boot. No overlap anchor means overlay ignored. |

## 3. Machine-readable contracts to add first

### `docs/context/data_artifact_taxonomy_current.json`

Add a small JSON taxonomy with these artifact classes:

```text
canonical
derived
cache_only
evidence_only
disposable
```

Each artifact entry should include:

```text
path_glob
taxonomy
source_quality
required_for
writable_during_boot
repair_policy
strict_missing_status
planning_missing_status
notes
```

### `docs/context/portfolio_allocation_route_contract_v0.json`

Add a route contract with:

```text
route_id
schema_version
strict_invariants
subroutes
required_inputs
optional_inputs
fail_closed_conditions
planning_warnings
```

This route contract is the source of truth for WARN vs FAIL.

## 4. Files to add

```text
core/data_readiness_gate.py
scripts/run_data_readiness_gate.py
docs/architecture/data_readiness_gate_v0.md
docs/context/data_artifact_taxonomy_current.json
docs/context/portfolio_allocation_route_contract_v0.json
tests/test_data_readiness_gate.py
tests/test_data_readiness_gate_write_guard.py
```

## 5. Files to touch

```text
launch.py
tests/test_provider_ports.py
```

Optional later touch, only if existing helpers are insufficient:

```text
data/provenance.py
```

Do not touch optimizer/replay behavior in the first slice unless a failing test proves a tiny helper extraction is necessary.

## 6. v0 gate stages

### Stage 1 — context contract

Reuse `scripts/build_context_packet.py --validate` or equivalent importable validation logic.

Strict FAIL if current-truth context is missing, invalid, or contradictory.
Planning WARN/FAIL depending severity.

### Stage 2 — route contract + taxonomy load

Load and validate:

```text
docs/context/data_artifact_taxonomy_current.json
docs/context/portfolio_allocation_route_contract_v0.json
```

Strict FAIL if either file is missing or malformed after they are introduced.

### Stage 3 — git/worktree classification

Read git status and `docs/context/dirty_worktree_manifest.md`.

Strict local boot may allow `classified_dirty`, but strict FAIL on unclassified dirty files in:

```text
canonical data
provider code
provenance code
boot gate code
source files that define route behavior
tests that define data contracts
```

Safe GitHub boot should additionally require clean worktree and upstream alignment.

Detached clean worktrees may satisfy phase-close GitHub proof through
`--expected-ref` and `--expected-sha`, where boot preflight compares local
`HEAD` with `git ls-remote origin refs/heads/<expected-ref>`. A detached
worktree without upstream and without expected proof fails as proof unavailable.

`scripts/governance_preflight.py` is not required for BOOT-0A phase-close. It is
deferred to BOOT-0B with the context-packet dependency set and must not be
retroactively treated as a BOOT-0A failure.

### Stage 4 — provider boundary

No direct provider import/call from the gate.

Strict FAIL if boot calls:

```text
yfinance
Alpaca
build_market_data_provider
download_recent_close_prices
repair_stale_price_endpoints_with_live_overlay
run_and_save_scan
broker APIs
```

### Stage 5 — canonical presence

Route-aware presence probe only. For Portfolio & Allocation v0, check:

```text
data/processed/prices_tri.parquet OR data/processed/prices.parquet
data/processed/tickers.parquet
data/processed/universe_r3000_daily.parquet when replay strict output is required
data/universe/pinned_thesis_universe.yml
```

Do not scan all `data/processed`.

### Stage 6 — price/return sanity

Use fixture-backed and selected-asset checks:

```text
monotonic dates
no duplicate dates after normalization
no duplicate columns
price levels positive and level-like
returns bounded and return-like
finite required selected cells
endpoint parity for selected/current assets
```

Do not run a full matrix audit in v0.

### Stage 7 — PIT/pinned universe

Check:

```text
universe mode = r3000_pit for replay certification
PIT file exists/nonempty
(date, permno) not duplicated in checked window
requested replay dates covered
selected assets intersect PIT members as of route dates
pinned manifest loads
pinned tickers resolve or fail closed when route uses them
```

### Stage 8 — selected replay artifact probe

Probe only the selected/latest artifact that the dashboard would reuse. Do not scan all runtime cache.

FAIL if reused artifact has:

```text
missing dashboard_cache_signature after producer contract exists
signature mismatch
method/control mismatch
run_id/source_id/method_id blank
manifest/parquet row mismatch
schema mismatch
artifact_scope mismatch
date_window mismatch
source file signature mismatch
budget violation
```

WARN if no artifact is present and dashboard can avoid reuse or label replay as not certified.

### Stage 9 — write guard

Run the gate inside a file mutation guard. The only allowed automatic write is:

```text
runtime/boot_status_current.json
```

`docs/context/boot_status_current.json` is a legacy fallback/read path during
the BOOT-0A migration, not the canonical generated runtime verdict. No markdown
companion or alternate durable boot-status path is part of v0.

Strict FAIL if any other file changes, appears, disappears, or has modified hash/mtime/size.

## 7. Minimal `boot_status_current.json` for v0

The canonical v0 payload lives at `runtime/boot_status_current.json`.
`docs/context/boot_status_current.json` is legacy compatibility evidence only.

v0 should implement a smaller payload than the target schema:

```json
{
  "schema_version": "data_readiness_gate.v0",
  "generated_at_utc": "2026-05-26T00:00:00Z",
  "mode": "strict",
  "overall_status": "FAIL",
  "planning_status": "PASS",
  "strict_status": "FAIL",
  "route_id": "portfolio_allocation.strict.v0",
  "boot_contract": {
    "read_only": true,
    "provider_calls_allowed": false,
    "canonical_writes_allowed": false,
    "broker_calls_allowed": false,
    "replay_rebuild_allowed": false,
    "repairs_performed": []
  },
  "git_alignment": {
    "local_head": "",
    "remote_head": "",
    "head_matches_remote": null,
    "dirty_worktree_status": "unknown"
  },
  "checks": [],
  "route_readiness": {
    "portfolio_allocation.optimizer_current": "DEFER",
    "portfolio_allocation.daily_replay": "DEFER",
    "portfolio_allocation.benchmarks": "DEFER"
  },
  "summary": {
    "blockers": [],
    "warnings": [],
    "next_actions": []
  }
}
```

## 8. Tests to add first

```text
tests/test_data_readiness_gate.py
  - planning can PASS/WARN while strict FAILS on stale selected asset
  - strict FAILS when route contract is missing/malformed
  - strict FAILS when required canonical price source is missing
  - strict FAILS when tickers.parquet is missing for selected assets
  - strict FAILS on price/return slot swap
  - strict FAILS on duplicate dates or duplicate asset columns
  - strict FAILS when PIT universe is missing for replay-trusted route
  - strict FAILS when pinned manifest is missing/malformed for pinned route
  - strict WARNs on missing replay artifact when replay can be marked uncertified
  - strict FAILS on replay artifact mismatch when artifact would be reused
  - boot_status_current.json records provider_calls_allowed=false and canonical_writes_allowed=false

tests/test_data_readiness_gate_write_guard.py
  - gate writes only runtime/boot_status_current.json
  - gate rejects non-boot-status output paths
  - gate fails if parquet, manifests, runtime cache, scan cache, lifecycle logs, or provider-derived files mutate
  - gate fails if atomic-write `.tmp` residue appears under guarded data/cache roots
  - gate fails if provider/live overlay code path tries to write a cache

tests/test_provider_ports.py additions
  - boot gate modules do not import yfinance directly
  - boot gate modules do not import Alpaca provider directly
  - boot gate modules do not call build_market_data_provider
  - strict preflight rejects provider-call attempts
```

## 9. Commands for first slice

```text
.\.venv\Scripts\python -m pytest tests\test_data_readiness_gate.py -q
.\.venv\Scripts\python -m pytest tests\test_data_readiness_gate_write_guard.py -q
.\.venv\Scripts\python -m pytest tests\test_provider_ports.py -q
.\.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py -q
.\.venv\Scripts\python -m pytest tests\test_portfolio_universe.py tests\test_pinned_universe.py -q
.\.venv\Scripts\python -m pytest tests\test_strategy_replay_artifact.py -q
.\.venv\Scripts\python scripts\build_context_packet.py --validate
.\.venv\Scripts\python scripts\run_data_readiness_gate.py --mode planning
.\.venv\Scripts\python scripts\run_data_readiness_gate.py --strict
.\.venv\Scripts\python launch.py --preflight --mode planning
.\.venv\Scripts\python launch.py --preflight --strict
```

## 10. Definition of done for v0

v0 is done when:

```text
1. The accepted direction is documented.
2. The artifact taxonomy JSON exists and validates.
3. The Portfolio & Allocation route contract JSON exists and validates.
4. The gate writes runtime/boot_status_current.json only when explicitly requested and nothing else.
5. Strict boot blocks trusted output on missing/stale/malformed route-required data.
6. Planning boot can open with warnings.
7. Provider calls are impossible during gate execution.
8. Tests prove no canonical data, manifests, replay artifacts, provider caches, or scan caches mutate during boot.
```
