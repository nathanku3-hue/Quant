# Bridge Contract - Current

## Active Addendum — GV-FS0 F1B NO_POSITION Terminal Bridge (2026-07-18)

- `SYSTEM_DELTA`: F1B adds a separate NO_POSITION fixture/decision and routes it through the same book, five snapshots, two verifier attempts, certification, result, presentation, and adapter path as F1A.
- `PM / Product Delta`: the second synthetic certified component is banked and independently closed; no permanent bundle or default product screen exists yet, so shipped-product score remains 39/100.
- `OPEN_DECISION`: none for F1B closure. Opening F1C permanent publication requires a separate owner-authorized round.
- `RECOMMENDED_NEXT_STEP`: stop before F1C and preserve the closed F1A/F1B component identities.
- `DO_NOT_REDECIDE`: preserve F1A and the frozen protocol; do not open F1C/F1D, publication, default routing, providers, real data, PEAD, broker/live capital, or FS1.
- `PHASE_STATUS`: F1A PASS; F1B terminal SAW PASS at `4359f35`; later gates unopened.

## Prior Active Addendum — GV-FS0 F1A Certified OPEN Terminal Close (2026-07-18)

- `SYSTEM_DELTA`: commit `066bdda` closes F1A OPEN with conforming event authority, exact raw-verifier economics/hash binding, two attempts, certification, result identity, and injected presentation binding.
- `PM / Product Delta`: one synthetic OPEN component is now CERTIFIED and independently closed; terminal NAV is `1044`. This is not a permanent two-component product bundle.
- `OPEN_DECISION`: none for F1A closure.
- `RECOMMENDED_NEXT_STEP`: open F1B only and pass NO_POSITION through the identical implementation path.
- `DO_NOT_REDECIDE`: preserve the frozen protocol and F1A economics; do not open F1C/F1D, publication, default routing, providers, real data, PEAD, or FS1.
- `PHASE_STATUS`: F1A PASS; F1B next; later gates unopened.

## Active Addendum — GV-FS0 Protocol V1 Terminal Freeze Audit (2026-07-17)

- `SYSTEM_DELTA`: GV-FS0 protocol artifacts and guards are fixed through candidate branch `d5d03ec`; frozen protocol, manifest, and vector bytes remain unchanged by hosted-CI repairs.
- `PM / Product Delta`: Protocol freeze evidence is terminal PASS: local checks, mutation probes, A/B/C review, and hosted Windows/Linux byte parity all pass. No certified portfolio slice or user-facing product exists yet.
- `OPEN_DECISION`: None for protocol freeze closure. Reducer/product work requires a separate owner decision.
- `RECOMMENDED_NEXT_STEP`: Hold protocol evidence; open the reducer/product round only by separate authorization.
- `DO_NOT_REDECIDE`: Do not reopen precision decisions; do not treat protocol evidence as already executed reducer output; do not implement PortfolioBook, execution, snapshots, certification, bundles, Streamlit, provider, real-data, or FS1 work in this closeout.
- `PHASE_STATUS`: Protocol freeze terminal SAW PASS; economic implementation remains NO-GO until separately authorized.

## Active Addendum — GV-FS0 Protocol V1 Freeze Candidate (2026-07-17)

- `SYSTEM_DELTA`: The approved GV-FS0 precision patch is encoded in the consolidated contract and 18 deterministic machine artifacts. Canonical bytes, raw tokens, domain hashes, registries/tables, manifest representations, bootstrap/enforced guards, independent vectors, and isolated reconstruction boundaries are implemented.
- `PM / Product Delta`: Protocol proof is locally green with 135 focused tests, local schema-bundle resolution, exact intent cardinality, and Windows/Linux byte parity. No certified portfolio slice or user-facing product exists yet.
- `OPEN_DECISION`: None for implementation scope. The remaining action is evidence closure: immutable candidate commit, enforced mutation proof, hosted CI, and independent audit/SAW.
- `RECOMMENDED_NEXT_STEP`: Bank the protocol candidate, run enforced mode against that exact commit, retain the non-merged mutation branch evidence, then audit the immutable candidate.
- `DO_NOT_REDECIDE`: Do not reopen the four precision decisions; do not treat local protocol proof as reducer authorization; do not implement PortfolioBook, execution, snapshots, certification, bundles, Streamlit, provider, real-data, or FS1 work.
- `PHASE_STATUS`: Phase 1 protocol implementation locally PASS; freeze authorization remains pending committed-base proof and audit; economic implementation remains NO-GO.

## Prior Program State — PEAD Strict-PIT Formally Closed (2026-07-14)

- **Status**: `TERMINATED_DIAGNOSTIC_ONLY` at merge commit `150d322` (tag `pead-v8-diagnostic-terminal` at `076f26b`).
- **Shipped outcome**: Bounded 2019 long-only future-informed diagnostic (M7F4-v8). NOT strict-PIT, NOT alpha, NOT tradable.
- **Original objective**: 2015–2019 dollar-neutral Q5−Q1 strict-PIT PEAD. **Not achieved.**
- **Research validity**: ~30/100; delivery/closure: 88/100.
- **Prohibited**: Strategy/UI promotion, readiness flag changes, provider access, curve/alpha claims, ranking/scoring, alerts, recommendations, broker/order paths.
- **Reopen condition**: Only for one source-intake slice with genuine effective-dated identifiers + committed data-owner approval; mapping and curves remain closed until ID0 passes.

## Active Addendum — M7F5-ID0 Terminal Provenance Block (2026-07-14)

- `SYSTEM_DELTA`: M7F5-ID0 Commit A `c5a9ab8` requires exact source/envelope bytes plus a reachable, unchanged committed data-owner approval blob under `docs/authorization/`; Commit B `410d0ca` banks current-source BLOCK evidence; truth repair `a51f349` and terminal SAW `398732c` close A/B/C review.
- `PM / Product Delta`: Current Compustat security master remains blocked for strict-PIT identifier authority with `BLOCKED_DATED_COMPUSTAT_IDENTIFIER_PROVENANCE_REQUIRED`; research validity remains near 30 and M7F4-v8 remains a diagnostic, not a strict curve.
- `OPEN_DECISION`: Obtain a genuine effective-dated identifier source with committed data-owner approval, authorize historical identifier acquisition, or terminate PEAD strict-PIT work.
- `RECOMMENDED_NEXT_STEP`: Hold promotion; choose exactly one separately authorized owner decision.
- `DO_NOT_REDECIDE`: Do not infer identifier-validity dates from current snapshots, caller-created JSON, generic date columns, `updated_at`, provider metadata, or non-committed approvals; do not run mapping/curve/readiness/Strategy/UI work from this BLOCK evidence.
- `PHASE_STATUS`: M7F5-ID0 terminal SAW PASS for a provenance BLOCK; strict PIT/as-of identifier authority `BLOCKED`; `m6b_data_contract_ready=false`.

## Prior Addendum — M7F4-v8 Terminal Commit C (2026-07-13)

- `SYSTEM_DELTA`: A2.1 `b4d35e1` repaired the residual-evidence count and added the real publication-branch regression; Commit B `9f37745` banks only the evidence JSON and two manifests; three distinct reviewers independently PASS the fixed Commit B package.
- `PM / Product Delta`: M7F4-v8 is `DIAGNOSTIC_COMPLETE` with 2,448 selected, 2,444 observed, four residual windows, two validated bridges, exact self-financing NAV/cost identities, and exact 16-state Shapley. Strict curve remains `BLOCKED`; research ceiling remains near 30.
- `OPEN_DECISION`: None for terminal diagnostic reconciliation. Future transactionality, memory bounding, evidence portability, or historical-link work each requires a separate bounded decision.
- `RECOMMENDED_NEXT_STEP`: Hold promotion and choose at most one separately authorized next scope.
- `DO_NOT_REDECIDE`: Do not flip readiness, treat sensitivity legs as a strict curve, claim PIT/as-of identity, describe neutral carry as a finite upper bound, or reopen provider/CCM/Strategy/UI scope.
- `PHASE_STATUS`: M7F4-v8 terminal SAW PASS; strict curve `BLOCKED`; `m6b_data_contract_ready=false`.

## Prior Addendum — M7F3-v7 SELF_FINANCING_PORTFOLIO_TRUTH

- Superseded as active implementation by M7F4-v8; retained as the accounting-design predecessor and audit history.

## Active Addendum — M7F3-v7 SELF_FINANCING_PORTFOLIO_TRUTH (2026-07-12)

- `SYSTEM_DELTA`: Hard-replaced M7F2-v6 active executable with M7F3-v7 self-financing portfolio truth on c0x/m7f0-v4. Drifted-prior equity turnover sequence; bridge parity; dead write-down; first-bad residual ~0.721%; exact 16-state Shapley. Commit A `bae1f656`; B evidence `b5c66bc`; C SAW+truth.
- `PM / Product Delta`: Diagnostic package complete with strict_curve BLOCKED. Score path ~70–73 diagnostic; research validity ~30. Residual exposure is first-bad sum not 4/2448. Selection 2448 unchanged.
- `OPEN_DECISION`: None for package close. Hold readiness/UI/historical-link/CCM.
- `RECOMMENDED_NEXT_STEP`: Hold promotion; optional stderr label polish only.
- `DO_NOT_REDECIDE`: Do not flip readiness; do not treat neutral carry as upper bound; do not open CCM; do not claim independent A/B/C without distinct agents (now proven).
- `PHASE_STATUS`: M7F3-v7 DIAGNOSTIC_COMPLETE; terminal SAW PASS; strict curve BLOCKED.

## Prior Addendum — M7F2-v6-final Outcome Envelope (2026-07-12)

- Superseded as active close package by M7F3-v7. Historical v6 evidence retained for audit; v6 executable retired.


# Bridge Contract - Current

## Active Addendum — M7F2-v6-final Outcome Envelope (2026-07-12)

- `SYSTEM_DELTA`: Hard-replaced M7F1-v5.2 with M7F2-v6-final on c0x/m7f0-v4. Pre-entry delist exclude before breadth/Q5; blank one-day bridge; strict BLOCK + neutral carry-to-cash + -100% write-down envelope; map identity selection metadata corrected. Commit A `c7724adcaa85`.
- `PM / Product Delta`: Diagnostic package complete (DIAGNOSTIC_COMPLETE) with strict_curve_status=BLOCKED. Selected ok 2444/2448; residual invalid 4; bridged 2; pre-entry excluded 12. Score target 70-74 diagnostic; research ceiling ~30; baseline 60 until SAW C closes.
- `OPEN_DECISION`: Accept diagnostic package and close terminal SAW C, or re-scope residual policy. Do not promote readiness or primary curve PASS.
- `RECOMMENDED_NEXT_STEP`: Commit C Reviewer A/B/C + validated SAW PASS (diagnostic) with strict_curve BLOCKED.
- `DO_NOT_REDECIDE`: Do not flip readiness; do not claim as-of/PIT link; do not treat neutral carry as justified upper bound; no v5.2 compatibility path; no event-id production policy.
- `PHASE_STATUS`: M7F2-v6-final evidence complete; terminal SAW pending Commit C.

## Prior Addendum — M7F1-v5.2-final Durable Residual BLOCK (2026-07-12)

- Superseded on package status by M7F2-v6-final. Historical residual BLOCK evidence remains for audit only.


# Bridge Contract - Current

## Active Addendum — M7F1-v5.2-final Durable Residual BLOCK (2026-07-12)

- `SYSTEM_DELTA`: M7F1-v5.2-final on `c0x/m7f0-v4`: source-wide spine, pre-2019 prior-20 load, pre-Q5 prior-20 tradability gate (roadmap deviation, not map repair), force map rebuild, stale-curve invalidate, ledger failure details. Commit A `138c8b7`; evidence bound to that commit.
- `PM / Product Delta`: Durable residual BLOCK (~62 band): 7/2448 selected windows invalid (5 special RET, 1 unresolved delist, 1 missing session). Prior-20 removed dead-identity bulk failures. Curve not promoted. Snapshot-link ceiling ~30 remains.
- `OPEN_DECISION`: Accept durable residual BLOCK and open bounded delisting-data/policy gate for residual specials/`DLRET`/missing-session — or re-scope. Do **not** open historical-link yet.
- `RECOMMENDED_NEXT_STEP`: Owner open bounded delisting-data/policy gate for 7 residual invalids only; keep readiness false.
- `DO_NOT_REDECIDE`: Do not flip readiness; do not claim as-of/PIT link; do not restore pre-Q5 complete-60; do not treat uncommitted v5 diagnostic as package; do not open historical-link yet.
- `PHASE_STATUS`: C0X PASS; M7F1-v5.2-final durable residual BLOCK; Commit C terminal SAW ADVISORY_PASS (A/B/C all PASS).

## Prior Addendum — C0X → M7F0-v4 (2026-07-12)

- `SYSTEM_DELTA`: C0X trust bootstrap + M7F0-v4 2019 CRSP Q5 long-only mechanical vertical on branch `c0x/m7f0-v4` (base `aee7f4c`). C0A closure theater abandoned.
- `PM / Product Delta`: Mechanical flagged research curve evidence available under snapshot CUSIP8 ceiling; not strict M6b; not alpha.
- `OPEN_DECISION`: Superseded by M7F1-v5.2-final residual path.
- `RECOMMENDED_NEXT_STEP`: See active M7F1-v5.2-final addendum.
- `DO_NOT_REDECIDE`: Do not repair invalid C0A envelopes; do not claim as-of link; do not flip `m6b_data_contract_ready`.
- `PHASE_STATUS`: C0X PASS; M7F0-v4 superseded as selection contract by v5.2-final.

# Bridge Contract - Current

## Active Addendum — Request Artifact Identity Truth Reconciliation V1 (2026-07-11)

- `RoundID`: `ROUND-20260711-REQUEST-ARTIFACT-IDENTITY-TRUTH-RECONCILIATION-V1`; `ScopeID`: `REQUEST_ARTIFACT_IDENTITY_TRUTH_RECONCILIATION_V1`.
- `SYSTEM_DELTA`: Reconciled mandatory current truth to the valid terminal reviewer-independence PASS at commit `e50219051df8bc8fc1f21312325f01cea4a8e18d`. The former dispatch Markdown, JSON, and dependent PASS report remain quarantined as `INVALID_NOT_DISPATCHED`; no Gate A or Gate B/C message is proven sent.
- `PM / Product Delta`: Commit 1 `a86c3a0fcc34d29e8d76cded5616c6cbe77f500e` still banks the exact four request payloads, and commit `c642a94944831adbd7ecc06fb16259c87fcdd213` still holds the detached envelope with lifecycle `PREPARED_NOT_SENT`. No payload or envelope bytes changed.
- `EVIDENCE_DELTA`: Three distinct read-only Reviewer A/B/C agents, each pinned to `c642a94944831adbd7ecc06fb16259c87fcdd213`, independently passed semantics, raw Git/blob identity, and hash/lifecycle/forbidden-scope checks against payload commit `a86c3a0fcc34d29e8d76cded5616c6cbe77f500e`; terminal SAW is PASS. Truth reconciliation context validation, governance preflight, planning boot preflight, and fixed-artifact byte checks also PASS.
- `OPEN_DECISION`: None for request-artifact identity closure. Gate A/B/C dispatch is a separate explicit owner decision and remains denied by default.
- `RECOMMENDED_NEXT_STEP`: Hold the verified artifacts at `PREPARED_NOT_SENT`; do not rerun implementation or reviewers and do not dispatch without a separate owner authorization.
- `DO_NOT_REDECIDE`: Do not redirect to or cherry-pick divergent `51b1471ff93741fd339d506399413c928479db5a`; reject legacy, reconstructed, or unbound artifacts. No remotes, dispatch, source/provider access, factual validation, readiness promotion, Gate D, publication, or data output.
- `PHASE_STATUS`: PASS for request-artifact identity repair and terminal reviewer independence. Dispatch remains denied; A/B/C/D factual statuses and `m6b_data_contract_ready=false` remain unchanged.

## Prior Addendum — Checkout Hygiene / Governance Recovery (2026-07-11)

- `RoundID`: `ROUND-20260711-CHECKOUT-HYGIENE-GOV-RECOVERY`; `ScopeID`: `CHECKOUT_HYGIENE_GOV_RECOVERY_V1`.
- `SYSTEM_DELTA`: Path A banked; GOV-002/GOV-008 fixed; locked PEAD evidence LF restored; planning preflight green at `e470137`.
- `PM / Product Delta`: Hygiene green did not establish exact request-artifact identity and therefore did not enable dispatch.
- `OPEN_DECISION`: Superseded by the active request-artifact identity repair.
- `RECOMMENDED_NEXT_STEP`: See the active identity-repair addendum.
- `DO_NOT_REDECIDE`: Do not treat hygiene green as BootReady or source-access authority.
- `PHASE_STATUS`: Hygiene/governance recovery PASS for planning mode.

## Prior Addendum — P0 Trust-Substrate Repair (2026-07-11)

- `RoundID`: `ROUND-20260711-V2-PEAD-P0-TRUST-SUBSTRATE-REPAIR`; `ScopeID`: `V2_PEAD_P0_TRUST_SUBSTRATE_REPAIR`.
- `SYSTEM_DELTA`: Boot identity now removes ambient Git redirection/configuration, disables replacement objects, requires raw HEAD/upstream commits plus a verified HEAD tree, and rejects loose/packed `refs/replace/*`; the strict Path A loader rejects duplicate JSON object keys at every depth before evidence or authorization evaluation and before any output write.
- `PM / Product Delta`: P0 repair and fresh independent A/B/C review pass. Subsequent hygiene/governance blockers are addressed in the active recovery addendum.
- `EVIDENCE_DELTA`: Focused adversarial tests and fresh A/B/C pass for Git environment isolation, loose/packed replacement refs, forged displayed ancestry, unborn/broken/tag-shaped identity, duplicate authority/evidence keys, and no-output/no-temp duplicate-input failures.
- `OPEN_DECISION`: Superseded on next-step status by hygiene recovery; still valid for P0 identity guardrails.
- `RECOMMENDED_NEXT_STEP`: See active hygiene recovery addendum.
- `DO_NOT_REDECIDE`: Do not weaken Git identity or duplicate-key fail-closed rules.
- `PHASE_STATUS`: P0 code repair banked; planning preflight green after hygiene recovery.

## Authoritative Addendum - V2 PEAD M6b Slice 0 Active-Contract Deconfliction (2026-07-02)

- `RoundID`: `ROUND-20260702-V2-PEAD-M6B-SLICE0-CONTRACT-DECONFLICTION`.
- `ScopeID`: `V2_PEAD_M6B_SLICE0_ACTIVE_CONTRACT_DECONFLICTION_DOCS_ONLY`.
- `SYSTEM_DELTA`: Updated only the active M6b phase brief so first-public/unrestated EPS is the sole strict Gate A PASS route; restated EPS remains a non-strict diagnostic label and cannot promote strict readiness.
- `PM / Product Delta`: The canonical Ship-Fast Decision Gate template now requires repository remote/root, commit, tree, artifact path, and artifact hash verification for every approval/request packet; identity mismatch requires denial and rerouting, not synthetic provenance.
- `EVIDENCE_DELTA`: Local Quant verification found that the claimed R0.1 commit `cc96053513f445f143632103c478367bbf674e12` does not resolve in this repository and `R0.1-preflight-plan.md` is absent at the root. No R0.1 authority transferred into Quant.
- `OPEN_DECISION`: Dispatch the already prepared Gate A and Gate B/C data-owner source-access requests.
- `RECOMMENDED_NEXT_STEP`: Request-dispatch sequencing only; await separate data-owner responses before any source artifact, provider, factual validation, or implementation work.
- `DO_NOT_REDECIDE`: Do not change historical addenda, treat a restated-EPS exception as strict evidence, reconstruct R0.1 in Quant, or begin data/provider/ETL/curve/readiness work.
- `PHASE_STATUS`: Slice 0 is docs-only; canonical current evidence and strict readiness remain unchanged.

## Authoritative Addendum - V2 PEAD Strict M6b Phase 0 Successor Requests (2026-07-01)

- `RoundID`: `ROUND-20260701-V2-PEAD-M6B-STRICT-DATA-PHASE0-SUCCESSOR`.
- `ScopeID`: `V2_PEAD_M6B_STRICT_DATA_PHASE0_DOCS_ONLY`.
- `SYSTEM_DELTA`: Created versioned 20260701 successor Gate A contract and source-access request artifacts; preserved all 20260630 predecessors and their historical hashes.
- `PM / Product Delta`: Gate A request now requires data-owner capability attestation at approval, conditional one-to-one timing linkage when the PIT record lacks eligible timing, and an authorized immutable calendar source of record with replayable session mapping.
- `EVIDENCE_DELTA`: Successor contract SHA-256 `27a065e5a37d44acd5e423e448d0a894274b48215eb0bcfc32968d5ba5931063`; successor request SHA-256 `913196ba279dd49442ce6b3bbde54d185c188a2d26e21cf462d853bbe295505b`.
- `OPEN_DECISION`: Data owner must approve or decline separate Gate A and Gate B/C source-access requests; Gate D remains deferred pending a source-independent consumer-interface audit.
- `RECOMMENDED_NEXT_STEP`: Submit the successor Gate A and Gate B/C requests only after the request-only Thin SAW closeout passes.
- `DO_NOT_REDECIDE`: Do not inspect local raw artifacts, use credentials or providers, run Gate validation, generate data outputs, or infer readiness from these request artifacts.
- `PHASE_STATUS`: Canonical current evidence and strict readiness remain unchanged.

## Authoritative Addendum - V2 PEAD Strict M6b Path A Gate Infrastructure (2026-06-30)

- `RoundID`: `ROUND-20260629-V2-PEAD-M6B-STRICT-PATH-A-INFRA`.
- `ScopeID`: `V2_PEAD_M6B_STRICT_PATH_A_DATA_GATE_INFRA`.
- `SYSTEM_DELTA`: Repaired the evidence-only, atomic JSON validator so malformed authorization JSON/schema and synthetic-test-plus-authorization are CLI input errors and current gate PASS requires detached exact-file authorization plus all four verified local source-byte hashes.
- `PM / Product Delta`: Data Path A is active, but strict M6b remains fail-closed. M6a is sparse engine/framework evidence only; Strategy promotion and Frontend/UI remain held.
- `QUALITY_DELTA`: Strict-gate tests PASS 68/68; existing M6a tests PASS 12/12; compile, two-run determinism, explicit-`--output` argparse rejection, synthetic canonical-output rejection before atomic write, payload-only restated-approval rejection, malformed-evidence/authorization no-output errors, authorization mismatch, source-byte tamper, atomic-cleanup, static-isolation, output-isolation, and canonical context build/validation checks PASS.
- `EVIDENCE_DELTA`: `docs/context/e2e_evidence/pead_m6b_strict_path_a_readiness.json` SHA-256 `0ef4b2504f7f573eab734614054e3c3e9ffa746b02522a6ef00a51453010574a`; A/B/C/D=`BLOCKED`; source bytes unverified; `strict_vintage_pit=false`; restated-EPS exception=`NOT_AUTHORIZED`; `m6b_data_contract_ready=false`.
- `OPEN_DECISION`: No exception is authorized. Inherited wording that permits a flagged restated-EPS exception is superseded on current truth surfaces and cannot satisfy strict Gate A.
- `RECOMMENDED_NEXT_STEP`: Next action: obtain authorized, verifiable evidence for the smallest blocked strict-data gate.
- `DO_NOT_REDECIDE`: Do not use synthetic fixtures, tests, validator existence, reviewer approval, or illustrative B as readiness evidence; do not open UI or Strategy promotion.
- `PHASE_STATUS`: Infrastructure locally validated; strict M6b data contract remains BLOCKED pending authoritative gate evidence and terminal infrastructure review.

