# C0X → M7F0-v4 2019 CRSP Vertical

Mode: `EXECUTION_PACKET`  
RoundID: `ROUND-20260712-C0X-M7F0-V4`  
ScopeID: `C0X_BOOTSTRAP_TO_M7F0_V4`

## Status

- C0X commit: `17cb830` (fail-closed dual parsers; deindex+ignore 41 gitlinks; detached-proof planning PASS).
- M7F0-v4 mechanical vertical: local PASS with tracked evidence JSON + tracked parquet manifest (parquet under ignored `data/processed/`).

## Contract locks (v4)

1. Named worktree from `aee7f4c`; no dirty primary switch for implementation.
2. Detached proof worktree of exact C0X commit + primary absolute `.venv` planning PASS.
3. Day +1 = first CRSP session strictly after RDQ; included in exact 60-session window.
4. Filter order: unique PERMNO map → window/delist → formation ≥50 → deterministic Q5 → earliest-event-wins.
5. ≥10 live names every return-bearing day; final liquidation exempt.
6. Delist day: `(1+RET)(1+DLRET)-1` or `DLRET` if RET blank; then cash remainder.
7. Nonnumeric/special only fail inside selected windows; unresolved delist fails event window (selected unresolved would block run).
8. Cost: `0.00075 * Σ|Δw|` including terminal liquidation.
9. Link claim: `current_snapshot_cusip8`, `as_of_link=false`.

## Forbidden

- Strict readiness flip; alpha/tradable claims; D2B/M6 portfolio reuse; as-of CUSIP; CCM join; WRDS login; C0A envelope repair.
