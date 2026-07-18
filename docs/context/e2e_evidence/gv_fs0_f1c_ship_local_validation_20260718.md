Superseded on shipment status by `docs/context/e2e_evidence/gv_fs0_f1c_ship_terminal_20260719.md` and terminal SAW `docs/saw_reports/saw_gv_fs0_f1c_ship_terminal_20260719.md`; still valid for local implementer evidence of the pre-materialization 201/202 boundary.

# GV-FS0 F1C-SHIP Local Validation

Mode: `EXECUTION_PACKET`
Date: 2026-07-18
Base: `c37db092f092f00ad615109815bfacb13124c4da`
RoundID: `ROUND-20260718-GV-FS0-F1C-SHIP-LOCAL`
ScopeID: `GV_FS0_F1C_SHIP_LOCAL_VERTICAL`
Status: `LOCAL_IMPLEMENTATION_COMPLETE; SHIPMENT_BLOCKED`

## Result

F1C-SHIP is implemented locally as one vertical from exact clean F1B closeout `c37db09`:

```text
OPEN + NO_POSITION certified results
→ exact two-role canonical bundle
→ contract-compliant atomic publisher and recovery lock
→ permanent-bundle-only adapter load path
→ Certified Portfolio default route
→ headless Streamlit proof of both roles
→ Windows/Linux product parity workflow
→ exact-baseline zero-new-failure comparison
```

No provider, real-data, PEAD, benchmark, optimizer-authority, broker, protocol, or GV-FS1 scope was opened.

The gate is not shipped. The permanent repository bundle is not materialized, the candidate is not committed, hosted CI has not run, independent Reviewer A/B/C has not reviewed an immutable commit, and no branch push occurred.

## Canonical bundle identity

| Field | Value |
|---|---|
| Schema | `gv_fs0_certified_bundle_v1` |
| Roles | `OPEN`, then `NO_POSITION` |
| Bundle hash | `527c86b9e50386bf9e5847037642910b47b81697dbf089df3038099feab6282c` |
| Bundle ID | `BUNDLE_527c86b9e50386bf9e5847037642910b47b81697dbf089df3038099feab6282c` |
| Canonical byte length | `55774` |
| File SHA-256 | `a9dda224da21ab4abfe1f27afdb2875bb34f240d469caf20a90b7e635adb96e5` |
| Two-run equality | PASS |

Bundle identity includes both complete certified results, their authoritative hashes, presentations, and role order. It excludes its own `bundle_hash` and `bundle_id`.

## Implementation

| Area | Path | Result |
|---|---|---|
| Pure bundle validation | `core/gv_fs0_bundle.py` | Schema, component identity, presentation identity, order, bundle hash/ID, and canonical-byte checks |
| Publication/recovery | `core/gv_fs0_publish.py` | Observe-before-build, exclusive lock, compare-under-lock, idempotence, temp+fsync+replace, exact reread, durable recovery lock |
| Permanent consumer | `views/gv_fs0_portfolio_adapter.py` | Loads only validated permanent bytes and injects both roles through existing rendering |
| Default authority | `views/page_registry.py`, `dashboard.py` | Default route renamed `Certified Portfolio`; legacy optimizer/replay/lifecycle calls removed from default renderer |
| Product CI | `.github/workflows/gv-fs0-product.yml` | Ubuntu/Windows product proof, two-run build, tracked-byte assertion, parity record comparison |
| Product tests | `tests/gv_fs0_product/test_bundle_publication_and_default.py` | Bundle, recovery matrix, default authority, headless rendering, tracked-artifact identity |
| Superseded default tests | `tests/test_dash_1_page_registry_shell.py`, `tests/test_dash_2_portfolio_ytd.py`, `tests/test_position_lifecycle.py` | Backward-compatibility assertions replaced by certified-authority assertions |

## Publication matrix

| Case | Result |
|---|---|
| Existing active or recovery lock | `PUBLICATION_LOCKED`; lock retained; no age/PID break |
| Identical valid candidate | Idempotent success; no replace; mtime unchanged |
| Target differs from observed prebuild state | `PUBLICATION_TARGET_CHANGED`; no overwrite |
| Failure before replace | Prior target preserved; temp removed; normal lock release |
| Failure after replace | `PUBLICATION_POST_REPLACE_VERIFICATION_FAILED`; durable `RECOVERY_REQUIRED` lock |
| Recovery record replacement failure | `PUBLICATION_RECOVERY_RECORD_FAILED`; existing lock retained |
| Partial or reversed-role bundle | Schema/role validation blocks |

