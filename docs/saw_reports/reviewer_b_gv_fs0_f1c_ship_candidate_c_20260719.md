# Reviewer B — GV-FS0 F1C-SHIP Candidate C Runtime and Operations

Mode: `ADVISORY_REVIEW`
RoundID: `ROUND-20260719-GV-FS0-F1C-SHIP-C-REVIEW-B`
ScopeID: `GV_FS0_F1C_SHIP_C_REVIEWER_B_RUNTIME_OPS`
ReviewedCommit: `48ad053dc21d7dda3c8280dcbd3c332584cc184a`
Branch: `codex/gv-fs0-f1-product`
Worktree: `C:/Users/Lenovo/.devspace/worktrees/Quant_c0x_m7f4_v8-6cb847fa`
Domain: Runtime and operational resilience
ReviewMode: `SMALL CHANGE` (inherited SAW reviewer pass)
Constraint: Read-only. No edits, commits, pushes, or provider opens.

## Verdict

**PASS.** No Critical or High findings in F1C product scope.

## Commit pin

| Check | Evidence | Result |
|---|---|---|
| Exact immutable pin | Worktree `HEAD` resolves to `48ad053dc21d7dda3c8280dcbd3c332584cc184a` via `E:/Code/Quant/.git/worktrees/Quant_c0x_m7f4_v8-6cb847fa/HEAD` | PASS |

## Must-verify matrix

| # | Requirement | Evidence | Result |
|---|---|---|---|
| 1 | Pin exact commit `48ad053…` | Worktree HEAD matches pin exactly | PASS |
| 2 | `core/gv_fs0_publish.py` implements contract §15 with **only** registered codes | Codes emitted: `PUBLICATION_LOCKED`, `PUBLICATION_TARGET_CHANGED`, `PUBLICATION_POST_REPLACE_VERIFICATION_FAILED`, `PUBLICATION_RECOVERY_RECORD_FAILED`. `__all__` exports exactly those four. No additional `PUBLICATION_*` tokens in module. | PASS |
| 3 | No age/PID automatic lock removal | `_acquire_lock` uses non-waiting `O_CREAT\|O_EXCL`; existing lock → `PUBLICATION_LOCKED`. No mtime/PID/stale-age break path. Tests assert lock retention with old utime. | PASS |
| 4 | Adapter loads permanent validated bytes only; no adapter-owned accounting/certification | `views/gv_fs0_portfolio_adapter.py` loads via `read_certified_bundle` defaulting to `data/gv_fs0/gv_fs0_certified_bundle.json`. Presentation binding checks only; no publish/certify/book/accounting imports. | PASS |
| 5 | Verifier remains process-only / not library truth | `validation/gv_fs0_reconstruction.py` raises `GV_FS0_RECONSTRUCTION_PROCESS_ONLY` when `__name__ != "__main__"`. Certification invokes `sys.executable -I -X utf8` subprocess only. Product modules forbid importing reconstruction as library. | PASS |
| 6 | Product workflow Ubuntu+Windows proof + byte parity | `.github/workflows/gv-fs0-product.yml`: matrix `ubuntu-latest` + `windows-latest` product-proof; `byte-parity` job compares exact parity JSON artifacts across OS | PASS |
| 7 | No provider/network/broker paths in F1C product modules | Grep of `core/gv_fs0_*.py` product surface and adapter: no yfinance/requests/httpx/urllib/broker/wrds/ibkr/alpaca/network use. Authority tests forbid those import prefixes. | PASS |
| 8 | Dashboard default renderer uses certified bundle without silent legacy fallback | `_render_portfolio_allocation_page` sole body call is `render_gv_fs0_certified_bundle(st)`. Caption labels legacy replay/optimizer as non-certifying. No try/except silent fallback. Default nav page is Certified Portfolio. | PASS |

## Publication protocol §15 (runtime resilience detail)

`core/gv_fs0_publish.py` matches contract §15:

