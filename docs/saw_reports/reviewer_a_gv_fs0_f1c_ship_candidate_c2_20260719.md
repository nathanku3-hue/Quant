# Reviewer A — GV-FS0 F1C-SHIP Candidate C2 Strategy and Regression (Re-pin)

Mode: `ADVISORY_REVIEW`  
RoundID: `ROUND-20260719-GV-FS0-F1C-SHIP-CANDIDATE-C2-REVIEW-A`  
ScopeID: `GV_FS0_F1C_SHIP_CANDIDATE_C2_REVIEWER_A_STRATEGY_REGRESSION`  
Hierarchy Confirmation: Approved | Session: current-thread | Trigger: inherited SAW reviewer re-pin pass (SMALL CHANGE) | Domains: Strategy correctness and regression risks | FallbackSource: owner F1C-SHIP candidate C2 pin + prior C reports on `48ad053`

Reviewer role: strategy correctness and regression risks only.  
Reviewer posture: independent, read-only. No code edits outside this report path, no commit, no push, no providers. **Not a shipment claim.**

Worktree: `C:/Users/Lenovo/.devspace/worktrees/Quant_c0x_m7f4_v8-6cb847fa`  
ReviewedCommit (immutable pin C2): `91b9bf1459439443298886ad6acc4a6181154431`  
Parent C (immutable): `48ad053dc21d7dda3c8280dcbd3c332584cc184a`  
Base F1B: `c37db092f092f00ad615109815bfacb13124c4da`  
Branch intent: `codex/gv-fs0-f1-product`  
Python pin intent: `E:/Code/Quant/.venv/Scripts/python.exe` (live pytest not re-executed in this re-pin session)

## Re-pin notice

Prior Reviewer A/B/C on parent C `48ad053dc21d7dda3c8280dcbd3c332584cc184a` **remain valid for product scope** (economics, publication codes, adapter, default authority, no providers). This pass is a **re-pin after CI portability / Windows CRLF fix only**. C2 changes **only** `.gitattributes` with pin `data/gv_fs0/gv_fs0_certified_bundle.json text eol=lf` so Windows checkout keeps **55774 LF bytes**.

## Verdict

**PASS.** No Critical or High strategy/regression findings on exact candidate C2. Strategy surface is identical to parent C.

## Commit pin and C2 delta

| Check | Evidence | Result |
|---|---|---|
| Exact C2 pin | Worktree `HEAD` (`E:/Code/Quant/.git/worktrees/Quant_c0x_m7f4_v8-6cb847fa/HEAD`) = `91b9bf1459439443298886ad6acc4a6181154431`. Branch ref `codex/gv-fs0-f1-product` = same OID. `logs/HEAD` records `48ad053…` → `91b9bf1…` message `fix(gv-fs0): pin permanent bundle LF for Windows hosted parity`. GitHub commit API matches. | **PASS** |
| Parent is C | GitHub parents[0] and `logs/HEAD` parent = `48ad053dc21d7dda3c8280dcbd3c332584cc184a` | **PASS** |
| C2 delta only `.gitattributes` | GitHub commit stats: total 1 addition, 0 deletions; sole file `.gitattributes`; patch adds only `data/gv_fs0/gv_fs0_certified_bundle.json text eol=lf` | **PASS** |
| `git show HEAD:.gitattributes` equivalent | Worktree + GitHub contents@C2: four lines including architecture LF, contracts JSON LF, contracts bin `-text`, and bundle `text eol=lf`. Blob OID `3f770a71f5f852b9af7140582835cbe9a4d6b106` | **PASS** |
| Bundle blob identity vs parent C | `data/gv_fs0/gv_fs0_certified_bundle.json` git blob OID `2a2887723363044466c218d5a3aab0a82d4171ad` and size **55774** identical at C and C2 (GitHub contents + git blob API) | **PASS** |

## Must-verify checklist (prior C findings re-confirmed)

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Exact commit is C2 `91b9bf1…` | **PASS** | Worktree HEAD + branch + GitHub |
| 2 | OPEN terminal economics: shares 10, cash 904, NAV 1044 | **PASS** | Permanent bundle OPEN presentation/terminal unchanged (shares `10`, cash `"904"`, NAV `"1044"`). Product tests still hard-code path. C2 did not touch product modules or bundle bytes. |
| 3 | NO_POSITION flat: shares 0, cash/NAV 1000 | **PASS** | Bundle NO_POSITION presentation/terminal unchanged. |
| 4 | Permanent bundle two-role OPEN then NO_POSITION, CERTIFIED both; length 55774; file SHA-256 `a9dda224…`; bundle_hash `527c86b9…` | **PASS** | Blob OID stable; size 55774; tests/constants/commit messages pin SHA-256 `a9dda224da21ab4abfe1f27afdb2875bb34f240d469caf20a90b7e635adb96e5` and hash `527c86b9e50386bf9e5847037642910b47b81697dbf089df3038099feab6282c`. |
| 5 | No legacy `strategy_replay` authority for FS0 certification | **PASS** | `strategies/strategy_replay.py` still `__authority__ = "REVOKED_BY_GV_FS0_20260716"`. Unchanged vs C. |
| 6 | Default portfolio route is certified-bundle authority | **PASS** | `dashboard.py::_render_portfolio_allocation_page` sole call remains `render_gv_fs0_certified_bundle(st)`. Unchanged vs C. |
| 7 | `.gitattributes` LF pin present for permanent bundle | **PASS** | Line `data/gv_fs0/gv_fs0_certified_bundle.json text eol=lf` present at C2. |

## Strategy correctness notes

1. **C2 is transport/portability only** — no economics, role order, certification, adapter, or default-route mutation.
2. **Prior A findings on `48ad053` carry forward** for product strategy scope.
3. **Windows CRLF root cause** (hosted checkout materializing 55775 CRLF bytes) is addressed by the LF pin; strategy identity remains the banked 55774 / `a9dda224…` object.
4. **Not shipment** — C2 message explicitly requires A/B/C re-pin; hosted Windows product green + byte-parity still gate ship/push claims.

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| None | No in-scope strategy or economic regression on C2 | None | Reviewer A | Closed |
| Low | Live focused pytest not re-executed in this Reviewer A re-pin session | Optional live confirm on C2 pin | Reconcile / SAW | Residual evidence gap, not strategy defect |
| Low (carry) | Truth surfaces may still lag candidate custody text | Refresh bridge/done after closeout T | Docs/Ops | Out of strategy scope |

## Ownership statement

Reviewer A is independent of implementer ownership for candidate C2, used the pinned worktree at exact `91b9bf1…`, and performed read-only strategy/regression re-pin verification only. No provider, PEAD, FS1, protocol redesign, historical suite repair, commit, or push.

## NextAction

Reconcile with Reviewer B and Reviewer C on exact pin `91b9bf1459439443298886ad6acc4a6181154431`; require hosted Windows product green and Windows/Linux product byte-parity before any shipment or push claim. Do not restore default replay/optimizer authority.

## ClosurePacket

```
ClosurePacket: RoundID=ROUND-20260719-GV-FS0-F1C-SHIP-CANDIDATE-C2-REVIEW-A; ScopeID=GV_FS0_F1C_SHIP_CANDIDATE_C2_REVIEWER_A_STRATEGY_REGRESSION; ChecksTotal=7; ChecksPassed=7; ChecksFailed=0; Verdict=PASS; OpenRisks=live_pytest_not_rerun_in_A_session_not_shipment; NextAction=reconcile_with_reviewers_B_C_then_hosted_windows_parity_and_terminal_SAW_before_ship_or_push
```

SAW Verdict: **PASS**