## Authoritative Addendum - V2 PEAD Strict M6b Path A Gates Opened (2026-06-29)

- `RoundID`: `ROUND-20260629-V2-PEAD-M6B-STRICT-DATA-PATH-A`.
- `ScopeID`: `V2_PEAD_M6B_STRICT_DATA_PATH_A_GATES`.
- `SYSTEM_DELTA`: Opened strict M6b Path A data gates in `docs/phase_brief/v2-pead-m6b-strict-data-path-a.md` for first-public EPS vintage, delisting-adjusted tradable returns, as-of liquidity/tradability screen, and short borrow assumptions. Refreshed stale cross-stream docs to June 25 M6 truth.
- `PM / Product Delta`: Fastest valid reboot is strict M6b Data Path A, not Strategy or Frontend. Data is done for diagnostic/M6a-engine use but not "done done" for a tradable research run.
- `QUALITY_DELTA`: Strict M6b data readiness remains fail-closed (`m6b_data_contract_ready = false`) until all four strict data gates pass or receive explicit flagged exceptions.
- `EVIDENCE_DELTA`: Stale cross-stream docs (`multi_stream_contract_current.md`, `post_phase_alignment_current.md`) refreshed to June 25 M6 truth. Strict M6b Path A brief established.
- `OPEN_DECISION`: Execute strict M6b Path A data prep for Gates 1-4.
- `RECOMMENDED_NEXT_STEP`: Start strict M6b Path A data prep for first-public EPS, delisting-adjusted tradable returns, as-of liquidity/tradability screen, and borrow assumptions.
- `DO_NOT_REDECIDE`: Do not wire best-available B into strict M6b, do not modify strict readiness flags, and do not build alpha-named frontend or strategy code before strict data gates pass.
- `PHASE_STATUS`: Strict M6b Path A data gates opened; real M6 curve remains blocked fail-closed pending strict data.

## Authoritative Addendum - V2 PEAD M6b Option 1 Repair PASS (2026-06-25)

- `RoundID`: `ROUND-20260625-V2-PEAD-M6B-BESTAVAIL-OPTION1-REPAIR`.
- `ScopeID`: `V2_PEAD_M6B_BESTAVAIL_OPTION1_TERMINAL_WINDOW_AND_COMMIT_REPAIR`.
- `SYSTEM_DELTA`: B now enforces full 60-session eligibility before the sparse engine, adds direct script bootstrap for standalone invocation, and commits B JSON/parquet through `--commit-bestavail-run` with data gate first and rollback-protected package replacement.
- `PM / Product Delta`: The repaired B artifact is coherent as an illustrative 60-session engine sanity diagnostic only. It still does not authorize alpha, tradable, or strict M6b readiness claims.
- `QUALITY_DELTA`: Direct `--data-gate` PASS; direct `--commit-bestavail-run` PASS; B focused pytest PASS 5/5; M6 sparse-engine pytest PASS 12/12; compile PASS; JSON/parquet consistency PASS with 975 rows, matching parquet SHA, `2016-01-15` to `2019-11-27`, duplicate dates 0, and null gross/net returns 0.
- `EVIDENCE_DELTA`: Repaired run evidence reports `selected_events_after_signal_filter=27941`, `selected_events_with_incomplete_60_session_window=0`, `full_60_session_eligibility_enforced=true`, and `commit_protocol.command=--commit-bestavail-run`. SAW repair report published at `docs/saw_reports/saw_v2_pead_m6b_bestavail_option1_repair_20260625.md`.
- `OPEN_DECISION`: None for B repair. Strict Path A remains separate and unauthorized.
- `RECOMMENDED_NEXT_STEP`: Keep B closed as a flagged engine sanity diagnostic only; only separately authorized strict Path A data gates can support future alpha/tradable work.
- `DO_NOT_REDECIDE`: Do not wire best-available B into strict M6b, do not modify strict readiness flags, and do not use B as alpha/tradable evidence.
- `PHASE_STATUS`: M6b Option 1 B repair PASS locally under hard claim ceiling.


## Authoritative Addendum - V2 PEAD M6b Option 1 Reviewer C BLOCK (2026-06-25)

- `RoundID`: `ROUND-20260625-V2-PEAD-M6B-BESTAVAIL-OPTION1-REVIEWER-C`.
- `ScopeID`: `V2_PEAD_M6B_BESTAVAIL_OPTION1_REVIEWER_C_DATA_INTEGRITY_PERFORMANCE`.
- `SYSTEM_DELTA`: Reviewer C replayed and validated the B gate/run artifacts but found a data-integrity blocker: 1,796 / 29,737 selected events have `exit_idx` beyond the 2015-2019 return-calendar max, so terminal cohorts cannot complete the configured 60-session holding rule inside the B frame.
- `PM / Product Delta`: B remains illustrative-only and cannot close as a coherent 60-session diagnostic curve until terminal-window eligibility is repaired or explicitly excluded/flagged. It still does not authorize alpha, tradable, or strict M6b readiness claims.
- `QUALITY_DELTA`: Gate/run import replay PASS with stable content hashes; focused combined pytest PASS 14/14; compile PASS; parquet/JSON consistency PASS for 997 rows and `2016-01-15` to `2019-12-31`; runtime reference scan PASS; direct script invocation BLOCKS with `ModuleNotFoundError: No module named 'scripts'`.
- `EVIDENCE_DELTA`: Reviewer C report published at `docs/saw_reports/saw_v2_pead_m6b_bestavail_option1_reviewer_c_20260625.md`; ClosureValidation PASS; SAWBlockValidation PASS.
- `OPEN_DECISION`: Repair B terminal-window coverage and direct standalone invocation, regenerate B artifacts, then rerun Reviewer A and Reviewer C. Reviewer B still remains pending after repair.
- `RECOMMENDED_NEXT_STEP`: Enforce full 60-session coverage within the 2015-2019 B return calendar or explicitly remove/flag terminal-truncated cohorts before regenerated metrics are reported.
- `DO_NOT_REDECIDE`: Do not wire best-available B into strict M6b, do not modify strict readiness flags, and do not use B as alpha/tradable evidence.
- `PHASE_STATUS`: M6b Option 1 Reviewer C is BLOCK.


## Authoritative Addendum - V2 PEAD M6b Option 1 Reviewer A BLOCK (2026-06-25)

- `RoundID`: `ROUND-20260625-V2-PEAD-M6B-BESTAVAIL-OPTION1-REVIEWER-A`.
- `ScopeID`: `V2_PEAD_M6B_BESTAVAIL_OPTION1_REVIEWER_A_STRATEGY_CORRECTNESS`.
- `SYSTEM_DELTA`: Reviewer A reviewed the standalone B implementation and found a High strategy-correctness blocker: late-2019 events can enter while returns are capped at 2019-12-31, so the advertised 60-session holding semantics can be truncated at the terminal boundary.
- `PM / Product Delta`: B remains illustrative-only, not alpha, not tradable, and not strict M6b readiness. The curve artifact should not be accepted until terminal-window eligibility is repaired or explicitly removed from reported metrics.
- `QUALITY_DELTA`: Focused combined pytest PASS 14/14; compile PASS; closure packet validator PASS; SAW block validator PASS for the Reviewer A report.
- `EVIDENCE_DELTA`: Reviewer A report published at `docs/saw_reports/saw_v2_pead_m6b_bestavail_option1_reviewer_a_20260625.md`.
- `OPEN_DECISION`: Repair or explicitly remove terminal-truncated B windows, regenerate B artifacts, then rerun Reviewer A.
- `RECOMMENDED_NEXT_STEP`: Enforce full 60-session eligibility inside the 2015-2019 B frame before rerunning the standalone curve.
- `DO_NOT_REDECIDE`: Do not broaden B beyond 2015-2019, do not wire B into strict M6b, and do not claim alpha/tradability.
- `PHASE_STATUS`: M6b Option 1 Reviewer A is BLOCK.


## Authoritative Addendum - V2 PEAD M6b Best-Available Option 1 RUN COMPLETE (2026-06-25)

- `RoundID`: `ROUND-20260625-V2-PEAD-M6B-BESTAVAIL-OPTION1`.
- `ScopeID`: `V2_PEAD_M6B_DATA_GATE_BESTAVAIL_POLICY_READ_ONLY`.
- `SYSTEM_DELTA`: Option 1 is selected and documented: M6b-DATA-GATE is read-only policy evidence only, and the future B run is a standalone 2015-2019 best-available illustrative diagnostic, not a reusable M6b data adapter.
- `PM / Product Delta`: Best-available B is accepted only with hard flags and only for engine sanity. It remains not alpha, not tradable, and not M6b strict readiness.
- `QUALITY_DELTA`: Gate CLI replay wrote the no-curve policy artifact. Standalone B emitted flagged JSON plus daily parquet. Focused combined pytest passed 14/14 and the new standalone script compiles.
- `EVIDENCE_DELTA`: Data-gate artifact exists at `docs/context/e2e_evidence/pead_m6b_data_gate_bestavail_policy_20260625.json`; standalone run artifact exists at `docs/context/e2e_evidence/pead_m6b_bestavail_illustrative_2015_2019.json`; daily parquet exists at `data/processed/pead_m6b_bestavail_illustrative_2015_2019_daily_returns.parquet`.
- `OPEN_DECISION`: Independent terminal review/SAW reconciliation remains pending; no strict A data or alpha/tradable claim is authorized by B.
- `RECOMMENDED_NEXT_STEP`: Run independent Reviewer A/B/C or a bounded reviewer pass for the Option 1 B artifact before any closure language.
- `DO_NOT_REDECIDE`: Do not wire best-available B into strict M6b, do not modify `m6b_real_run_wiring_allowed`, do not change strict readiness flags, and do not use B as alpha/tradable evidence.
- `PHASE_STATUS`: M6b-DATA-GATE and standalone M6b-RUN-BESTAVAIL completed locally under hard B flags; strict A remains deferred.


## Authoritative Addendum - V2 PEAD M6a.1 Reviewer C Rerun PASS (2026-06-25)

- `RoundID`: `ROUND-20260625-V2-PEAD-M6A-1-REVIEWER-C-RERUN`.
- `ScopeID`: `V2_PEAD_M6A_1_REVIEWER_C_DATA_INTEGRITY_AND_PERFORMANCE_RERUN`.
- `SYSTEM_DELTA`: Independent Reviewer C rerun validated the M6a.1 sparse DuckDB interval engine, numeric relation projection, object-dtype guards, duplicate return rejection, deterministic daily hash parity, turnover parity, full-universe synthetic smoke, and fail-closed CLI behavior.
- `PM / Product Delta`: Reviewer C is now PASS for data integrity and performance path. This is reviewer evidence only and does not authorize a real curve, CAGR, daily return parquet, provider access, UI, alpha interpretation, ranking/scoring, alerts, recommendations, or broker/order paths.
- `QUALITY_DELTA`: Focused M6a.1 PASS 12/12; M5a+M6a.1 PASS 16/16; broader PEAD PASS 109/109; compile PASS; fail-closed CLI replay PASS; full-universe smoke PASS with 4.04s call duration under the 60-second budget.
- `EVIDENCE_DELTA`: `docs/saw_reports/saw_v2_pead_m6a_1_reviewer_c_rerun_20260625.md` published and validated; current M6 evidence SHA256 remains `d55da0ec4ed551b763f0f445f5397a3014181bfaa04e2eae96378db303924dee`.
- `OPEN_DECISION`: Complete or reconcile remaining independent Reviewer B terminal evidence before M6a.1 terminal SAW closure.
- `RECOMMENDED_NEXT_STEP`: Run/reconcile Reviewer B, then perform final M6a.1 closure reconciliation; only then open M6b data-prep for separate strict data gates.
- `DO_NOT_REDECIDE`: Do not treat Reviewer C PASS or engine-scale readiness as strict PIT vintage, delisting-adjusted tradable net CAGR, alpha, strategy promotion, ranking/scoring, alerts, recommendations, broker/order authority, or M6b data readiness.
- `PHASE_STATUS`: M6a.1 core implementation complete locally; Reviewer C terminal rerun PASS; Reviewer B/final reconciliation still pending; M6b data gates remain blocked.


## Authoritative Addendum - V2 PEAD M6a.1 Core Guard Completion (2026-06-25)

- `RoundID`: `ROUND-20260625-V2-PEAD-M6A-SCALE-SPARSE-PORTFOLIO-ENGINE`.
- `ScopeID`: `V2_PEAD_M6A_SCALE_SPARSE_PORTFOLIO_ENGINE`.
- `SYSTEM_DELTA`: The sparse engine now derives a sorted global `return_idx:int32` calendar, joins with `entry_idx <= return_idx <= exit_idx`, projects numeric-only DuckDB relations, rejects object dtypes, uses one-worker compensated aggregation, and hashes canonical daily output for reproducibility.
- `PM / Product Delta`: The M6a.1 core delivery is locally complete; this improves parity and scale safety only and does not emit a curve or change M6b data readiness.
- `QUALITY_DELTA`: Focused M6 PASS 12/12, M5a+M6 PASS 16/16, broader PEAD PASS 109/109; the 11,798,280-position-day smoke remains bounded by 1024MB and 60 seconds.
- `EVIDENCE_DELTA`: `--validate-inputs` returns 0 and `--run` returns 2 with blocked evidence; runtime evidence now declares calendar, projection/dtype, and deterministic hash guards.
- `OPEN_DECISION`: Reviewer A and Reviewer B terminal reruns passed for strategy correctness and runtime resilience; a fresh Reviewer C rerun remains required because the available C report predates the sparse-core remediation.
- `RECOMMENDED_NEXT_STEP`: Obtain a fresh Reviewer C terminal rerun; only then open M6b data-prep for its separate strict data gates.
- `DO_NOT_REDECIDE`: Do not add physical repartitioning, chunking, Numba, or multiprocessing without a bounded profile proving necessity. Do not interpret engine readiness as M6b data readiness.
- `PHASE_STATUS`: M6a.1 core implementation complete locally; Reviewer A and Reviewer B terminal reruns PASS; fresh Reviewer C and M6b data gates remain blocked.


## Authoritative Addendum - V2 PEAD M6a.1 Sparse Portfolio Engine Scale Remediation (2026-06-25)

- `RoundID`: `ROUND-20260625-V2-PEAD-M6A-SCALE-SPARSE-PORTFOLIO-ENGINE`.
- `ScopeID`: `V2_PEAD_M6A_SCALE_SPARSE_PORTFOLIO_ENGINE`.
- `SYSTEM_DELTA`: Replaced the event-row Python loop, per-security dataframe slices, dataframe-list accumulation, and dense turnover pivot in `build_daily_portfolio_returns` with a DuckDB ASOF start lookup, bounded per-security return-ordinal interval join, sparse previous/current weight-union turnover, explicit final trade-to-zero exit, and direct daily aggregation under a 1024MB DuckDB cap.
- `PM / Product Delta`: M6a.1 is scale-ready as an engine-only framework component. This does not authorize a real curve, CAGR, daily return parquet, or M6b data acceptance.
- `QUALITY_DELTA`: M6 focused tests PASS 10/10; M5a+M6 PASS 14/14; broader PEAD regression PASS 107/107. The full-universe synthetic smoke covers 196,638 events x 60 sessions (11,798,280 bounded position-days) in 5.59 seconds under the configured 1024MB cap.
- `EVIDENCE_DELTA`: Current blocked evidence has `m6a_scale_engine_ready=true` and `m6b_real_run_wiring_allowed=true`, while `m6b_data_contract_ready=false`; the flag is explicitly engine-scale-only.
- `OPEN_DECISION`: Independent terminal Reviewer A/B/C evidence is still required for SAW closure of this code change.
- `RECOMMENDED_NEXT_STEP`: After independent review, start M6b data-prep only for the separate EPS-vintage, delisting-adjusted tradable-return, and full as-of tradability/liquidity data gates.
- `DO_NOT_REDECIDE`: Do not treat scale readiness as strict PIT vintage, delisting-adjusted tradable net CAGR, alpha, strategy promotion, ranking/scoring, alerts, recommendations, or broker/order authority.
- `PHASE_STATUS`: M6a.1 engine repair implemented and locally validated; terminal independent SAW review pending. M6b data remains blocked independently.


## Authoritative Addendum - V2 PEAD M6a PIT Walk-Forward Equity Framework FAIL-CLOSED (2026-06-24)

- `RoundID`: `ROUND-20260624-V2-PEAD-M6A-PIT-WALK-FORWARD-EQUITY-FRAMEWORK`.
- `ScopeID`: `V2_PEAD_M6A_PIT_WALK_FORWARD_EQUITY_FRAMEWORK_FAIL_CLOSED`.
- `SYSTEM_DELTA`: Implemented `scripts/pead_m6_pit_walk_forward_equity_curve.py` and `tests/test_pead_m6_pit_walk_forward_equity_curve.py`. The runner now has a strict M6 input contract, decision-date walk-forward fold builder, synthetic strict-input portfolio engine, explicit nonzero cost model, equity/CAGR/drawdown/Sharpe/turnover metric functions, and evidence JSON schema.
- `PM / Product Delta`: M6 is split into M6a framework/input-contract evidence and M6b data-prep/real-run. Current artifacts fail closed and produce no tradable equity curve or CAGR.
- `QUALITY_DELTA`: M6 focused tests PASS 7/7; M5a+M6 focused tests PASS 11/11; broader PEAD regression slice PASS 104/104; M6 script compile PASS. `--validate-inputs` writes blocked evidence; `--run` writes blocked evidence and exits code 2.
- `EVIDENCE_DELTA`: `docs/context/e2e_evidence/pead_m6_pit_walk_forward_equity_curve.json` records `workflow_status=blocked_fail_closed`, failure reasons `pit_vintage_blocked`, `delisting_missing`, `tradable_return_missing`, and `tradability_liquidity_screen_missing`; `daily_returns_emitted=false`; `equity_curve_emitted=false`.
- `OPEN_DECISION`: Approve or hold M6b data-prep. M6b must add first-public/unrestated EPS vintage or explicitly accept best-available restated EPS with flags, plus delisting-adjusted tradable daily returns and a full as-of tradability/liquidity screen.
- `RECOMMENDED_NEXT_STEP`: Start M6b data-prep only; do not treat M6a as a passed curve or CAGR run.
- `DO_NOT_REDECIDE`: Do not claim strict vintage-PIT, delisting-adjusted tradable net CAGR, live alpha, strategy promotion, ranking/scoring, alerts, recommendations, or broker/order readiness from M6a. Do not mutate locked D3/D2B or publish daily M6 return parquet from current inputs.
- `PHASE_STATUS`: M6a framework/input-contract evidence implemented; real M6 curve blocked fail-closed pending M6b data.

## Authoritative Addendum - V2 PEAD M5a Net Multi-Factor Local Run PASS (2026-06-24)

- `RoundID`: `ROUND-20260624-V2-PEAD-M5A-NET-MULTIFACTOR-DIAGNOSTIC`.
- `ScopeID`: `V2_PEAD_M5A_NET_MULTIFACTOR_DIAGNOSTIC_ONLY`.
- `SYSTEM_DELTA`: Built and published the daily multifactor factor artifact (`pead_d3m_ken_french_daily_multifactor`) against the full universe session spine. Ran the net multi-factor diagnostic runner (`pead_m5a_net_multifactor_alpha_test.py`) with `--spread-cost-bps-per-day 0` and `--no-enforce-counts` to generate diagnostic evidence `pead_m5a_net_multifactor_alpha_test.json`.
- `PM / Product Delta`: Daily multifactor factors and diagnostic alpha test results published under strict full-universe session spine mapping. Bypassed count contracts via `--no-enforce-counts` to align with full universe data.
- `QUALITY_DELTA`: Full repository test suite runs and passes cleanly (exit 0, 2057 passed). Thin SAW report created at `docs/saw_reports/saw_v2_pead_m5a_net_multifactor_run_20260624.md`.
- `EVIDENCE_DELTA`: Factor table Parquet/manifest pair published atomically. Diagnostic JSON output successfully written to `docs/context/e2e_evidence/pead_m5a_net_multifactor_alpha_test.json`.
- `OPEN_DECISION`: Proceed to the next scheduled quantitative research phase.
- `RECOMMENDED_NEXT_STEP`: Review the diagnostic OLS multi-factor regressions in the published JSON.
- `DO_NOT_REDECIDE`: All alpha-named dashboard integration, alerts, and trading paths remain strictly blocked.
- `PHASE_STATUS`: M5a local run PASS.

## Authoritative Addendum - V2 PEAD Alpha Interpretation Gate OPEN (2026-06-24)

- `RoundID`: `ROUND-20260624-V2-PEAD-ALPHA-INTERPRETATION-GATE`.
- `ScopeID`: `V2_PEAD_ALPHA_INTERPRETATION_GATE_DOCS_ONLY`.
- `SYSTEM_DELTA`: A docs-only Alpha Interpretation Gate is opened before any further dashboard scope. The gate reclassifies the current full-universe M1B statistic as descriptive methodology evidence only, because the evidence policy itself forbids alpha, full-factor alpha, net-performance, causal, tradability, strict PIT, and population-validity claims.
- `PM / Product Delta`: Replace any dashboard-first or alpha-dashboard route with a gate-controlled branch: Path A may show only a descriptive evidence panel with hard disclaimers; Path B must first run M5 PIT/data/method upgrades before any real alpha assertion.
- `QUALITY_DELTA`: No code, tests, data artifacts, provider calls, dashboard runtime, ranking/scoring, alert, recommendation, broker/order, staging, or commit scope is authorized or performed.
- `EVIDENCE_DELTA`: Full-universe M1B evidence records `alpha_ct=0.0007053337347976517` and HAC t-stat `9.582565792521386`, but its policy has `allowed_use=bounded_methodology_review_only`, `interpretation_performed=false`, and forbidden alpha/PIT/tradability claims; limitations include current-vintage Compustat EPS, Compustat proxy returns, no delisting adjustment, and gross single-factor equal-weight Q5-minus-Q1.
- `OPEN_DECISION`: Approve or hold `docs/phase_brief/v2-pead-alpha-interpretation-gate.md`.
- `RECOMMENDED_NEXT_STEP`: Review the Alpha Interpretation Gate; only after approval choose Path A descriptive evidence panel or Path B M5 PIT/data/method upgrade.
- `DO_NOT_REDECIDE`: Do not write alpha-named or alpha-implying dashboard/code while the gate is unapproved or the 28-commit branch state is unreconciled with `main`; do not claim alpha, tradability, PIT, net performance, population validity, ranking/scoring, alerts, recommendations, or order readiness from the current evidence.
- `PHASE_STATUS`: M4B.1 remains PASS; Alpha Interpretation Gate is OPEN; alpha dashboard and alpha code remain blocked.