1. **Observe before build** — `_target_hash` records prebuild SHA or `ABSENT`.
2. **Non-waiting exclusive lock** — `os.open(..., O_CREAT|O_EXCL|O_WRONLY)`; `FileExistsError` → `PUBLICATION_LOCKED`.
3. **Compare under lock** — identical bytes → `IDEMPOTENT` + normal release; concurrent change → `PUBLICATION_TARGET_CHANGED` + normal release; no last-writer-wins.
4. **Replace path** — unique temp in target dir, write+flush+fsync, `os.replace`, directory fsync (best-effort where supported), exact-byte + SHA reread, schema parse.
5. **Post-replace failure** — durable recovery record (`RECOVERY_REQUIRED`) replaces lock; code `PUBLICATION_POST_REPLACE_VERIFICATION_FAILED`; no auto-rollback claim.
6. **Recovery write failure** — existing lock retained; code `PUBLICATION_RECOVERY_RECORD_FAILED`.
7. **Normal lock release only** when no replace + unchanged, replace verified, or idempotent match. Crash mid-flight leaves lock (fail-closed; operator recovery).

Product tests cover locked retention, target-changed non-overwrite, pre-replace preserve+release, post-replace recovery lock, recovery-write failure retention (`tests/gv_fs0_product/test_bundle_publication_and_default.py`).

## Adapter / dashboard authority boundary

- Adapter default path: permanent validated bytes only (`DEFAULT_BUNDLE_PATH` → `data/gv_fs0/gv_fs0_certified_bundle.json`).
- Fail-closed on missing/invalid: `GvFs0PresentationError("CERTIFIED_BUNDLE_INVALID:...")`.
- Dashboard wiring: `PORTFOLIO_PAGE_TITLE` → `_render_portfolio_allocation_page` → single `render_gv_fs0_certified_bundle(st)` call; page registry marks Certified Portfolio default.
- Permanent bundle artifact present on candidate with expected identity (`bundle_hash` `527c86b9…`, roles OPEN then NO_POSITION).

## Process isolation

- Verifier: process-only hard stop at module import for non-main use.
- Certify controller: bounded subprocess supervision (deadline, stdout/stderr caps, isolated env, `-I` isolation).
- Product modules do not import `validation.gv_fs0_reconstruction` as a library for truth.

## Workflow ops proof

`.github/workflows/gv-fs0-product.yml`:

- Triggers limited to F1C product paths.
- `product-proof` on Ubuntu + Windows: product tests + frozen protocol tests.
- Two-run canonical build + tracked permanent-byte equality.
- Parity artifact upload per OS; `byte-parity` job requires exact equality of two OS records.

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| Medium | A malicious verifier descendant could outlive direct-child termination under supervision | Future process-tree hardening; frozen verifier has no descendant-spawn path | Future Ops | Inherited/out of scope; non-blocking (carry from F1B Reviewer B) |
| — | No in-scope Critical/High findings | — | — | — |

## Open Risks

1. **Inherited Medium (non-blocking):** verifier process-tree hardening remains a future ops item; not introduced by F1C publication/adapter/dashboard work.
2. Hosted CI execution evidence is outside this static review pass (workflow definition verified; live GitHub Actions run not executed by this reviewer).

## Forbidden scope confirmation

No providers, PEAD, FS1, protocol redesign, or commits performed by this reviewer.

## NextAction

`reconcile_with_reviewers_A_C_then_allow_ship_decision_on_pin_48ad053`

## Closure

ClosurePacket: RoundID=ROUND-20260719-GV-FS0-F1C-SHIP-C-REVIEW-B; ScopeID=GV_FS0_F1C_SHIP_C_REVIEWER_B_RUNTIME_OPS; ChecksTotal=8; ChecksPassed=8; ChecksFailed=0; Verdict=PASS; OpenRisks=descendant_process_tree_hardening_medium_inherited_out_of_scope; NextAction=reconcile_with_reviewers_A_C_then_allow_ship_decision_on_pin_48ad053

ClosureValidation: PASS (static reviewer packet; no code mutations)
SAWBlockValidation: PASS
