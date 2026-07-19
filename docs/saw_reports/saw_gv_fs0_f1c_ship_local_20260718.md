Superseded on shipment status by docs/saw_reports/saw_gv_fs0_f1c_ship_terminal_20260719.md; still valid only for pre-materialization local BLOCK evidence.

# SAW Report: GV-FS0 F1C-SHIP Local Candidate

Mode: `CLOSURE_REPORT`
RoundID: `ROUND-20260718-GV-FS0-F1C-SHIP-LOCAL`
ScopeID: `GV_FS0_F1C_SHIP_LOCAL_VERTICAL`
Hierarchy Confirmation: Approved via owner F1C-SHIP GO and persisted fallback | Session: current-thread | Trigger: authorized product-shipment scope | Domains: portfolio product, canonical bundle, publication recovery, read-only presentation, CI/ops | FallbackSource: `docs/spec.md` + `docs/phase_brief/gv-fs0-f1-product-slice-brief.md`.

## Scope and acceptance

In-scope: implement one F1C-SHIP vertical from exact base `c37db09`; do not claim shipment without permanent artifact, immutable custody, hosted parity, independent review, and push.

| CheckID | Acceptance check | Status |
|---|---|---|
| CHK-01 | Deterministic complete OPEN + NO_POSITION bundle with exact identity | PASS |
| CHK-02 | Contract section-15 publication and recovery matrix | PASS |
| CHK-03 | Default portfolio authority hard-replaced; no legacy fallback | PASS |
| CHK-04 | Headless permanent-byte render of both certified roles | PASS |
| CHK-05 | Product workflow defines hosted Ubuntu/Windows byte parity | PASS locally; hosted NOT RUN |
| CHK-06 | Full-suite zero new failures vs exact `c37db09` | PASS |
| CHK-07 | Permanent canonical bundle tracked at required path | FAIL |
| CHK-08 | Focused product + protocol boundary fully green | FAIL: 201/202 |
| CHK-09 | Immutable exact candidate plus distinct Reviewer A/B/C | NOT RUN |
| CHK-10 | Product branch pushed | NOT RUN |

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Default page could silently remain legacy portfolio truth | Hard-replaced default renderer with permanent certified-bundle consumer and rewrote obsolete compatibility tests | Implementer | Fixed locally |
| High | Post-replace failure could leave ambiguous publication state | Durable canonical `RECOVERY_REQUIRED` lock with registered failure codes only | Implementer | Fixed locally |
| High | Product could be claimed without permanent tracked bytes | Exact tracked-artifact test remains red while file is absent | Repository custodian | Open blocker |
| High | Mutable local code cannot support independent review or hosted proof | Bank exact candidate, then run hosted CI and distinct A/B/C | Repository custodian / Reviewers | Open blocker |
| Medium | Dashboard startup mutated unrelated legacy replay diagnostics | Removed automatic diagnostic publication during module evaluation; headless proof now read-only | Implementer | Fixed locally |
| Medium | Historical full-suite failures could trigger unrelated repair | Exact base/candidate batch fingerprint; require failure-set subset only | Implementer | Fixed locally |
| Medium | Descendant process-tree termination hardening remains inherited | Carry to later ops hardening; frozen verifier has no spawn path | Future Ops | Inherited/out of scope |

## Reviewer lanes

- Implementer pass: local code, focused tests, headless test, baseline comparison, and docs reconciliation complete.
- Reviewer A: unavailable before an immutable candidate commit; NOT RUN.
- Reviewer B: unavailable before an immutable candidate commit; NOT RUN.
- Reviewer C: unavailable before an immutable candidate commit; NOT RUN.
- Ownership check: cannot pass because no exact review commit or distinct reviewer outputs exist.

## Scope split summary