## Prior Addendum - V2 PEAD M4B.1 Evidence Contract Repair PASS (2026-06-23)

- `RoundID`: `ROUND-20260623-V2-PEAD-M4B-1-EVIDENCE-CONTRACT-REPAIR`.
- `ScopeID`: `V2_PEAD_M4B_1_EVIDENCE_CONTRACT_REPAIR`.
- `SYSTEM_DELTA`: M4B.1 evidence contract repair is fully verified. CLI `--publish-evidence-pair` guard prevents writing files to disk if contract verification checks fail. Dataclass immutability of `EvidenceProfile` and child-parent hash linkage verified.
- `PM / Product Delta`: M4B.1 evidence contract is now PASS. M4C/dashboard exposure remains blocked as a separate scoping decision.
- `QUALITY_DELTA`: Full repository test suite runs and passes cleanly (exit 0). Focused contract repair tests pass successfully.
- `EVIDENCE_DELTA`: SAW Report `saw_v2_pead_m4b_1_evidence_contract_repair_20260623.md` and SE Execution Report `se_v2_pead_m4b_1_evidence_contract_repair_20260623.md` generated and validated.
- `OPEN_DECISION`: Scope M4C/dashboard exposure under a separate scoping decision.
- `RECOMMENDED_NEXT_STEP`: Resolve M4C/dashboard scoping block.
- `DO_NOT_REDECIDE`: Do not open M4C/dashboard work; do not generate PEAD data, mutate canonical JSON/evidence, manifests, processed artifacts, strategy/UI, provider, ranking/scoring, alerts, recommendations, or broker/order paths until authorized.
- `PHASE_STATUS`: M4B.1 evidence-contract closure PASS; M4C/dashboard blocked.

## Latest Addendum - V2 PEAD M4B Full-Universe Validation and Inference PASS (2026-06-22)

- RoundID: ROUND-20260622-V2-PEAD-M4B-FULL-UNIVERSE-VALIDATION-INFERENCE.
- ScopeID: V2_PEAD_M4B_FULL_UNIVERSE_VALIDATION_INFERENCE.
- SYSTEM_DELTA: Rebuilt and published the D3 daily benchmark against the full D2B manifest to `data/processed/pead_d3_ken_french_daily_benchmark.parquet`. Generated `pead_real_data_validation_full_universe.json` and `pead_calendar_time_inference_m1b_full_universe.json` for the full universe by implementing memory footprint optimizations (early lineage tracking, column pruning, garbage collection) in `scripts/pead_real_data_validation.py` to run calendar-time portfolio regressions within local memory limits.
- PM / Product Delta: Full-universe validation and inference successfully run and published under strict memory bounds. Bypassed count contracts for full universe via `--no-enforce-counts` CLI parameter. Legacy validation and calendar-time sample files remain completely untouched and protected under their locked SHA256 hashes.
- QUALITY_DELTA: Full repository `pytest -q` runs and passes successfully (exit 0).
- EVIDENCE_DELTA: Legacy validation JSON SHA256 verified unchanged at `96cdc975d0b4798c6775b12e7bc9dc6af4fb7e9178a4d0ad54feeab8100e980e`. Legacy calendar-time inference JSON SHA256 verified unchanged at `c80bb7ed583a933dae664251ffe1fc56a0bcaf5f9a086b1e42740047a5018b76`. Full-universe validation evidence generated at `docs/context/e2e_evidence/pead_real_data_validation_full_universe.json` and full-universe calendar-time inference at `docs/context/e2e_evidence/pead_calendar_time_inference_m1b_full_universe.json`.
- OPEN_DECISION: None. Bounded full-universe artifacts successfully verified.
- RECOMMENDED_NEXT_STEP: Open next phase-end scoping round for Strategy Research Replay dashboard exposure of the full-universe results.
- DO_NOT_REDECIDE: Do not modify strategy logic in `strategies/pead_event_study.py`, mathematical formulas, or build code. Keep yfinance/provider access blocked.
- PHASE_STATUS: M4B full-universe validation and inference PASS.

## Latest Addendum - V2 PEAD M4A Clean-Exit Blocker Fix PASS (2026-06-22)

- RoundID: ROUND-20260622-V2-PEAD-M4A-MEMORY-BOUNDED-FULL-UNIVERSE.
- ScopeID: V2_PEAD_M4A_MEMORY_BOUNDED_D2A_D2B_EXPANSION.
- SYSTEM_DELTA: D2A and D2B now have bounded-memory local full-universe build paths that preserve existing formulas, IID/session semantics, and atomic manifest publication.
- PM / Product Delta: M4A remains code/test readiness only and publishes no alpha or action authority; the actionable execution_microstructure/full-suite clean-exit blocker is now cleared.
- QUALITY_DELTA: focused M4A tests PASS 55/55; broader PEAD D2/D3/event-study regression PASS 79/79; targeted execution_microstructure/status rerun PASS; full repository pytest clean exit PASS.
- EVIDENCE_DELTA: stale pytest/Streamlit smoke processes were stopped; execution_microstructure focused checks PASS 44/44; combined execution_microstructure/context-hygiene/policy-target AppTest PASS 54/54; orchestrator spool-flush and main-console flush-failure regressions PASS; `.venv\Scripts\python -m pytest -q` returned exit 0 in 264.6s; no lingering Python processes remained afterward.
- OPEN_DECISION: whether strict independent Reviewer A/B/C must run before M4B, or whether local clean-exit evidence is enough to move into M4B full-universe artifact dry-run/publication.
- RECOMMENDED_NEXT_STEP: move to M4B full-universe artifact dry-run/publication; keep M3/M5 WRDS/CRSP entitlement paths blocked.
- DO_NOT_REDECIDE: do not reopen provider access, PIT claims, estimator/UI changes, alpha verdicts, ranking/scoring, alerts, recommendations, broker/order paths, or artifact publication inside M4A.
- PHASE_STATUS: M4A execution_microstructure/full-suite clean-exit blocker PASS; strict independent Reviewer A/B/C remains an optional governance gate before M4B.

## Latest Addendum - V2 PEAD M2 Read-Only Status DONE (2026-06-21)

- `RoundID`: `ROUND-20260621-V2-PEAD-M2-READ-ONLY-STATUS`.
- `ScopeID`: `V2_PEAD_M2_READ_ONLY_STATUS_PANEL`.
- `SYSTEM_DELTA`: Strategy Research Replay now exposes a PEAD Evidence Status tab that verifies both locked PEAD evidence artifacts internally and renders PM-readable readiness states instead of hashes/manifests/paths.
- `PM / Product Delta`: M2 ships product value by making the closed M1B evidence visible as read-only status while keeping alpha verdict and promotion explicitly blocked.
- `QUALITY_DELTA`: focused PEAD status tests and Streamlit AppTest coverage verify dual-artifact loading, sanitized fail-closed behavior, no visible audit plumbing, legacy route preservation, and no provider/Parquet/recompute path.
- `EVIDENCE_DELTA`: protected validation JSON remains SHA256 `96cdc975d0b4798c6775b12e7bc9dc6af4fb7e9178a4d0ad54feeab8100e980e`; M1B JSON remains SHA256 `c80bb7ed583a933dae664251ffe1fc56a0bcaf5f9a086b1e42740047a5018b76`.
- `OPEN_DECISION`: owner product review of the status wording/presentation only; alpha-verdict review remains separate.
- `RECOMMENDED_NEXT_STEP`: inspect PEAD Evidence Status and either accept the read-only presentation or request bounded copy/layout changes.
- `DO_NOT_REDECIDE`: do not tune the estimator, mutate evidence/data artifacts, expose hashes as the main UI, claim alpha, promote strategy, rank/score, alert, recommend, or connect broker/order paths.
- `PHASE_STATUS`: M2 frontend read-only status implemented; alpha verdict, promotion, and action surfaces remain blocked pending separate approval.

## Latest Addendum - V2 PEAD M1B Dashboard Marker Closure PASS (2026-06-21)

- `RoundID`: `ROUND-20260621-V2-PEAD-M1B-DASHBOARD-MARKER-CLOSURE`.
- `ScopeID`: `V2_PEAD_M1B_DASHBOARD_MARKER_CLOSURE`.
- `SYSTEM_DELTA`: the inherited full-suite blocker was repaired by restoring the Plotly event-ledger trace names in `dashboard.py` to `ENTER` and `EXIT`; the newer lifecycle hover wording is preserved.
- `PM / Product Delta`: M1B terminal closure is now green. This closes the dashboard marker regression only; it does not create an alpha verdict, strategy promotion, or product/action surface.
- `QUALITY_DELTA`: focused lifecycle regression PASS; `dashboard.py` compile PASS; full repository `pytest -q` PASS; Reviewer A/B/C PASS; closure packet and SAW block validators PASS.
- `EVIDENCE_DELTA`: M1B JSON remains SHA256 `c80bb7ed583a933dae664251ffe1fc56a0bcaf5f9a086b1e42740047a5018b76`; protected 20260620 validation JSON remains SHA256 `96cdc975d0b4798c6775b12e7bc9dc6af4fb7e9178a4d0ad54feeab8100e980e`.
- `OPEN_DECISION`: open a separate alpha-verdict review gate if desired; do not combine it with dashboard expansion or action-surface work.
- `RECOMMENDED_NEXT_STEP`: run a bounded alpha-verdict review gate against the already-published M1B evidence, with interpretation/action authority still explicitly separate.
- `DO_NOT_REDECIDE`: do not tune the estimator, mutate D1/D2B/D3/protected JSON/M1B JSON, change lifecycle semantics, claim PIT/full-universe/tradable alpha, rank/score, alert, recommend, or connect broker/order paths.
- `PHASE_STATUS`: M1B terminal SAW PASS; alpha verdict, promotion, and action surfaces remain blocked pending separate approval.

## Latest Addendum - V2 PEAD Calendar-Time Inference M1B DONE (2026-06-21)

- `RoundID`: `ROUND-20260621-V2-PEAD-CALENDAR-TIME-INFERENCE-M1B`.
- `ScopeID`: `V2_PEAD_CALENDAR_TIME_INFERENCE_IMPLEMENTATION`.
- `SYSTEM_DELTA`: the bounded calendar-time Q5-minus-Q1 estimator is implemented and one strict JSON evidence artifact is published; protected prior evidence and D1/D2B/D3 artifacts remain unchanged.
- `PM / Product Delta`: M1B converts the selected method into reproducible numbers-only methodology evidence, but does not create an alpha verdict, strategy promotion, or any product/action surface.
- `METHOD_DELTA`: all-quantile latest-event overlap resolution, no-security expected-missing accounting, minimum 10 finite securities per leg, HAC(59), and robustness-only paired stationary bootstrap are implemented.
- `EVIDENCE_DELTA`: `docs/context/e2e_evidence/pead_calendar_time_inference_m1b.json` SHA256 `c80bb7ed583a933dae664251ffe1fc56a0bcaf5f9a086b1e42740047a5018b76`; counts are 19,812 null-date rows excluded, 226,772 expected extreme rows, 1,519 missing rows, 2,539 retained sessions, and zero internal gaps.
- `QUALITY_DELTA`: focused PEAD tests PASS 50/50; deterministic CLI/schema/protected-hash checks PASS; Reviewer A/B PASS and Reviewer C technical recheck PASS after High findings were fixed.
- `OPEN_DECISION`: terminal SAW remains BLOCK on one inherited dashboard full-suite failure and unavailable hierarchy-only Reviewer C confirmation.
- `RECOMMENDED_NEXT_STEP`: authorize one bounded closure-recovery round for the dashboard marker regression, then rerun hierarchy-only Reviewer C; do not open product/action scope.
- `DO_NOT_REDECIDE`: do not promote quarterly, tune HAC, mutate D1/D2B/D3/protected JSON, claim alpha, rank/score, alert, recommend, connect broker/order paths, or widen into PIT/full-universe claims.
- `PHASE_STATUS`: M1B implementation/evidence DONE; terminal SAW BLOCK; alpha verdict and product actions remain blocked.

## Latest Addendum - V2 PEAD M1A Inference Methodology PARTIAL (2026-06-21)

- `RoundID`: `ROUND-20260621-V2-PEAD-ALPHA-INFERENCE-METHODOLOGY-GATE`.
- `ScopeID`: `V2_PEAD_CALENDAR_TIME_INFERENCE_METHOD_CONTRACT`.
- `SYSTEM_DELTA`: one calendar-time inference contract is selected, but terminal approval is blocked pending independent Reviewer C count/data-integrity recheck; no estimator code or evidence output changed.
- `PM / Product Delta`: M1A replaces the invalid quarterly-gate removal path with a bounded M1B implementation candidate, but creates no alpha verdict and does not yet authorize M1B execution.
- `METHOD_DELTA`: signal-only event-date assignment, all-quantile latest-event security/date resolution before Q1/Q5 filtering, authoritative `+1..+60` sessions, equal weighting, minimum 10 finite securities per leg, single-factor calendar-time regression, HAC(59), and fully specified robustness-only stationary bootstrap.
- `QUALITY_DELTA`: focused existing PEAD regression passed 37/37; parent-side corrected feasibility count check passes with 19,812 null-`return_date` rows excluded, 226,772 extreme expected rows, and 1,519 missing asset rows.
- `RESEARCH_DELTA`: Fama (1998) journal page 295 / PDF page 13 directly supports rolling calendar-time portfolios for cross-event correlation; claim validation passes 2/2. Exact daily/HAC/bootstrap parameters remain repo-policy adaptations.
- `OPEN_DECISION`: rerun independent Reviewer C on the corrected M1A count contract, then approve or hold the bounded four-file M1B implementation.
- `RECOMMENDED_NEXT_STEP`: rerun Reviewer C terminal recheck; do not implement M1B until that review passes.
- `DO_NOT_REDECIDE`: do not promote quarterly, tune HAC, use future window completeness for signal assignment, fall back to older overlapping events, or widen into product/actions.
- `PHASE_STATUS`: M1A methodology PARTIAL; terminal SAW BLOCK pending Reviewer C. M1B and alpha verdict not complete.

## Latest Addendum - V2 PEAD Read-Only Evidence Dashboard DONE (2026-06-20)

- `RoundID`: `ROUND-20260620-V2-PEAD-READ-ONLY-EVIDENCE-DASHBOARD`.
- `ScopeID`: `V2_PEAD_READ_ONLY_EVIDENCE_DASHBOARD`.
- `SYSTEM_DELTA`: Strategy Research Replay now has an additive JSON-read-only evidence view with hash/schema fail-closed behavior.
- `PM / Product Delta`: the approved D4 slice is implemented as an actual read-only evidence dashboard, not an internal status report or a new approval packet.
- `QUALITY_DELTA`: focused dashboard tests pass 14/14; locked validation plus dashboard tests pass 24/24; broader PEAD regression passes 121/121; compile and Streamlit health checks pass.
- `EVIDENCE_DELTA`: the reader requires JSON SHA256 `96cdc975d0b4798c6775b12e7bc9dc6af4fb7e9178a4d0ad54feeab8100e980e`; the evidence artifact was not changed.
- `REVIEW_DELTA`: Reviewer A/B/C all PASS with no remaining findings; Reviewer A's initial Low legacy-route coverage gap was fixed and rechecked.
- `OPEN_DECISION`: owner product acceptance of the read-only evidence presentation only.
- `RECOMMENDED_NEXT_STEP`: inspect the `Read-Only Evidence` view and either accept it or request bounded presentation changes.
- `DO_NOT_REDECIDE`: no PEAD recomputation, formula/artifact mutation, provider or Parquet access, alpha claim/promotion, rank/score, alert, recommendation, or broker/order path.
- `PHASE_STATUS`: D4 read-only evidence dashboard DONE; all action/interpretation expansion remains blocked.

## Latest Addendum - V2 PEAD Real-Data Validation DONE (2026-06-20)

- `RoundID`: `ROUND-20260620-V2-PEAD-DOCS-CONTEXT-RECONCILIATION`.
- `ScopeID`: `V2_PEAD_REAL_DATA_VALIDATION_CONTEXT_RECONCILIATION`.
- `SYSTEM_DELTA`: existing PEAD real-data validation evidence is now reflected as current planner truth; no formulas, strategy code, dashboard code, data artifacts, or evidence JSON changed.
- `PM / Product Delta`: the next action is not dashboard implementation; it is owner review of the validation JSON and its limitations before any separate dashboard-scoping decision.
- `EVIDENCE_DELTA`: `docs/context/e2e_evidence/pead_real_data_validation_20260620.json` has SHA256 `96cdc975d0b4798c6775b12e7bc9dc6af4fb7e9178a4d0ad54feeab8100e980e`.
- `COUNT_DELTA`: validation evidence records 754,920 rows, 12,582 events, 362 issuers, 11,450 eligible events, and 1,132 ineligible events.
- `INFERENCE_DELTA`: daily event-date CAR/BHAR records 2,777 HAC cohort gaps with HAC SE/t-stat null; quarterly output is `ex_post_descriptive_only = true`.
- `LIMITATION_DELTA`: 500-GVKEY sample, current-vintage EPS, Compustat return proxy, and no delisting adjustment remain explicit limitations.
- `REVIEW_DELTA`: focused tests 10/10, full PEAD regression 99/99, Reviewer A/B/C PASS, and SAW validators PASS were already performed before this docs-context reconciliation.
- `OPEN_DECISION`: owner review of the JSON evidence; after approval only, decide separately whether to scope dashboard exposure.
- `RECOMMENDED_NEXT_STEP`: review `docs/context/e2e_evidence/pead_real_data_validation_20260620.json` against limitations, allowed use, and forbidden use; do not start dashboard work in the same decision.
- `DO_NOT_REDECIDE`: do not change PEAD formulas, evidence artifacts, strategy code, dashboard code, or JSON; do not claim alpha, promote strategy, rank/score, alert, or touch broker/order paths.
- `PHASE_STATUS`: PEAD real-data validation evidence DONE for owner review; dashboard implementation and alpha interpretation remain blocked.

## Latest Addendum - V2 PEAD D3 Strategy Benchmark Handoff DONE (2026-06-20)

- `RoundID`: `ROUND-20260620-V2-D3-STRATEGY-BENCHMARK-HANDOFF`.
- `ScopeID`: `V2_D3_STRATEGY_BENCHMARK_HANDOFF_VALIDATION`.
- `SYSTEM_DELTA`: added an artifact-backed handoff regression; no production strategy or data behavior changed.
- `PM / Product Delta`: the D3 artifact-to-strategy handoff gate is closed, so D4 dashboard-integration scoping is now the next separate decision.
- `QUALITY_DELTA`: new handoff tests passed 5/5; combined handoff, artifact, and strategy tests passed 26/26.
- `HANDOFF_DELTA`: the 754,920-row D2B left join remains many-to-one, all non-null D2B return dates are covered, and all 11,450 complete events receive 60 benchmark observations.
- `FORMULA_DELTA`: no formula changed; real-event checks confirm CAR is `sum(asset - benchmark)` and BHAR is `prod(1 + asset) - prod(1 + benchmark)`.
- `MISSINGNESS_DELTA`: one missing benchmark observation masks CAR/BHAR while preserving complete raw cumulative asset return.
- `REVIEW_DELTA`: initial Reviewer A/B/C High findings were fixed; final independent reruns all returned PASS with no remaining Critical/High findings. SAW evidence: `docs/saw_reports/saw_v2_d3_strategy_benchmark_handoff_20260620.md`.
- `OPEN_DECISION`: approve or hold one bounded D4 dashboard-integration scoping round.
- `RECOMMENDED_NEXT_STEP`: define the D4 reader/view boundary and acceptance checks without implementing dashboard behavior in the scoping round.
- `DO_NOT_REDECIDE`: do not change D2B selection/session semantics, D3 source/formula, benchmark missingness, or the existing strategy formulas; do not interpret alpha or widen into ranking/scoring, alerts, or broker paths.
- `PHASE_STATUS`: D3 strategy benchmark handoff DONE; PEAD phase-end and D4 implementation not claimed.

## Latest Addendum - V2 PEAD D3 Benchmark Artifact Publication DONE (2026-06-20)

- `RoundID`: `ROUND-20260620-V2-D3-BENCHMARK-ARTIFACT-PUBLICATION`.
- `ScopeID`: `V2_D3_KEN_FRENCH_BENCHMARK_ARTIFACT_PUBLICATION`.
- `SYSTEM_DELTA`: D3 now has a published Ken French daily benchmark artifact and atomic manifest pointer covering the repaired 2,810-session D2B spine.
- `PM / Product Delta`: the project moved from D3 publication pending to benchmark input available; abnormal-return interpretation remains a separate gate.
- `QUALITY_DELTA`: focused D3/D2B tests passed 38/38; builder publication reported 2,810 / 2,810 coverage; independent artifact validation found hash match, zero missing sessions, zero duplicate dates, finite numeric fields, and formula error `0.0`.
- `ARTIFACT_DELTA`: published Parquet SHA256 `f7dede990475b4ecf499fbf1dee3c4a81298073f018cc3a1ba1559f3e702c589`; manifest path `data/processed/pead_d3_ken_french_daily_benchmark.parquet.manifest.json`.
- `SOURCE_DELTA`: source release remains `This file was created by using the 202604 CRSP database.` with source ZIP SHA256 `4b384ddeed3ba5541c433071272aece0734129ff5a016790333632eee8eac518`.
- `FORMULA_DELTA`: artifact stores decimal `mktrf`, decimal `rf`, and `benchmark_return = mktrf + rf`; `mktrf` alone remains forbidden as total market return.
- `REVIEW_DELTA`: SAW PASS evidence is `docs/saw_reports/saw_v2_d3_benchmark_artifact_publication_20260620.md`; Reviewer A/B/C returned PASS with no in-scope Critical/High findings.
- `OPEN_DECISION`: approve or hold a separate bounded D3 strategy benchmark handoff validation round.
- `RECOMMENDED_NEXT_STEP`: validate strategy consumption of the published benchmark artifact without alpha interpretation, dashboard integration, ranking/scoring, alerts, broker paths, full build, staging, or commit.
- `DO_NOT_REDECIDE`: do not change D2B security-selection semantics, do not patch/fill/interpolate/zero/substitute benchmark dates, do not splice sources, and do not run CAR/BHAR interpretation or dashboard/product integration in this publication closure.
- `PHASE_STATUS`: D3 benchmark artifact publication DONE; PEAD phase-end not claimed.

## Latest Addendum - V2 PEAD D2B Terminal Reviewer Rerun PASS (2026-06-20)

