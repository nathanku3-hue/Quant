# Lane 2 status — 2026-08-09

## Custody

- Worktree: `.worktrees/devspace-053ca7a4f582fb3e` (`codex/pit-source-authority-1`)
- Strategic lock: `docs/architecture/aov_strategic_direction_lock_20260809.md`
- Vintage authority: `docs/architecture/historical_fundamental_vintage_authority.md`
- `financial_alpha_evidence` remains **0**
- Prospective Clock #1 left untouched; outcomes sealed

## Authority gate (supersedes opportunistic A1 drive)

```text
HISTORICAL_A1_A2 = BLOCKED UNTIL VINTAGE + PARITY CLOSE
```

Current tree still carries the material contradiction:

- replay requires `FilingVer=Original`
- capture scripts request/emit `Current/Restated`
- A1 report path has claimed `historical_spg_asof_original=true`

**No A1/A2 economic admission is permitted** until Quant/Data freezes one provider-vintage authority, removes the losing active path/label, and current↔historical AOV same-input parity passes.

Capture / merge / unit tests may continue as **instrumentation only**. They do not earn A1/A2.

## Market (instrumentation progress)

- Warmup complete: `data/aov0/historical/raw/market_warmup_to_20250516` parts **000–032** (2024-07-08 → 2025-05-16, 217 sessions, 96 CIQ securities with any history)
- Backfill in progress: `market_backfill_to_20240705` parts for SMA200 + 252-day horizon readiness
- Gap capture `market_gap_20250623_20250919` deprioritized while backfill owns Excel

## Fundamentals / cash (instrumentation)

- Official SOFR historical admitted: `nyfed_sofr_20230101_20260807.json` (897 rows, 2023-01-03 → 2026-08-06)
- Period matrix + transition captures not yet landed under a frozen winning vintage
- Do **not** treat mixed Original / Current/Restated bytes as A1-ready

## Code / tests

- Historical AOV replay machinery present and unit-tested (local historical aov0 suite)
- Driver `scripts/aov0_lane2_a1_driver.ps1` remains a **post-gate** tool: may not admit A1 economics while the vintage contradiction stands

## Operational blocker (Excel/CIQ)

Excel/CIQ automation can become unstable after repeated capture restarts (`CO_E_SERVER_EXECUTION_FAILURE`, modal CIQ dialogs, null add-in). Warmup proved the pipeline works when Excel/CIQ is healthy. Recovery is operational, not strategic.

### Recovery recipe (manual or next agent)

1. Close all Excel via Task Manager; wait 30s
2. Start Excel interactively once; dismiss any **CIQ Pro Office Tools** dialogs
3. Confirm CIQ ribbon formulas work (`=SPG(...)` smoke)
4. Resume bounded capture only as instrumentation

## Ordered next steps

1. **P0 — Vintage:** prove provider semantics; choose Option A (Original) or Option B (explicit as-of Current/Restated schema); remove losing active path/label (`historical_fundamental_vintage_authority.md`)
2. **P0 — Parity:** same-input current↔historical AOV economic parity proof
3. Recover Excel/CIQ; finish market backfill under the frozen vintage
4. Capture fundamentals / period matrix / transitions under the **winning** FilingVer only
5. Run A1 five-arm exact frozen replay **only after** steps 1–2; admit only if ≥252 trading days + CIQSEC + gates
6. Freeze A2 contract only if A1 `candidate_pass`; one-shot held-out A2 after freeze
7. Historical CIQ workers: start at 2 after vintage freeze; scale to 3–4 only from measured stability

## Non-claims

- No A1/A2 economic admission yet
- No Parent/Child mutation
- No prospective outcome open
- No financial-alpha uplift
- Strategy live capital remains closed