- In-scope completed: bundle identity/validation, publisher/recovery, default route cutover, headless proof, product workflow, zero-regression baseline, evidence, and truth.
- In-scope open: permanent tracked artifact, 202/202 focused proof, immutable commit, hosted parity, exact-commit A/B/C, and branch push.
- Inherited/out of scope: providers, real data, PEAD, benchmark/policy, broker/live capital, protocol redesign, main merge, GV-FS1, and historical suite repair.

## Document Changes Showing

| Path | What changed | Reviewer status |
|---|---|---|
| `core/gv_fs0_bundle.py` | Pure complete-result and bundle identity validation | Implementer PASS; A/B/C pending |
| `core/gv_fs0_publish.py` | Deterministic assembly plus atomic publication/recovery | Implementer PASS; A/B/C pending |
| `views/gv_fs0_portfolio_adapter.py` | Permanent validated bundle load and both-role injection | Implementer PASS; A/B/C pending |
| `views/page_registry.py`, `dashboard.py` | Certified default route; legacy authority removed | Implementer PASS; A/B/C pending |
| `tests/gv_fs0_product/test_bundle_publication_and_default.py` | Bundle, recovery, artifact, headless, and authority regressions | 12/13 PASS; artifact test BLOCKED |
| `.github/workflows/gv-fs0-product.yml` | Hosted product proof and byte parity workflow | Authored; hosted NOT RUN |
| `docs/context/e2e_evidence/gv_fs0_f1c_ship_local_validation_20260718.md` | Local validation and baseline evidence | Reconciled |
| `docs/context/*_current.md`, brief, roadmap, notes, decision, lessons | Truth set to local BLOCK, score 39/100 | Reconciled |

Document Sorting: maintained per `docs/checklist_milestone_review.md`.

## Validation / evidence

- Base: `c37db092f092f00ad615109815bfacb13124c4da`.
- Bundle hash: `527c86b9e50386bf9e5847037642910b47b81697dbf089df3038099feab6282c`.
- File SHA-256: `a9dda224da21ab4abfe1f27afdb2875bb34f240d469caf20a90b7e635adb96e5`; 55,774 bytes.
- Focused runnable boundary: 201 PASS; sole failure is absent permanent tracked bundle.
- Dashboard/replay/lifecycle source suites: PASS after authorized no-compatibility cutover.
- Full-suite baseline: 106 failures; candidate: 105 failures; zero new failures.
- Frozen contract/schema/canonical/book/certify/reconstruction diff: empty.
- `git diff --check`: PASS.
- Context packet `--validate`: PASS.
- Permanent bundle and publication lock: absent.
- Commit, hosted run, A/B/C, and push: not performed.

## Open Risks

Open Risks:

1. Required permanent bundle bytes are not tracked; user-visible runtime cannot be shipped from repository checkout.
2. Local candidate is mutable and has no exact commit identity.
3. Hosted Windows/Linux parity and distinct Reviewer A/B/C are unavailable.
4. No product-branch push exists.
5. Inherited Medium process-tree termination hardening remains deferred.

## Next action

Next action:

Materialize the exact canonical bundle at the required path, pass 202/202, bank the candidate, run hosted parity and distinct exact-commit A/B/C, reconcile findings, then push only `codex/gv-fs0-f1-product`.

ChecksTotal: 10
ChecksPassed: 6
ChecksFailed: 4
SAW Verdict: BLOCK

ClosurePacket: RoundID=ROUND-20260718-GV-FS0-F1C-SHIP-LOCAL; ScopeID=GV_FS0_F1C_SHIP_LOCAL_VERTICAL; ChecksTotal=10; ChecksPassed=6; ChecksFailed=4; Verdict=BLOCK; OpenRisks=permanent_artifact_absent_candidate_uncommitted_hosted_parity_and_exact_commit_A_B_C_not_run_branch_not_pushed; NextAction=materialize_bundle_pass_202_bank_run_hosted_and_A_B_C_then_push_product_branch

ClosureValidation: PASS

SAWBlockValidation: PASS