- `RoundID`: `ROUND-20260620-V2-D2B-SESSION-SPINE-FINAL-REVIEW-RERUN`.
- `ScopeID`: `V2_D2B_AUTHORITATIVE_MARKET_SESSION_SPINE_FINAL_REVIEW`.
- `SYSTEM_DELTA`: D2B session-spine repair moved from terminal SAW BLOCK to terminal SAW PASS after final independent Reviewer A/B/C reran against the repaired state.
- `PM / Product Delta`: the D2B repaired source-backed market-session spine is now reviewer-promoted closure evidence; D3 benchmark artifact publication becomes the next separate approval gate.
- `QUALITY_DELTA`: parent focused validation passed the 70-test matrix; Reviewer A/B/C all returned PASS with no in-scope Critical/High findings.
- `REVIEW_DELTA`: historical BLOCK evidence remains at `docs/saw_reports/saw_v2_d2b_session_spine_repair_20260619.md`; current terminal PASS evidence is `docs/saw_reports/saw_v2_d2b_session_spine_repair_rerun_20260620.md`.
- `ARTIFACT_DELTA`: active D2B SHA256 remains `c3da606af340ba5b531d3d0382e1f2c83469e29a42dd7c0cc9c356cba82594a1`; no D2B data artifact was rebuilt in this rerun.
- `D3_DELTA`: no `pead_d3_ken_french_daily_benchmark*` artifact exists and no D3 publication was performed.
- `OPEN_DECISION`: approve or hold one separate bounded D3 benchmark artifact publication round.
- `RECOMMENDED_NEXT_STEP`: run only the bounded D3 benchmark artifact publication gate against the repaired 2,810-session D2B spine; do not run CAR/BHAR interpretation in the same round.
- `DO_NOT_REDECIDE`: do not restore D2A distinct dates as the market calendar; do not patch benchmark dates inside D3; do not change D2B security-selection semantics. CAR/BHAR interpretation, quintiles, dashboard, ranking/scoring, alerts, broker/order paths, full build, staging, and commit remain blocked.
- `PHASE_STATUS`: D2B session-spine repair terminal reviewer gate PASS; PEAD phase-end not claimed.

## Latest Addendum - V2 PEAD D2B Authoritative Market-Session Spine Repair (2026-06-19)

- `RoundID`: `ROUND-20260619-V2-D2B-SESSION-SPINE-REPAIR`.
- `ScopeID`: `V2_D2B_AUTHORITATIVE_MARKET_SESSION_SPINE`.
- `SYSTEM_DELTA`: D2B now derives its 2015-01-02 through 2026-03-06 market-session spine from the exact official Ken French source bytes instead of treating every distinct D2A observation date as an open session.
- `PM / Product Delta`: 52 U.S. market-closed dates were removed from the session spine without deleting D2A evidence or changing fixed-security selection semantics. The corrected artifact retains 12,582 events and 754,920 rows while eligible handoffs increase from 4,867 to 11,450.
- `QUALITY_DELTA`: authoritative sessions are `2,862 -> 2,810`; complete benchmark coverage is `2,810 / 2,810` in memory; focused validation passes 70 tests; the full strategy smoke produces 687,000 complete rows with zero duplicate keys and zero closed dates.
- `MEMORY_DELTA`: Reviewer C's full-frame handoff High finding is repaired by chunked full-D2A validation and selected-security projection. Active-scale peak RSS is 1,756.7 MiB with no `ArrayMemoryError`.
- `FAIL_CLOSED_DELTA`: cross-row event metadata/timing drift and normalization-colliding D2A duplicate keys now fail closed through direct regressions.
- `ARTIFACT_DELTA`: active D2B SHA256 is `c3da606af340ba5b531d3d0382e1f2c83469e29a42dd7c0cc9c356cba82594a1`; prior immutable SHA256 `8e2f39c2cb12bd0b50c9a134b280b5ecb8cd438f8a2249c6842c226250228b99` is retained for rollback.
- `D3_DELTA`: D3 reconstructs and validates the source-backed D2B session hash with zero missing dates, but no D3 Parquet or manifest was published.
- `REVIEW_DELTA`: terminal SAW is `BLOCK`, not PASS, because final independent Reviewer A/B/C could not run after the last code fixes due reviewer usage limits. Evidence path: `docs/saw_reports/saw_v2_d2b_session_spine_repair_20260619.md`.
- `OPEN_DECISION`: rerun final independent Reviewer A/B/C after reviewer capacity returns, then approve or hold one separate bounded D3 benchmark artifact publication round.
- `RECOMMENDED_NEXT_STEP`: rerun final Reviewer A/B/C on the repaired D2B session-spine state; only after PASS decide whether to publish and validate the D3 benchmark artifact against the repaired 2,810-session spine.
- `DO_NOT_REDECIDE`: do not restore D2A distinct dates as the market calendar; do not patch benchmark dates inside D3; do not change D2B security-selection semantics. CAR/BHAR interpretation, quintiles, dashboard, ranking/scoring, alerts, broker/order paths, full build, staging, and commit remain blocked.
- `PHASE_STATUS`: D2B session-spine code/artifact/test/smoke evidence complete, but terminal SAW remains BLOCK on unavailable final Reviewer A/B/C; D3 publication not performed; PEAD phase-end not claimed.

## Latest Addendum - V2 PEAD D3 Benchmark Artifact Builder PARTIAL (2026-06-19)

- `RoundID`: `ROUND-20260619-V2-D3-BENCHMARK-ARTIFACT-IMPLEMENTATION`.
- `ScopeID`: `V2_D3_BENCHMARK_ARTIFACT_BUILDER_AND_COVERAGE_GATE`.
- `SYSTEM_DELTA`: D3 now has an executable Ken French benchmark builder and focused tests, but no benchmark artifact was published because coverage failed closed.
- `PM / Product Delta`: the next bottleneck is not source availability; the official Ken French daily source is fetchable and covers through 2026-04-30. The blocker is that current D2B/D2A required sessions include 52 dates absent from official Ken French daily factors.
- `QUALITY_DELTA`: focused D3 tests pass 7/7; real build stopped before manifest publication with missing benchmark sessions. Source release observed: `This file was created by using the 202604 CRSP database.` Source SHA256: `4b384ddeed3ba5541c433071272aece0734129ff5a016790333632eee8eac518`.
- `STRATEGY_DELTA`: a review-driven summary repair preserves raw `cumulative_total_return` for complete asset windows when only benchmark coverage is missing; benchmark return, CAR, BHAR, `window_complete`, and `eligible_for_analysis` still fail closed.
- `MISSING_SESSION_DELTA`: required D2B sessions = 2,862; missing benchmark sessions = 52. Examples: 2015-01-19, 2015-05-25, 2015-11-26, 2018-12-05, 2022-06-20, 2025-01-09, 2026-01-19.
- `OPEN_DECISION`: approve or hold a bounded D2B/D2A market-session spine audit and repair.
- `RECOMMENDED_NEXT_STEP`: audit and repair the upstream D2B/D2A session spine so it represents actual benchmark-compatible trading sessions, then rerun the D3 builder.
- `DO_NOT_REDECIDE`: do not fill, drop, interpolate, zero, substitute, or splice benchmark dates inside D3; do not publish a partial benchmark artifact; do not run CAR/quintile interpretation, dashboard, ranking, alerts, broker, full build, staging, or commit.
- `PHASE_STATUS`: D3 artifact builder/tests PARTIAL; benchmark artifact publication BLOCKED; PEAD phase-end not claimed.

## Latest Addendum - V2 PEAD D3 Benchmark Input Design Gate DONE (2026-06-19)

- `RoundID`: `ROUND-20260619-V2-D3-BENCHMARK-INPUT-DESIGN-GATE`.
- `ScopeID`: `V2_D3_BENCHMARK_INPUT_CONTRACT_ONLY`.
- `SYSTEM_DELTA`: D3 benchmark-input semantics are now fixed before implementation: canonical source is Ken French daily Fama/French 3 Factors, source percent fields must be stored as decimal returns, and `benchmark_return = mktrf + rf`.
- `PM / Product Delta`: the next PEAD step is no longer "what benchmark means"; it is a separate bounded implementation of an immutable benchmark artifact that fully covers the D2B 2015-01-02 through 2026-03-06 session spine.
- `QUALITY_DELTA`: read-only local audit confirms `data/processed/ff_factors.parquet` has only 1,003 rows from 2022-01-03 through 2025-12-31, so it is insufficient and cannot be promoted as the D3 benchmark input.
- `TERMINOLOGY_DELTA`: existing strategy `car` means beta-1 market-adjusted CAR, not regression alpha; raw cumulative return remains separate from CAR/BHAR.
- `OPEN_DECISION`: approve or hold one bounded D3 benchmark artifact implementation round.
- `RECOMMENDED_NEXT_STEP`: implement only the D3 benchmark artifact builder/manifest/tests against this contract; do not interpret CAR/quintiles in that same step.
- `DO_NOT_REDECIDE`: do not use `mktrf` alone as total benchmark return, do not use `^GSPC` as canonical PEAD benchmark, do not fill missing benchmark dates, do not splice source regimes silently, and do not widen into provider authorization claims, strategy code changes, CAR/alpha interpretation, dashboard, ranking, alerts, broker, full build, staging, or commit.
- `PHASE_STATUS`: D3 benchmark-input design gate DONE; PEAD phase-end not claimed.

## Latest Addendum - V2 PEAD D2B Fixed Event-Security Window Data Slice DONE (2026-06-19)

- `RoundID`: `ROUND-20260619-V2-D2B-EVENT-IID-WINDOW`.
- `ScopeID`: `V2_D2B_FIXED_EVENT_SECURITY_PLUS_60_SAMPLE`.
- `SYSTEM_DELTA`: D2B now selects one fixed event security from the prior 20 global sessions using finite mean dollar volume with a 15-observation floor and deterministic score/count/IID/security ordering; it retains exact global `+1..+60` rows without imputation or security switching.
- `PM / Product Delta`: the bounded sample contains 12,582 events, 362 issuers, 754,920 rows, 12,568 selected events, 14 no-security events, 522 short windows, 7,179 missing/non-finite windows, and 4,867 eligible handoffs.
- `QUALITY_DELTA`: 26 focused and 58 combined tests pass; full-sample strategy smoke uses 4,867 events, 881,588 unique canonical return rows, zero duplicate keys, the identical 2,862-session spine, and produces 292,020 complete rows.
- `ARTIFACT_DELTA`: SHA256 `8e2f39c2cb12bd0b50c9a134b280b5ecb8cd438f8a2249c6842c226250228b99`; stable hash-validated input byte snapshots bind validation to reads; publication is immutable Parquet then atomic manifest with pre-commit `BaseException` cleanup.
- `REVIEW_DELTA`: Final Reviewer A/B/C reconciliation PASS (11/11, 10/10, 12/12). The overlap-handoff and input-TOCTOU High findings and all in-scope Medium findings are resolved; no Critical/High finding remains open. Terminal evidence: `docs/saw_reports/saw_v2_d2b_event_iid_window_20260619.md`.
- `OPEN_DECISION`: approve or hold one bounded D3 benchmark-input contract/design gate.
- `RECOMMENDED_NEXT_STEP`: bounded D3 benchmark-input contract/design gate only; no provider fetch or alpha interpretation without separate approval.
- `DO_NOT_REDECIDE`: do not reintroduce `IID01` preference/fallback, post-event security switching, per-security row-offset windows, missing-return compression, imputation/delisting labels, path-based hash-then-reopen reads, duplicate canonical return keys, or a second strategy window algorithm. Do not widen into provider, dashboard, benchmark implementation, CAR/alpha interpretation, ranking, alerts, broker, full build, staging, or commit.
- `PHASE_STATUS`: D2B bounded Data slice DONE; PEAD phase-end not claimed.

## Latest Addendum - V2 PEAD D2A Security-Level Return Repair Complete (2026-06-19)

- `RoundID`: `ROUND-20260618-V2-D2A-SECURITY-RETURN-REPAIR`.
- `ScopeID`: `V2_D2A_SECURITY_LEVEL_TOTAL_RETURN_SAMPLE`.
- `SYSTEM_DELTA`: D2A now preserves `(gvkey, iid)` continuity, uses `TR_level = prccd * trfd / ajexdi`, emits canonical `security_id/date/total_return`, and commits an immutable Parquet through an atomic manifest pointer.
- `PM / Product Delta`: the corrected exactly-500-GVKEY sample has 1,491,022 rows, 795 securities, 117 multi-IID GVKEYs, zero duplicate `(security_id,date)` keys, and SHA256 `f8b988055c99c42e28ebf470acbe9d7b6477a08c2ff2c5c71357b292a0fae957`.
- `QUALITY_DELTA`: source-level TR/price level errors are `0.0`; changed valid TR levels produce nonzero returns at `0.9999991170562655`; 32 focused tests and Reviewer A/B/C final re-review pass.
- `EVIDENCE_DELTA`: the invalid legacy sample is retained only as superseded evidence at SHA256 `0432fc703fab997329801c02352c359984544889da8097abb76e7765758652ab`.
- `OPEN_DECISION`: D2B must define fixed event-level IID selection; no D2A formula decision remains.
- `RECOMMENDED_NEXT_STEP`: start D2B fixed event-level IID selection plus `+60` market-session extraction separately.
- `DO_NOT_REDECIDE`: do not reintroduce issuer-level dedup before returns, call dollar volume ADV, use the legacy formula/sample, run a full build, or widen into benchmark/provider/strategy/UI interpretation.
- `SAW_REPORT`: `docs/saw_reports/saw_v2_d2a_security_return_repair_20260619.md`.

## Latest Addendum - V2 PEAD D1 Parent Closure Evidence Reconciled (2026-06-18)

- `RoundID`: `ROUND-20260618-V2-D1-PARENT-CLOSURE-RECONCILIATION`.
- `ScopeID`: `V2_D1_PARENT_CLOSURE_EVIDENCE_RECONCILIATION`.
- `SYSTEM_DELTA`: D1 implementation remains unchanged from the repaired/rebuilt artifact; this closure-only round reconciles the existing full D1 SAW, verifies the Parquet hash against the manifest, records untracked D1 ownership, and refreshes current truth without duplicating repair or promotion ownership.
- `PM / Product Delta`: D1 is now closure-evidence-published for the repaired Compustat-current SUE artifact with SHA256 `81b2689b48943373f58586ddc382fb609dbce022cde93d4d502333cae5541855`; D2 remains the next implementation stream.
- `QUALITY_DELTA`: Parent closure evidence confirms the manifest row counts and raw extreme-SUE gate, preserves the current-vintage EPS/restatement-hindsight limitation, and does not claim strict filing-vintage PIT EPS.
- `OWNERSHIP_DELTA`: `scripts/pead_d1_sue_builder.py`, `tests/test_pead_d1_sue.py`, `docs/phase_brief/v2-pead-d1-repair-brief.md`, and `docs/saw_reports/saw_v2_d1_repair_20260618.md` remain untracked local D1-owned files in this worktree; closure evidence is present, but clean tracked-repo closure is not claimed.
- `AUTHORITATIVE_D1_SAW`: `docs/saw_reports/saw_v2_d1_repair_20260618.md`.
- `RECONCILIATION_SAW`: `docs/saw_reports/saw_v2_d1_parent_closure_reconciliation_20260618.md`.
- `OPEN_DECISION`: No D1 formula decision remains. D2 identity/return construction remains separate.
- `RECOMMENDED_NEXT_STEP`: start a separate D2 repair beginning with `(gvkey, iid)` return continuity before any daily ADV representative selection.
- `DO_NOT_REDECIDE`: Do not rebuild D1 again, reinterpret D1 as strict PIT EPS evidence, run D2/Ken French/provider/dashboard/strategy work in this closure, or treat D1 closure as alpha/CAR/promotion evidence.

## Latest Addendum - V2 PEAD D1 Repair Complete, D2 Separate (2026-06-18)

- `RoundID`: `ROUND-20260618-V2-D1-REPAIR`.
- `ScopeID`: `V2_D1_SUE_FORMULA_LIQUIDITY_ATOMIC_REPAIR`.
- `SYSTEM_DELTA`: D1 now uses raw numeric `epspxq`, early `(gvkey,rdq)` identity deduplication, exact t-4 continuity, retained raw SUE, RDQ `+/-5 std` clipped SUE, a units-correct flag-only liquidity field, and atomic Parquet/manifest publication.
- `PM / Product Delta`: The repaired artifact has 346,511 rows, 233,586 valid SUE rows, 13,216 GVKEYs, RDQ 2015-01-02 through 2026-06-16, and SHA256 `81b2689b48943373f58586ddc382fb609dbce022cde93d4d502333cae5541855`.
- `QUALITY_DELTA`: Manifest quality metrics record raw `abs(SUE) > 5` at 441 / 233,586 valid rows (0.1888%), below the 0.5% fail-closed threshold; empty processed-output paths preserve the prior bundle; current-vintage EPS/restatement-hindsight limitation is explicit.
- `RECONCILIATION_DELTA`: Early RDQ deduplication removed 1,447 contaminated lag-valid events from the prior 235,033 valid count.
- `SAW_REPORT`: `docs/saw_reports/saw_v2_d1_repair_20260618.md` records PASS after independent Reviewer A/B/C final re-review.
- `OPEN_DECISION`: D1 has no open formula decision. D2 identity/return construction remains separate.
- `RECOMMENDED_NEXT_STEP`: separate D2 repair starting with `gvkey+iid` returns before any daily ADV selection.
- `DO_NOT_REDECIDE`: Do not reintroduce `ajexq` division, move RDQ deduplication after stateful transforms, use liquidity as a row filter, or mix builder/artifact/manifest versions. Do not widen this closure into D2, Ken French, providers, strategy interpretation, UI, alerts, promotion, or broker paths.

## Latest Addendum — V2 PEAD Strategy Contract Handoff-Ready, Data Handoff Blocked (2026-06-18)

- `SYSTEM_DELTA`: Strategy layer now has an in-memory PEAD contract for issuer/security event schema, explicit market-session `+1..+60` windows, raw/CAR/BHAR outcomes, cohort quantiles, HAC spread stats, and bounded summary path.
- `PM / Product Delta`: Strategy contract is now approved as handoff-ready for corrected D1/D2 inputs after Reviewer A/B/C rerun PASS; it is still not real PEAD evidence or an alpha baseline.
- `OPEN_DECISION`: No Strategy decision required. Data stream must repair D1/D2 before any real contract smoke or research interpretation.
- `RECOMMENDED_NEXT_STEP`: wait_for_corrected_D1_D2_data_handoff_then_run_strategy_contract_smoke_without_interpreting_alpha.
- `DO_NOT_REDECIDE`: Do not repair D1/D2 in this stream; do not run full D2 build, provider access, Parquet writes, real CAR/quintile interpretation, candidate ranking/scoring, UI, alerts, broker/order paths, or promotion.
- `SAW_REPORT`: `docs/saw_reports/saw_v2_pead_strategy_contract_rerun_20260618.md` records PASS; `docs/saw_reports/saw_v2_pead_strategy_contract_20260618.md` remains historical BLOCK evidence before reviewer capacity returned.

Status: Current integration bridge
Authority: advisory-only PM/planner bridge. This file does not authorize live trading, broker automation, promotion, provider ingestion, strategy search, candidate ranking, candidate scoring, candidate validation, alerts, dashboard content redesign, macro scoring, factor scoring, or scope widening.
Purpose: connect Quant's technical state back to product/system truth after the Portfolio Optimizer View Test and Performance Hardening round.

## ⚠️ Audit Correction Addendum — V2-D0.4E-AUDIT (2026-06-18)

Read-only schema audit found three P0 gaps in the V2-D0.4E data contract below. This addendum takes precedence over V2-D0.4E claims.

**Gap 1 — PERMNO-GVKEY bridge is BROKEN:**
- `crsp_ccmxpf_linktable.parquet`: all 76,851 rows have `lpermno=NULL` and `lpermco=NULL`.
- The "~90-95% CUSIP match rate" stated below is UNVERIFIED and likely incorrect — the SQL Compustat fallback (local_wrds_pead_v2_fetcher.py line 152) selects `NULL::INTEGER AS lpermno` and `NULL::INTEGER AS lpermco` without emitting CUSIP.
- **Corrected status**: No PERMNO bridge. No CUSIP join surface. `crsp_ccmxpf_linktable` is a GVKEY+IID list only.
- **Downstream impact**: `prices_tri.parquet` (20.55M rows, has total_ret) cannot be joined to comp_fundq via this bridge. PEAD D2+ event returns must use comp_secd/prices_daily path (GVKEY-keyed) only.

**Gap 2 — total_return/trfd coverage is INCOMPLETE:**
- `prices_daily_compustat.parquet` 31.35M rows: 13.22M rows (42%) missing total_return/trfd.
- 2015-2019 `comp_secd_2015_2019`: ~38% trfd missing.
- "2015-2026 full coverage" overstates. Actual: row count confirmed, research-grade total-return layer INCOMPLETE.

**Gap 3 — yfinance ^GSPC is NOT a canonical benchmark:**
- `yfinance ^GSPC` is price-return only (no dividends), not total-return.
- PEAD benchmark must use Ken French Mkt-RF (public) or local SPY TRI (already present).
- Do NOT use yfinance ^GSPC as official benchmark in any PEAD D3-D4 validation.

**What remains valid from V2-D0.4E:**
- `comp_fundq.parquet`: 350,110 rows, gvkey+rdq+epspxq+ajexq+prccq → **PEAD D1 SUE signal can start**
- WRDS entitlement ceiling: settled, do not re-probe
- `comp_secd_2015_2019` + `prices_daily_compustat`: row counts confirmed, usable for GVKEY-keyed price path with trfd caveat

---

## Latest Addendum - V2-D0.4E WRDS Fetch Ceiling Reached + Compustat-Only PEAD Data Layer DONE

- `RoundID`: `ROUND-20260618-V2-D0-4E-WRDS-FETCH-CEILING-COMPUSTAT-ONLY-DONE`
- `ScopeID`: `V2_D0_4E_WRDS_FETCH_CEILING_AND_COMPUSTAT_ONLY_DATA_LAYER`
- `SYSTEM_DELTA`: `WRDS fetch has reached its entitlement ceiling. crsp_a_stock (CRSP) and tr_ibes (IBES) schemas are confirmed inaccessible under current conditional subscription. Compustat-only PEAD data layer is complete. Four artifacts in data/raw/wrds/ are now provenance-stamped with SHA256 manifests.`
- `PM_DELTA`: `Progress moves to 62/100 for data layer. PEAD V2 analysis layer is now unblocked on Compustat-only path. No further WRDS fetch probing is warranted until subscription is upgraded.`
- `FETCH_RESULTS`:
  - `comp_fundq`: `DONE — 350,110 rows, 11 MB, manifest sha256=58bbf125...`
  - `comp_secd_2015_2019`: `DONE — 23,141,359 rows, 329 MB, manifest sha256=5891113c...`
  - `crsp_ccmxpf_linktable`: `DONE — 76,851 rows (CUSIP bridge via comp.security, lpermno=NULL), 0.4 MB`
  - `crsp_dsf`: `FAIL — crsp_a_stock inaccessible (conditional CRSP subscription)`
  - `crsp_stocknames`: `FAIL — crsp_a_stock inaccessible`
  - `ibes_actpsum_epsus / ibes_det_epsus / ibes_statsum_epsus`: `FAIL — tr_ibes inaccessible`
  - `crsp_dsi`: `FAIL — crsp_a_indexes inaccessible`
