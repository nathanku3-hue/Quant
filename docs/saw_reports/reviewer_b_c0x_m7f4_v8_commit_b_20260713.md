# Reviewer B — M7F4-v8 Commit B Runtime and Operations

Reviewer: `/root/reviewer_b_m7f4_v8`

Mode: `ADVISORY_REVIEW`

Reviewed commit: `9f37745a114691e0fb67c681816536ca1f014bb3`

Verdict: `PASS`

## Scope

Read-only exact-object runtime and operational review. No provider access, full data rerun, remotes, publication, or edits.

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| Medium | Publication is atomic per file but not transactional across map, ledger, two legs, evidence, and manifests (`scripts/pead_m7f4_v8_2019_crsp_vertical.py:2623`, `:2768`, `:2865`, `:3114`); an OOM or generic exception can leave a mixed-generation partial package | Before any future rerun, remove partials and reconcile every hash; add injected-abort cleanup in a separately authorized repair | Runtime/Ops | Open, non-blocking for clean Commit B |
| Medium | Full-panel and scenario/Shapley materialization has no enforceable memory cap, checkpoint, or resume boundary (`scripts/pead_m7f4_v8_2019_crsp_vertical.py:2433`, `:2744`) | Keep the fixed diagnostic cohort; separately design bounded/checkpointed execution before expansion | Runtime/Ops | Open, non-blocking |

No Critical or High findings.

## Checks

- All eight snapshot files match their exact Commit B Git objects.
- Compile PASS.
- Independent snapshot subset 44/44 PASS. The omitted 45th test depends on the v7 stub absent from the snapshot; the exact Commit B v7 blob was separately inspected and is the expected exit-2-only stub. This does not re-claim the implementer's 45/45 run.
- Commit B changes only the evidence JSON and two manifests relative to A2.1.
- Tracked evidence, ignored artifact hashes, and row metadata reconcile: ledger 3,674 rows; each scenario leg 267 rows; map 23,672 rows.
- The clean rerun and manual failed-partial removal are accepted for this fixed package; generalized OOM recovery or transactional publication is not claimed.

Ownership independence: PASS; Reviewer B is distinct from the implementer and Reviewers A/C.
