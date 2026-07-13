# M7F4-v8 EXACT_SELF_FINANCING_IDENTITY

Mode: `EXECUTION_PACKET`
RoundID: `ROUND-20260712-M7F4-V8-EXACT-SELF-FINANCING-IDENTITY`
ScopeID: `M7F4_V8_EXACT_SELF_FINANCING_IDENTITY`
Branch: `c0x/m7f4-v8`
Base: `3bc6aed84a41da1fdd2db01226b0dc527789384a`
Implementation: `m7f4-v8`
Lineage rule: V8 has no active predecessor compatibility or supersession interface; claim ceiling remains unchanged.

Hierarchy Confirmation: Approved by inherited owner GO | Session: current-thread | Trigger: resumed-execution | Domains: Quant Research, Portfolio Accounting, Data Integrity, Docs/Ops | FallbackSource: active M7F3 brief plus repository specification

## Purpose and current score

Commit A `3671b849dc1f87b4462f980810d25bc3af53367c` is a genuine functional accounting milestone, but Slice 2 remains blocked pending A2. Current score is **68/100**: accounting 82, lineage 64, closure 40, research validity near **30/100** because the CUSIP8 link is a non-PIT snapshot. A2 is limited to checkout identity binding, exact selection enforcement, and true predecessor retirement before any new 2019 evidence run.

## Locked accounting identity

For day `t`, maintain explicit equity dollars, event-cash dollars, and global idle-cash dollars with `NAV_open,t`.

1. Solve open cost against actual post-cost equity trades:

   `C_open,t = 0.00075 × Σ_i |w_target_equity,i,t × (NAV_open,t − C_open,t) − E_open,i,t|`

   The contraction is solved deterministically to absolute residual tolerance `1e-14 × max(1, NAV_open,t)`.

2. Open cost and reduced target capital:

   `NAV_after_open_cost,t = NAV_open,t − C_open,t`

   `c_open,t = C_open,t / NAV_open,t`

   Allocate all active target sleeves from `NAV_after_open_cost,t`. If there are zero active slots, preserve all post-cost NAV in explicit global idle cash. Initial capital is injected exactly once; exhausted NAV is never recapitalized.

3. Apply `RET` to live equity only; cash return is zero and dead write-down sleeves remain zero.

4. Charge mandatory close equity exits once:

   `C_close,t = 0.00075 × close_equity_trade_dollars,t`

   `c_close,t = C_close,t / NAV_after_ret,t`

   Then scale all surviving dollar sleeves, including global idle cash, by the post-close-cost NAV ratio.

5. On the terminal day, liquidate equity sleeves only:

   `C_terminal,t = 0.00075 × terminal_equity_trade_dollars,t`

   `c_terminal,t = C_terminal,t / NAV_before_terminal,t`

   Event cash and global idle cash contribute zero terminal turnover.

6. Report separately:

   `daily_pre_cost_gross_return,t = NAV_after_ret,t / NAV_after_open_cost,t − 1`

   `daily_net_return,t = NAV_end,t / NAV_open,t − 1`

   `NAV_pre_cost_gross_end,t = NAV_open,t × (1 + daily_pre_cost_gross_return,t)`

   `NAV_cost_drag_dollars,t = NAV_pre_cost_gross_end,t − NAV_end,t`

   The cumulative net-return path must equal the explicit carried NAV state within absolute tolerance `1e-10`.

## Audit defects and required repairs

- D1: Costs must alter carried next-day state, not only the displayed return series.
- D2: Scale-all open costs require deterministic fixed-point parity with actual post-cost equity trade dollars.
- D3: Equity-to-cash and cash-to-equity transitions must enter actual equity trade dollars exactly once.
- D4: Zero active slots must preserve NAV in global idle cash; zero NAV must never restart at one.
- D5: Terminal liquidation must exclude event cash and global idle cash.
- D6: Duplicate `(return_date, event_id)` rows must fail closed.
- D7: Git-blob SHA-256 is authoritative; worktree SHA-256 is diagnostic. CRLF/LF-only differences are allowed only when normalized source bytes are identical; all other worktree/blob differences block execution. No fallback authority exists.
- D8: Publish both event-set hash and canonical selected-row hash over stable selection columns.
- D9: Persist flattened bridge parity inputs and outputs (`prev_prc`, `next_prc`, `next_ret`, `gap_prc`, absolute error, tolerance, pass/fail) in ledger columns and evidence summary.
- D10: Terminal SAW later requires explicit in-scope/out-of-scope blocks and validator-clean Reviewer A/B/C artifacts.
- D11: Every Git subprocess must remove all ambient `GIT_*` selectors/config overrides, disable replacements, bind one repository top-level/Git-dir/common-dir context, and reject any `refs/replace/*` before resolving commit, tree, branch, or blob.
- D12: Before any map, ledger, curve, evidence, or manifest output is published, final selection must equal count `2448`, event-set SHA-256 `caeccc642e5d052b211cc5ecfc335bf4f63d0fd7d63018a6b40c5d6965ad2e6d`, and canonical-row SHA-256 `7f336eefaf7de6840a907a94361297111a2abc66702ad41b0aa0733016435749`.