- `EXISTING_LOCAL_DATA_DEDUP`:
  - `prices_daily_compustat.parquet` (31.3M rows, 2020-2026, comp.secd) — already present, NOT re-fetched
  - `security_master_compustat.parquet` (75,913 rows, ticker/exchg/cusip) — already present, NOT re-fetched
- `PEAD_ANALYSIS_CONTRACT`:
  - `Announcement date`: `comp_fundq.rdq`
  - `EPS surprise (SUE)`: `epspxq_t − epspxq_{t−4}` (random-walk model, standard academic baseline)
  - `Post-announcement returns`: `comp_secd_2015_2019` + `prices_daily_compustat.parquet` (2015-2026 full coverage)
  - `Universe filter`: `security_master_compustat.parquet` (exchg, secstat)
  - `Market benchmark`: `yfinance ^GSPC` (already in tech stack)
  - `PERMNO-GVKEY bridge`: `crsp_ccmxpf_linktable` (CUSIP-based, ~90-95% match rate, lpermno=NULL)
- `ENTITLEMENT_CEILING_SETTLED`: `crsp_a_stock=blocked; tr_ibes=blocked; crsp_a_indexes=blocked. DO NOT re-probe these schemas. Upgrade path: contact institutional WRDS admin for crsp_a_stock and tr_ibes subscription.`
- `OPEN_DECISION`: `Build PEAD V2 analysis layer (SUE computation, event-window return, signal validation) using Compustat-only artifacts.`
- `RECOMMENDED_NEXT_STEP`: `build_pead_v2_sue_signal_and_event_window_return_pipeline_using_compustat_only_data.`
- `DO_NOT_REDECIDE`: `WRDS entitlement ceiling is settled external constraint. Do not re-probe crsp_a_stock, tr_ibes, or crsp_a_indexes. Do not commit raw WRDS parquet to repo. crsp_ccmxpf_linktable lpermno=NULL is known and accepted.`

## Latest Addendum - V2-D0.4D Local Human Probe DONE + PEAD V2 Fetcher Ready

- `RoundID`: `ROUND-20260618-V2-D0-4D-PROBE-DONE-PEAD-FETCHER-READY`
- `ScopeID`: `V2_D0_4D_LOCAL_HUMAN_PROBE_DONE`
- `SYSTEM_DELTA`: `D0.4D local human probe executed 2026-06-18. All five tables confirmed accessible=true. WRDS PEAD V2 data fetcher (local_wrds_pead_v2_fetcher.py) is ready for local human run.`
- `PM_DELTA`: `Progress moves to 95/100. Permission truth probe is closed. Data fetch layer is unblocked. PEAD_V2_001 starter data can now be pulled locally.`
- `CURRENT_STATE`: `crsp.dsf=accessible_true; crsp.stocknames=accessible_true; crsp.ccmxpf_linktable=accessible_true; comp.fundq=accessible_true; ibes.det_epsus=accessible_true. data/raw/wrds/ directory created. Fetcher script ready.`
- `OPEN_DECISION`: `Run local_wrds_pead_v2_fetcher.py with TUN off to fetch PEAD V2 starter data.`
- `RECOMMENDED_NEXT_STEP`: `run_pead_v2_fetcher_locally_then_build_pead_feature_pipeline.`
- `DO_NOT_REDECIDE`: `Permission probe truth is closed. Do not re-run D0.4D probe. Fetcher is local-only; do not commit raw WRDS parquet to repo.`

## Latest Addendum - V2-D0.4C Local Read-Only Permission Probe Approval

- `RoundID`: `ROUND-20260603-V2-D0-4C-LOCAL-READ-ONLY-PERMISSION-PROBE-APPROVAL`
- `ScopeID`: `V2_D0_4C_LOCAL_READ_ONLY_PERMISSION_PROBE_APPROVAL_DOCS_ONLY`
- `SYSTEM_DELTA`: `The future local human permission probe is approved for exactly five hard-coded rows, but D0.4C itself does not execute WRDS or emit output.`
- `PM_DELTA`: `Progress moves to 91/100 after docs-only validation; D0.4D is queued as the first local human execution packet.`
- `CURRENT_STATE`: `all rows probe_approved_not_executed, not_formally_approved, approval_ref=null; permission_truth not_closed.`
- `OPEN_DECISION`: `Prepare D0.4D local human execution packet and run only when the local human executes it.`
- `RECOMMENDED_NEXT_STEP`: `queue_d0_4d_local_human_execution_packet_no_run.`
- `DO_NOT_REDECIDE`: `No credential read, secret.txt read, Codex/subagent login, WRDS execution in D0.4C, discovery helpers, schema discovery, row counts, samples, snapshots, data output, runtime writes, approval_ref changes, formal approval, SafeBoot, or BootReady.`

## Latest Addendum - V2-D0.4B WRDS Local Auth Method Confirmed

- `RoundID`: `ROUND-20260603-V2-D0-4B-WRDS-LOCAL-AUTH-METHOD-CONFIRMED`
- `ScopeID`: `V2_D0_4B_WRDS_LOCAL_AUTH_METHOD_CONFIRMED_NO_EXECUTION`
- `SYSTEM_DELTA`: `WRDS local authentication method is user-attested available through user-owned local credentials, but actual login has not been verified by Codex/subagents, credentials were not read, and formal table-level permission truth is not closed.`
- `PM_DELTA`: `Replace overbroad provider-access-blocked phrasing with local-auth-available-but-unverified-and-not-approved; this is a correction artifact, not execution approval.`
- `CURRENT_STATE`: `local_auth_method=user_attested_local_auth_available; actual_login_verified_by_agent=false; formal_approval_ref=null; permission_truth=not_closed; wrds_execution=governance_blocked_until_probe_approval.`
- `ARTIFACTS`: `docs/authorization/V2_D0_4B_WRDS_LOCAL_AUTH_METHOD_CONFIRMED.md; docs/authorization/V2_D0_4B_WRDS_LOCAL_AUTH_METHOD_CONFIRMED.json.`
- `OPEN_DECISION`: `Approve or decline a separate local read-only permission probe execution window; until then only probe planning is allowed.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_prepare_local_read_only_permission_probe_plan_only_then_seek_separate_probe_execution_approval.`
- `DO_NOT_REDECIDE`: `No secret.txt or credential reading/quoting/testing/use, WRDS login/provider access, SSH, Python WRDS, SAS, SQL, library/table/schema discovery, row counts, sample rows, snapshots, provider output logs, runtime/dashboard/scoring/broker writes, approval_ref fabrication, or row approval.`

## Latest Addendum - V2-D0.2 WRDS Entitlement Evidence Request

- `RoundID`: `ROUND-20260603-V2-D0-2-ENTITLEMENT-EVIDENCE-REQUEST`
- `ScopeID`: `V2_D0_2_WRDS_ENTITLEMENT_EVIDENCE_REQUEST_NO_CREDENTIAL_USE`
- `SYSTEM_DELTA`: `The next PM task is prepared as a non-secret evidence request, not a credential or provider action.`
- `PM_DELTA`: `Product can now send a copyable table-level entitlement request while keeping V2-D0.1 blocked.`
- `CURRENT_STATE`: `All five rows remain evidence_missing/pending with approval_ref=null.`
- `REQUEST_ARTIFACTS`: `docs/authorization/V2_D0_2_WRDS_ENTITLEMENT_EVIDENCE_REQUEST.md; docs/authorization/V2_D0_2_WRDS_ENTITLEMENT_EVIDENCE_REQUEST.json.`
- `OPEN_DECISION`: `Send the request and collect or decline dated attributable non-secret entitlement evidence.`
- `RECOMMENDED_NEXT_STEP`: `send_v2_d0_2_evidence_request_then_collect_or_decline_non_secret_entitlement_evidence_or_hold.`
- `DO_NOT_REDECIDE`: `No row approval, account/password use, WRDS/provider access, login, SSH, Python WRDS, SAS, SQL, schema/table discovery, row counts, snapshots, data output, dashboard/runtime, scoring/ranking, alerts, broker paths, legacy cleanup, secret remediation, SafeBoot, or BootReady is authorized.`

## Latest Addendum - V2-D0.1 Authorization Intent Evidence Missing

- `RoundID`: `ROUND-20260603-V2-D0-1-AUTHORIZATION-INTENT`
- `ScopeID`: `V2_D0_1_WRDS_PERMISSION_TRUTH_AUTHORIZATION_INTENT`
- `SYSTEM_DELTA`: `Authorization intent is now recorded as an intent packet, but no qualifying non-secret entitlement evidence exists for the five V2-D0.1 rows.`
- `PM_DELTA`: `Product has approval intent language to preserve, but cannot treat any row as approved until non-secret entitlement evidence and exact approval_ref text exist.`
- `CURRENT_STATE`: `All five rows remain evidence_missing/pending with approval_ref=null; packet is not final approval.`
- `AUTHORIZATION_ARTIFACTS`: `docs/authorization/V2_D0_1_WRDS_PERMISSION_TRUTH_AUTHORIZATION.md; docs/authorization/V2_D0_1_WRDS_PERMISSION_TRUTH_AUTHORIZATION.json.`
- `SECRET_HANDLING`: `secret.txt is local secret material and is not non-secret entitlement evidence.`
- `OPEN_DECISION`: `Provide or decline non-secret entitlement evidence, then provide exact approval text if evidence exists.`
- `RECOMMENDED_NEXT_STEP`: `collect_or_decline_non_secret_entitlement_evidence_then_record_exact_approval_text_or_hold.`
- `DO_NOT_REDECIDE`: `No row approval, WRDS/provider access, credentials use, probe execution, snapshots, data writes, dashboard/runtime, scoring/ranking, alerts, broker paths, legacy cleanup, secret remediation, SafeBoot, or BootReady is authorized.`

## Latest Addendum - V2-D0.1 TODO-MATRIX-001 Permission Truth Bookkeeping

- `RoundID`: `ROUND-20260602-V2-D0-1-TODO-MATRIX-001-BOOKKEEPING`
- `ScopeID`: `V2_D0_1_PERMISSION_TRUTH_BOOKKEEPING`
- `SYSTEM_DELTA`: `The V2-D0.1 permission-truth bookkeeping artifact now resolves TODO-MATRIX-001 without opening provider/probe/runtime scope.`
- `PM_DELTA`: `Product can now distinguish V2-D0.1 entitlement truth from PEAD_V2_001 starter scope, but still cannot run WRDS/provider access or approve rows without evidence and approval text.`
- `CURRENT_STATE`: `permission_truth.py records exact five V2-D0.1 rows pending by default, approval_ref-required approval, allowed_uses=["provenance_contract"], and ibes.det_epsus pending for V2-D0.1 but not_requested for PEAD starter.`
- `IMPLEMENTATION_ARTIFACTS`: `v2_discovery/data_lab/permission_truth.py`
- `TEST_EVIDENCE`: `.venv\Scripts\python -m pytest tests\test_v2_wrds_permission_truth_scope.py tests\test_v2_wrds_permission_matrix.py tests\test_v2_snapshot_manifest_contract.py tests\test_v2_data_lab_no_v1_writes.py -q -> PASS, 51 passed; .venv\Scripts\python -m compileall v2_discovery\data_lab tests\test_v2_wrds_permission_truth_scope.py -q -> PASS.`
- `OPEN_DECISION`: `Supply or decline non-secret entitlement evidence and explicit approval text for V2-D0.1.`
- `RECOMMENDED_NEXT_STEP`: `collect_or_decline_v2_d0_1_entitlement_evidence_and_approval_text_or_hold.`
- `DO_NOT_REDECIDE`: `No WRDS/provider access, credentials, probe execution, snapshots, data writes, dashboard reader, scoring/ranking, alerts, broker paths, SQLite, SafeBoot, BootReady, legacy cleanup, V2 validity/C3 lock, or public/main closure is authorized.`

## Latest Addendum - V2-D0.1 Scope and Clean-Room Runtime Decision

- `RoundID`: `ROUND-20260602-V2-D0-1-SCOPE-CLEANROOM-RUNTIME`
- `ScopeID`: `V2_D0_1_SCOPE_AND_CLEANROOM_RUNTIME_DECISION`
- `SYSTEM_DELTA`: `PEAD scope conflict is resolved and clean-room runtime schema_registry.py default-exclusion is resolved.`
- `PM_DELTA`: `Product next step is no longer PEAD starter choice; it is entitlement evidence and approval text or hold.`
- `CURRENT_STATE`: `V2-D0.1 requests all five rows; PEAD_V2_001 starter is four-row Compustat PEAD; schema_registry.py is non-credentialed review/source anchor by default.`
- `HANDOVER`: `docs/handover/V2_D0_1_SCOPE_AND_CLEANROOM_RUNTIME_DECISION_20260602.md`
- `OPEN_DECISION`: `Supply or decline V2-D0.1 five-row entitlement evidence and explicit approval text.`
- `RECOMMENDED_NEXT_STEP`: `collect_or_decline_v2_d0_1_five_row_entitlement_evidence_and_explicit_approval_text_or_hold.`
- `DO_NOT_REDECIDE`: `No WRDS/provider access, probe execution, credentials, snapshots, data writes, dashboard reader, scoring/ranking, alerts, broker paths, SQLite, SafeBoot, BootReady, or legacy cleanup action is authorized.`

## Latest Addendum - V2-D0.1 Expert 1-6 Follow-Up Reconciliation

- `RoundID`: `ROUND-20260602-V2-D0-1-EXPERT-1-6-FOLLOWUP`
- `ScopeID`: `V2_D0_1_EXPERT_1_6_FOLLOWUP_RECONCILIATION`
- `SYSTEM_DELTA`: `Expert follow-up guidance is now recorded with agreement/confidence levels, real follow-up questions, and TODO gaps.`
- `PM_DELTA`: `The only product decision that truly needs attention is PEAD starter shape: I/B/E/S analyst-surprise first cell vs four-row Compustat-rdq starter.`
- `CURRENT_STATE`: `V2-D0.1 remains entitlement-only; Backend/Data local validator strictness is PATCH_RESOLVED_LOCAL; clean-room probe and legacy cleanup are future approval-gated work.`
- `HANDOVER`: `docs/handover/V2_D0_1_EXPERT_1_6_FOLLOWUP_RECONCILIATION_20260602.md`
- `OPEN_DECISION`: `Supply or decline V2-D0.1 five-row entitlement evidence and approval text; separately resolve PEAD starter signal conflict if PEAD packet is next.`
- `RECOMMENDED_NEXT_STEP`: `resolve_pead_starter_signal_or_collect_v2_d0_1_five_row_entitlement_evidence_and_approval_text_or_hold.`
- `DO_NOT_REDECIDE`: `No WRDS/provider access, probe execution, credentials, snapshots, data writes, dashboard reader, scoring/ranking, alerts, broker paths, SQLite, SafeBoot, BootReady, or legacy cleanup action is authorized.`

## Latest Addendum - V2-D0.1 Expert 1-6 Agreement and High-Confidence TODO Gates

- `RoundID`: `ROUND-20260602-V2-D0-1-EXPERT-1-6-TODO-GATES`
- `ScopeID`: `V2_D0_1_EXPERT_1_6_AGREEMENT_TODO_GATES`
- `SYSTEM_DELTA`: `Expert 1-6 agreement ratings are recorded as high-confidence TODO gates; numeric values were not supplied and must not be inferred.`
- `PM_DELTA`: `The only product-safe V2-D0.1 action is entitlement evidence and approval text collection, not WRDS probe execution or alpha work.`
- `CURRENT_STATE`: `V2-D0.1 is entitlement-only; Backend/Data row-level validator is PATCH_RESOLVED after focused tests and subagent SAW review; Security approval text and legacy WRDS quarantine risk remain open gates.`
- `SAW_REPORT`: `docs/saw_reports/saw_v2_d0_1_expert_1_6_todo_gates_20260602.md`
- `QUANT_RESEARCH_DELTA`: `PEAD_V2_001_BOUNDARY_PACKET is a conditional next packet only after WRDS/PIT authority is approved.`
- `RESEARCH_VALIDITY_DELTA`: `No V2 alpha is currently research_valid; V2_ALPHA_VALIDITY_PACKET template is required before any V2 validity claim.`
- `OPEN_DECISION`: `Supply or decline non-secret WRDS entitlement evidence plus explicit approval text for V2-D0.1.`
- `RECOMMENDED_NEXT_STEP`: `collect_v2_d0_1_entitlement_evidence_and_approval_text_or_hold.`
- `DO_NOT_REDECIDE`: `No WRDS/provider access, probe execution, snapshots, data writes, dashboard reader, scoring/ranking, alerts, broker paths, SQLite, SafeBoot, or BootReady is authorized.`

## Latest Addendum - V2-D0 Multi-Expert Reconciliation Gate

- `RoundID`: `ROUND-20260602-V2-D0-MULTI-EXPERT-RECONCILIATION`
- `ScopeID`: `MULTI_EXPERT_RECONCILIATION_GATE`
- `SYSTEM_DELTA`: `Expert A/B/C reconciliation completed; Backend PATCH findings were fixed with stricter probe-contract drift rejection and snapshot storage schema parity.`
- `PM_DELTA`: `The packet is accepted as an expert-review deliverable, but the product next step is permission-truth authorization, not a WRDS probe or dashboard/alpha feature work.`
- `CURRENT_STATE`: `V2-D0 remains offline contract substrate; Expert A requires WRDS entitlement evidence before any probe; dashboard reader HOLD; G9 context-only.`
- `OPEN_DECISION`: `Supply or decline non-secret WRDS account/library/table entitlement evidence and approval text for V2-D0.1 permission-truth authorization.`
- `RECOMMENDED_NEXT_STEP`: `collect_non_secret_WRDS_entitlement_evidence_or_hold.`
- `DO_NOT_REDECIDE`: `No WRDS/provider access, snapshot generation, data output, data/processed write, runtime write, dashboard reader, ranking/scoring, recommendations, alerts, broker/order paths, SQLite, SafeBoot, or BootReady is authorized.`

## Latest Addendum - V2-D0 WRDS Permission + Snapshot Provenance Contract

- `RoundID`: `ROUND-20260601-V2-D0-WRDS-PERMISSION-SNAPSHOT`
- `ScopeID`: `V2-D0_WRDS_PERMISSION_AND_SNAPSHOT_PROVENANCE_CONTRACT`
- `SYSTEM_DELTA`: `V2-D0 now has offline WRDS permission, probe, snapshot manifest, and schema-registry contracts with focused no-V1-write guardrails.`
- `PM_DELTA`: `The repo can discuss WRDS-backed V2 Edge Finder substrate in concrete permission/provenance terms without legitimizing provider access or generated data.`
- `CURRENT_STATE`: `G9 FINRA packet is context-only ADVISORY_PASS; dashboard reader is HOLD; V2-D0 contract work is implemented offline. DataReadyStrict, SafeBoot, and BootReady remain blocked by separate governed-data gates.`
- `OPEN_DECISION`: `Approve exact WRDS account/library/table permission truth before any read-only probe; separately approve snapshot generation/storage/rollback before any data output.`
- `RECOMMENDED_NEXT_STEP`: `approve_exact_wrds_permission_truth_before_read_only_probe_or_hold.`
- `DO_NOT_REDECIDE`: `No WRDS/provider access, PIT snapshot generation, committed WRDS output, V1 canonical mutation, dashboard runtime integration, ranking/scoring, recommendations, alerts, broker/order paths, SQLite, boot-status edit, SafeBoot, or BootReady is authorized by V2-D0.`

## Latest Addendum - V2 Alpha Factory Immediate Todo Directive

- `RoundID`: `ROUND-20260601-V2-ALPHA-FACTORY-DIRECTIVE`
- `ScopeID`: `SCOPE-DOCS-ONLY-IMMEDIATE-TODO-FIRSTS`
- `SYSTEM_DELTA`: `A docs-only directive now makes WRDS/PIT/provenance the first TODO before V2 alpha-family work.`
- `PM_DELTA`: `The product direction is WRDS-grounded V2 Alpha Factory: first prove permissions/PIT/provenance, then pursue PEAD variants, corporate-actions variants, meta-labeling survival, and later Orbis/BvD network shock.`
- `CURRENT_STATE`: `Directive recorded only; DataReadyStrict remains BLOCKED_MISSING_GOVERNED_ARTIFACTS, SafeBoot false, and BootReady BLOCKED.`
- `OPEN_DECISION`: `Approve/edit the first bounded WRDS permission/PIT/provenance planning scope, including whether any provider probe or snapshot generation is allowed.`
- `RECOMMENDED_NEXT_STEP`: `plan_wrds_permission_pit_provenance_layer_first_as_docs_or_clean_worktree_research_scope_before_alpha_variant_work.`
- `DO_NOT_REDECIDE`: `No WRDS/provider access, data snapshot generation, SQLite store, candidate ranking/scoring, promotion, live trading, broker/order execution, alerts, autonomous allocation, boot-status edit, or BootReady claim is authorized by this directive.`

## Latest Addendum - Governed Data Source Provenance Intake

- `RoundID`: `ROUND-20260528-GOVERNED-DATA-SOURCE-PROVENANCE-INTAKE`
- `ScopeID`: `SCOPE-APPROVE-RAW-SOURCES-BEFORE-ARTIFACT-GENERATION`
- `SYSTEM_DELTA`: `Source-provenance intake packet exists at docs/architecture/governed_data_source_provenance_intake_20260528.md; it approves raw/source provenance review only and does not authorize generation yet.`
- `PM_DELTA`: `GovernedDataAuthorizationPacket and DataSourceAcquisitionPacket are PASS, but DataReadyStrict remains BLOCKED until source provenance, manifests, hashes, generated artifacts, and validation proof exist.`
- `CURRENT_STATE`: `GovernanceGateV0 PASS; BootStatusPathContract PASS; GovernedDataAuthorizationPacket PASS; DataSourceAcquisitionPacket PASS; DataReadyStrict BLOCKED_MISSING_GOVERNED_ARTIFACTS; SafeBoot false; BootReady BLOCKED.`
- `BLOCKING_REASON`: `Strict data readiness still lacks approved source provenance, manifests, hashes, generated artifacts, and validation proof.`
- `OPEN_DECISION`: `Approve source provenance for prices, ticker/security master, WRDS/R3000 membership, and Rule100 history before any data/processed generation.`
- `RECOMMENDED_NEXT_STEP`: `approve_source_provenance_first_then_bounded_offline_regeneration_then_strict_data_readiness_and_require_github_boot_proof.`
- `DO_NOT_REDECIDE`: `No boot_preflight.py patch; no DataReadyStrict weakening; no data/processed generation from incomplete provenance; no placeholder parquet/CSV; no runtime/boot_status_current.json edit; no ignored/local-governed data commit unless policy changes; no BootReady claim.`

## Latest Addendum - Governed Data Source Acquisition / Bounded Regeneration Planning

