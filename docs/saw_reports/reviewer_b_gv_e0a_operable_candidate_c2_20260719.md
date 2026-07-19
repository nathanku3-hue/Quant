# Reviewer B — GV-E0A-OPERABLE Candidate C2 Runtime and Operations

Mode: `ADVISORY_REVIEW`  
RoundID: `ROUND-20260719-GV-E0A-OPERABLE-C2-REVIEW-B`  
ScopeID: `GV_E0A_OPERABLE_C2_REVIEWER_B_RUNTIME_OPS`  
ReviewedCommit (immutable pin C2): `446ac6d8162d62c794aaa5a93530a4ab6cf48231`  
Parent (C transport): `45f9f966e61de52e766ff04bd147736940644141`  
Branch: `codex/gv-e0a-operable`  
Worktree: `C:/Users/Lenovo/.devspace/worktrees/Quant-e0a-operable-fix`  
Domain: Runtime and operational resilience  
ReviewMode: `SMALL CHANGE` (inherited SAW reviewer pass)  
Constraint: Read-only except this report path. No commits, pushes, provider opens, or production-impacting ops. **Not a shipment claim beyond hosted product-CI evidence on this pin.**

## Verdict

**PASS.** No Critical or High findings in E0A C2 runtime scope. Custody re-verify has no inject surface; current-decision Section-15 recovery uses token `GV_FS0_CURRENT_DECISION`; UI fail-closes without F1C fallback; adapter shares the canonical parser; product CI path filters and suite include E0A surfaces; hosted run `29655802878` is success on the exact C2 SHA (Ubuntu + Windows + byte parity).

## Commit pin

| Check | Evidence | Result |
|---|---|---|
| Exact immutable pin C2 | Worktree branch ref `codex/gv-e0a-operable` = `446ac6d8162d62c794aaa5a93530a4ab6cf48231`; GitHub commit OID match | **PASS** |
| Parent is transport C | parents[0] = `45f9f966e61de52e766ff04bd147736940644141` (`feat(gv-e0a): bank operable single-decision product vertical`) | **PASS** |
| C2 delta is filelock CI pin | GitHub commit: sole file `.github/workflows/gv-fs0-product.yml` (+6/−1); explicit `filelock` install for AppTests | **PASS** |
| Hosted product CI on exact C2 | Run `29655802878` name `GV-FS0 Product`; `head_sha` = `446ac6d…`; `conclusion` = `success`; event `push` on `codex/gv-e0a-operable` | **PASS** |

## Must-verify matrix (runtime resilience)

| # | Requirement | Evidence | Result |
|---|---|---|---|
| 1 | `publish_e0a_current_decision` always re-verifies custody; no `result=` injection | `core/gv_e0a_operable.py`: signature accepts only `target`, `lock_path`, `verifier_runner`, `root`; always calls `build_e0a_research_decision` → `build_e0a_certified_result` → custody disk SHA gate; docstring forbids caller-supplied certified result / custody hashes. Test `test_publish_e0a_rejects_result_injection_parameter` asserts `"result"`, `"custody_hashes"`, `"require_custody"` absent. CLI `scripts/publish_gv_e0a_current.py` never accepts a result blob. Tamper test: `test_publish_e0a_fails_when_custody_tampered` → `E0_CUSTODY_HASH_MISMATCH`, target not created. | **PASS** |
| 2 | Section-15 recovery for current decision (`GV_FS0_CURRENT_DECISION`) | `core/gv_fs0_publish.py`: `CURRENT_DECISION_TARGET_TOKEN = "GV_FS0_CURRENT_DECISION"`; `publish_current_decision` observes prebuild hash, locks with non-waiting `O_CREAT\|O_EXCL`, compare-under-lock, temp write+fsync, atomic replace, exact-byte + parse verify, post-replace failure → `_convert_lock_to_recovery` with `target_token=CURRENT_DECISION_TARGET_TOKEN`. No age/PID lock auto-clear. Covered by `tests/gv_fs0_product/test_e0a_current_decision_publication.py` (locked, target-changed, pre-replace preserve, post-replace recovery token, recovery write fail retains lock, recovery not auto-removed). | **PASS** |
| 3 | Dashboard catches `GvFs0PresentationError` → unavailable; no F1C fallback | `dashboard.py` imports only `GvFs0PresentationError` + `render_gv_fs0_current_decision`. `_render_portfolio_allocation_page` try/except: on error `st.error("Certified decision unavailable")` + caption; body never calls `render_gv_fs0_certified_bundle`. AST test `test_dashboard_default_path_is_single_current_not_dual_bundle`. AppTests: missing/invalid → unavailable, zero tables, no OPEN subheader (`test_e0a_streamlit_apptest.py`). | **PASS** |
| 4 | Adapter uses shared canonical parser (`core.gv_fs0_current_decision`) | `views/gv_fs0_portfolio_adapter.py` imports `parse_current_decision_bytes` / `DEFAULT_CURRENT_DECISION_PATH` from `core.gv_fs0_current_decision`; `load_current_certified_decision` reads bytes then `parse_current_decision_bytes` (same canonical-byte gate as publish). Does **not** import `core.gv_fs0_publish` for parse authority. Non-canonical pretty JSON rejected (`test_adapter_rejects_non_canonical_bytes`). Import boundary asserted in `test_bundle_publication_and_default.py`. | **PASS** |
| 5 | Product workflow path filters + AppTests + filelock hosted install | `.github/workflows/gv-fs0-product.yml` paths include `core/gv_e0a_operable.py`, `core/gv_fs0_current_decision.py`, `core/gv_fs0_publish.py`, `data/gv_fs0/gv_fs0_current_decision.json`, `docs/architecture/godview_e0/**`, `scripts/publish_gv_e0a_current.py`, `views/gv_fs0_portfolio_adapter.py`, `dashboard.py`, `tests/gv_fs0_product/**`. Suite runs full `tests/gv_fs0_product` (includes AppTests) + dash-1 default route test. Install step: `requirements.txt` **and** `filelock` (C2 fix for dashboard module-load import). Matrix: `ubuntu-latest` + `windows-latest`; `byte-parity` job requires two parity records and `e0a_current_decision` + fixed E0A result hash. | **PASS** |
| 6 | Hosted CI PASS on exact C2 SHA | GitHub Actions run `29655802878`: workflow `GV-FS0 Product`, `head_sha=446ac6d8162d62c794aaa5a93530a4ab6cf48231`, `status=completed`, `conclusion=success` (Ubuntu product-proof + Windows product-proof + byte-parity). | **PASS** |