## Commit sequence

- **Commit A (`3671b84`):** v8 functional accounting engine, focused tests, this brief, initial v7 CLI retirement. No full 2019 run.
- **Commit A2:** sanitize and bind all Git identity calls; reject replacement refs; enforce the exact 2,448-event/count/hash contract before outputs; reduce v7 to a true stub; rerun committed-checkout audit. No full 2019 run.
- **Commit A2.1:** replace the stale residual-evidence count reference with `selection_contract["n_selected_events"]`; add a regression that executes the real residual-evidence publication branch; discard failed-run partial outputs before a fresh rerun. No policy or runtime redesign.
- **Commit B:** only after A2.1 audit GO, run the unchanged 2019 Slice 2 with source-session continuity asserted; publish evidence, ledger, manifests, neutral-carry/write-down legs, and Shapley blocks.
- **Commit C:** independent Reviewer A/B/C, validated SAW, decision/lesson/formula records, and seven current-truth surfaces.

## Commit-A acceptance checks

- V8 tests import v8 and pass at `>=38` focused tests.
- Duplicate position-days raise `M7F4BlockedError`.
- Fixed-point open cost equals `0.00075 × actual post-cost equity trade dollars` within the locked tolerance and is deterministic.
- Same-weight equity-to-cash transition is charged exactly once.
- Zero-active dates preserve post-cost NAV in global idle cash; subsequent re-entry uses carried cash without capital injection.
- Exhausted NAV blocks rather than recapitalizing.
- Cost-reduced NAV is the next day’s open state.
- Every open/close/terminal stage records base NAV, cost rate, trade dollars, and charged dollars with exact identities.
- True pre-cost gross return is separated from effective NAV cost drag.
- Pure cash terminal state has zero liquidation turnover; residual equity is charged once.
- Canonical selection-row hash is shuffle-stable and content-sensitive.
- Bridge parity values/errors are replayable from flattened ledger columns and evidence helpers.
- Missing committed blob, out-of-root code path, normalized worktree/blob mismatch, repository/Git-dir/common-dir mismatch, ambient Git splice, or replacement ref blocks identity; newline-only CRLF/LF difference passes with Git blob authoritative and no fallback.
- Count/hash mismatch blocks before map, ledger, curve, evidence, or manifest mutation.
- The real residual-evidence branch writes `n_selected_event_set` from the verified selection contract and publishes evidence plus both manifests without an undefined-symbol failure.
- The predecessor module contains only an exit-`2` stub and directs execution to v8 without engine exports, imports, call-through, aliases, fallback, or argument forwarding.
- Only the exact four A2 paths are staged; no evidence output or truth-surface close is included.

## Expected Commit-A2.1 paths

- `docs/phase_brief/v2-pead-m7f4-v8-exact-self-financing-identity.md`
- `scripts/pead_m7f4_v8_2019_crsp_vertical.py`
- `tests/test_pead_m7f4_v8_2019_crsp_vertical.py`

## Forbidden scope

- Full 2019 rerun or data-output generation before Commit A.
- Readiness or `m6b_data_contract_ready` promotion.
- Alpha/tradable/strategy/UI work.
- CCM, WRDS/provider access, or historical/as-of link work.
- Event-id production allowlists.
- Neutral carry described as a finite upper bound.
- Compatibility alias, supersession metadata, fallback authority, or active predecessor executable path.
- Remote, push, merge, publication, or dispatch action.

## Live loop state

- Slice 0: brief and functional accounting contract banked.
- Slice 1 / Commit A: banked at `3671b84`; committed-checkout tests passed 38/38, but audit found identity splicing, unenforced selection identity, and retained v7 engine complexity.
- Slice 1A / Commit A2: banked at `dd80c46`; committed checkout passed 44/44 and compile. The first Slice 2 attempt survived the high-memory scans but failed during residual-evidence assembly on an undefined stale count variable.
- Slice 1A.1 / Commit A2.1: bounded repair replaces the stale count reference and adds a real residual-evidence publication regression. Focused suite passes 45/45 and compile; commit and fresh committed-checkout audit remain.
- Slice 2: blocked until A2.1 is immutable and audit returns GO; then rerun unchanged 2019 with source-session continuity asserted from a new clean worktree.
- Slice 3: blocked until Commit B evidence exists.