- `RoundID`: `ROUND-20260528-GOVERNED-DATA-SOURCE-ACQUISITION`
- `ScopeID`: `SCOPE-SOURCE-INPUTS-AND-GENERATORS-FOR-STRICT-DATA-READINESS`
- `SYSTEM_DELTA`: `Source-acquisition planning packet exists at docs/architecture/governed_data_source_acquisition_20260528.md; it approves planning/source acquisition only, not generation, boot-time generation, or BootReady evidence.`
- `PM_DELTA`: `GovernedDataAuthorizationPacket is PASS, but source acquisition/generation remains BLOCK until trusted sources, approved generators or external bundle, manifests, hashes, and read-only validation are approved.`
- `CURRENT_STATE`: `GovernanceGateV0 PASS; BootStatusPathContract PASS; StrictProof PASS / DEGRADED; DataReadyStrict BLOCKED_MISSING_GOVERNED_ARTIFACTS; SafeBoot false; BootReady BLOCKED; RuntimeBootStatus local / ignored / not commit evidence.`
- `BLOCKING_REASON`: `Required canonical data artifacts are absent/ignored/local-governed and not backed by approved source manifests or generators.`
- `OPEN_DECISION`: `Choose A trusted external governed bundle, B source acquisition + bounded offline regeneration planning, or C quarantine BootReady.`
- `RECOMMENDED_NEXT_STEP`: `approve_source_acquisition_plus_bounded_offline_regeneration_planning_unless_trusted_bundle_exists_otherwise_quarantine_BootReady.`
- `DO_NOT_REDECIDE`: `No boot_preflight.py patch; no DataReadyStrict weakening; no placeholder parquet/CSV; no generation during boot; no runtime/boot_status_current.json edit; no data/processed commit unless policy changes; no BootReady claim.`

## Latest Addendum - Governed Data Artifact Authorization

- `RoundID`: `ROUND-20260528-GOVERNED-DATA-ARTIFACT-AUTHORIZATION`
- `ScopeID`: `SCOPE-APPROVE-INTAKE-OR-REGENERATION-FOR-STRICT-DATA-READINESS`
- `SYSTEM_DELTA`: `Governed data artifact authorization packet exists at docs/architecture/governed_data_artifact_authorization_20260528.md; it is advisory authorization only, not data generation or BootReady evidence.`
- `PM_DELTA`: `GovernanceGateV0 PASS, BootStatusPathContract PASS, and StrictProof PASS/degraded are preserved while DataReadyStrict remains BLOCKED_MISSING_GOVERNED_ARTIFACTS, SafeBoot false, and BootReady BLOCKED.`
- `LOCAL_TRUTH_DELTA`: `Local artifacts and dirty context are not clean GitHub truth and are not BootReady evidence.`
- `OPEN_DECISION`: `Approve bounded offline regeneration authorization or approve a trusted external bundle for data/processed/prices_tri.parquet, data/processed/prices.parquet, data/processed/tickers.parquet, data/processed/universe_r3000_daily.parquet, and data/processed/rule100_softmax_v1_history.csv.`
- `RECOMMENDED_NEXT_STEP`: `approve_bounded_offline_regeneration_authorization_or_approved_external_bundle_otherwise_quarantine_BootReady.`
- `DO_NOT_REDECIDE`: `No boot_preflight.py patch; no DataReadyStrict weakening; no generation during boot; no placeholder parquet/CSV; no data/processed commit unless policy changes; no runtime/boot_status_current.json edit; no BootReady claim.`

## Latest Addendum - Research Validity Runner v0 Commit Anchor

- `SYSTEM_DELTA`: `Research-validity evidence gating now exists in pushed commit 8716c51781d8524de4147cf42f17e52466913de4.`
- `PM_DELTA`: `The project now has a committed boundary before any strategy, signal, candidate, replay, optimizer output, or dashboard surface can claim research-valid status.`
- `GIT_DELTA`: `GitHub is aligned through 8716c51781d8524de4147cf42f17e52466913de4 on origin/codex/optimizer-core-structured-diagnostics.`
- `DIRTY_WORKTREE_DELTA`: `Remaining dirty/untracked files are inherited or later local context and are not part of the research-validity commit.`
- `OPEN_DECISION`: `Handle remaining inherited/local dirty context as separate buckets before claiming safe boot.`
- `RECOMMENDED_NEXT_STEP`: `classify_remaining_dirty_context_then_continue_boot_preflight_staging.`
- `DO_NOT_REDECIDE`: `Do not mix boot-preflight, dashboard, optimizer/lifecycle, packet zips, or unrelated dirty files into the research-validity commit.`

## Latest Addendum - Portfolio Replay Role Contract

- `SYSTEM_DELTA`: `Portfolio replay rows now carry explicit context_role and row_role schema fields, making replay exposure truth mechanically distinct from lifecycle/event audit intent.`
- `PM_DELTA`: `A row can now be read as current holding, historical context, flat replay exposure, cash, or unavailable without relying on ambiguous Weight labels or status-only inference.`
- `ARTIFACT_COMPAT_DELTA`: `Selected-method replay artifacts hydrate missing role columns from backward-compatible defaults while unrelated schema drift still fails closed.`
- `CODE_QUALITY_DELTA`: `Dashboard context normalization delegates to strategies.strategy_replay.normalize_context_frame_for_replay(...) instead of maintaining a private duplicate.`
- `DIAGNOSTIC_DELTA`: `Closed-trade returns, exit reason quality, zero-exposure BUY rows, hold-time, and reason-code concentration are computed from the existing DashboardReplayContext and include replay identity/cache hash.`
- `TEST_DELTA`: `Scoped compile PASS; targeted role/compat/diagnostic regressions PASS; affected replay/dashboard/AppTest suite PASS with 169 tests.`
- `SAW_DELTA`: `Implementer and Reviewer A/B/C all returned PASS; parent reconciliation added Reviewer C hardening regressions for no diagnostic rebuild and strict legacy-only role hydration.`
- `OPEN_DECISION`: `Hold, or separately continue backend dashboard_cache_signature/saved-artifact policy work.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_continue_backend_dashboard_cache_signature_policy.`
- `DO_NOT_REDECIDE`: `No provider ingestion, canonical market-data write, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, strategy promotion, or diagnostic-triggered replay rebuild is authorized.`

## Latest Addendum - Optimizer History Diagnostics Split

- `SYSTEM_DELTA`: `Portfolio Optimizer universe diagnostics now split true missing local price history from stale local price endpoints while preserving the fail-closed insufficient_history gate.`
- `PM_DELTA`: `GOOGL-style rows with thousands of observations but stale local endpoints no longer read like short-history cases in the UI.`
- `UI_DELTA`: `Universe Audit metrics show Missing History and Stale Endpoint separately, and rows include Latest Price Date.`
- `TEST_DELTA`: `Scoped compile PASS; focused optimizer universe/view suite PASS with 62 tests.`
- `OPEN_DECISION`: `Repairing stale local price columns and rebuilding pre-2025 Rule100 evidence artifacts remain separate Data/Backend follow-ups.`
- `RECOMMENDED_NEXT_STEP`: `repair_stale_price_endpoints_or_build_rule100_pre2025_evidence_artifacts_or_hold.`
- `DO_NOT_REDECIDE`: `Do not relax stale endpoint gating, synthesize BUY/SELL history from prices alone, add provider ingestion, canonical writes, broker behavior, alerts, rankings, recommendations, scoring, autonomous allocation, or promotion claims.`

## Latest Addendum - Dashboard Replay Aux Weight Semantics + Stacked Timeline

- `SYSTEM_DELTA`: `Portfolio & Allocation now aligns ENTER/EXIT and Buy/Sell displayed weights to the same daily selected-method replay target_weight used by the timeline and latest snapshot.`
- `PM_DELTA`: `The page is now not only one-bundle by identity; its visible replay weights also use one semantic source, while original lifecycle/event weights remain audit metadata.`
- `UI_DELTA`: `Strategy Replay Timeline now displays portfolio composition as a stacked step-area allocation chart rather than many independent zero-heavy lines.`
- `FAIL_CLOSED_DELTA`: `Partial saved/transitional event or snapshot schemas render empty/unavailable states instead of crashing the Strategy Replay section.`
- `TEST_DELTA`: `Scoped compile PASS; targeted aux/timeline/fail-soft regressions PASS with executable Plotly trace validation; affected backend replay suite PASS with 80 tests; affected frontend replay suite PASS with 134 tests; latest focused dashboard file PASS with 66 tests.`
- `OPEN_DECISION`: `Backend producers still need dashboard_cache_signature policy work for production saved-artifact UI hits; this round does not change that policy.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_continue_backend_dashboard_cache_signature_emission_policy.`
- `DO_NOT_REDECIDE`: `No provider ingestion, canonical market-data write, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, or promotion claims are authorized.`

## Latest Addendum - Dashboard Replay Horizon-Aware Asset Universe Fix

- `SYSTEM_DELTA`: `Portfolio & Allocation now builds replay requests with separate allocation_assets and horizon-aware replay_assets: optimizer/PIT loading uses current signed assets, while the replay bundle can carry zero-weight context-only rows for mapped lifecycle/history tickers inside the selected replay window.`
- `PM_DELTA`: `MU can stay absent from current positive-weight allocation after its SELL while still appearing in the 1Y replay decision history when its BUY/SELL rows are in the horizon.`
- `INTEGRITY_DELTA`: `_normalize_context_frame(...) remains strict; context-only rows are added after backend bundle construction and cache signatures include both replay_assets and allocation_assets, so historical flat tickers are not reused as allocatable holdings.`
- `TEST_DELTA`: `Scoped compile PASS; targeted MU/context/coverage/cache regressions PASS with 4 tests; focused Portfolio/YTD dashboard file PASS with 61 tests; optimizer/replay follow-up PASS with 71 tests.`
- `OPEN_DECISION`: `Saved artifact producers/readers still need separate policy if durable artifacts should serve horizon-aware supersets or subsets beyond exact dashboard_cache_signature matching.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_run_saw_gate_for_horizon_asset_universe_fix.`
- `DO_NOT_REDECIDE`: `No current-allocation universe widening, provider ingestion, canonical market-data write, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, or promotion claims are authorized.`

## Latest Addendum - Replay Selected Price Loading + MU/SNDK Eligibility Trace

- `SYSTEM_DELTA`: `Dashboard selected-method replay now builds full-window r3000_pit membership proof first, then limits price/return loading to signed selected permnos that intersect that PIT window.`
- `PM_DELTA`: `Replay performance is improved without making the replay watchlist-only; MU/SNDK disappearance is explained by a separate strategy/data eligibility trace.`
- `PERFORMANCE_DELTA`: `load_batched_pit_replay_data(..., selected_permnos=...) loaded 2 selected price columns across 89 trading dates while preserving proof of 27 PIT members in the local 2026-01-02..2026-05-11 probe; refreshed local elapsed was 0.5015s.`
- `DIAGNOSTIC_DELTA`: `trace_thesis_ticker_eligibility(("MU","SNDK"), ...) reports pinned universe, ticker-map permno, PIT membership, local price/return rows, Rule100 history, sizing/current-hold state, and latest failed gate.`
- `TRACE_RESULT`: `Through 2026-05-11, MU is pinned/mapped/PIT-present/locally priced and latest fails technical quality; SNDK is pinned/mapped/PIT-present/locally priced, has no Rule100 history rows, and latest fails factor threshold.`
- `TEST_DELTA`: `Focused compile PASS; selected-price loader regression PASS; executable dashboard selected-permno guard PASS; MU/SNDK fixture trace regressions including non-finite return rejection PASS; broader affected suite PASS with 112 tests.`
- `OPEN_DECISION`: `Continue strategy/data diagnosis for MU/SNDK separately from replay performance if product wants deeper Rule100 history/candidate-frame remediation.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_run_separate_strategy_data_eligibility_investigation_for_mu_sndk.`
- `DO_NOT_REDECIDE`: `Do not make dashboard replay watchlist-only; no provider ingestion, canonical market-data write, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, or promotion claims are authorized.`

## Latest Addendum - Dashboard Replay Horizon Superset Cache Fix

- `SYSTEM_DELTA`: `Portfolio & Allocation now reuses a wider ready in-session daily replay for a shorter selected horizon when the cached context is a proven superset, instead of immediately rebuilding the transitional replay source.`
- `PM_DELTA`: `A user switching from Max to 1Y should no longer pay another PIT replay build when the Max daily replay already contains the 1Y dates and identity is unchanged.`
- `PERFORMANCE_DELTA`: `_ensure_daily_portfolio_replay_context(...) checks `_valid_cached_ytd_replay_context(...)` before entering the Building daily portfolio replay source path.`
- `FAIL_CLOSED_DELTA`: `Reuse requires matching method/cap/controls/signed assets/sampling/data signature after excluding replay_dates and actual requested-date rows in replay_df; missing rows clear replay/YTD cache rather than carrying stale evidence.`
- `TEST_DELTA`: `Scoped compile PASS; targeted superset-cache regressions PASS with 3 tests; focused Portfolio/YTD dashboard file PASS with 56 tests; optimizer/replay coverage PASS with 50 tests.`
- `OPEN_DECISION`: `Backend producers should still emit dashboard_cache_signature for production saved-artifact UI hits; accepting durable saved-artifact supersets for shorter windows remains a separate explicit policy.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_coordinate_backend_dashboard_cache_signature_emission_and_saved_artifact_superset_policy.`
- `DO_NOT_REDECIDE`: `No provider ingestion, canonical market-data write, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, or promotion claims are authorized.`

## Latest Addendum - Max Replay Timeline Sampling Fix

- `SYSTEM_DELTA`: `Strategy Replay max-window timeline sampling now normalizes grouped weekly keep-dates through the pandas Series .dt accessor, preventing the Portfolio page AttributeError on long replay windows.`
- `PM_DELTA`: `Selecting Max can render the display-sampled timeline without breaking the single daily replay source used by allocation and Portfolio Performance.`
- `FAIL_CLOSED_DELTA`: `Timeline sampling remains display-only from daily replay rows and cannot become a second replay request or Portfolio Performance source.`
- `TEST_DELTA`: `Scoped compile PASS; targeted max-window sampler regression PASS with 2 tests; focused Portfolio/YTD dashboard file PASS with 53 tests.`
- `OPEN_DECISION`: `Backend artifact producers should still emit dashboard_cache_signature for production saved-artifact UI hits; until then dashboard falls back to labeled transitional build when allowed.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_coordinate_backend_dashboard_cache_signature_emission.`
- `DO_NOT_REDECIDE`: `No provider ingestion, canonical market-data write, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, or promotion claims are authorized.`

## Latest Addendum - Portfolio Replay Selection Identity Hardening

- `SYSTEM_DELTA`: `Portfolio & Allocation now uses explicit signed PortfolioReplaySelection state for replay asset identity instead of hidden optimizer_universe session state; signatures include typed assets and selected price content hash.`
- `PM_DELTA`: `A skipped, failed, or stale optimizer-control render can no longer silently drive a coherent replay for the first 10 price columns or an old universe.`
- `FAIL_CLOSED_DELTA`: `Missing, stale, mismatched, or unavailable selection returns portfolio_replay_selection_unavailable and clears replay/YTD caches.`
- `TEST_DELTA`: `Scoped compile PASS; focused replay-selection/advisory regressions PASS with 6 tests; focused optimizer-selection AppTests PASS with 6 tests.`
- `OPEN_DECISION`: `Transitional dashboard aux event/decision loading remains a backend producer follow-up tied to dashboard_cache_signature emission.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_coordinate_backend_dashboard_cache_signature_emission_for_aux_rows.`
- `DO_NOT_REDECIDE`: `No provider ingestion, canonical market-data write, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, or promotion claims are authorized.`

## Latest Addendum - Portfolio Single-Source Replay Page

- `SYSTEM_DELTA`: `Portfolio & Allocation now coordinates one daily replay context before rendering allocation, performance, timeline, ENTER/EXIT events, latest buys/sells, and decision log surfaces.`
- `PM_DELTA`: `The page no longer presents optimizer fallback allocation/performance as if it belongs to the replay result; visible allocation and performance are both daily replay evidence.`
- `FAIL_CLOSED_DELTA`: `If daily replay is unavailable, Portfolio Performance renders unavailable instead of falling back to optimizer weights/local-live/equal-weight price paths.`
- `UI_DELTA`: `Duplicate Trade Event Log table is removed; ENTER/EXIT Events remains the event visualization, and Latest Buys/Sells is a filtered view of Buy/Sell Decision Log rows.`
- `TEST_DELTA`: `Scoped compile PASS; focused Portfolio/replay/optimizer suite PASS with 178 tests; context build/validation PASS.`
- `OPEN_DECISION`: `SAW reviewer gate remains pending for implementation closure; backend dashboard_cache_signature emission remains a separate coordination follow-up.`
- `RECOMMENDED_NEXT_STEP`: `run_saw_reviewer_gate_or_hold_for_backend_dashboard_cache_signature_emission.`
- `DO_NOT_REDECIDE`: `No provider ingestion, canonical market-data write, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, or promotion claims are authorized.`

## Latest Addendum - Saved Artifact Single-Source Aux Surface Fix

- `SYSTEM_DELTA`: `Saved-artifact replay context construction now preserves artifact event/decision surfaces exactly; valid empty saved artifact aux rows stay empty instead of being filled from separately loaded dashboard frames.`
- `PM_DELTA`: `When Portfolio & Allocation says replay source is saved artifact, replay rows, latest snapshot, ENTER/EXIT annotations, and Buy/Sell Decision Log rows are all from the saved artifact rather than a hidden mixed source.`
- `FAIL_CLOSED_DELTA`: `A saved artifact with daily portfolio rows but no event/decision rows renders empty event/decision surfaces instead of silently borrowing fallback rows.`
- `TEST_DELTA`: `Scoped compile PASS; focused saved-artifact regression PASS; focused frontend suite PASS with 106 tests; SAW Implementer and Reviewer A/B/C PASS.`
- `SAW_DELTA`: `Frontend/UI saved replay source-selector report is now discoverable at docs/saw_reports/saw_frontend_ui_saved_replay_source_selector_20260514.md.`
- `OPEN_DECISION`: `Backend artifact producers should still emit dashboard_cache_signature for production saved-artifact UI hits; until then dashboard falls back to labeled transitional build when allowed.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_coordinate_backend_dashboard_cache_signature_emission.`
- `DO_NOT_REDECIDE`: `No provider ingestion, canonical market-data write, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, or promotion claims are authorized.`

## Latest Addendum - Backend Replay Reader Identity Hardening

- `SYSTEM_DELTA`: `Saved selected-method replay manifests now reject blank top-level run_id, source_id, and method_id before optional expected-ID checks or parquet/manifest equality can validate a bundle.`
- `PM_DELTA`: `A saved replay artifact can no longer be treated as valid just because both manifest and parquet carry the same blank identity while the UI/backend caller omits expected run/source ids.`
- `FAIL_CLOSED_DELTA`: `Blank identity fails closed with manifest_identity_blank:<field> and returns unavailable empty replay output.`
- `TEST_DELTA`: `Scoped compile PASS; targeted blank manifest+parquet identity regression PASS with 3 tests; focused backend replay suite PASS with 79 tests.`
- `SAW_DELTA`: `Backend identity hardening SAW report is published at docs/saw_reports/saw_backend_replay_reader_identity_hardening_20260514.md.`
- `OPEN_DECISION`: `Backend artifact producers should still emit dashboard_cache_signature for production saved-artifact UI hits; until then dashboard falls back to labeled transitional build when allowed.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_coordinate_backend_dashboard_cache_signature_emission.`
- `DO_NOT_REDECIDE`: `No provider ingestion, canonical market-data write, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, or promotion claims are authorized.`

## Latest Addendum - Frontend/UI Saved Replay Source Selector

- `SYSTEM_DELTA`: `Portfolio & Allocation now builds a pure DashboardReplayRequest, prefers a backend-valid saved replay artifact only when the dashboard cache signature also matches, and otherwise uses an explicitly labeled transitional backend build only when fallback is allowed.`
- `PM_DELTA`: `YTD latest weights, latest snapshot, Strategy Replay rows, ENTER/EXIT annotations, and Buy/Sell Decision Log now come from one DashboardReplayContext selected by saved-artifact vs transitional-build source mode.`
- `FAIL_CLOSED_DELTA`: `Unavailable, stale, mismatched, or over-budget saved artifacts clear replay/YTD session state when fallback is disabled and cannot reuse prior latest weights.`
- `TEST_DELTA`: `Scoped compile PASS; requested frontend suite PASS with 105 tests; executable saved-artifact context test PASS.`
- `OPEN_DECISION`: `Backend artifact producers should emit dashboard_cache_signature for production saved-artifact UI hits; until then dashboard falls back to labeled transitional build when allowed.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_coordinate_backend_dashboard_cache_signature_emission.`
- `DO_NOT_REDECIDE`: `No provider ingestion, canonical market-data write, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, or promotion claims are authorized.`

## Latest Addendum - Saved Replay Artifact Reader + Budget

- `SYSTEM_DELTA`: `Backend selected-method replay can now read saved replay-output parquet+manifest bundles only when run/source/method, controls, date window, input signatures, source-file signatures, schema, row/status counts, and timing match the requested context.`
- `PERFORMANCE_DELTA`: `ReplayBudgetPolicy now makes cold-start seconds, rerun/cache seconds, max rows, max dates, and max elapsed ms explicit for saved reads and budget-wrapped builds.`
- `FAIL_CLOSED_DELTA`: `Invalid, stale, mismatched, or over-budget artifact reads/builds return unavailable typed results with empty replay output; prior weights are not stale-carried forward.`
- `INTEGRITY_DELTA`: `DataFrame controls now include content hashes, parquet rows require exact non-null identity fields, and malformed timing fails closed.`
- `TEST_DELTA`: `Scoped compile PASS; focused replay suites PASS with 76 tests and durations under budget.`
- `OPEN_DECISION`: `Frontend/UI can separately choose when to consume the saved reader; this backend slice does not rewire dashboard.py.`
- `RECOMMENDED_NEXT_STEP`: `coordinate_frontend_saved_reader_consumption_or_hold.`
- `DO_NOT_REDECIDE`: `No provider ingestion, canonical market-data write, broker/live trading, alert, ranking, scoring, recommendation, autonomous allocation, or promotion claim is authorized.`

## Latest Addendum - Overlay Overlap Anchor Fix

- `SYSTEM_DELTA`: `Scaled live overlays now require same-ticker overlap; unanchored selected-price or benchmark live rows are unavailable/dropped instead of stitched into current evidence.`
- `PM_DELTA`: `A stale local asset ending in February can no longer be bridged to fresh May live data without a same-ticker anchor date.`
- `TEST_DELTA`: `Scoped compile PASS; affected stale-data suite PASS with 112 tests after SAW rerun reconciliation.`
- `SAW_DELTA`: `Implementer and Reviewer A/B/C all returned PASS; SAW report is PASS.`
- `OPEN_DECISION`: `Hold, or separately approve replay-state hygiene / saved replay artifact-reader performance-budget work.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_separately_approve_replay_state_hygiene_or_saved_replay_artifact_reader_budget.`
- `DO_NOT_REDECIDE`: `No provider ingestion, canonical market-data write, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, or promotion claims are authorized.`

