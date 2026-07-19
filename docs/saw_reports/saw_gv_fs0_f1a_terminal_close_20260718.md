# SAW Report: GV-FS0 F1A Terminal Close

Mode: `CLOSURE_REPORT`
RoundID: `ROUND-20260718-GV-FS0-F1A-TERMINAL`
ScopeID: `GV_FS0_F1A_CERTIFIED_OPEN_TERMINAL`
Hierarchy Confirmation: Approved via persisted fallback | Session: current-thread | Trigger: project-init fallback | Domains: portfolio accounting, verifier supervision, certification, read-only presentation | FallbackSource: `docs/spec.md` + `docs/phase_brief/gv-fs0-f1-product-slice-brief.md`.

## Scope and acceptance

In-scope: close only the synthetic OPEN path at implementation `699e664` plus repair `066bdda`.

| CheckID | Acceptance check | Status |
|---|---|---|
| CHK-01 | Deterministic fixture, decision, book, event, snapshot, certification, and result identities | PASS |
| CHK-02 | Frozen authority tokens, ordering, transition ownership, and duplicate semantics | PASS |
| CHK-03 | Exact five-session OPEN economics ending at NAV 1044 | PASS |
| CHK-04 | Verifier input contains only original projected inputs | PASS |
| CHK-05 | Exactly two bounded isolated attempts execute across infrastructure failures | PASS |
| CHK-06 | Full raw verifier economics/hash bind before formal result and certification | PASS |
| CHK-07 | One retained result and all ten certification checks TRUE | PASS |
| CHK-08 | Final adapter rejects presentation/snapshot/certification drift | PASS |
| CHK-09 | No permanent bundle or provider/data output | PASS |
| CHK-10 | Product, protocol, combined, generator, freeze, compile, and diff checks pass | PASS |
| CHK-11 | Distinct Reviewer A/B/C PASS on exact repair commit | PASS |

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Nonconforming authority tokens and absent legacy revocation | Frozen tokens plus machine revocation marker/test | Implementer | Fixed; Reviewer A PASS |
| High | Raw verifier semantics/hash could be discarded during formalization | Exact complete projection and raw canonical-hash binding | Implementer | Fixed; Reviewer C PASS |
| High | Presentation drift could render under CERTIFIED | Exact row projection and presentation-hash validation | Implementer | Fixed; Reviewer B PASS |
| High | Unexpected infrastructure error could skip attempt two | Normalize runner exceptions and execute both ordinals | Implementer | Fixed; Reviewer B PASS |
| Medium | Duplicate rules, inherited-pipe deadline, and combined-suite reload regression | Idempotence/conflict checks, bounded EOF deadline, stable import test | Implementer | Fixed |
| Medium | Deadline-bounded malicious descendant is not terminated as a process tree | Carry as later operational hardening; frozen verifier has no spawn path | Future Ops | Open, non-blocking |

## Reviewer lanes

- Reviewer A `/root/reviewer_a_f1a`: PASS; exact economics, authority tokens, legacy revocation, and 180-test combined regression verified.
- Reviewer B `/root/reviewer_b_f1a`: PASS; presentation binding, two attempts under OSError, bounded supervision, isolation, and no bundle verified.
- Reviewer C `/root/reviewer_c_f1a`: PASS; complete raw economic/hash binding, duplicate rules, canonical integrity, and retained-result determinism verified.
- Ownership check: primary implementer and all three reviewers are distinct; PASS.

## Scope split summary

- In-scope actions: OPEN implementation, review repairs, exact-commit reviewer reruns, and current-truth reconciliation.
- Inherited/out-of-scope actions: F1B NO_POSITION is next but unopened; F1C/F1D, publication, default routing, providers, real data, PEAD, and FS1 remain held.

## Document Changes Showing

| Path | Change summary | Reviewer status |
|---|---|---|
| `core/gv_fs0_book.py` | Primary OPEN events, snapshots, frozen authority, duplicate semantics | Reviewer A/C PASS |
| `core/gv_fs0_certify.py` | Bounded attempts, raw verifier binding, certification/result | Reviewer B/C PASS |
| `views/gv_fs0_portfolio_adapter.py` | Injected read-only presentation binding | Reviewer B PASS |
| `tests/gv_fs0_product/**` | Exact/adversarial product coverage | Reviewer A/B/C PASS |
| `docs/context/*_current.md` | F1A terminal truth and F1B-only handoff | Reconciliation PASS |

Document Sorting: maintained per `docs/checklist_milestone_review.md`.

## Validation / evidence

- Exact repair commit: `066bdda4881832b004d9e50ac44e360f5c70c781`.
- Product: 43/43 PASS; protocol: 137/137 PASS; combined: 180/180 PASS.
- Generator check, freeze bootstrap, compile, SE evidence validator, and closure validator PASS.
- Distinct terminal Reviewer A/B/C PASS; no in-scope Critical/High remains.

Open Risks: malicious descendant process-tree termination remains Medium operational hardening; frozen verifier has no descendant-spawn path.

Next action: open F1B only and pass NO_POSITION through the identical book/certification/adapter path.

ChecksTotal: 11
ChecksPassed: 11
ChecksFailed: 0
SAW Verdict: PASS

ClosurePacket: RoundID=ROUND-20260718-GV-FS0-F1A-TERMINAL; ScopeID=GV_FS0_F1A_CERTIFIED_OPEN_TERMINAL; ChecksTotal=11; ChecksPassed=11; ChecksFailed=0; Verdict=PASS; OpenRisks=descendant_process_tree_hardening_medium; NextAction=open_F1B_only

ClosureValidation: PASS

SAWBlockValidation: PASS
