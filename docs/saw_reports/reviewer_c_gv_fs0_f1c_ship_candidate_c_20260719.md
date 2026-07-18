# Reviewer C — GV-FS0 F1C-SHIP Candidate C Data Integrity and Performance

Mode: `ADVISORY_REVIEW`  
RoundID: `ROUND-20260719-GV-FS0-F1C-SHIP-C-REVIEW-C`  
ScopeID: `GV_FS0_F1C_SHIP_C_REVIEWER_C_DATA_INTEGRITY`  
Hierarchy Confirmation: Approved | Session: current-thread | Trigger: inherited SAW reviewer pass (SMALL CHANGE) | Domains: Data integrity and performance path | FallbackSource: owner F1C-SHIP candidate C pin + `docs/phase_brief/gv-fs0-f1-product-slice-brief.md`

Reviewer role: data integrity and performance path only.  
Reviewer posture: independent, read-only. No code edits outside this report path, no commit, no push, no providers.

Worktree: `C:/Users/Lenovo/.devspace/worktrees/Quant_c0x_m7f4_v8-6cb847fa`  
ReviewedCommit (immutable pin): `48ad053dc21d7dda3c8280dcbd3c332584cc184a`  
Base: `c37db092f092f00ad615109815bfacb13124c4da`  
Branch intent: `codex/gv-fs0-f1-product`  
Python pin intent: `E:/Code/Quant/.venv/Scripts/python.exe` (local live pytest not re-executed in this tool surface; hosted Ubuntu product job used as practical re-run)

## Verdict

**PASS.** No Critical or High in-scope data-integrity defects on exact candidate C.  
Residual Medium: hosted Windows product-proof job failed; Windows/Linux product byte-parity job therefore skipped.

## Commit pin

| Check | Evidence | Result |
|---|---|---|
| Exact immutable pin | Worktree `HEAD` at `E:/Code/Quant/.git/worktrees/Quant_c0x_m7f4_v8-6cb847fa/HEAD` is `48ad053dc21d7dda3c8280dcbd3c332584cc184a`. `logs/HEAD` records base `c37db09…` → `48ad053…` with message `feat(gv-fs0): bank F1C-SHIP candidate C (transport only)`. Branch `codex/gv-fs0-f1-product` and `origin/codex/gv-fs0-f1-product` resolve to the same OID. GitHub commit API matches. | **PASS** |

## Must-verify matrix

| # | Requirement | Evidence | Result |
|---|---|---|---|
| 1 | Pin exact commit `48ad053…` | Worktree HEAD + branch refs + GitHub commit OID identical | **PASS** |
| 2 | Tracked permanent bundle exact 55,774 bytes and file SHA-256 `a9dda224da21ab4abfe1f27afdb2875bb34f240d469caf20a90b7e635adb96e5` | GitHub contents API for `data/gv_fs0/gv_fs0_certified_bundle.json@48ad053`: `size=55774`. Commit message pins the same length and SHA-256. Product constants `EXPECTED_BYTE_LENGTH=55774`, `EXPECTED_FILE_SHA256=a9dda224…`. Hosted Ubuntu product job step `Build canonical bundle twice and emit parity artifact` succeeded (reads tracked bytes, requires equality to rebuild, emits `file_sha256`). Git blob OID is `2a2887723363044466c218d5a3aab0a82d4171ad` (Git object id; content integrity is the content SHA-256 above). | **PASS** |
| 3 | Two-run `build_default_certified_bundle` produces identical bytes matching tracked file | Hosted Ubuntu product job step 6 on run `29651468309` **success**: builds twice via `certified_bundle_bytes(build_default_certified_bundle())`, requires `first == second`, then `tracked == first`. Product tests `test_complete_bundle_identity_is_exact_and_deterministic` and `test_tracked_permanent_bundle_matches_current_build` hard-lock the same contract. | **PASS** (Ubuntu hosted re-run) |
| 4 | Frozen contracts/schemas/verifier not mutated vs base `c37db09` | Commit file tree vs base is only product surfaces: `.github/workflows/gv-fs0-product.yml` (added), `core/gv_fs0_bundle.py`, `core/gv_fs0_publish.py`, `dashboard.py`, `data/gv_fs0/gv_fs0_certified_bundle.json`, `tests/gv_fs0_product/*`, `tests/test_dash_1_page_registry_shell.py`, `tests/test_dash_2_portfolio_ytd.py`, `tests/test_position_lifecycle.py`, `views/gv_fs0_portfolio_adapter.py`, `views/page_registry.py`. **Empty** for `contracts/gv_fs0/**`, `core/gv_fs0_canonical.py`, `validation/gv_fs0_*`, `scripts/*gv_fs0_protocol*`, `tests/test_gv_fs0_*.py`, `.github/workflows/gv-fs0-protocol-freeze.yml`. Hosted Protocol Freeze workflow run `29651468270` on same SHA **success**. | **PASS** |
| 5 | Product suite `tests/gv_fs0_product` + frozen `tests/test_gv_fs0_*.py` total 202 and pass | Product CI step runs both globs. Hosted Ubuntu product-proof step `Run product and frozen protocol regression` **success** on exact pin (run `29651468309`, job `88098415350`). Prior local boundary was 201/202 with sole miss = absent permanent artifact; candidate C materializes that artifact so the tracked-byte test becomes green. Hosted Windows product-proof same suite step **failure** (exit 1); logs not publicly readable. Local live pytest not re-run in this session. | **PASS** (Ubuntu hosted 202 path); Windows residual noted |
| 6 | Product/protocol CI split present | Separate workflows: `.github/workflows/gv-fs0-product.yml` vs `.github/workflows/gv-fs0-protocol-freeze.yml`. Both triggered on push of pin; protocol freeze success; product defined with Ubuntu+Windows product-proof + byte-parity job. | **PASS** |
| 7 | No new inherited full-suite repair claims; F1C does not claim historical suite green | Commit message: transport-only bank, **not a shipment claim**, score remains 39/100. Prior F1C local evidence: zero-new-failure vs `c37db09` with **105 remaining** inherited failures; explicitly no inherited repair opened. No claim of historical suite green in candidate C message or banked product paths. | **PASS** |