## Latest Addendum - Portfolio Market-Data Freshness Endpoint Cache

- `SYSTEM_DELTA`: `Endpoint freshness now has a reusable PriceEndpointFreshness snapshot computed once per loaded prices_wide signature and reused across Portfolio YTD, optimizer selected-price prep/default ordering, and optimizer universe eligibility.`
- `PERFORMANCE_DELTA`: `Actual local (2857, 2000) matrix: snapshot 0.2966s vs legacy loop 0.9555s, exact endpoint match, and downstream 50 lookup reuse 0.001531s.`
- `RECONCILIATION_DELTA`: `Reviewer High findings were patched: weighted YTD now rejects partial live provider frames missing positive-weight assets, replay-derived YTD weights are signature-bound, and cached full replay/YTD contexts are signature-bound before chart reuse.`
- `PM_DELTA`: `The stale-data fail-closed layer keeps its correctness semantics without paying repeated multi-path full-matrix freshness scans on Streamlit reruns.`
- `TEST_DELTA`: `Focused data-orchestrator/optimizer/universe/dashboard suite PASS, 113 tests; scoped compile PASS.`
- `OPEN_DECISION`: `Complete targeted Reviewer A/B rechecks for this performance slice, then hold or proceed to saved replay artifact-reader/performance-budget work.`
- `RECOMMENDED_NEXT_STEP`: `finish_targeted_rechecks_for_endpoint_cache_then_hold_or_saved_replay_artifact_reader_budget.`
- `DO_NOT_REDECIDE`: `Do not relax fail-closed stale asset behavior, do not reintroduce shared-date proof as per-asset coverage, and do not add provider ingestion, canonical writes, broker/live trading, alerts, rankings, recommendations, scoring, autonomous allocation, or promotion claims.`

## Latest Addendum - Portfolio Market-Data Freshness Fail-Closed Fix

- `SYSTEM_DELTA`: `Portfolio & Allocation now treats freshness per asset endpoint rather than shared matrix date across benchmark YTD, portfolio YTD, optimizer price prep/order, and universe eligibility; scaled live overlays require same-ticker overlap.`
- `CONTRACT_DELTA`: `Endpoint/tolerance semantics are centralized in core.data_orchestrator via price_column_latest_date(...) and price_endpoint_is_fresh(...); portfolio_universe passes OptimizerUniversePolicy.max_endpoint_staleness_days instead of reimplementing helpers.`
- `PM_DELTA`: `Stale partial market data no longer appears as current evidence; stale weighted legs fail closed and stale selected assets are dropped/excluded with diagnostics.`
- `TEST_DELTA`: `Affected stale-data suite PASS with 112 tests after SAW rerun reconciliation; broader affected dashboard/replay suite PASS with 171 tests; scoped compile PASS.`
- `SAW_DELTA`: `Independent SAW rerun completed: Implementer and Reviewer A/B/C all returned PASS with no in-scope Critical/High findings.`
- `OPEN_DECISION`: `Hold, or separately approve replay-state hygiene / saved replay artifact-reader performance-budget work.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_separately_approve_replay_state_hygiene_or_saved_replay_artifact_reader_budget.`
- `DO_NOT_REDECIDE`: `No provider ingestion, canonical market-data write, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, or promotion claims are authorized.`

## Latest Addendum - Dashboard Backend Bundle Integration Verification

- `SYSTEM_DELTA`: `Dashboard selected-method replay now consumes the backend build_selected_method_replay(...) bundle through _build_dashboard_strategy_replay_context(...), with a per-date r3000_pit input_loader instead of a dashboard-local direct build_strategy_replay(...) path.`
- `TEST_DELTA`: `Focused replay/dashboard suite PASS; scoped compile PASS; full pytest PASS; Streamlit readiness smoke PASS on http://127.0.0.1:8520/portfolio-and-allocation with HTTP 200.`
- `PM_DELTA`: `The previously open dashboard backend-bundle consumption risk is closed for the transitional build path; saved artifact-reader consumption and explicit cold-start/rerun performance budget remain future architecture work.`
- `OPEN_DECISION`: `Hold, or separately approve saved artifact-reader consumption plus performance-budget enforcement.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_approve_saved_replay_artifact_reader_and_performance_budget.`
- `DO_NOT_REDECIDE`: `This verification does not authorize provider ingestion, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, or promotion claims.`

## Latest Addendum - Replay Coverage Contract Audit Fix

- `SYSTEM_DELTA`: `The v6 selected-method replay coverage contract audit BLOCK findings are fixed: coverage_segments metadata, specific input_unavailable reasons, uncovered-date batch emission, duplicate-test cleanup, next-return performance alignment, and covered/unavailable perf hardening are implemented.`
- `PERFORMANCE_DELTA`: `Uncovered replay dates now batch cash-closed rows before performance attachment; row-heavy no_priced_members windows use fast explicit-row emission; tiny PIT replay frames use direct return lookup; inverse-volatility skips SLSQP when the closed-form target already satisfies max_weight.`
- `TEST_DELTA`: `Focused replay coverage PASS with 11 tests; durations show row-heavy no_priced_members daily-scale 1.21s under the 10s budget, CASH-only daily-scale 0.30s, and 4-asset 5Y 1.20s under the 5s budget; affected replay/optimizer PASS with 68 tests; context bootstrap/hygiene PASS; full pytest PASS.`
- `BOOTSTRAP_DELTA`: `scripts/build_context_packet.py now discovers current truth surfaces and selects a complete New Context Packet from planner_packet_current.md before older handovers, so docs/context/current_context.* no longer validates while pointing at the Rule100/YTD packet.`
- `SAW_DELTA`: `Formal SAW Implementer and Reviewer A/B/C rechecks completed after resume and all passed; SAW report is PASS.`
- `PM_DELTA`: `The daily-scale replay audit path is now genuinely faster rather than only less tightly tested, and unavailable coverage reasons remain planner-readable.`
- `OPEN_DECISION`: `Dashboard backend-bundle integration/runtime smoke is now verified; hold or approve the saved artifact-reader/performance-budget follow-up.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_approve_saved_replay_artifact_reader_and_performance_budget.`
- `DO_NOT_REDECIDE`: `This audit fix does not authorize provider ingestion, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, or promotion claims.`

## Latest Addendum - Selected-Method Replay Source Evidence Handoff

- `SYSTEM_DELTA`: `Backend build_selected_method_replay(...) and dashboard DashboardReplayContext now provide focused tested selected-method replay evidence for replay rows, latest snapshot, YTD weight preference, ENTER/EXIT annotations, and Buy/Sell audit rows.`
- `PM_DELTA`: `The replay architecture has moved from docs-only invariant to a bounded implemented source path with durable saved replay-output artifact/run id support, and the dashboard transitional build now consumes the backend bundle end to end.`
- `ARTIFACT_DELTA`: `write_selected_method_replay_artifact_atomic(...) writes a display-only replay-output parquet plus manifest with run_id, source_id, method_id, input signatures, date window, row/status counts, and timing under data/runtime_cache/strategy_replay.`
- `ATOMICITY_DELTA`: `The selected-method replay artifact writer stages parquet and manifest first, then promotes with rollback so manifest failure after parquet promotion does not leave orphan saved evidence.`
- `TIMEFRAME_PIT_RULE`: `Portfolio Performance display horizons may be YTD/1Y/3Y/5Y/Max, but replay evidence must load each date as PIT input with end_date=as_of_date and universe_mode=r3000_pit; failed dates must be cash_closed/unavailable, not stale carry-forward.`
- `LATEST_TRADES_UX`: `Buy/Sell Decision Log defaults to latest trades first, renders before heavy replay output, and remains collapsed replay-audit-only context, not live orders or trade signals.`
- `PERFORMANCE_DELTA`: `Replay rows carry asset_return, return_contribution, portfolio_return, and portfolio_equity so YTD/performance can be derived from replay output instead of optimizer session weights.`
- `ROLLBACK_NOTE`: `If the dashboard context regresses, disable the replay-context/YTD preference and return to legacy optimizer weights; do not rewrite canonical market data, lifecycle ledgers, or frozen audit history.`
- `OPEN_DECISION`: `Hold, or separately approve saved artifact-reader consumption plus performance-budget enforcement.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_approve_saved_replay_artifact_reader_and_performance_budget.`
- `DO_NOT_REDECIDE`: `Do not treat focused backend/dashboard tests as strategy promotion, live trading, alerts, rankings, recommendations, or autonomous allocation.`

## Latest Addendum - Frontend/UI Shared Replay Bundle

- `SYSTEM_DELTA`: `Portfolio & Allocation Strategy Replay now has a dashboard-level selected-method replay context feeding replay rows, latest snapshot, ENTER/EXIT annotations, and Buy/Sell audit rows.`
- `UI_DELTA`: `The Strategy Replay surface no longer calls read_lifecycle_log() or reads data/portfolio_lifecycle_buy_sell_log.jsonl directly; both are supplied through DashboardReplayContext.`
- `YTD_DELTA`: `Portfolio Performance primes the latest selected-method replay snapshot before YTD and prefers those weights before legacy optimizer_weights fallback.`
- `BOUNDARY`: `This is a minimal frontend adapter around the current backend replay API; no saved replay-output artifact, provider ingestion, canonical write, alert, broker behavior, ranking, scoring, or recommendation was added.`
- `OPEN_DECISION`: `Backend integration still needs a durable replay-output artifact/run id for the full ultra-modular replay architecture.`
- `RECOMMENDED_NEXT_STEP`: `backend_replay_output_artifact_or_hold.`
- `DO_NOT_REDECIDE`: `Do not treat Buy/Sell audit rows as live orders or trade signals, and do not add broker/live trading, alerts, rankings, recommendations, provider ingestion, or unchecked optimizer behavior.`

## Latest Addendum - Urgent Ultra-Modular Replay Architecture Enforcement

- `SYSTEM_DELTA`: `Docs/Ops has hardened the next milestone contract: for any selected method, one replay run/source must feed YTD, current allocation/latest snapshot, Strategy Replay, ENTER/EXIT annotations, Buy/Sell Decision Log, and saved evidence.`
- `PM_DELTA`: `The product goal is a human-reviewed AI research evidence loop with one replay source of truth, not multiple UI bridges that appear consistent while reading different artifacts.`
- `ARCHITECTURE_GOAL`: `selected-method adapter -> one replay run -> daily portfolio output -> event/annotation output -> YTD/performance -> decision log -> saved evidence artifact.`
- `TRANSITIONAL_BRIDGE_BOUNDARY`: `Temporary bridges may keep visible UI usable during migration, but they must be labeled transitional, bounded to a source, non-canonical, and unable to claim final replay evidence.`
- `GUARDRAILS`: `No future-data leakage, no stale-data carry-forward, no fake improvements, no overfitting, no broker/live trading, no alerts/rankings/recommendations/candidate scoring/autonomous allocation.`
- `DONE_GATE`: `PASS requires shared replay source, selected-method adapters, shared YTD/performance, shared latest allocation snapshot, shared annotation source, shared decision-log source, saved evidence artifact, and explicit performance budget.`
- `OPEN_DECISION`: `Approve the first implementation slice for the single selected-method replay source, or hold.`
- `RECOMMENDED_NEXT_STEP`: `start_urgent_ultra_modular_replay_architecture_slice_with_single_selected_method_replay_source.`
- `DO_NOT_REDECIDE`: `Do not treat current UI/YTD bridges, frozen Rule100 history, compact Buy/Sell tape, or separate overlays as the canonical selected-method replay source.`

## Latest Addendum - Visible Rule100 / QQQ / Buy-Sell Replay Audit

- `SYSTEM_DELTA`: `The focused visible Portfolio & Allocation patch is runtime-audited: default method is Rule of 100, QQQ is visible beside SPY, and the buy/sell decision log is visible before heavy replay output.`
- `UI_DELTA`: `Browser DOM on http://localhost:8509/ shows selected Rule of 100, max_weight=0.35, SPY +11.07%, QQQ +15.50%, and Buy/Sell Decision Log (29 trades, replay audit only) with BUY 16 / SELL 13.`
- `DATA_DELTA`: `QQQ benchmark display is sourced through local+live_overlay and is no longer dropped when SPY has fresher local data.`
- `OPEN_DECISION`: `Start the first urgent ultra-modular replay architecture slice, or hold.`
- `RECOMMENDED_NEXT_STEP`: `start_urgent_ultra_modular_replay_architecture_slice.`
- `DO_NOT_REDECIDE`: `Do not reinterpret the buy/sell replay tape as live orders/trade signals, and do not add broker/live trading, alerts, rankings, recommendations, provider ingestion, or unchecked optimizer behavior.`

## Latest Addendum - Urgent Ultra-Modular Replay Architecture Milestone Note

- `SYSTEM_DELTA`: `A separate urgent ultra-modular replay architecture milestone is now queued after the current visible Portfolio & Allocation QQQ/YTD/default-method patch.`
- `PM_DELTA`: `The next architecture direction is an endless AI auto-research loop that proposes, replays, annotates, compares, and saves evidence for human review; it is not an unchecked optimizer or autonomous trading loop.`
- `SCOPE_SPLIT`: `Current patch = focused UI/YTD visibility fixes. Larger milestone = one replay engine, one strategy plug-in contract, one daily portfolio output format, one event/annotation format, one YTD/performance path, and one saved evidence artifact.`
- `GUARDRAILS`: `No future-data leakage, stale inputs fail closed, overfitting controls require same-window/same-cost/same-engine baseline deltas, fake improvements are rejected without replayable evidence, and no broker/live trading/alerts/rankings/recommendations are authorized.`
- `ACCEPTANCE_TESTS`: `Rule100 visible sizing parity and QQQ/YTD stale-overlay fixes remain acceptance tests before the modular replay milestone starts.`
- `OPEN_DECISION`: `After QQQ/default-method visible fixes are manually audited, approve the first ultra-modular replay architecture slice or hold.`
- `RECOMMENDED_NEXT_STEP`: `manual_audit_qqq_ytd_and_default_method_visible_fixes_then_start_urgent_ultra_modular_replay_architecture.`
- `DO_NOT_REDECIDE`: `Do not widen the current focused UI/YTD patch into code architecture work before visible fixes are verified; do not add broker/live trading, provider ingestion, ranking/scoring, alerts, or autonomous optimizer behavior.`

## Latest Addendum - Rule100 Dynamic UI/Replay Sizing + Benchmark Stale Overlay

- `SYSTEM_DELTA`: `Rule of 100 visible allocation and Strategy Replay now use controls.max_weight as both the per-name budget and single-name cap through rule100_config_from_max_weight(...).`
- `DATA_DELTA`: `Frozen Rule100 audit/history defaults remain unchanged; rule100_softmax_v1_history.csv was not rewritten as a 35% UI-policy artifact.`
- `UI_DELTA`: `Direct Rule of 100 UI allocation now agrees with Strategy Replay; at max_weight=35%, two equal eligible names target 35%/35% with 30% cash.`
- `YTD_DELTA`: `Benchmark YTD fallback is stale-aware per ticker: fresh local SPY can remain local while stale/missing QQQ attempts live overlay and is not forward-filled into a fresh curve if overlay fails.`
- `RUNTIME_DELTA`: `Dashboard YTD live fallback uses a bounded timeout, and AppTest route coverage caps replay dates for deterministic test runtime without changing production replay horizon.`
- `OPEN_DECISION`: `Hold, or separately approve a versioned/labeled Rule100 UI-policy history artifact if historical 35% target traces are required.`
- `RECOMMENDED_NEXT_STEP`: `manual_audit_rule100_visible_weights_and_qqq_ytd_then_hold_or_versioned_history_artifact.`
- `DO_NOT_REDECIDE`: `Do not rewrite frozen Rule100 history/audit artifacts, promote provider data to canonical market data, add ranking/scoring, alerts, broker behavior, live trading, or a new optimizer objective.`

## Latest Addendum - Data/PIT Strategy Replay Hardening + UI Wiring

- `SYSTEM_DELTA`: `Strategy Replay input caching now fails closed on r3000_pit membership and dashboard replay consumes per-date StrategyReplayInputs before generating target weights.`
- `DATA_DELTA`: `Display-only replay artifacts are confined to data/runtime_cache/strategy_replay; custom cache_dir values under data/processed are rejected.`
- `UI_DELTA`: `Portfolio & Allocation Strategy Replay no longer passes a raw prices_wide replay matrix; it loads one PIT input slice per replay date and calls build_strategy_replay(..., prices=replay_inputs).`
- `RECONCILIATION_DELTA`: `SAW Medium findings were reconciled by preserving empty/failed replay dates as explicit cash_closed rows.`
- `OPEN_DECISION`: `Hold, or separately approve a longer replay output artifact/evidence window.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_collect_strategy_replay_multi_date_output_evidence.`
- `DO_NOT_REDECIDE`: `Do not treat replay input artifacts as target-weight output, canonical market data, provider ingestion, ranking/scoring, alerting, broker behavior, live trading, or a new optimizer objective.`

## Latest Addendum - Rule100 Softmax v1.1 Contract Fix

- `SYSTEM_DELTA`: `Rule100 softmax v1.1 research audit now matches its comparison/summary-only artifact contract; stale history is retired instead of treated as current.`
- `DATA_DELTA`: `data/processed/rule100_softmax_v1_1_history.csv is absent; stale bytes were moved to data/processed/rule100_softmax_v1_1_history.retired.csv.`
- `SCORING_DELTA`: `v1.1 factor coverage counts approved factor groups, not raw columns, and missing factor strength shrinks toward neutral 0.50 by coverage.`
- `TEST_DELTA`: `tests/test_policy_target_timeline_apptest.py now uses AppTest.from_file("dashboard.py") and proves TSM 2026-05-11 renders target 0%, event weight 10%, cash 80%.`
- `CLOSURE_DELTA`: `Focused tests, full pytest, context validation, HTTP readiness, and SAW Implementer/Reviewer A/B/C passes completed.`
- `OPEN_DECISION`: `Hold, or separately approve a longer v1.1 promotion evidence window.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_collect_v1_1_multi_date_shadow_evidence.`
- `DO_NOT_REDECIDE`: `Do not promote v1.1 to runtime, recreate v1.1 history, mutate the lifecycle log, or add broker/alert/ranking/scoring behavior.`

## Latest Addendum - Rule of 100 Method Label

- `SYSTEM_DELTA`: `Position Lifecycle Replay history now has an additive Rule100 softmax v1 target-weight overlay instead of showing only stale v0 event weights.`
- `DATA_DELTA`: `data/processed/rule100_softmax_v1_history.csv records event_weight, softmax_v1_target_weight, softmax_v1_cash_residual, eligibility reason, and score by PIT date/ticker.`
- `UI_DELTA`: `Transaction Log labels the immutable ledger weight as Event Weight and the derived v1 sizing as Softmax v1 Target / Softmax v1 Cash.`
- `CURRENT_STATE_DELTA`: `On 2026-05-11, TSM remains event weight 10% but softmax v1 target is 0%, with AMAT 10%, LRCX 10%, and CASH 80%.`
- `OPEN_DECISION`: `Hold, or separately approve richer continuous score inputs if visible >10% single-name sizing is required.`
- `RECOMMENDED_NEXT_STEP`: `manual_audit_lifecycle_history_overlay_then_decide_score_richness.`
- `DO_NOT_REDECIDE`: `Do not overwrite the v0 lifecycle event log or turn Kelly into a second stack.`

## Previous Addendum - Rule of 100 Method Label

- `SYSTEM_DELTA`: `The Portfolio Optimizer method registry now exposes Rule of 100 as a user-facing lifecycle allocation mode.`
- `PM_DELTA`: `Users can choose the concrete Rule100 lifecycle policy from the existing Method dropdown without introducing a generic strategy framework.`
- `UI_DELTA`: `Rule of 100 now renders PIT softmax v1 target weights for eligible lifecycle holds, stores source=rule100_softmax_v1, and still bypasses optimizer execution.`
- `CURRENT_STATE_DELTA`: `Current softmax v1 target is AMAT 10%, LRCX 10%, TSM 0%, CASH 80%; TSM is excluded from sizing because it is tighten_below_hold_threshold.`
- `OPEN_DECISION`: `Hold, or separately approve richer continuous score inputs if visible >10% single-name sizing is required.`
- `RECOMMENDED_NEXT_STEP`: `review_rule100_softmax_v1_live_weights_then_decide_score_richness.`
- `DO_NOT_REDECIDE`: `No new optimizer objective, ranking, scoring, alert, broker behavior, provider ingestion, live trading, or Phase 54 sleeve reopen.`

## Latest Addendum - Rule100 Softmax v1 Audit

- `SYSTEM_DELTA`: `Rule100 now has a dedicated softmax v1 sizing helper module plus a shared replay/audit harness; Kelly is comparator-only.`
- `PM_DELTA`: `The same PIT lifecycle frame can now emit a softmax-first comparison artifact set without multiplying full solution stacks.`
- `DATA_DELTA`: `Artifacts are versioned under data/processed/rule100_softmax_v1* and include summary, comparison, sample, and cash outputs.`
- `UI_DELTA`: `The explicit Rule of 100 UI path now computes softmax v1 targets at render time from the PIT candidate frame instead of replay last_weight.`
- `OPEN_DECISION`: `Hold, or separately approve richer continuous score inputs if v1 should produce more visible concentration than 10%/10% in the current equal-score state.`
- `RECOMMENDED_NEXT_STEP`: `review_rule100_softmax_v1_live_weights_then_decide_score_richness.`
- `DO_NOT_REDECIDE`: `Do not turn Kelly into a second full stack or change lifecycle replay log semantics.`

## Latest Addendum - Rule100 Lifecycle Policy v0

- `SYSTEM_DELTA`: `The concrete PIT lifecycle strategy is now Rule100 Lifecycle Policy v0; no generic replay/audit framework was introduced.`
- `PM_DELTA`: `The replay now distinguishes BUY, HOLD, TRIM, TIGHTEN, EXIT, and NO_ACTION in the audit tape while preserving dashboard-compatible ENTER/EXIT runtime events.`
- `POLICY_DELTA`: `Rule100State wraps proxy demand/supply/pricing/margin with explicit provenance; entry requires 3/4 factors, technical entry zone, and multi-observation confirmation; hold tolerates 2/4; trim/tighten are audit-only; full exit requires >20% hard stop or confirmed trend veto.`
- `DATA_DELTA`: `Promoted runtime lifecycle log now has 29 events vs the 33-event baseline; open holds remain AMAT/LRCX/TSM.`
- `AUDIT_DELTA`: `V0 decision tape has BUY=16, SELL=13, HOLD=739, TRIM=55, TIGHTEN=257, NO_ACTION=4344, no <=5-day round trips, and trade_event_delta=-4 vs baseline.`
- `OPEN_DECISION`: `Audit whether TRIM/TIGHTEN should later change weights, or hold v0 as audit-only.`
- `RECOMMENDED_NEXT_STEP`: `audit_rule100_v0_delta_then_decide_whether_trim_tighten_should_affect_weights.`
- `DO_NOT_REDECIDE`: `No generic strategy contract, provider ingestion, canonical writes, broker orders, alerts, ranking, scoring, dashboard recommendation labels, or Phase 54 Rule-of-100 sleeve reopen.`

