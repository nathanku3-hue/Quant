## What Was Done
- Completed the sparse-engine core: DuckDB direct aggregation, global trading-calendar `return_idx:int32`, `entry_idx/exit_idx` interval bounds, numeric-only projected relations, object-dtype rejection, single-thread compensated aggregation, and canonical daily SHA-256 output hashing.
- Turnover continues to preserve entry, overlap, exit, and final trade-to-zero parity; no wide matrix, chunking, physical repartitioning, Numba, or multiprocessing was added.
- Focused M6 PASS 12/12; M5a+M6 PASS 16/16; broader PEAD PASS 109/109; 11,798,280-position-day smoke is within the configured bound.

## What Is Locked
- Engine completion does not satisfy M6b data readiness. Strict EPS vintage, delisting-adjusted tradable returns, and full as-of tradability/liquidity remain absent and fail closed.
- No provider/data/UI/alpha/ranking/action/real-curve scope was opened.

## What Is Next
- **Single next action: obtain independent Reviewer A/B/C terminal review for the completed M6a.1 core; only then start M6b data-prep for its independent data gates.**
- `V2-PEAD-M6A-SCALE-SPARSE-PORTFOLIO-ENGINE`: core implementation complete locally; independent SAW review pending.
- `V2-PEAD-M6B-DATA-PREP`: blocked by independent strict data decisions.
- `V2-PEAD-REAL-RUN-EQUITY-CURVE`: blocked until M6b closes its data contract.

## First Command
`.venv\\Scripts\\python.exe -m pytest tests\\test_pead_m6_pit_walk_forward_equity_curve.py -q`