Only the four frozen publication codes are used.

## Default screen proof

Headless Streamlit AppTest publishes canonical bytes through the real publication protocol, opens the default `portfolio` route, and verifies:

- page title `Certified Portfolio`;
- `GV-FS0 Certified Paper Portfolio — OPEN`;
- `GV-FS0 Certified Paper Portfolio — NO_POSITION`;
- two certified tables and captions;
- OPEN terminal shares `10`, cash `904`, NAV `1044`;
- NO_POSITION terminal shares `0`, cash/NAV `1000`;
- no replay-unavailable fallback;
- no mutation of unrelated replay diagnostics during dashboard startup.

The default renderer contains one source call: `render_gv_fs0_certified_bundle(st)`. It contains no optimizer, strategy replay, lifecycle, YTD, data-health, or drift-monitor authority call.

## Focused regression

| Suite | Collected | Current result |
|---|---:|---|
| Product | 65 | 64 PASS; 1 BLOCKED because tracked permanent file is absent |
| Frozen protocol | 137 | 137 PASS |
| Combined runnable boundary | 201 | 201 PASS |

The absent-artifact test is `test_tracked_permanent_bundle_matches_current_build`. It is intentionally not weakened or skipped.

## Complete-suite zero-regression comparison

The full suite was split into deterministic filename batches in an untouched baseline worktree at exact `c37db09` and the candidate worktree using the same Python environment.

| Batch | Baseline | Candidate | Delta |
|---|---:|---:|---:|
| A-D | 1 failure | 0 failures | -1 |
| E-H | 39 failures | 39 failures | 0 |
| I-L | 0 failures | 0 failures | 0 |
| M-P | 19 failures | 19 failures after replacing one revoked default-route assertion | 0 |
| Q-T | 2 failures | 2 failures | 0 |
| U-Z | 45 failures | 45 failures | 0 |
| Total | 106 failures | 105 failures | **-1; zero new failures** |

Inherited failures remain concentrated in missing historical feature/fixture/manifest artifacts, PEAD evidence, pinned-universe data, Rule100 history, and V2 proxy fixtures. No inherited repair was opened.

The former baseline dashboard AppTest failure is removed by the certified default route. Obsolete tests requiring replay/YTD/lifecycle authority on the default portfolio page were rewritten because backward compatibility was explicitly revoked.

## Boundary checks

- Frozen contract/schema/verifier bytes: untouched.
- `core/gv_fs0_book.py` and `core/gv_fs0_certify.py`: behavior preserved.
- Legacy replay: remains present only as non-certifying research history; no silent fallback.
- Permanent bundle: absent from working tree; no partial or single-role file written.
- Publication lock: absent.
- Provider/network/broker paths: untouched.
- `git diff --check`: PASS.

## Open blockers

1. **Permanent artifact custody:** `data/gv_fs0/gv_fs0_certified_bundle.json` is absent. The approved workspace mutation interface cannot materialize generated bytes from a runtime command; the exact tracked-artifact test therefore remains red.
2. **Immutable custody:** no implementation commit exists; local bytes remain mutable.
3. **Hosted proof:** `.github/workflows/gv-fs0-product.yml` has not run on Ubuntu/Windows; parity is locally specified, not hosted-proven.
4. **Independent review:** no distinct Reviewer A/B/C pass exists for an exact candidate commit.
5. **Shipment:** no push occurred.

## Score

Shipped-product score remains **39/100**. Local headless behavior exists, but score movement is not authorized until the permanent bundle, immutable commit, hosted parity, exact-commit A/B/C, and push exist together.

## Correct next action

Materialize the exact canonical bundle at the permanent tracked path, run all 202 focused tests, bank one immutable F1C-SHIP candidate, run hosted Windows/Linux parity and exact-commit Reviewer A/B/C, reconcile any findings, then push only `codex/gv-fs0-f1-product`. Do not open adjacent scope.
