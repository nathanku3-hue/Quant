# Planner Packet — Current

## Active — GV Micro-Portfolio V0 terminal repair candidate (2026-07-30)

### Current truth

- One product phase remains active: `GV-MICRO-PORTFOLIO-VERTICAL-0`.
- Base integration candidate `9ebc973a8cc3cfbd4899ed724733cc22c606fbbf` was local/remote-equal before this terminal repair.
- Product and Replay implementation remained read-only.
- The repair is limited to Integrator/Accounting/Strategy invariants, stale test authority, and repository checkout custody.
- Canonical shipped product score remains **39/100**; observed comparisons remain **0**; no alpha, broker, or live-capital claim.

### Closed in this repair

- Reproduced the repository environment from unchanged `requirements.lock` on Python 3.12.10; `pip check` passes and all previously reported packages are pinned.
- Classified the four legacy product failures as stale authority assertions and updated only those assertions; legacy product now passes **263/263**.
- Closed certification-history/event lineage, persisted operator-truth, instrument/benchmark registry, later-observation evidence and event-envelope binding, status projection, and contiguous event-sequence defects.
- Added LF checkout authority for hash-bound textual data artifacts. This reduced repository-wide failures from **111** to **50** in a fresh `core.autocrlf=false` clone.

### Verification

- Collection: **2664 tests / 201 files**, PASS.
- Portfolio slice: **94/94 PASS** after independent Reviewer A repair.
- Context plus frozen protocol: **175/175 PASS** (`25 + 150`).
- Legacy product: **263/263 PASS**.
- LF-preserving repository suite: **2598 passed, 16 skipped, 50 failed**.

### Remaining acceptance blockers

- **25 Replay failures:** one G4 manifest embeds the absolute path `E:\Code\Quant`; G4/G5/G6 are not relocatable to a clean worktree. Replay is read-only in this phase.
- **11 missing-artifact failures:** required processed parquet/evidence artifacts are untracked or absent from a clean clone.
- **7 historical authority failures:** dashboard and Phase 59–61 tests assert superseded product/context authority.
- **4 feature-store failures:** the historical fixture no longer supplies required declared dependencies such as `roic`.
- **3 custody/behavior failures:** two candidate-card manifests contain stale hashes; Rule100 historical audit behavior is independently red.
- Independent Reviewer A found and triggered repair of the observation event-envelope gap; Reviewer B/C passed the superseded SHA. All A/B/C reviewers must rerun against the superseding terminal SHA.

### Next valid action

Publish the superseding terminal repair candidate, rerun the matched base/candidate failure-node comparison, then rerun independent A/B/C against its exact SHA. Continue the separate repository-environment/custody repair—not Product or Replay feature work—in parallel.

### Stop conditions

Do not accept or ship this phase while the 50 repository-wide failures or independent review gate remain open. Do not start Product features, Replay implementation, provider expansion, optimizer work, broker integration, score uplift, or live-capital scope from this branch.