## Data integrity path (detail)

### Permanent bundle identity

| Field | Value |
|---|---|
| Path | `data/gv_fs0/gv_fs0_certified_bundle.json` |
| Schema | `gv_fs0_certified_bundle_v1` |
| Roles (order) | `OPEN`, then `NO_POSITION` |
| Bundle hash | `527c86b9e50386bf9e5847037642910b47b81697dbf089df3038099feab6282c` |
| Bundle ID | `BUNDLE_527c86b9e50386bf9e5847037642910b47b81697dbf089df3038099feab6282c` |
| Canonical byte length | `55774` |
| File SHA-256 | `a9dda224da21ab4abfe1f27afdb2875bb34f240d469caf20a90b7e635adb96e5` |
| Certification status | Both components `CERTIFIED` |
| Two-run equality | Hosted Ubuntu PASS |

### Publication / atomic write path

`core/gv_fs0_publish.py` (product layer, not frozen protocol rewrite):

- Observe target hash before build.
- Exclusive non-waiting lock (`O_CREAT|O_EXCL`); no age/PID break.
- Compare under lock; identical → `IDEMPOTENT` without replace.
- Temp write + flush + fsync → `os.replace` → directory fsync best-effort → exact reread + SHA + parse.
- Post-replace failure → durable `RECOVERY_REQUIRED` record; only four registered publication codes.
- Performance: bounded synthetic two-role path; no row-loop ETL; no provider I/O. No material F1C performance risk on this synthetic fixture.

### Frozen surface non-mutation

Diff vs `c37db09` does not touch frozen contracts, schemas, registries, tables, vectors, canonical encoder, reconstruction verifier, or protocol freeze tests/workflow. Protocol freeze hosted proof on the same SHA succeeded, reinforcing freeze integrity.

## Performance path

- Synthetic OPEN + NO_POSITION certification path is small (fixed events/sessions).
- Bundle assembly is pure hash/schema validation over two complete results.
- Publication is single-file atomic replace; no multi-GB path, no full-suite repair ETL.
- Residual inherited Medium (out of scope): verifier descendant process-tree hardening; frozen verifier has no spawn path.

## Hosted CI evidence (exact pin)

| Workflow | Run | Conclusion | Relevance |
|---|---|---|---|
| GV-FS0 Protocol Freeze | `29651468270` | **success** | Frozen protocol surfaces green on pin |
| GV-FS0 Product | `29651468309` | **failure** (overall) | Ubuntu product-proof **success** including 202-suite + two-run tracked rebuild; Windows product-proof **failure** at suite step; byte-parity **skipped** |

Artifact: `gv-fs0-product-parity-Linux` uploaded (329 bytes) — only Linux parity record present because Windows job did not reach parity emission.

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| Medium | Hosted Windows product suite failed on pin `48ad053`; Windows/Linux product byte-parity job skipped | Diagnose Windows product-proof logs; repair CI deps/path if environmental, or product path if OS-specific; re-run product workflow to green both OS and parity | Implementer / CI | Open residual (not Critical data-byte defect; Ubuntu proves tracked bytes + two-run identity) |
| Low | Local live pytest not re-executed inside this Reviewer C tool surface | Optional local confirm: `E:/Code/Quant/.venv/Scripts/python.exe -m pytest tests/gv_fs0_product tests/test_gv_fs0_*.py -q --basetemp=tmp/pytest` on exact pin | Reconcile / SAW | Residual evidence gap; Ubuntu hosted substitutes for suite green |
| Low | Truth surfaces still describe pre-C “permanent artifact absent / 201/202” | Refresh bridge/done/impact after A/B/C + closeout T | Docs/Ops | Out of data-integrity code scope |
| — | No Critical/High data integrity defect on tracked bundle identity, freeze non-mutation, or publication atomic path | — | Reviewer C | Closed |

## Ownership statement

Reviewer C is independent of implementer ownership for candidate C, used the pinned worktree at exact `48ad053…`, and performed read-only data-integrity / performance verification only. No provider, PEAD, FS1, protocol redesign, historical suite repair, commit, or push.

## Open Risks

1. Hosted Windows product matrix red → product Windows/Linux byte-parity not proven for shipment T.
2. Local Reviewer C session did not re-hash file bytes with a local Python process; integrity rests on GitHub size + Ubuntu rebuild/SHA path + test constants.
3. Inherited Medium process-tree hardening remains deferred (carry from F1B).

## NextAction

Reconcile with Reviewers A/B on pin `48ad053dc21d7dda3c8280dcbd3c332584cc184a`; clear Windows product CI failure and complete hosted product byte-parity before shipment/push claim. Do not open historical suite repair, providers, PEAD, FS1, or protocol redesign.

## ClosurePacket

```
ClosurePacket: RoundID=ROUND-20260719-GV-FS0-F1C-SHIP-C-REVIEW-C; ScopeID=GV_FS0_F1C_SHIP_C_REVIEWER_C_DATA_INTEGRITY; ChecksTotal=7; ChecksPassed=7; ChecksFailed=0; Verdict=PASS; OpenRisks=windows_product_ci_red_byte_parity_skipped_local_pytest_not_rerun; NextAction=reconcile_with_A_B_clear_windows_product_ci_then_hosted_parity_and_terminal_SAW_before_ship
```

SAW Verdict: **PASS**