## Latest Addendum - Lifecycle Decision Export

- `SYSTEM_DELTA`: `Lifecycle replay now exports a PIT-safe decision tape for audit before further Rule-of-100 lifecycle work.`
- `PM_DELTA`: `The system can inspect why it bought, sold, held, or did nothing on each ticker-date instead of judging only emitted ENTER/EXIT markers.`
- `DATA_DELTA`: `Export artifacts are data/portfolio_lifecycle_decision_log.jsonl, data/portfolio_lifecycle_buy_sell_log.jsonl, and docs/context/e2e_evidence/lifecycle_decision_audit_20260512.json.`
- `AUDIT_DELTA`: `Current export has 5424 decision rows, 18 BUY, 15 SELL, open AMAT/LRCX/TSM, no <=5-day round trips, and audit flags for factor-deterioration holds and suppressed raw exits.`
- `CLOSURE_DELTA`: `Focused export tests and compile pass; independent SAW subagent ownership remains pending unless explicitly authorized.`
- `OPEN_DECISION`: `Audit the decision tape, then approve or revise the true Rule-of-100 lifecycle policy.`
- `RECOMMENDED_NEXT_STEP`: `audit_decision_tape_then_design_true_rule100_lifecycle_policy.`
- `DO_NOT_REDECIDE`: `BUY/SELL fields are replay-analysis labels only; no broker order, alert, ranking, scoring, provider ingestion, canonical write, or dashboard recommendation is authorized.`

## Latest Addendum - Lifecycle Replay Churn + Weight Policy

- `SYSTEM_DELTA`: `Position Lifecycle Replay now uses max-10 10% ENTER weights, 3-day entry confirmation, 3-of-4 PIT lifecycle factor confirmation, 20-day minimum hold, 2-day exit confirmation, 20% hard-exit override, and 10-day post-exit cooldown.`
- `PM_DELTA`: `If replay is not sell-all, Portfolio & Allocation remains invested in current lifecycle holds; the final log is calmer and not 100% cash. Current open holds are AMAT, LRCX, and TSM at 10% each, with residual cash.`
- `DATA_DELTA`: `Pre-fix replay evidence had 103 events and 0.04 ENTER weights; drop-in evidence had 69 events and 0.10 weights; optimal evidence has 33 events, 0.10 weights, and no <=5-day churn round trips.`
- `UI_DELTA`: `Port 8509 smoke shows AMAT/LRCX/TSM/CASH, does not show 100% cash, and restores SPY/QQQ YTD traces through local benchmark fallback when live yfinance is rate-limited.`
- `YTD_FIX_DELTA`: `The visible +7645112.18% portfolio return was caused by swapped prices/returns in core.data_orchestrator. UnifiedDataPackage.prices now holds TRI levels, returns holds daily returns, and Portfolio YTD uses local TRI history first. Port 8509 smoke now shows Portfolio +14.25%.`
- `CLOSURE_DELTA`: `Focused tests, full pytest, context validation, HTTP readiness, and headless browser smoke passed; independent SAW subagent ownership is recorded as pending/BLOCK unless the user explicitly authorizes a subagent rerun.`
- `OPEN_DECISION`: `Hold, or separately approve a broader lifecycle execution-ledger/accounting model.`
- `RECOMMENDED_NEXT_STEP`: `manual_audit_portfolio_allocation_on_8509_then_hold_or_lifecycle_ledger_policy.`
- `DO_NOT_REDECIDE`: `Do not reopen the rejected Phase 54 Rule-of-100 sleeve, add ranking/scoring, provider ingestion, canonical writes, broker calls, alerts, new optimizer objectives, conviction mode, or Black-Litterman.`

## Latest Addendum - Pinned Strategy Universe Hardening

- `SYSTEM_DELTA`: `Thesis tickers are explicitly pinned into feature generation via manifest. Feature store unions pinned permnos after yearly_top_n. PIT replay defaults to scanner ∪ pinned. Shared eligibility gate used by both replay and diagnostics. Loader raises on missing/broken manifest.`
- `PM_DELTA`: `Strategy-universe inclusion is now explicit, auditable, and impossible to silently drop. 103 lifecycle events across 12 tickers. NVDA explicitly FAILED_GATE.`
- `OPEN_DECISION`: `Evaluate NVDA fundamental gate or proceed to Stream 2 strategy review.`
- `RECOMMENDED_NEXT_STEP`: `evaluate_nvda_fundamental_gate_or_stream2_strategy_review_or_hold.`
- `DO_NOT_REDECIDE`: `No provider ingestion, canonical market-data write, strategy search, ranking, scoring, alert, broker call, optimizer objective change, or scanner rule change is authorized.`

## Latest Addendum - Portfolio Lifecycle Current Holds Fix

- `SYSTEM_DELTA`: `Portfolio & Allocation now reconstructs current open holdings from PIT-safe Position Lifecycle Replay state before declaring sell-all cash.`
- `PM_DELTA`: `If replay has open ENTER positions without later EXIT events, the current allocation shows held names plus residual cash rather than 100% cash.`
- `DATA_DELTA`: `Lifecycle JSONL is read locally; future-dated replay rows are ignored; JSON position memory is fallback only when lifecycle evidence is empty.`
- `UI_DELTA`: `Open lifecycle holdings enter the universe as included_current_hold and render as Allocation (Lifecycle Holds) when no fresh PIT ENTER candidate exists.`
- `CLOSURE_DELTA`: `Focused compile, 58-test portfolio/lifecycle suite, full pytest, browser smoke, context validation, SAW report validation, closure packet validation, and SE evidence validation passed; latest local replay check is not sell-all and has open AMAT, AVGO, and TSLA positions.`
- `OPEN_DECISION`: `Hold or separately approve a broader lifecycle transaction model / current-position accounting policy.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_review_lifecycle_position_accounting_policy.`
- `DO_NOT_REDECIDE`: `No provider ingestion, canonical market-data write, broker call, alert, ranking, scoring, new optimizer objective, conviction mode, or Black-Litterman is authorized.`

## Latest Addendum - Dashboard Unified Data Cache Performance Fix

- `SYSTEM_DELTA`: `Dashboard unified parquet data load is now wrapped in st.cache_resource and keyed by processed/static parquet file signatures.`
- `PM_DELTA`: `Normal Streamlit widget reruns should no longer pay the verified ~8s DuckDB/parquet wide-frame load when source data has not changed.`
- `DATA_DELTA`: `Cache invalidation tracks source parquet resolved path, mtime_ns, and size for price, patch, macro/liquidity, ticker, fundamentals, calendar, and sector-map inputs.`
- `CLOSURE_DELTA`: `Focused compile/tests, portfolio regressions, full pytest, Streamlit HTTP smoke, context validation, and independent SAW Implementer/Reviewer A/B/C passes completed.`
- `OPEN_DECISION`: `Hold or separately measure the alpha-engine daily loop and scanner financial-statement cache follow-ups.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_measure_alpha_backtest_runtime_or_scanner_financial_cache.`
- `DO_NOT_REDECIDE`: `No provider ingestion, canonical market-data write, strategy search, ranking, scoring, alert, broker call, optimizer objective change, or scanner rule change is authorized.`

## Latest Addendum - Dashboard Scanner Testability Hardening

- `SYSTEM_DELTA`: `Dashboard scanner deterministic math now lives in strategies/scanner.py with focused boundary-value tests; dashboard.py preserves provider/cache/persistence ownership and delegates enrichment.`
- `PM_DELTA`: `Scanner labels and tactical fields are more regression-resistant without changing product semantics or authorizing new recommendations.`
- `TEST_DELTA`: `Scanner formula tests, strategy/config/ETL coverage, and the process guardrail passed in the focused suite.`
- `CLOSURE_DELTA`: `Focused compile, 49-test affected suite, full pytest, and SAW Reviewer C final recheck passed.`
- `OPEN_DECISION`: `Hold, run longer full regression, or continue the next review section.`
- `RECOMMENDED_NEXT_STEP`: `continue_review_or_hold.`
- `DO_NOT_REDECIDE`: `No provider ingestion, canonical market-data write, scanner semantic change, strategy search, ranking, scoring policy change, alert, broker call, dashboard redesign, or candidate-card dashboard merge is authorized.`

## Latest Addendum - Dashboard Architecture Safety Slice

- `SYSTEM_DELTA`: `PID liveness probing is centralized in utils.process.pid_is_running; dashboard/updater/parameter-sweep/release-controller/phase16 wrappers delegate to it.`
- `PM_DELTA`: `The dashboard and runtime lock paths are safer on Windows without changing product behavior.`
- `UI_DELTA`: `dashboard.py now uses one modular-strategy matrix initializer, delegates portfolio price cleanup to core.data_orchestrator.clean_price_frame, and refuses to spawn a second backtest when a PID file points to a live process.`
- `CLOSURE_DELTA`: `Focused compile/tests and HTTP smoke passed; full pytest was attempted but timed out after 304 seconds, so closure relies on affected-suite evidence plus SAW review.`
- `OPEN_DECISION`: `Hold or continue to Section 2 Code Quality review.`
- `RECOMMENDED_NEXT_STEP`: `continue_code_quality_review_section_or_hold.`
- `DO_NOT_REDECIDE`: `No provider ingestion, canonical market-data write, strategy search, ranking, scoring, alert, broker call, dashboard content redesign, or candidate-card dashboard merge is authorized.`

## Latest Addendum - Portfolio Optimizer View Test and Performance Hardening

- `SYSTEM_DELTA`: `/portfolio-and-allocation` optimizer rendering now has Streamlit AppTest coverage, UI-to-SLSQP bound coverage, display-only Parquet overlay cache, copy-safe overlay scaling cache, and cached optimizer reruns.`
- `PM_DELTA`: `The Portfolio & Allocation surface is more reliable and responsive without changing product semantics or allocation policy.`
- `DATA_DELTA`: `Recent close overlays are cached under data/runtime_cache/optimizer_live_overlay as display-only Parquet files with temp->replace writes; cold misses schedule background refresh and return local TRI prices.`
- `CLOSURE_DELTA`: `Implementation evidence and independent SAW rerun are PASS; Low runtime hygiene follow-ups are carried without blocking closure.`
- `OPEN_DECISION`: `Hold, measure next dashboard runtime bottleneck, or separately approve portfolio thesis-anchor policy planning.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_measure_next_dashboard_runtime_bottleneck_or_approve_portfolio_thesis_anchor_policy_planning.`
- `DO_NOT_REDECIDE`: `No canonical provider ingestion, market-data write, lower-bound allocation policy, new optimizer objective, MU conviction, WATCH investability expansion, Black-Litterman, alert, broker call, ranking, scoring, or candidate-card dashboard merge is authorized.`

## Latest Addendum - Portfolio Data Boundary Refactor

- `SYSTEM_DELTA`: `Portfolio Optimizer selected-stock display freshness and strategy-metrics parsing are now data-orchestrator responsibilities rather than Streamlit view responsibilities.`
- `PM_DELTA`: `The product keeps the same Portfolio & Allocation behavior while reducing UI/provider coupling on the approved DASH-2 freshness path.`
- `DATA_DELTA`: `core/data_orchestrator.py owns close extraction, duplicate-safe local TRI overlay scaling/stitching, stale-while-revalidate display cache behavior, scheduler fail-soft handling, and data/backtest_results.json metrics parsing; views/optimizer_view.py no longer imports yfinance or parses that JSON file.`
- `CLOSURE_DELTA`: `SAW rerun is PASS after reconciling partial live overlay preservation, stale session-state clearing, duplicate anchor dates, stale cache semantics, and scheduler submit failure.`
- `OPEN_DECISION`: `Approve PORTFOLIO_THESIS_ANCHOR_POLICY_PLANNING, request more hygiene, or hold.`
- `RECOMMENDED_NEXT_STEP`: `approve_portfolio_thesis_anchor_policy_planning_or_hold.`
- `DO_NOT_REDECIDE`: `No canonical provider ingestion, market-data write, optimizer objective change, MU conviction, WATCH investability expansion, Black-Litterman, alert, broker call, ranking, scoring, or candidate-card dashboard merge is authorized.`

## Latest Addendum - Optimizer Core Structured Diagnostics Implementation

- `SYSTEM_DELTA`: `Optimizer-core diagnostics are now implemented as a structured reporting layer without changing the approved objective or accepting lower-bound policy.`
- `PM_DELTA`: `The product can now explain infeasible caps, forced equal weight, SLSQP failures, active bounds, and fallback allocations without silently treating fallback as optimized output.`
- `CLOSURE_DELTA`: `SAW PASS after reconciling the data-integrity finding: non-finite diagnostic weights now fail closed as errors and cannot be reported as optimized.`
- `OPEN_DECISION`: `Approve PORTFOLIO_THESIS_ANCHOR_POLICY_PLANNING, request more diagnostics, or hold.`
- `RECOMMENDED_NEXT_STEP`: `approve_portfolio_thesis_anchor_policy_planning_or_hold.`
- `DO_NOT_REDECIDE`: `MU conviction, WATCH investability expansion, Black-Litterman, simple tilt, new optimizer objective, scanner rules, manual override, provider ingestion, broker calls, alerts, and replay behavior remain blocked.`

## Latest Addendum - Optimizer Core Policy Audit

- `SYSTEM_DELTA`: `Optimizer-core lower-bound/SLSQP policy is now separated from the universe-construction closure into its own audit artifacts.`
- `PM_DELTA`: `The quarantined diff is rejected as-is; the product can discuss optimizer constraints without silently accepting model math.`
- `OPEN_DECISION`: `Approve a future optimizer-core implementation round, request revisions, or hold.`
- `RECOMMENDED_NEXT_STEP`: `hold_optimizer_core_implementation_until_policy_approval.`
- `DO_NOT_REDECIDE`: `Universe eligibility, WATCH investability, MU conviction, Black-Litterman, scanner behavior, provider ingestion, broker calls, alerts, and new objectives remain blocked.`

## Latest Addendum - Portfolio Universe Closure Quarantine

- `SYSTEM_DELTA`: `Portfolio Universe Construction Fix is closed as PASS with optimizer-core lower-bound/SLSQP math quarantined out of scope.`
- `PM_DELTA`: `The allocation-universe patch remains mechanical: universe construction, eligibility, diagnostics, labels, tests, audit UI, and contract docs only.`
- `QUARANTINE_DELTA`: `Dirty strategies/optimizer.py lower-bound/SLSQP changes were saved to docs/quarantine/optimizer_core_lower_bounds_slsqp_diff_20260510.patch and reverted from the active closure.`
- `OPEN_DECISION`: `Open OPTIMIZER_CORE_POLICY_AUDIT or hold; do not accept optimizer-core math changes without separate policy, tests, and SAW.`
- `RECOMMENDED_NEXT_STEP`: `open_optimizer_core_policy_audit_or_hold.`
- `DO_NOT_REDECIDE`: `No MU hard floor, conviction mode, WATCH investability, Black-Litterman, manual override, scanner rewrite, provider ingestion, broker call, alert, or new objective is authorized.`
- `PROVENANCE_ANCHOR`: `D-353 / Phase 64 provenance and validation gates remain closed; evidence anchor includes docs/phase_brief/phase64-brief.md and R64.1 dependency hygiene.`

## Latest Addendum - Portfolio Universe Construction Fix

- `PORTFOLIO_DELTA`: `Portfolio Optimizer defaults now come from build_optimizer_universe(...) rather than df_scan display order or selected_tickers[:20].`
- `ELIGIBILITY_DELTA`: `ENTER STRONG BUY and ENTER BUY are eligible; WATCH is research-only; EXIT/KILL/AVOID/IGNORE are excluded by default.`
- `DIAGNOSTIC_DELTA`: `Universe Audit now reports included/excluded rows, missing ticker mappings, local price-history failures, and max-weight feasibility or equal-weight-boundary risk.`
- `NO_CHANGE`: `No MU hard floor, Black-Litterman, conviction mode, thesis anchor sizing, manual override, scanner rewrite, provider ingestion, broker call, alert, or new objective was added.`
- `EVIDENCE`: `.venv\Scripts\python -m pytest tests\test_portfolio_universe.py tests\test_dash_2_portfolio_ytd.py -q` PASS; scoped compile PASS for `strategies/portfolio_universe.py`, `views/optimizer_view.py`, and `dashboard.py`; browser smoke PASS on port `8503`.

## Latest Addendum - DASH-2 Portfolio Allocation Runtime Slice

- `DASHBOARD_DELTA`: `Portfolio & Allocation now keeps Portfolio Optimizer top-level, renders YTD Performance below it, calculates portfolio YTD from current optimizer weights, and shows SPY/QQQ comparison metrics.`
- `DATA_DELTA`: `Selected stock and benchmark prices use an in-memory yfinance adjusted-close freshness overlay for runtime display only; no canonical provider ingestion or file write was added.`
- `NO_CHANGE`: `No broker call, alert, candidate ranking, candidate scoring, factor-scout integration, candidate-card merge, or canonical evidence change was added.`
- `EVIDENCE`: `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py -q` PASS; `.venv\Scripts\python -m pytest tests\test_dash_1_page_registry_shell.py -q` PASS; scoped compile PASS; browser check at `http://127.0.0.1:8502/portfolio-and-allocation` showed optimizer before YTD and prices through `2026-05-08`.

## Header

- `BRIDGE_ID`: `20260510-d383-phase65-g8-2-system-scouted-candidate-card-bridge`
- `DATE_UTC`: `2026-05-10`
- `SCOPE`: `D-353/R64.1/F/G0/G1/G2/G3/G4/G5/G6/G7/G7.1/G7.1A/G7.1B/G7.1C/G7.1D/G7.1E/G7.1F/G7.1G/G7.2/G7.3/G7.4/G8/G8.1/G8.1A/G8.1B-R/DASH-1 complete + G8.2 current`
- `STATUS`: `phase65-g8-2-system-scouted-candidate-card-current`
- `OWNER`: `PM / Architecture Office`

## Live Truth Now

- `SYSTEM_NOW`: `Quant has two candidate-card-only research objects: MU from human nomination and MSFT from the governed LOCAL_FACTOR_SCOUT output.`
- `ACTIVE_SCOPE`: `G8.2 is candidate-card-only Data + Docs/Ops work: one MSFT static card, manifest, policy, handover, focused tests, truth surfaces, and SAW.`
- `BLOCKED_SCOPE`: `New scout outputs, DELL/AMD/LRCX/ALB cards, rankings, scores, thesis validation, buy/sell/hold, buying range, dashboard merge, provider ingestion, alerts, and broker behavior remain blocked.`

## What Changed This Round

- `SYSTEM_DELTA`: `MSFT can now move from governed LOCAL_FACTOR_SCOUT intake to a structured candidate-card-only research object without becoming validated alpha.`
- `PRODUCT_DELTA`: `Terminal Zero now proves both intake-to-card paths: human-nominated MU and pipeline-scouted MSFT.`
- `DATA_DELTA`: `Added one static MSFT candidate card and manifest; no canonical market-data write or provider ingestion occurred.`
- `GOVERNANCE_DELTA`: `Candidate-card validation now rejects factor-score leakage and optional governance flags must remain true when present.`
- `DASHBOARD_DELTA`: `No dashboard runtime change. Existing MSFT dashboard rows are legacy runtime output, not the G8.2 card.`
- `NO_CHANGE`: `No new scout output, no score, no rank, no actionability, no buying range, no alert, no broker call, no provider call, no dashboard merge, and no cards for user-seeded tickers.`

## PM / Product Delta

- `STRONGER_NOW`: `The discovery proof is more complete because a system-scouted intake item can become a governed research object.`
- `WEAKER_NOW`: `Dashboard semantics are still split: legacy runtime rows can show action-shaped labels while candidate cards remain file-backed status objects only.`
- `STILL_UNKNOWN`: `Whether the next move should be G9 market-behavior signal card, G8.3 user-seeded candidate card, a dashboard card reader, or hold.`

## Planner Bridge

- `OPEN_DECISION`: `Approve G9 one market-behavior signal card, approve G8.3 one user-seeded candidate card, approve dashboard card reader/status shell, or hold.`
- `RECOMMENDED_NEXT_STEP`: `approve_g9_one_market_behavior_signal_card_or_g8_3_one_user_seeded_candidate_card_or_dash_card_reader_or_hold.`
- `WHY_THIS_NEXT`: `G8.2 completed the system-scouted intake-to-card proof; the next safe choices either add one evidence signal, test the user-seeded card path, or expose cards as status-only dashboard objects.`
- `NOT_RECOMMENDED_NEXT`: `Do not start ranking, scoring, buying range, provider ingestion, alerts, broker paths, or merge MSFT into legacy dashboard action labels.`

## Locked Boundaries

- `DO_NOT_REDECIDE`:
  - `MSFT is the only G8.2 ticker because it is the sole governed LOCAL_FACTOR_SCOUT output.`
  - `MU and MSFT are the only candidate cards after G8.2.`
  - `Candidate-card-only does not mean validated, actionable, ranked, scored, or recommended.`
  - `The existing dashboard MSFT row at runtime is not the G8.2 candidate card.`
  - `Future dashboard integration must be status-only unless separately approved.`
  - `No live trading, broker automation, alerting, ranking, scoring, recommendation, or provider ingestion is authorized.`

## Evidence Used

- `opportunity_engine/candidate_card_schema.py`
- `data/candidate_cards/MSFT_supercycle_candidate_card_v0.json`
- `data/candidate_cards/MSFT_supercycle_candidate_card_v0.manifest.json`
- `data/discovery/local_factor_scout_output_tiny_v0.json`
- `tests/test_g8_2_system_scouted_candidate_card.py`
- `docs/architecture/g8_2_system_scouted_candidate_card_policy.md`
- `docs/handover/phase65_g82_system_scouted_candidate_card_handover.md`

## Open Risks

- `Inherited dirty dashboard runtime worktree remains visible in git status.`
- `Legacy dashboard rows still use action-shaped labels that are separate from candidate cards.`
- `Factor model validation remains future debt before predictive or ranked use.`
- `GodView provider, options-license, ownership, insider, and market-behavior gaps remain open.`

## Latest Addendum - Portfolio Allocation State Split + Route Smoke

- `SYSTEM_DELTA`: `Portfolio & Allocation now stores explicit allocation state for optimizer output, cash-only fallback, current-hold replay, and Rule of 100 replay instead of inferring state only from legacy session keys.`
- `PM_DELTA`: `The visible Portfolio page stays the default route while the explicit Portfolio & Allocation url path resolves cleanly and replay output is labeled as replay output, not optimizer output.`
- `DATA_DELTA`: `portfolio_allocation_state now carries mode/source/weights/cash_only/latest_price_date, with legacy mirrors retained for compatibility and a separate current-hold replay payload when replay is active.`
- `OPEN_DECISION`: `Hold, or continue the next dashboard-runtime hygiene slice.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_measure_next_dashboard_runtime_bottleneck.`
- `DO_NOT_REDECIDE`: `No new optimizer objective, ranking, scoring, alert, broker behavior, provider ingestion, or live trading is authorized.`