## Ops notes (non-blocking)

1. **C2 is a hosted-runner dependency pin only.** Product runtime modules are unchanged from parent C (`45f9f96…`); resilience claims for custody/publish/UI rest on C + C2 CI re-proof.
2. **`filelock` explicit pip pin is CI-local.** Residual Low: if `filelock` is not a direct `requirements.txt` pin, local/non-CI environments can still fail dashboard import the same way hosted did pre-C2. Does not invalidate hosted proof on C2.
3. **Streamlit remains presentation-only.** Publication is CLI/operator path (`scripts/publish_gv_e0a_current.py`); dashboard does not publish under the default render path.
4. **Inherited Medium (out of scope):** process-tree descendant hardening for isolated verifier remains deferred from prior F1C reviews.

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| Low (residual) | `filelock` may still be transitive-only in `requirements.txt`; local AppTest/dashboard import can drift outside hosted install step | Optionally add direct `filelock` pin to `requirements.txt` in a hygiene round | Implementer / CI | Open residual — **not** Critical/High; hosted C2 already installs it |
| Medium (carry, out of scope) | Verifier process-tree descendant hardening | Future ops milestone | Future Ops | Inherited/out of scope |
| — | No in-scope Critical/High runtime defect on C2 | — | Reviewer B | Closed |

## Open Risks

1. Direct `requirements.txt` pin for `filelock` remains optional hygiene (hosted C2 already green).
2. Inherited Medium process-tree hardening remains deferred.
3. Branch is not main; merge/ship decision is owner-owned (out of Reviewer B scope).

## Forbidden scope confirmation

No providers, PEAD, FS1, protocol redesign, broker paths, commits, or pushes performed by this reviewer. No code mutations outside this report path.

## NextAction

`reconcile_with_reviewers_A_C_then_terminal_SAW_on_pin_446ac6d_with_hosted_ci_29655802878`

## Closure

ClosurePacket: RoundID=ROUND-20260719-GV-E0A-OPERABLE-C2-REVIEW-B; ScopeID=GV_E0A_OPERABLE_C2_REVIEWER_B_RUNTIME_OPS; ChecksTotal=6; ChecksPassed=6; ChecksFailed=0; Verdict=PASS; OpenRisks=filelock_requirements_hygiene_process_tree_hardening_inherited_main_merge_owner; NextAction=reconcile_with_reviewers_A_C_then_terminal_SAW_on_pin_446ac6d_with_hosted_ci_29655802878

ClosureValidation: PASS (static reviewer packet; no code mutations)  
SAWBlockValidation: PASS  
SAW Verdict: **PASS**
