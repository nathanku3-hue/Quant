# Done Checklist - Current

## Active Addendum — GV-FS0 F1B NO_POSITION Local Done State (2026-07-18)

- [x] F1A banked and independently closed at `e156c66`.
- [x] Separate NO_POSITION fixture/decision; quantity null; zero non-valuation source intents.
- [x] Shared book/reducer/snapshot/verifier/certification/result/adapter path.
- [x] Five flat sessions at shares `0`, cash/NAV `1000`, all contributions `0`.
- [x] Two isolated attempts; all ten certification checks TRUE; deterministic canonical bytes.
- [x] Product 52/52, protocol 137/137, combined 189/189 PASS.
- [x] No F1C/F1D publication/default-route/provider/data/FS1 action.
- [ ] Exact F1B commit banked on named product branch.
- [ ] Distinct Reviewer A/B/C PASS against exact F1B commit.
- [ ] F1C/F1D remain closed.

Next action: bank F1B only and run distinct A/B/C; stop before F1C.

## Prior Active Addendum — GV-FS0 F1A Certified OPEN Terminal Close (2026-07-18)

- [x] F1A implementation banked at `699e664` and review repair banked at `066bdda`.
- [x] Exact OPEN economics: NAV `1000 → 1009 → 1024 → 1034 → 1044`, cash `899 → 904`, receivable `5 → 0`.
- [x] Exactly two isolated verifier attempts and one retained result; all ten checks TRUE; CERTIFIED.
- [x] Frozen decision/certification authority tokens and legacy replay revocation enforced.
- [x] Raw verifier semantics/hash, duplicate rules, and presentation projection/hash fail closed under adversarial tests.
- [x] Product 43/43, protocol 137/137, combined 180/180, generator/freeze/compile PASS.
- [x] Distinct Reviewer A/B/C PASS on exact commit `066bdda`; terminal SAW PASS.
- [ ] F1B NO_POSITION — next and unopened.
- [ ] F1C/F1D, permanent publication, default routing, providers, real data, and FS1 — held.

Next action: open F1B only.

## Active Addendum — GV-FS0 Protocol V1 Terminal Freeze Audit (2026-07-17)

- [x] Immutable candidate `346d362` created and locally audited.
- [x] Hosted-CI portability repairs through `d5d03ec` preserve frozen protocol, manifest, and vector bytes.
- [x] 136 focused GV-FS0 tests pass, including the Windows glob and push-base guard regressions.
- [x] Deterministic generator, independent vectors, and enforced verifier pass against the repaired candidate.
- [x] Non-merged mutation probe branch tip `9954e32` restores cleanly and retains schema, registry, contract, vector, CRLF, and dishonest artifact-plus-manifest rejection pairs.
- [x] Independent Reviewer A/B/C terminal review PASS for exact repaired candidate.
- [x] Hosted Windows/Linux CI passes on run `29567754495`.
- [x] Terminal SAW reconciled from BLOCK to PASS after hosted CI evidence.
- [ ] Reducer authorization predicate acted on; currently false for this round.

Next action: hold until separate owner authorization opens reducer/product work. Economic implementation remains blocked in this round.

## Active Addendum — GV-FS0 Protocol V1 Freeze Candidate (2026-07-17)

- [x] Four approved precision decisions and four execution amendments are explicit in the normative contract.
- [x] Exactly 12 schemas and six other normative V1 artifacts regenerate deterministically.
- [x] Canonical encoder, raw-token parser, independent reference encoder, vectors, registries, tables, and manifest pass.
- [x] Manifest records lowercase SHA-256, declared Git object format, Git blob OIDs, byte lengths, and exactly one terminal LF.
- [x] Bootstrap mode rejects schema, registry, contract, vector, CRLF, and dishonest artifact-plus-manifest mutations.
- [x] 135 focused GV-FS0 tests pass, including isolated reconstruction, local schema-reference resolution, intent cardinality, and publication boundary tests.
- [x] Native Windows and Linux Python parity records are byte-identical locally.
- [x] Windows/Linux CI workflow implements bootstrap/enforced selection and downstream byte comparison.
- [ ] Immutable candidate commit created and locally audited.
- [ ] Enforced mode passes unchanged and rejects all required mutations relative to the committed candidate on a non-merged branch.
- [ ] Hosted Windows/Linux CI passes.
- [ ] Independent Reviewer A/B/C and terminal SAW approve the exact candidate.
- [ ] Reducer authorization predicate satisfied; currently false.

Next action: commit the immutable candidate, execute the enforced mutation probe, and audit that exact commit. Economic implementation remains blocked.

## Prior Program State — PEAD Strict-PIT Formally Closed (2026-07-14)

- **Status**: `TERMINATED_DIAGNOSTIC_ONLY` at merge commit `150d322` (tag `pead-v8-diagnostic-terminal` at `076f26b`).
- **Shipped outcome**: Bounded 2019 long-only future-informed diagnostic (M7F4-v8). NOT strict-PIT, NOT alpha, NOT tradable.
- **Original objective**: 2015–2019 dollar-neutral Q5−Q1 strict-PIT PEAD. **Not achieved.**
- **Research validity**: ~30/100; delivery/closure: 88/100.
- **Prohibited**: Strategy/UI promotion, readiness flag changes, provider access, curve/alpha claims, ranking/scoring, alerts, recommendations, broker/order paths.
- **Reopen condition**: Only for one source-intake slice with genuine effective-dated identifiers + committed data-owner approval; mapping and curves remain closed until ID0 passes.

## Active Addendum — M7F5-ID0 Terminal Provenance Block (2026-07-14)

- [x] Commit A `c5a9ab8` banked the standalone M7F5-ID0 authority gate, focused tests, and active brief.
- [x] Commit B `410d0ca` banked deterministic current-source BLOCK evidence at `docs/context/e2e_evidence/pead_m7f5_id0_dated_identifier_authority_20260714.json`.
- [x] Truth repair `a51f349` records runtime/check-out evidence SHA `4abd0112cd535bb1250952296860d8e3d7c160e4bcd510ec97091427580aa903` and committed Git-blob evidence SHA `f15bac8a6b8702b5c91d915812821605a3b4e33253d11ccee3dfd59ee9816913`.
- [x] Independent Reviewer A/B/C PASS and terminal SAW `398732c` PASS for the bounded provenance BLOCK gate.
- [x] Current result: `BLOCKED_DATED_COMPUSTAT_IDENTIFIER_PROVENANCE_REQUIRED` with reason `committed_git_blob_data_owner_approval_required`; all operational authorities remain false.
- [ ] Effective-dated source acquisition, committed data-owner approval, mapping generation, curve rerun, readiness promotion, Strategy/UI, and provider access — outside this close and blocked/unopened.

Next action: hold promotion; choose exactly one separately authorized owner decision.

## Prior Addendum — M7F4-v8 Terminal Commit C (2026-07-13)

- [x] A2.1 repair banked at `b4d35e1`: verified selection count used by residual evidence; real publication branch regression added.
- [x] Failed-run partial outputs removed before the fresh clean rerun.
- [x] Compile and focused tests 45/45 PASS; clean rerun completed without OOM.
- [x] Commit B `9f37745` contains only evidence JSON and two manifests.
- [x] Selection lock: 2,448 unique events with both required hashes; 2,444 observed + 4 residual.
- [x] Bridge 2/2 PASS; NAV/cost, carried-NAV, no-recapitalization, file-hash, and exact Shapley checks PASS.
- [x] Independent Reviewer A/B/C PASS with distinct identities and exact Commit B pin.
- [x] Decision/formula/lesson records, terminal SAW, active brief, and seven truth surfaces reconciled.
- [x] `strict_curve_status=BLOCKED`; `m6b_data_contract_ready=false`; no alpha/tradable/PIT-as-of claim.
- [ ] Strict primary curve, PIT/as-of link, generalized OOM recovery, and transactional publication — outside this close and blocked/unopened.

Next action: hold promotion; choose exactly one separately authorized next decision.

## Prior Addendum — M7F3-v7 SELF_FINANCING_PORTFOLIO_TRUTH

- Superseded as active implementation by M7F4-v8; retained for audit.

## Active Addendum — M7F3-v7 SELF_FINANCING_PORTFOLIO_TRUTH (2026-07-12)

- [x] Owner GO with deltas recorded (daily sequence, first-bad residual, dead write-down, cash no double-count, Shapley-16, selection hash, v6 path removed, Commit C truth).
- [x] Commit A code/tests/brief + v6 CLI retire: `bae1f65609b723cc6462d9bbd1967340a0cb3310`.
- [x] Focused tests 24/24 PASS.
- [x] Full 2019 rerun DIAGNOSTIC_COMPLETE; selection 2448 hash `caeccc642e5d052b211cc5ecfc335bf4f63d0fd7d63018a6b40c5d6965ad2e6d`.
- [x] first-bad residual sum 0.007208; Shapley 16-state sum-to-gap; legs differ in turnover/cost.
- [x] Commit B evidence only: `b5c66bc740926fc51294107a8951c2993400203a` (no full truth in B).
- [x] Distinct Reviewer A/B/C PASS.
- [x] Commit C SAW + seven-surface reconcile.
- [x] `m6b_data_contract_ready=false`; strict_curve BLOCKED; no CCM.
- [ ] Strict primary curve PASS; readiness/UI/alpha/as-of link — blocked by design.

## Prior Addendum — M7F2-v6-final (superseded as active close)

- Historical v6 diagnostic retained; not valid 70–74 close (audit 61). Executable path retired.


# Done Checklist - Current

## Active Addendum — M7F2-v6-final (2026-07-12)

- [x] Hard-rename/replace v5 runner/tests/brief with m7f2-v6-final (no compatibility path).
- [x] Pre-entry delist exclude before breadth/Q5 + rerank (structural; no event-id policy).
- [x] Bridge blank post-entry one-session gaps with adjacent price + next RET proof only.
- [x] Emit strict BLOCK + neutral_carry_to_cash + write_down_100pct with per-event attribution.
- [x] Map metadata: used_for_selection=true (identity); future_informed_identity_map=true.
- [x] Unit tests PASS (19/19).
- [x] Commit A code/tests/brief: `c7724adcaa855076be079c10224ea5cd2f0e60c0`.
- [x] Full 2019 rerun from Commit A: DIAGNOSTIC_COMPLETE; strict_curve_status=BLOCKED.
- [x] Evidence SHA-256 `58f84cd64e31a41e1307204317d331e54e87a1a23b661cbe9fbb5e4ea105aa8a`.
- [x] All seven truth surfaces refreshed (this Commit B).
- [x] Terminal independent Reviewer A/B/C + validated SAW C.
- [ ] Curve PASS 68-72 primary; not claimed (strict BLOCKED by residual ambiguities).
- Next action: Commit C A/B/C + SAW PASS (diagnostic scope) with strict_curve BLOCKED.


# Done Checklist - Phase 65 G8.2 System-Scouted Candidate Card

## Active Addendum — M7F1-v5.2-final (2026-07-12)

- [x] Four mandatory edits applied: prior-20 roadmap deviation; source-wide spine + pre-2019 load; VOL>0; first/last diagnostic-only; force map rebuild; stale curve invalidate.
- [x] Clean Commit A code/tests/brief only: `138c8b76028b2094793efb2d066c269bf7b805f6`.
- [x] Unit tests 17/17 PASS at Commit A.
- [x] Full 2019 rerun from Commit A with forced map rebuild.
- [x] Evidence bound to Commit A; curve not promoted; residual BLOCK 7/2448 recorded.
- [x] Commit B evidence + truth surfaces: `8740f57763fafc838b07b9bedcf2a593a0787351`.
- [x] Commit C full independent Reviewer A/B/C + SAW pinned to B (ADVISORY_PASS).
- [ ] Residual delisting-data/policy gate authorized/executed.
- [ ] Curve PASS 68–72; not achieved (durable residual BLOCK ~62).
- Next action: owner open bounded delisting-data/policy gate for 7 residual invalids only.

## Prior Addendum — Request Artifact Identity Truth Reconciliation V1 (2026-07-11)

- [x] Original Reviewer A/B/C BLOCK findings accepted: dispatch identity at `e470137` failed because the four current 20260701 request artifacts were absent.
- [x] False dispatch Markdown, JSON, and dependent PASS report quarantined as `INVALID_NOT_DISPATCHED`; no message is proven sent.
- [x] Dispatch Markdown and JSON hashes remain separately labeled: Markdown `ed2db3015413bc71edea919d5c15800514e74b5918253af3d86788614baf872d`; JSON `5975304aee17b6b46a481f690b3be7ac76ee37d5000e9e1e58fcbed1b88b8a30`.
- [x] Commit 1 `a86c3a0fcc34d29e8d76cded5616c6cbe77f500e` / tree `17d7dd85bee600b3658337b129774ffc629bad11` banks the exact four current request artifacts without semantic or byte changes.
- [x] Commit `c642a94944831adbd7ecc06fb16259c87fcdd213` contains the detached identity envelope with four distinct path/hash pairs and lifecycle `PREPARED_NOT_SENT`.
- [x] Three distinct read-only Reviewer A/B/C agents reviewed the fixed commits in separate pinned worktrees and returned PASS.
- [x] Terminal reviewer-independence SAW at commit `e50219051df8bc8fc1f21312325f01cea4a8e18d` is PASS.
- [x] Mandatory current-truth surfaces no longer report the superseded ownership BLOCK.
- [x] Legacy, divergent, reconstructed, redirected, cherry-picked, and otherwise unbound artifacts remain rejected.
- [x] Factual A/B/C/D statuses and `m6b_data_contract_ready=false` remain unchanged.
- [x] No remotes, dispatch, source inspection, provider use, factual validation, readiness promotion, Gate D, publication, or data output.
- [x] Request-artifact identity repair and terminal reviewer independence are closed PASS.
- [x] Context validation PASS; governance preflight PASS with 0 findings; planning boot preflight PASS; fixed-artifact byte checks PASS.
- [x] Thin SAW PASS published for the bounded truth-reconciliation slice.
- [ ] Gate A/B/C dispatch is authorized; a separate explicit owner decision is still absent.
- Next action: hold the unchanged envelope at `PREPARED_NOT_SENT`; do not rerun implementation or reviewers and do not dispatch.

## Prior Addendum — Checkout Hygiene / Governance Recovery (2026-07-11)

- [x] Hard dirty blocker identified as untracked Path A pair only (boot-core dirty remains advisory).
- [x] Path A source/test banked; GOV-002/GOV-008 fixed; evidence LF restored.
- [x] Governance PASS; planning boot preflight PASS; commit `e470137`.
- [x] Hygiene recovery completed, but exact request-artifact identity was not established and dispatch remained invalid.
- [ ] P2 publication / remotes / dispatch / source inspection / readiness promotion; still forbidden without separate authority.
- Next action: see the active request-artifact identity repair checklist.

## Prior Addendum — P0 Trust-Substrate Repair (2026-07-11)

- [x] Every `scripts/boot_preflight.py` Git subprocess sets `GIT_NO_REPLACE_OBJECTS=1`.
- [x] Git identity removes ambient Git redirection/configuration and requires raw HEAD/upstream commits plus a verified HEAD tree; unborn, broken, and tag-shaped identities fail closed.
- [x] Loose and packed `refs/replace/*` are discovered by Git enumeration and hard-fail identity verification before ancestry can be trusted.
- [x] Strict Path A evidence and authorization JSON rejects duplicate keys at any object depth before evaluation or output write; ambiguous legacy JSON is invalid.
- [x] Focused P0 adversarial tests pass for replacement-ref and duplicate-key paths.
- [x] This workspace reports verified Git identity with no replacement refs.
- [x] Planning governance preflight and hard unclassified dirty blockers cleared by hygiene recovery addendum above.
- [x] Fresh independent Reviewer A/B/C review and reconciliation is complete with no in-scope Critical/High findings for P0.
- [ ] P2 publication or Gate A/B/C source-access dispatch is authorized; still a separate decision after hygiene green.
- Next action: see active hygiene recovery checklist.

## Active Addendum - V2 PEAD M6b Slice 0 Contract Correction (2026-07-02)

- [x] Corrected only the active M6b phase brief so first-public/unrestated EPS is the sole strict Gate A pass route.
- [x] Declared `release_date_aligned_but_restated` non-strict; it cannot satisfy strict Gate A, `strict_vintage_pit`, or `m6b_data_contract_ready`.
- [x] Added repository remote/root, commit, tree, artifact path, artifact-hash, and mismatch-denial fields to the canonical Ship-Fast approval/request template.
- [x] Verified locally that the denied R0.1 commit does not resolve in Quant and root `R0.1-preflight-plan.md` is absent; no R0.1 material was introduced.
- [x] Refreshed bridge, impact, planner, multi-stream, post-phase, observability, current-context, notes, decision-log, and lesson current truth.
- [x] Thin SAW verifies active-contract correction, no forbidden Slice 0 action, evidence structure, and a single next action.
- [ ] Gate A/B/C factual evidence or source access is authorized; still absent.
- [ ] Strict M6b readiness is authorized; it remains false.
- Next action: submit only the prepared Gate A and Gate B/C data-owner source-access requests.

## Authoritative Addendum - V2 PEAD Strict M6b Phase 0 Successor Requests (2026-07-01)

- [x] Preserved 20260630 contract, request, and Thin SAW artifacts without mutation; created 20260701 successors with supersedes metadata and recomputed predecessor hashes.
- [x] Bound successor request JSON only to successor Gate A contract SHA-256 `27a065e5a37d44acd5e423e448d0a894274b48215eb0bcfc32968d5ba5931063`.
- [x] Added source-capability attestation-at-approval, conditional timing-artifact, immutable calendar source-of-record, eligible-session, and replayable session-mapping requirements to the successor Gate A contract.
- [x] Preserved Gate B candidate-only, Gate C attribute-scope-blocked, and Gate D integration-gap statuses in successor requests.
- [ ] Data owner has approved Gate A or Gate B/C source access; not supplied.
- [ ] Named local immutable source artifacts and fresh real-artifact reviewer capacity exist; not supplied.
- [ ] Gate A/B/C/D factual verification has occurred; prohibited in this round.
- [ ] Strict M6b readiness is authorized; it remains false.
- Next action: complete request-only Thin SAW closure, then submit the successor Gate A and Gate B/C data-owner requests.
- Status claim: canonical current evidence and strict readiness remain unchanged.

## Authoritative Addendum - V2 PEAD Strict M6b Path A Gate Infrastructure (2026-06-30)

- [x] Evidence-only strict Gate A-D validator writes only atomic JSON; payload content cannot self-authorize.
- [x] Distinct authorization is bound to exact evidence-file bytes and scope/mode/action; current gate PASS requires detached authorization and all four verified local source-byte hashes.
- [x] Focused strict-gate tests pass 68/68; existing M6a tests pass 12/12; compile passes.
- [x] Exact current-evidence CLI and deterministic second replay pass with SHA-256 `0ef4b2504f7f573eab734614054e3c3e9ffa746b02522a6ef00a51453010574a`.
- [x] Missing explicit `--output`, malformed evidence, malformed authorization JSON/schema, current-evidence-plus-authorization, and synthetic-test-plus-authorization exit 2 with no output or temporary file; synthetic canonical-output targeting is rejected before atomic write; payload-only restated approval is `NOT_AUTHORIZED`; well-formed authorization mismatch exits 0 with A-D blocked; source-byte, static/B-import isolation, output-isolation, and atomic temporary-file cleanup checks pass.
- [x] Current artifact records A/B/C/D `BLOCKED`, `strict_vintage_pit=false`, restated-EPS exception `NOT_AUTHORIZED`, and `m6b_data_contract_ready=false`.
- [x] M6a remains sparse engine/framework evidence only; Data Path A is active; UI/frontend and Strategy promotion are held; B remains isolated illustrative-only.
- [x] One post-validation truth refresh and canonical context build/validation record observed results without using synthetic fixtures, validator existence, tests, or review as readiness evidence.
- [ ] Terminal independent Reviewer A/B/C infrastructure review and reconciliation complete.
- [ ] Any strict data gate has authoritative `PASS` evidence; none currently does.
- [ ] Strict M6b readiness is authorized; it remains false.
- [x] Inherited wording that permits a flagged restated-EPS exception is superseded on current truth surfaces; the exception is `NOT_AUTHORIZED` and cannot satisfy strict Gate A.
- Next action: obtain authorized, verifiable evidence for the smallest blocked strict-data gate.

## Authoritative Addendum - V2 PEAD Strict M6b Path A Gates Opened (2026-06-29)

- [x] Refreshed stale cross-stream docs (`multi_stream_contract_current.md`, `post_phase_alignment_current.md`) to the June 25 M6 truth.
- [x] Opened strict M6b Path A data gates in `docs/phase_brief/v2-pead-m6b-strict-data-path-a.md`.
- [x] Defined Gate 1: First-public EPS vintage or explicit flagged exception.
- [x] Defined Gate 2: Delisting-adjusted tradable returns.
- [x] Defined Gate 3: Full as-of liquidity and tradability screen.
- [x] Defined Gate 4: Borrow assumptions and short-cost evidence.
- [x] Maintained fail-closed principle for `m6b_data_contract_ready = false`.
- [ ] Execute strict M6b Path A data prep for Gates 1-4; blocked pending separate data stream implementation and Reviewer C verification.

## Authoritative Addendum - V2 PEAD M6b Option 1 Repair PASS (2026-06-25)

- [x] Full 60-session eligibility is enforced before the B engine run.
- [x] Repaired run evidence reports `selected_events_with_incomplete_60_session_window=0`.
- [x] Direct standalone invocation reaches argparse and direct `--data-gate` passes.
- [x] Direct `--commit-bestavail-run` runs the data gate first and commits B JSON/parquet through a rollback-protected package path.
- [x] Rollback regression covers failure during second output replacement.
- [x] B focused tests pass 5/5.
- [x] M6 sparse-engine tests pass 12/12.
- [x] Standalone script compile passes.
- [x] Repaired B JSON/parquet consistency passes: 975 rows, matching parquet SHA, no duplicate dates, finite gross/net returns.
- [x] Reviewer A/B/C repair reconciliation is recorded in `docs/saw_reports/saw_v2_pead_m6b_bestavail_option1_repair_20260625.md`.
- [ ] B is usable for alpha/tradable claims; explicitly false and blocked.
- [ ] Strict Path A data gates are authorized; deferred and not authorized.


## Authoritative Addendum - V2 PEAD M6b Option 1 Reviewer C BLOCK (2026-06-25)

- [x] Reviewer C terminal rerun executed for M6b Option 1 data integrity and performance path.
- [x] Data-gate replay passes via supported import invocation and preserves stable JSON hash.
- [x] Standalone `--run-bestavail` replay passes via supported import invocation and preserves stable run JSON/daily parquet hashes.
- [x] Gate artifact emits no curve/parquet and keeps strict/alpha usability flags false.
- [x] Run artifact carries all eight claim-ceiling flags and keeps `m6b_strict_readiness=false` and `usable_for_alpha_inference=false`.
- [x] Daily parquet consistency passes: 997 rows, `2016-01-15` to `2019-12-31`, JSON SHA match, no duplicate dates, finite gross/net returns.
- [x] Focused combined pytest passes 14/14.
- [x] Standalone script compile passes.
- [x] Runtime artifact-name isolation scan passes for strict/runtime/UI/data paths outside the standalone script.
- [x] Reviewer C report validates: `docs/saw_reports/saw_v2_pead_m6b_bestavail_option1_reviewer_c_20260625.md`.
- [ ] 60-session terminal-window completeness passes; BLOCKED because 1,796 / 29,737 selected events have `exit_idx` beyond the 2015-2019 return-calendar max.
- [ ] Direct standalone invocation passes; BLOCKED because direct script execution fails with `ModuleNotFoundError: No module named 'scripts'`.
- [ ] Reviewer A/C pass after repair and Reviewer B completes.
- [ ] B is usable for alpha/tradable claims; explicitly false and blocked.


## Authoritative Addendum - V2 PEAD M6b Best-Available Option 1 RUN COMPLETE (2026-06-25)

- [x] Option 1 selected: read-only M6b-DATA-GATE plus standalone flagged diagnostic; reusable best-available M6b input adapter rejected.
- [x] Data-gate policy artifact written at `docs/context/e2e_evidence/pead_m6b_data_gate_bestavail_policy_20260625.json`.
- [x] Gate artifact emits no curve and no daily-return parquet.
- [x] Gate artifact carries all eight claim-ceiling flags: `illustrative_only`, `restated_vintage`, `no_delisting`, `survivorship_biased`, `coverage_2015_2019`, `provider_limited`, `not_alpha`, `not_tradable_claim`.
- [x] Gate artifact explicitly sets `m6b_strict_readiness=false` and `usable_for_alpha_inference=false`.
- [x] Standalone diagnostic script written at `scripts/pead_m6b_bestavail_illustrative_2015_2019.py`.
- [x] Isolation test written at `tests/test_pead_m6b_bestavail_illustrative_2015_2019.py`.
- [x] Data-gate CLI replay passes via import invocation.
- [x] Standalone `--run-bestavail` emits flagged 2015-2019 JSON and daily parquet.
- [x] Focused combined pytest passes 14/14.
- [x] Standalone script compile passes.
- [ ] Independent Reviewer A/B/C or bounded terminal SAW reconciliation passes for this Option 1 B artifact.
- [ ] B is usable for alpha/tradable claims; explicitly false and blocked.


## Authoritative Addendum - V2 PEAD M6a.1 Reviewer C Rerun PASS (2026-06-25)

- [x] Reviewer C terminal rerun executed for M6a.1 data integrity and performance path.
- [x] Focused M6a.1 tests pass 12/12.
- [x] M5a+M6a.1 tests pass 16/16.
- [x] Broader PEAD D1/D2/D2B/D3/event-study/M5a/M6 regression slice passes 109/109.
- [x] M6a.1 compile passes.
- [x] Temporary-output CLI replay verifies `--validate-inputs` exits 0, `--run` exits 2, and no daily-return parquet is emitted.
- [x] Full-universe smoke covers 196,638 selected events x 60 sessions in 4.04s under the 60-second budget and 1024MB cap.
- [x] Reviewer C evidence artifact validates: `docs/saw_reports/saw_v2_pead_m6a_1_reviewer_c_rerun_20260625.md`.
- [ ] Reviewer B/final reconciliation is complete for M6a.1 terminal SAW closure; still pending unless reconciled by separate evidence.
- [ ] Real M6 equity curve/daily return parquet/CAGR is authorized; explicitly blocked until M6b data-prep closes strict input gaps.


## Authoritative Addendum - V2 PEAD M6a.1 Sparse Portfolio Engine Scale Remediation (2026-06-25)

- [x] Event-row iteration, per-security dataframe slicing, dataframe-list accumulation, and dense turnover pivot are removed from `build_daily_portfolio_returns`.
- [x] A projected sorted global trading calendar provides `return_idx:int32`; events use `entry_idx/exit_idx` and active positions satisfy `entry_idx <= return_idx <= exit_idx`.
- [x] Required-column projection encodes event/security identifiers as `int32` and rejects object-dtype DuckDB relations before registration.
- [x] Daily gross/net returns aggregate directly from sparse security weights with single-thread compensated `fsum`; no position matrix or position parquet is materialized.
- [x] Turnover parity explicitly covers entry, exit, overlapping cohorts, and final trade-to-zero liquidation.
- [x] Static source guard rejects `itertuples`, `position_rows`, `pivot_table`, and the retired `ASOF JOIN` start path in the engine.
- [x] Canonical daily SHA-256 output hash is identical across shuffled event/return input order.
- [x] Full-universe synthetic smoke covers 196,638 selected events x 60 sessions under a DuckDB 1024MB cap and 60-second latency budget.
- [x] Current evidence differentiates engine readiness (`m6b_real_run_wiring_allowed=true`) from data readiness (`m6b_data_contract_ready=false`).
- [x] Focused M6 tests 12/12, M5a+M6 tests 16/16, broader PEAD slice 109/109, compile, and fail-closed CLI checks pass.
- [x] Independent Reviewer A terminal SAW rerun for strategy correctness and regression risk; published at `docs/saw_reports/saw_v2_pead_m6a_reviewer_a_rerun_20260625.md`.
- [x] Independent Reviewer B terminal SAW rerun for runtime and operational resilience, published at `docs/saw_reports/saw_v2_pead_m6a_reviewer_b_rerun_20260625.md`.
- [ ] Fresh independent Reviewer C terminal SAW rerun for the current sparse core; the available C artifact predates this remediation.
- [ ] Real M6 equity curve/daily return parquet/CAGR remains explicitly blocked until M6b data-prep closes strict input gaps.


## Authoritative Addendum - V2 PEAD M6a PIT Walk-Forward Equity Framework FAIL-CLOSED (2026-06-24)

- [x] M6 plan split into M6a framework/input-contract evidence and M6b data-prep/real-run.
- [x] `scripts/pead_m6_pit_walk_forward_equity_curve.py` implemented with `--validate-inputs` and fail-closed `--run` behavior.
- [x] PIT contract distinguishes timing-PIT from EPS vintage/unrestated PIT.
- [x] Current EPS label is `release_date_aligned_but_restated`; strict EPS vintage remains false.
- [x] Current real-run gate fails closed on `pit_vintage_blocked`, `delisting_missing`, `tradable_return_missing`, and `tradability_liquidity_screen_missing`.
- [x] Explicit nonzero cost model is required before net return/equity metrics can be computed.
- [x] Synthetic strict-input tests cover walk-forward folds, portfolio gross/net returns, equity/CAGR/drawdown/Sharpe/turnover metrics, and fold results.
- [x] Evidence JSON written at `docs/context/e2e_evidence/pead_m6_pit_walk_forward_equity_curve.json`.
- [x] M6 focused tests pass 7/7; M5a+M6 focused tests pass 11/11; broader PEAD regression slice passes 104/104.
- [x] No locked D3/D2B mutation, UI, alpha label, ranking/scoring, recommendation, alert, broker/order path, provider access, or M6 daily-return parquet publication occurred.
- [ ] Real M6 equity curve/daily return parquet/CAGR is authorized; explicitly blocked until M6b data-prep closes strict input gaps.
- [ ] Earlier 28-commit/main PR is opened or reconciled; not done in this round.

## Authoritative Addendum - V2 PEAD Alpha Interpretation Gate OPEN (2026-06-24)

- [x] Alpha Interpretation Gate brief opened at `docs/phase_brief/v2-pead-alpha-interpretation-gate.md`.
- [x] Full-universe M1B evidence policy and limitations are named as the active claim boundary.
- [x] Maximum honest current claim is limited to descriptive methodology evidence, not alpha.
- [x] Dashboard-first route is replaced by Path A descriptive evidence panel or Path B M5 PIT/data/method upgrade.
- [x] No code, data, provider, evidence mutation, dashboard runtime, ranking/scoring, alert, recommendation, order, staging, or commit scope is authorized in this docs-only round.
- [ ] Owner approves or holds the Alpha Interpretation Gate.
- [ ] Alpha-named dashboard/code is authorized; explicitly blocked pending gate approval and 28-commit/main reconciliation.

## Prior Addendum - V2 PEAD M4B.1 Evidence Contract Repair PASS (2026-06-23)

- [x] verify_evidence_pair, EvidenceProfile, parent_sha256, and publishable contract implementation verified.
- [x] CLI publish guard verified fail-closed on contract violation ("write failure does not persist").
- [x] Full repository test suite passes cleanly (exit 0).
- [x] SAW Report and SE Execution Report generated and validated.
- [x] M4B.1 evidence-contract closure PASS.
- [ ] M4C/dashboard authorized; BLOCKED pending separate review.

## Latest Addendum - V2 PEAD M4B Full-Universe Validation and Inference PASS (2026-06-22)

- [x] Rebuilt and published the D3 daily benchmark against the full D2B manifest to `data/processed/pead_d3_ken_french_daily_benchmark.parquet`.
- [x] Optimized memory footprint in `scripts/pead_real_data_validation.py` to allow full-universe execution without memory allocation failures.
- [x] Generated full-universe real-data validation evidence JSON at `docs/context/e2e_evidence/pead_real_data_validation_full_universe.json`.
- [x] Generated full-universe calendar-time inference evidence JSON at `docs/context/e2e_evidence/pead_calendar_time_inference_m1b_full_universe.json`.
- [x] Legacy validation and calendar-time sample files remain completely untouched and protected under their locked SHA256 hashes.
- [x] All unit tests pass successfully (`pytest -q` returns clean exit 0).

## Latest Addendum - V2 PEAD M4A Memory-Bounded Full-Universe Expansion (2026-06-22)

- [x] D2A full build has a bounded-memory local execution path.
- [x] D2A formulas and (gvkey, iid) lag semantics remain unchanged.
- [x] D2A full-build atomic manifest publication and cleanup are covered by focused tests.
- [x] D2B full build has a bounded-memory local execution path.
- [x] D2B fixed-security selection and +1..+60 session semantics remain unchanged.
- [x] D2B full-build invalid-input and manifest-interruption fail-closed behavior are covered by focused tests.
- [x] Focused M4A tests pass 55/55.
- [x] Broader PEAD D2/D3/event-study tests pass 79/79.
- [x] Full repository pytest returns a clean exit code after stale pytest/Streamlit smoke processes are stopped.
- [x] Targeted execution_microstructure/status rerun passes after teardown/process-liveness cleanup.
- [ ] Terminal independent Reviewer A/B/C SAW passes; currently blocked by subagent usage limit and required only if strict governance closure is demanded before M4B.
- [ ] Provider access, PIT/full-universe alpha claims, estimator/UI changes, ranking/scoring, alerts, recommendations, broker/order actions, or new data artifact publication are authorized; explicitly blocked.

## Latest Addendum - V2 PEAD M2 Read-Only Status DONE (2026-06-21)

- [x] Frontend-only M2 scope is limited to PEAD status rendering and Strategy tab routing.
- [x] `views/pead_validation_evidence.py` verifies both the locked validation JSON and the locked M1B JSON before rendering status.
- [x] Visible UI shows validation evidence locked, M1B evidence locked, alpha verdict blocked, and strategy promotion blocked.
- [x] Visible UI avoids SHA hashes, manifest paths, JSON paths, and Parquet plumbing on the successful status surface.
- [x] `views/strategy_view.py` exposes the PEAD status tab without breaking Strategy Matrix or Backtest Lab routes.
- [x] `tests/test_pead_validation_evidence.py` covers dual-artifact verification, M1B policy fail-closed behavior, sanitized fail-closed UI, no visible audit plumbing, AppTest rendering, legacy routes, and no provider/Parquet/recompute path.
- [x] Final focused validation, context validation, and terminal Implementer/Reviewer A/B/C SAW publication pass for this M2 round.
- [ ] Alpha verdict, promotion, ranking/scoring, alert, recommendation, or broker/order action is authorized; explicitly blocked pending separate approval.

## Latest Addendum - V2 PEAD M1B Dashboard Marker Closure PASS (2026-06-21)

- [x] Bounded Frontend/UI repair approved and kept to the dashboard event-ledger trace labels.
- [x] `dashboard.py` trace names restored to `ENTER` and `EXIT`.
- [x] Newer lifecycle hover wording preserved.
- [x] Focused lifecycle regression passes.
- [x] `dashboard.py` compile passes.
- [x] Full repository `pytest -q` passes.
- [x] M1B and protected validation JSON hashes verified unchanged.
- [x] Reviewer A/B/C closure reviews pass.
- [x] Terminal M1B SAW report updated to PASS.
- [ ] Alpha verdict, promotion, ranking/scoring, alert, recommendation, or broker/order action is authorized; explicitly blocked pending separate approval.

## Latest Addendum - V2 PEAD Calendar-Time Inference M1B (2026-06-21)

- [x] Independent Reviewer C terminal recheck after the M1A count correction passed.
- [x] Four-file M1B implementation completed in the allowlisted runtime/test files only.
- [x] M1B strict JSON evidence artifact published at `docs/context/e2e_evidence/pead_calendar_time_inference_m1b.json`.
- [x] Artifact SHA256 recorded as `c80bb7ed583a933dae664251ffe1fc56a0bcaf5f9a086b1e42740047a5018b76`.
- [x] Protected 20260620 validation JSON hash verified unchanged at `96cdc975d0b4798c6775b12e7bc9dc6af4fb7e9178a4d0ad54feeab8100e980e`.
- [x] Corrected counts are locked in the artifact: 19,812 null-date rows excluded, 226,772 expected rows, 1,519 missing rows, 2,539 retained sessions, zero internal gaps.
- [x] M1B focused tests pass 50/50 after Reviewer B/C hardening.
- [x] M1B CLI and schema validation pass.
- [ ] Full repository pytest passes. One inherited dashboard ENTER/EXIT marker assertion fails outside M1B ownership.
- [ ] M1B SAW Reviewer A/B/C closure. Reviewer C technical PASS; hierarchy-only terminal confirmation unavailable due usage limit.
- [ ] Any alpha verdict, promotion, ranking/scoring, alert, recommendation, or broker/order action is authorized; explicitly blocked.

## Latest Addendum - V2 PEAD M1A Inference Methodology Gate (2026-06-21)

- [x] Exactly one primary estimator is selected: calendar-time daily Q5-minus-Q1 regression.
- [x] Signal formation, active sessions, overlap handling, missingness, weighting, minimum leg count, model formula, HAC bandwidth, and robustness method are explicit.
- [x] Quarterly remains `ex_post_descriptive_only=true`; existing daily gap HAC is not altered.
- [x] Claim boundaries preserve the 500-GVKEY, current-vintage EPS, Compustat-return, and no-delisting limitations.
- [x] Product/spec, formula notes, decision log, research index, lesson, and current truth surfaces are updated.
- [x] Focused existing PEAD regression passes 37/37 and documentation diff checks pass.
- [x] Relevant primary literature/PDF evidence is verified against Fama (1998), journal page 295 / PDF page 13; research claim validation passes 2/2.
- [x] Parent-side corrected count check records 19,812 null-`return_date` rows excluded, 226,772 extreme expected rows, 1,519 missing asset rows, and a 2,539-session count-qualified interval.
- [ ] Terminal independent Reviewer C recheck after the count correction. BLOCKED by subagent usage limit.
- [ ] M1B estimator code/tests and a new deterministic evidence artifact are implemented; explicitly not part of M1A.
- [ ] Any alpha verdict, promotion, ranking/scoring, alert, recommendation, or broker/order action is authorized; explicitly blocked.

## Latest Addendum - V2 PEAD Read-Only Evidence Dashboard DONE (2026-06-20)

- [x] `views/pead_validation_evidence.py` reads only the locked JSON byte snapshot and verifies the expected SHA256 before parsing/rendering.
- [x] Missing file, hash mismatch, invalid/non-object JSON, required-schema drift, and limitation drift fail closed before metrics/lineage render.
- [x] Exact review-only title and warning render.
- [x] Artifact/hash state, D1/D2B/D3 lineage, 754,920 rows, 12,582 events, 362 issuers, 11,450 eligible, and 1,132 ineligible render.
- [x] Daily 2,777 HAC-gap/null-stat warning and quarterly descriptive-only warning render.
- [x] The four locked limitations render.
- [x] Promotional/action language is absent in positive form; the required negative disclaimer remains.
- [x] Strategy Matrix, Backtest Lab, and Read-Only Evidence routes have focused routing coverage.
- [x] Focused dashboard tests pass 14/14; dashboard plus locked validation tests pass 24/24; broader PEAD matrix passes 121/121.
- [x] Independent Reviewer A/B/C PASS with no remaining findings.
- [ ] Alpha interpretation/promotion, ranking/scoring, alerts, recommendations, broker/order paths, provider access, Parquet reads, and artifact mutation. NOT AUTHORIZED.

## Latest Addendum - V2 PEAD Real-Data Validation DONE (2026-06-20)

- [x] Existing PEAD real-data validation JSON inspected read-only at `docs/context/e2e_evidence/pead_real_data_validation_20260620.json`.
- [x] Evidence JSON SHA256 verified as `96cdc975d0b4798c6775b12e7bc9dc6af4fb7e9178a4d0ad54feeab8100e980e`.
- [x] Counts reconciled into current context: 754,920 rows; 12,582 events; 362 issuers; 11,450 eligible; 1,132 ineligible.
- [x] Daily event-date CAR/BHAR limitation recorded: 2,777 HAC gaps and HAC SE/t-stat null.
- [x] Quarterly limitation recorded: `ex_post_descriptive_only = true`.
- [x] Evidence limitations recorded: 500-GVKEY sample, current-vintage EPS, Compustat return proxy, and no delisting adjustment.
- [x] Prior validation status recorded: focused tests 10/10, full PEAD regression 99/99, Reviewer A/B/C PASS, and SAW validators PASS.
- [x] Current truth surfaces updated so the planner starts from PEAD real-data validation DONE.
- [ ] Owner review of `docs/context/e2e_evidence/pead_real_data_validation_20260620.json`. PENDING next decision.
- [ ] Separate dashboard-scoping decision. BLOCKED until owner approves the JSON review.
- [ ] Dashboard implementation, alpha claims, strategy promotion, ranking/scoring, alerts, and broker/order paths. NOT AUTHORIZED.

## Latest Addendum - V2 PEAD D3 Strategy Benchmark Handoff DONE (2026-06-20)

- [x] D3 manifest SHA matches the published immutable Parquet and `allowed_use` contains benchmark input use.
- [x] D2B-to-D3 `return_date` left join validates as many-to-one and preserves 754,920 rows.
- [x] All non-null D2B return dates are covered by the 2,810-row D3 artifact.
- [x] All 11,450 complete events have exactly 60 benchmark observations.
- [x] CAR and BHAR formulas match `summarize_event_windows` on deterministic real-event spot checks.
- [x] Missing benchmark coverage makes CAR/BHAR null while preserving raw cumulative asset return.
- [x] New handoff test passes: 5/5.
- [x] Combined handoff, D3 artifact, and strategy regression passes: 26/26.
- [x] No conditional strategy defect fix was required; production code and published data artifacts are unchanged.
- [x] Reviewer A/B/C final reruns PASS after all High findings were resolved.
- [x] SAW PASS report and closure/context validators pass.
- [ ] D4 dashboard-integration scope. PENDING separate approval/decision.
- [ ] D4 dashboard implementation and alpha interpretation. NOT AUTHORIZED by this closure.

## Latest Addendum - V2 PEAD D3 Benchmark Artifact Publication DONE (2026-06-20)

- [x] User approval interpreted as exactly one bounded D3 benchmark artifact publication gate.
- [x] Pre-publication focused gate passed: `.venv\Scripts\python -m pytest tests\test_pead_d3_benchmark_artifact.py tests\test_pead_d2b_event_window_contract.py -q` -> 38 passed.
- [x] Builder publication passed: `.venv\Scripts\python scripts\pead_d3_benchmark_artifact.py --build`.
- [x] Immutable Parquet published: `data/processed/pead_d3_ken_french_daily_benchmark.f7dede990475b4ecf499fbf1dee3c4a81298073f018cc3a1ba1559f3e702c589.parquet`.
- [x] Atomic manifest pointer published: `data/processed/pead_d3_ken_french_daily_benchmark.parquet.manifest.json`.
- [x] Parquet SHA256 matches manifest: `f7dede990475b4ecf499fbf1dee3c4a81298073f018cc3a1ba1559f3e702c589`.
- [x] Artifact row count is 2,810 and date range is 2015-01-02 through 2026-03-06.
- [x] D2B benchmark coverage is complete: 2,810 / 2,810 required sessions, zero missing.
- [x] `benchmark_return = mktrf + rf` validation passed with max absolute formula error `0.0`.
- [x] No duplicate `return_date` rows and all benchmark numeric fields are finite.
- [x] Independent Reviewer A/B/C returned PASS with no in-scope Critical/High findings.
- [x] SAW PASS report exists at `docs/saw_reports/saw_v2_d3_benchmark_artifact_publication_20260620.md`.
- [x] No D2B semantic change, benchmark-date patching, fill, interpolation, zero substitution, fallback benchmark, or source splice occurred.
- [ ] Strategy benchmark handoff validation. PENDING separate approval.
- [ ] CAR/BHAR/quintile interpretation. BLOCKED pending separate approval after handoff validation.

## Latest Addendum - V2 PEAD D2B Terminal Reviewer Rerun PASS (2026-06-20)

- [x] Parent focused matrix passed for D2A, D2B, D3, and strategy handoff: 70 collected tests.
- [x] Reviewer A final rerun PASS: strategy correctness and D2B semantic preservation; no Critical/High findings.
- [x] Reviewer B final rerun PASS: runtime/operational resilience and forbidden-action boundaries; no Critical/High findings.
- [x] Reviewer C final rerun PASS: data integrity and performance path; no Critical/High findings.
- [x] Historical 2026-06-19 BLOCK report remains intact as pre-rerun evidence.
- [x] Current terminal PASS report exists at `docs/saw_reports/saw_v2_d2b_session_spine_repair_rerun_20260620.md`.
- [x] Active D2B artifact remains SHA256 `c3da606af340ba5b531d3d0382e1f2c83469e29a42dd7c0cc9c356cba82594a1`; no D2B data artifact rebuild occurred.
- [x] No `pead_d3_ken_french_daily_benchmark*` artifact exists; no D3 publication occurred.
- [x] D2B session-spine repair terminal reviewer closure is PASS.
- [ ] D3 benchmark artifact publication. PENDING separate approval.
- [ ] CAR/BHAR/quintile interpretation. BLOCKED.

## Latest Addendum - V2 PEAD D2B Authoritative Market-Session Spine Repair (2026-06-19)

- [x] Independent D3 Reviewer B/C rerun found no new Critical/High issue.
- [x] The exact official Ken French source bytes define the authoritative session dates within the D2A sample range.
- [x] All 52 D2A-only market-closed dates are excluded from D2B session offsets without deleting D2A source evidence.
- [x] D2B prior-20 liquidity selection, 15-observation floor, and deterministic score/count/IID/security ordering remain unchanged.
- [x] Corrected D2B output retains 12,582 events, 754,920 rows, and exactly 60 rows per event.
- [x] Eligible handoffs increase from 4,867 to 11,450 with zero true-to-false transitions.
- [x] Active D2B artifact SHA256 is `c3da606af340ba5b531d3d0382e1f2c83469e29a42dd7c0cc9c356cba82594a1`; prior immutable artifact is retained.
- [x] D3 reconstructs and validates all 2,810 required sessions in memory with zero missing dates.
- [x] Full strategy smoke passes with 11,450 events, 687,000 complete rows, zero duplicate keys, and zero closed dates.
- [x] Focused validation passes: 70 tests.
- [x] Active-scale handoff validates all D2A rows in bounded chunks and completes at 1,756.7 MiB peak RSS without `ArrayMemoryError`.
- [x] Cross-row event metadata/timing drift and normalized duplicate D2A keys fail closed.
- [ ] Terminal Reviewer A/B/C SAW rerun after final fixes. BLOCKED by reviewer usage limit; SAW report published at `docs/saw_reports/saw_v2_d2b_session_spine_repair_20260619.md`.
- [ ] D3 benchmark artifact publication. PENDING separate approval.
- [ ] CAR/BHAR/quintile interpretation. BLOCKED.

## Latest Addendum - V2 PEAD D3 Benchmark Artifact Builder (2026-06-19)

- [x] D3 builder script exists at `scripts/pead_d3_benchmark_artifact.py`.
- [x] D3 focused tests exist at `tests/test_pead_d3_benchmark_artifact.py`.
- [x] Official Ken French daily ZIP fetch path is implemented with approved host guard.
- [x] Source release and source download SHA256 are captured.
- [x] Source percent returns are converted to decimal returns.
- [x] `benchmark_return = mktrf + rf` is enforced.
- [x] `mktrf` alone as total benchmark return is rejected in tests.
- [x] D2B manifest/session hash validation is implemented.
- [x] Missing benchmark dates fail closed with no fill/interpolation.
- [x] Immutable Parquet plus atomic manifest publication path is implemented and tested.
- [x] Strategy summary repair preserves raw cumulative asset return for complete asset windows when benchmark coverage is missing, while CAR/BHAR and eligibility remain blocked.
- [x] Focused compile passes.
- [x] Focused D3 tests pass: 7 passed; post-review strategy regression passes after the narrow summary fix.
- [x] Real build attempted and stopped before publication on missing benchmark sessions.
- [ ] D3 benchmark artifact published. BLOCKED by 52 missing D2B-required sessions in official Ken French daily factors.
- [ ] CAR/BHAR/quintile interpretation. BLOCKED.

## Latest Addendum - V2 PEAD D3 Benchmark Input Design Gate (2026-06-19)

- [x] Canonical benchmark source is Ken French daily Fama/French 3 Factors.
- [x] Source citation and methodology citation are recorded in the contract.
- [x] Source percent units and canonical decimal-return units are explicit.
- [x] Formula is locked: `benchmark_return = mktrf + rf` after percent-to-decimal conversion.
- [x] `mktrf` alone is forbidden as total market return.
- [x] Join key is strictly `return_date` against the D2B market-session spine.
- [x] Missing benchmark dates remain missing; no fill, interpolation, zero substitution, or fallback benchmark.
- [x] CAR/BHAR requires all 60 benchmark observations.
- [x] Existing strategy `car` terminology is documented as beta-1 market-adjusted CAR, not regression alpha.
- [x] Future immutable Parquet/manifest publication contract is specified.
- [x] Implementation acceptance tests are specified.
- [x] Read-only local audit records current `ff_factors.parquet` as insufficient: 1,003 rows, 2022-01-03 through 2025-12-31.
- [x] D3 design gate is docs-only; no provider, data artifact, strategy code, dashboard, staging, or commit action was performed.
- [ ] D3 benchmark artifact implementation. PENDING separate approval.
- [ ] Real CAR/BHAR/quintile interpretation. BLOCKED.

## Latest Addendum - V2 PEAD D2B Fixed Event-Security Window (2026-06-19)

- [x] Prior-liquidity window is the previous 20 global market sessions strictly before each event.
- [x] Candidate count uses finite `dollar_volume`; eligibility requires at least 15 observations; score is the arithmetic mean of finite values.
- [x] Selection order is score DESC, count DESC, normalized `iid` ASC, `security_id` ASC, with no `IID01` preference/fallback.
- [x] Exactly one event-level security is fixed across all 60 rows; no post-event replacement or switch occurs.
- [x] `return_date(e,k)` is the `k`th global session after the event for `k=1..60`; missing rows are retained and no imputation/delisting label is added.
- [x] `handoff_eligible` requires one selected security, all 60 dates, and all 60 finite returns.
- [x] Input manifest/hash validation and reads use stable byte snapshots; output uses immutable Parquet then atomic manifest; pre-commit `BaseException` cleanup is covered.
- [x] D2A normalization occurs once in the CLI path.
- [x] Artifact evidence matches: 12,582 events, 362 issuers, 754,920 rows, 12,568 selected, 14 no-security, 522 short, 7,179 missing/non-finite, 4,867 eligible, 2,862 sessions, SHA256 `8e2f39c2cb12bd0b50c9a134b280b5ecb8cd438f8a2249c6842c226250228b99`.
- [x] Tests pass: 26 focused and 58 combined.
- [x] Full-sample adapter smoke passes: 4,867 events, 881,588 unique canonical return rows, zero duplicate keys, 292,020 complete strategy rows, identical global spine, no second window algorithm.
- [x] Reviewer A/B initial High overlap-handoff and input-TOCTOU findings are resolved.
- [x] Final Reviewer A/B/C reconciliation PASS: A 11/11, B 10/10, C 12/12; no Critical/High finding remains open.
- [x] Bounded D2B Data slice complete. This is not PEAD phase-end.
- [x] Bounded D3 benchmark-input contract/design gate. COMPLETED as docs-only design; provider fetch and alpha interpretation remain blocked.

## Latest Addendum - V2 PEAD D2A Security-Level Return Repair (2026-06-19)

- [x] Every `(gvkey, iid)` series is preserved through level, lag, fallback, and guardrail construction.
- [x] `TR_level = prccd * trfd / ajexdi`; canonical `total_return` lags only within `(gvkey, iid)`.
- [x] Output exposes `security_id`, `date`, and `total_return`; `(security_id,date)` is unique.
- [x] The sample contains exactly 500 GVKEYs, 795 securities, 1,491,022 rows, and 117 multi-IID GVKEYs.
- [x] Active Parquet SHA256 matches the atomic manifest pointer: `f8b988055c99c42e28ebf470acbe9d7b6477a08c2ff2c5c71357b292a0fae957`.
- [x] Source-level formula error is `0.0`; changed valid TR levels produce nonzero returns above 99%.
- [x] `--build` and `--event-window-only` fail closed in D2A; dollar volume is not ADV.
- [x] Legacy invalid sample is retained only as superseded evidence at original SHA256 `0432fc703fab997329801c02352c359984544889da8097abb76e7765758652ab`.
- [x] Focused D2A/strategy tests pass: 32 passed.
- [x] Reviewer A/B/C final SAW passes with no in-scope Critical/High findings.
- [x] D2B fixed event-level IID selection and `+60` market-session extraction. COMPLETED in the subsequent bounded D2B round with final Reviewer A/B/C PASS.

## Latest Addendum - V2 PEAD D1 Parent Closure Reconciliation (2026-06-18)

- [x] Existing full D1 SAW exists at `docs/saw_reports/saw_v2_d1_repair_20260618.md` and validator blocks pass.
- [x] D1 Parquet SHA256 matches the manifest SHA256 `81b2689b48943373f58586ddc382fb609dbce022cde93d4d502333cae5541855`.
- [x] Current-vintage Compustat/restatement-hindsight limitation remains explicit; strict PIT EPS is not claimed.
- [x] Untracked local D1 builder, test, brief, and SAW ownership is disclosed; clean tracked-repo closure is not claimed.
- [x] Thin reconciliation SAW is published at `docs/saw_reports/saw_v2_d1_parent_closure_reconciliation_20260618.md`.
- [x] No D1 implementation, test, rebuild, provider, dashboard, strategy, staging, or commit action was performed.
- [x] D2 return/IID repair. COMPLETED across subsequent D2A and bounded D2B rounds.
- [ ] Dashboard integration. DEFERRED; D2B is not dashboard authorization and D3 benchmark-input design remains next.

## Latest Addendum - V2 PEAD D1 Repair (2026-06-18)

- [x] Raw numeric `epspxq` is used; `ajexq` is not divided; `adj_eps` remains a compatibility field.
- [x] Duplicate `(gvkey,rdq)` rows are resolved before exact t-4 lag and rolling calculations.
- [x] Raw `sue_price_scaled` and RDQ cross-sectional `+/-5 std` `sue_price_scaled_clipped` coexist.
- [x] `cshoq_lag1` is treated as millions and `liquidity_pass = prccq_lag1 * cshoq_lag1 > 50` is flag-only.
- [x] `valid_sue` is independent of `liquidity_pass`.
- [x] Parquet and manifest use temp-to-replace publication.
- [x] D1 artifact rebuilt: 346,511 rows, 233,586 valid SUE rows, 13,216 GVKEYs, SHA256 `81b2689b48943373f58586ddc382fb609dbce022cde93d4d502333cae5541855`.
- [x] Manifest quality metrics record raw `abs(SUE) > 5` at 441 / 233,586 valid rows (0.1888%), below the 0.5% fail-closed threshold.
- [x] Empty processed-output paths fail before touching the existing Parquet/manifest bundle.
- [x] Current-vintage Compustat EPS/restatement-hindsight limitation is recorded.
- [x] Duplicate-RDQ counterexample regression covers stage-order contamination.
- [x] Focused D1/PEAD tests pass: 27 passed.
- [x] Context validation and context hygiene pass after D1 truth refresh.
- [x] Independent Reviewer A/B/C final SAW passes complete; report published at `docs/saw_reports/saw_v2_d1_repair_20260618.md`.
- [x] D2 return/IID/event-window contract repaired. COMPLETED across subsequent D2A and bounded D2B rounds; D2B final Reviewer A/B/C PASS.
- [ ] Ken French public patch implemented. DEFERRED.
- [ ] Provider total-return contract validated. DEFERRED.

## Latest Addendum — V2 PEAD Strategy Contract SAW Rerun Promotion (2026-06-18)

- [x] Strategy contract implemented without touching Data-stream builders/artifacts.
- [x] Event windows use explicit market sessions and strict `+1..+60` semantics.
- [x] Raw cumulative return is separated from benchmark-gated CAR/BHAR.
- [x] Malformed dates, booleans, duplicate keys, missing skeletons, and reserved benchmark collisions fail closed.
- [x] Focused synthetic test suite passes: 13 tests.
- [x] Affected strategy/statistics/legacy PEAD tests pass: 23 tests.
- [x] Docs-as-code updated with formulas, boundaries, and decision log.
- [x] SAW report artifact exists and validator scripts pass.
- [x] Independent Reviewer A/B/C rerun completes after reconciliation. PASS; no in-scope Critical/High findings.
- [x] Strategy skeleton is handoff-ready for corrected D1/D2 inputs only.
- [x] Corrected D1/D2 data handoff exists. D2B bounded sample and canonical strategy adapter smoke complete.
- [x] Corrected D1/D2 data handoff contract smoke accepted with final D2B Reviewer A/B/C PASS; no alpha interpretation authorized.
- [ ] Real quintile/CAR/backtest interpreted. BLOCKED.

Status: Current with Portfolio Universe Construction PASS and optimizer-core quarantine complete
Authority: advisory-only integration artifact. This file does not authorize live trading, broker automation, promotion, strategy search, provider ingestion, alerts, dashboard content redesign, signal ranking, macro scoring, factor scoring, candidate ranking, candidate scoring, thesis validation, or scope widening by itself.
Purpose: define machine-checkable done criteria for current Phase 65 portfolio universe and candidate-card work.

## ⚠️ Audit Correction Addendum — V2-D0.4E-AUDIT (2026-06-18)

The following checked items in V2-D0.4E below contain **false or overstated completion claims** per read-only schema audit. This addendum overrides them.

- [!] **PERMNO-GVKEY bridge**: `crsp_ccmxpf_linktable.parquet` 76,851 rows fetched, but `lpermno` and `lpermco` are ALL NULL. This is NOT a PERMNO bridge — it is a Compustat GVKEY-only list. The SQL fallback (line 152, `local_wrds_pead_v2_fetcher.py`) does not SELECT CUSIP either. Downstream CUSIP join is impossible with current artifacts. **Status: BROKEN, not DONE.**
- [!] **Full 2015-2026 daily price coverage**: Row count 54.4M is confirmed, but total_return/trfd has 42% missing in `prices_daily_compustat` (13.22M / 31.35M rows) and ~38% missing in 2015-2019 period. "Coverage confirmed" should read: row-count confirmed, total-return coverage is INCOMPLETE.
- [!] **security_master `secstat`**: `security_master_compustat.parquet` does not contain `secstat` field (per audit); 12,101 GVKEYs have multiple IIDs — primary-security selection rule needed.

These items remain checked as fetched/present but are annotated INCOMPLETE per the above findings.

---

## Latest Addendum - V2-D0.4E WRDS Fetch Ceiling + Compustat-Only Data Layer

- [x] WRDS entitlement ceiling confirmed: `crsp_a_stock`, `tr_ibes`, `crsp_a_indexes` all return `InsufficientPrivilege`.
- [x] D0.4D LIMIT-0 probe confirmed accessible=true for CRSP/IBES views — recorded as SECURITY INVOKER false positive; full reads require underlying schema.
- [x] `comp_fundq.parquet` fetched: 350,110 rows, SHA256=58bbf125, manifest present.
- [x] `comp_secd_2015_2019.parquet` fetched: 23,141,359 rows (2015-01-01–2019-12-31), SHA256=5891113c, manifest present.
- [x] `crsp_ccmxpf_linktable.parquet` fetched: 76,851 rows via CUSIP bridge (comp.security), lpermno=NULL accepted, manifest present.
- [x] Dedup check completed: `prices_daily_compustat.parquet` (31.3M rows 2020-2026) and `security_master_compustat.parquet` (75,913 rows) confirmed present — NOT re-fetched.
- [x] Full 2015-2026 daily price coverage confirmed: `comp_secd_2015_2019` + `prices_daily_compustat` = 54.4M rows.
- [x] PEAD analysis contract documented in bridge_contract_current.md addendum V2-D0.4E.
- [x] Historical pre-reconciliation D1 build: 235,033 valid events. Superseded by the latest D1 repair addendum after early RDQ dedup removed 1,447 contaminated lag-valid events; final valid count is 233,586. Builder: `scripts/pead_d1_sue_builder.py`. (2026-06-18)
- [x] PEAD D2 pre-requisite — the prior primary-IID artifact remains superseded evidence only; D2A now preserves every `(gvkey,iid)` return series and D2B performs fixed event-level selection. (Updated 2026-06-19)
- [x] PEAD D2 pre-requisite — normalized security-level total-return D2A contract completed at SHA256 `f8b988055c99c42e28ebf470acbe9d7b6477a08c2ff2c5c71357b292a0fae957`; the prior invalid formula remains forbidden. (Updated 2026-06-19)
- [x] PEAD D2 event-window returns: bounded D2B fixed-security exact-`+60` artifact completed at SHA256 `8e2f39c2cb12bd0b50c9a134b280b5ecb8cd438f8a2249c6842c226250228b99`; final Reviewer A/B/C PASS. (Updated 2026-06-19)
- [ ] PEAD D3-D4 signal validation + benchmark adjustment (Ken French Mkt-RF). PENDING D2.
- [ ] PEAD V2 analysis layer full validation. PENDING.
- [ ] Formal approval_ref per row. PENDING (external constraint, not blocking PEAD build).
- [ ] CRSP/IBES subscription upgrade. EXTERNAL — contact WRDS admin when needed.

## Latest Addendum - V2-D0.4D Local Human Probe Execution DONE

- [x] D0.4D local human execution packet run: 2026-06-18.
- [x] All five tables returned `accessible=true`.
- [x] Result artifact: `V2_D0_4D_PERMISSION_PROBE_RESULTS.redacted.json`.
- [x] WRDS data fetcher ready: `local_wrds_pead_v2_fetcher.py`.
- [x] Data output directory prepared: `data/raw/wrds/`.
- [x] Override authority: user explicit instruction (正式解除) 2026-06-18.
- [ ] PEAD V2 data fetch completed (fetcher script ready, not yet run). PENDING.
- [ ] Formal approval_ref recorded per row. PENDING.

## Latest Addendum - V2-D0.4C Local Read-Only Permission Probe Approval

- [x] RoundID recorded: `ROUND-20260603-V2-D0-4C-LOCAL-READ-ONLY-PERMISSION-PROBE-APPROVAL`.
- [x] ScopeID recorded: `V2_D0_4C_LOCAL_READ_ONLY_PERMISSION_PROBE_APPROVAL_DOCS_ONLY`.
- [x] Markdown approval artifact exists: `docs/authorization/V2_D0_4C_LOCAL_READ_ONLY_PERMISSION_PROBE_APPROVAL.md`.
- [x] JSON approval artifact exists: `docs/authorization/V2_D0_4C_LOCAL_READ_ONLY_PERMISSION_PROBE_APPROVAL.json`.
- [x] SAW report exists: `docs/saw_reports/saw_v2_d0_4c_local_read_only_permission_probe_20260603.md`.
- [x] Exact five-row future probe scope recorded.
- [x] All rows are `probe_approved_not_executed`, `not_formally_approved`, and `approval_ref=null`.
- [x] D0.4D queued as next packet.
- [x] D0.4D local human execution packet run. DONE 2026-06-18.
- [x] Formal permission truth confirmed via probe: all five accessible=true.

## Latest Addendum - V2-D0.4B WRDS Local Auth Method Confirmed

- [x] RoundID recorded: `ROUND-20260603-V2-D0-4B-WRDS-LOCAL-AUTH-METHOD-CONFIRMED`.
- [x] ScopeID recorded: `V2_D0_4B_WRDS_LOCAL_AUTH_METHOD_CONFIRMED_NO_EXECUTION`.
- [x] Markdown correction artifact exists: `docs/authorization/V2_D0_4B_WRDS_LOCAL_AUTH_METHOD_CONFIRMED.md`.
- [x] JSON correction artifact exists: `docs/authorization/V2_D0_4B_WRDS_LOCAL_AUTH_METHOD_CONFIRMED.json`.
- [x] SAW report exists: `docs/saw_reports/saw_v2_d0_4b_wrds_local_auth_method_20260603.md`.
- [x] Required decision language recorded: `WRDS local authentication method is user-attested available through user-owned local credentials, but actual login has not been verified by Codex/subagents, credentials were not read, and formal table-level permission truth is not closed.`
- [x] State fields recorded: `local_auth_method=user_attested_local_auth_available`, `actual_login_verified_by_agent=false`, `formal_approval_ref=null`, `permission_truth=not_closed`, `wrds_execution=governance_blocked_until_probe_approval`.
- [x] All five rows are `probe_plan_pending`, `not_approved`, and `approval_ref=null`.
- [ ] Actual login verified by Codex/subagents. BLOCKED/false.
- [ ] Formal table-level permission truth closed. BLOCKED/not_closed.
- [ ] Any row approved. BLOCKED/not_approved.
- [ ] Probe execution authorized by this artifact. BLOCKED.
- [ ] Any secret.txt/credential read, WRDS/provider execution, schema discovery, row count, sample row, snapshot, data output, runtime/dashboard/scoring/broker write, or approval_ref fabrication occurred. BLOCKED/forbidden.

## Latest Addendum - V2-D0.2 WRDS Entitlement Evidence Request

- [x] RoundID recorded: `ROUND-20260603-V2-D0-2-ENTITLEMENT-EVIDENCE-REQUEST`.
- [x] ScopeID recorded: `V2_D0_2_WRDS_ENTITLEMENT_EVIDENCE_REQUEST_NO_CREDENTIAL_USE`.
- [x] Evidence-request markdown packet exists: `docs/authorization/V2_D0_2_WRDS_ENTITLEMENT_EVIDENCE_REQUEST.md`.
- [x] Evidence-request JSON packet exists: `docs/authorization/V2_D0_2_WRDS_ENTITLEMENT_EVIDENCE_REQUEST.json`.
- [x] SAW report exists: `docs/saw_reports/saw_v2_d0_2_entitlement_evidence_request_20260603.md`.
- [x] Copyable non-secret evidence-request message exists.
- [x] All five rows are listed with `evidence_status=evidence_missing`, `permission_status=pending`, and `approval_ref=null`.
- [x] The artifact forbids credential use, provider access, probes, schema/table discovery, row counts, snapshots, data output, runtime checks, row approval, legacy cleanup, secret remediation, SafeBoot, and BootReady.
- [ ] `TODO-ENTITLEMENT-001`: qualifying non-secret entitlement evidence exists. PENDING/BLOCKING.
- [ ] `TODO-APPROVAL-001`: valid exact approval text and row/table approval_ref exist. PENDING/BLOCKING.
- [ ] Any row is approved. BLOCKED.
- [ ] Any WRDS/provider access, credentials use, probe execution, snapshot, data output, runtime action, legacy cleanup, secret remediation, SafeBoot, or BootReady is authorized. BLOCKED.

## Latest Addendum - V2-D0.1 Authorization Intent Evidence Missing

- [x] RoundID recorded: `ROUND-20260603-V2-D0-1-AUTHORIZATION-INTENT`.
- [x] ScopeID recorded: `V2_D0_1_WRDS_PERMISSION_TRUTH_AUTHORIZATION_INTENT`.
- [x] Authorization-intent markdown packet exists: `docs/authorization/V2_D0_1_WRDS_PERMISSION_TRUTH_AUTHORIZATION.md`.
- [x] Authorization-intent JSON packet exists: `docs/authorization/V2_D0_1_WRDS_PERMISSION_TRUTH_AUTHORIZATION.json`.
- [x] Packet status is `INTENT_RECORDED_EVIDENCE_MISSING`, not final approval.
- [x] All five rows are listed with `evidence_status=evidence_missing`, `permission_status=pending`, and `approval_ref=null`.
- [x] Future approval text template is included without claiming approval.
- [x] `secret.txt` is recorded as local secret material and not non-secret entitlement evidence.
- [ ] `TODO-ENTITLEMENT-001`: qualifying non-secret entitlement evidence exists. PENDING/BLOCKING.
- [ ] `TODO-APPROVAL-001`: valid exact approval text and row/table approval_ref exist. PENDING/BLOCKING.
- [ ] Any row is approved. BLOCKED.
- [ ] Any WRDS/provider access, credentials use, probe execution, snapshot, data write, dashboard/runtime, scoring/ranking, alert, broker path, legacy cleanup, secret remediation, SafeBoot, or BootReady is authorized. BLOCKED.

## Latest Addendum - V2-D0.1 TODO-MATRIX-001 Permission Truth Bookkeeping

- [x] RoundID recorded: `ROUND-20260602-V2-D0-1-TODO-MATRIX-001-BOOKKEEPING`.
- [x] ScopeID recorded: `V2_D0_1_PERMISSION_TRUTH_BOOKKEEPING`.
- [x] Offline permission-truth artifact exists: `v2_discovery/data_lab/permission_truth.py`.
- [x] Focused scope tests exist: `tests/test_v2_wrds_permission_truth_scope.py`.
- [x] Regression/no-write tests remain linked: `tests/test_v2_wrds_permission_matrix.py`; `tests/test_v2_snapshot_manifest_contract.py`; `tests/test_v2_data_lab_no_v1_writes.py`.
- [x] V2-D0.1 exact five rows default to `pending`.
- [x] Approved status requires row/table `approval_ref`.
- [x] `allowed_uses` for approved rows is strictly `["provenance_contract"]`.
- [x] PEAD_V2_001 starter scope is separate from V2-D0.1 entitlement truth.
- [x] `ibes.det_epsus` is `pending` for V2-D0.1 and `not_requested` for PEAD starter.
- [x] `TODO-MATRIX-001`: V2-D0.1 permission-truth metadata/builder gap is RESOLVED.
- [x] Focused tests pass: `.venv\Scripts\python -m pytest tests\test_v2_wrds_permission_truth_scope.py tests\test_v2_wrds_permission_matrix.py tests\test_v2_snapshot_manifest_contract.py tests\test_v2_data_lab_no_v1_writes.py -q` -> PASS, 51 passed.
- [x] Compile check passes: `.venv\Scripts\python -m compileall v2_discovery\data_lab tests\test_v2_wrds_permission_truth_scope.py -q` -> PASS.
- [ ] `TODO-ENTITLEMENT-001`: five-row non-secret entitlement evidence exists. PENDING.
- [ ] `TODO-APPROVAL-001`: explicit V2-D0.1 approval text exists. PENDING.
- [ ] `TODO-CLEANROOM-001`: full clean-room surface and proof packet exist. PENDING.
- [ ] `TODO-LEGACY-WRDS-001`: legacy WRDS/BvD triage and cleanup authority is approved/completed. OPEN.
- [ ] `TODO-VALIDITY-001`: V2 alpha validity packet and `C3_LOCK_PEAD_V2_001_v1` are built. PENDING.
- [ ] `TODO-PUBLIC-MAIN-001`: public/main status mismatch is resolved. OPEN.
- [ ] Any WRDS/provider access, probe, credential use, snapshot, data write, dashboard reader, scoring/ranking, alert, broker path, SQLite, SafeBoot, BootReady, or legacy cleanup action is authorized. BLOCKED.

## Latest Addendum - V2-D0.1 Scope and Clean-Room Runtime Decision

- [x] RoundID recorded: `ROUND-20260602-V2-D0-1-SCOPE-CLEANROOM-RUNTIME`.
- [x] ScopeID recorded: `V2_D0_1_SCOPE_AND_CLEANROOM_RUNTIME_DECISION`.
- [x] Handover created: `docs/handover/V2_D0_1_SCOPE_AND_CLEANROOM_RUNTIME_DECISION_20260602.md`.
- [x] `TODO-PEAD-DECISION-001` resolved: PEAD_V2_001 starter is four-row Compustat PEAD.
- [x] `ibes.det_epsus` recorded as `pending` for V2-D0.1 once requested and `not_requested` for PEAD_V2_001 starter.
- [x] `TODO-CLEANROOM-RUNTIME-001` resolved: `schema_registry.py` excluded from credentialed runtime by default.
- [ ] `TODO-ENTITLEMENT-001`: five-row non-secret entitlement evidence exists. PENDING.
- [ ] `TODO-APPROVAL-001`: explicit V2-D0.1 approval text exists. PENDING.
- [ ] `TODO-CLEANROOM-001`: full clean-room surface and proof packet exist. PENDING.
- [x] `TODO-MATRIX-001`: separate entitlement-status and PEAD-starter-scope fields or equivalent builder/override exist. RESOLVED by `v2_discovery/data_lab/permission_truth.py`.
- [ ] Any WRDS/provider access, probe, credential use, snapshot, data write, dashboard reader, scoring/ranking, alert, broker path, SQLite, SafeBoot, BootReady, or legacy cleanup action is authorized. BLOCKED.

## Latest Addendum - V2-D0.1 Expert 1-6 Follow-Up Reconciliation

- [x] RoundID recorded: `ROUND-20260602-V2-D0-1-EXPERT-1-6-FOLLOWUP`.
- [x] ScopeID recorded: `V2_D0_1_EXPERT_1_6_FOLLOWUP_RECONCILIATION`.
- [x] Handover created: `docs/handover/V2_D0_1_EXPERT_1_6_FOLLOWUP_RECONCILIATION_20260602.md`.
- [x] Agreement/confidence levels recorded for all six experts.
- [x] Backend/Data status corrected to `PATCH_RESOLVED_LOCAL` for current workspace raw-payload strictness.
- [x] V2-D0.1 five-row entitlement target recorded.
- [x] Real follow-up questions recorded without adding low-value expert questions.
- [x] Clean-room probe definition and dirty-root rule recorded as future approval-gated work.
- [x] Research-validity thresholds and C3 lock requirement recorded.
- [ ] `TODO-ENTITLEMENT-001`: non-secret entitlement evidence exists. PENDING.
- [ ] `TODO-APPROVAL-001`: explicit V2-D0.1 approval text exists. PENDING.
- [x] `TODO-PEAD-DECISION-001`: I/B/E/S analyst-surprise vs Compustat-rdq PEAD starter is resolved by `ROUND-20260602-V2-D0-1-SCOPE-CLEANROOM-RUNTIME`.
- [ ] `TODO-CLEANROOM-001`: clean-room probe surface is built and validated. PENDING.
- [ ] `TODO-LEGACY-WRDS-001`: legacy WRDS/BvD triage and cleanup authority is approved/completed. OPEN.
- [ ] `TODO-VALIDITY-001`: V2 alpha validity packet and `C3_LOCK_PEAD_V2_001_v1` are built. PENDING.
- [ ] `TODO-PUBLIC-MAIN-001`: public/main status mismatch is resolved. OPEN.
- [x] `TODO-MATRIX-001`: V2-D0.1-specific permission-truth builder or row override exists. RESOLVED by `v2_discovery/data_lab/permission_truth.py`.
- [ ] Any WRDS/provider access, probe, credential use, snapshot, data write, dashboard reader, scoring/ranking, alert, broker path, SQLite, SafeBoot, BootReady, or legacy cleanup action is authorized. BLOCKED.

## Latest Addendum - V2-D0.1 Expert 1-6 Agreement and High-Confidence TODO Gates

- [x] RoundID recorded: `ROUND-20260602-V2-D0-1-EXPERT-1-6-TODO-GATES`.
- [x] ScopeID recorded: `V2_D0_1_EXPERT_1_6_AGREEMENT_TODO_GATES`.
- [x] Expert 1-6 agreement gate recorded as high-confidence TODO guidance.
- [x] Missing numeric rating values are explicitly not inferred.
- [x] V2-D0.1 recorded as entitlement-only.
- [x] Backend/Data row-level validator recorded as `PATCH_RESOLVED` after focused tests.
- [x] Security approval text requirement recorded.
- [x] Legacy WRDS helper/quarantine risk recorded as open gate.
- [x] Quant Research `PEAD_V2_001_BOUNDARY_PACKET` recorded as conditional after WRDS/PIT authority.
- [x] Research Validity recorded: no V2 alpha is currently `research_valid`.
- [x] `V2_ALPHA_VALIDITY_PACKET` template requirement recorded.
- [x] SAW report published: `docs/saw_reports/saw_v2_d0_1_expert_1_6_todo_gates_20260602.md`.
- [x] Focused V2-D0 tests, compileall, security/provider tests, and context build/validate pass for this round.
- [ ] Non-secret WRDS entitlement evidence exists. PENDING user/source evidence.
- [ ] Explicit V2-D0.1 approval text exists. PENDING user/source approval.
- [ ] WRDS/PIT authority exists for PEAD boundary packet execution. BLOCKED.
- [ ] V2 alpha validity packet template exists. PENDING future docs/design work.
- [ ] Any WRDS/provider access, probe execution, snapshot, data write, dashboard reader, scoring/ranking, alert, broker path, SQLite, SafeBoot, or BootReady claim is authorized. BLOCKED.

## Latest Addendum - V2-D0 Multi-Expert Reconciliation Gate

- [x] RoundID recorded: `ROUND-20260602-V2-D0-MULTI-EXPERT-RECONCILIATION`.
- [x] ScopeID recorded: `MULTI_EXPERT_RECONCILIATION_GATE`.
- [x] Expert A Data/WRDS/Provenance returned PASS.
- [x] Expert A probe authorization recorded as NEEDS USER EVIDENCE.
- [x] Expert B Backend/Contracts/Tests returned PATCH.
- [x] Expert B PATCH findings fixed in `v2_discovery/data_lab/wrds_probe.py` and `v2_discovery/data_lab/snapshot_manifest.py`.
- [x] Probe contract validator rejects root drift, credential/connection/output extras, `next_allowed_action` drift, denied-action drift, code-ref drift, and dataset row drift.
- [x] Snapshot storage URI dataclass validation rejects bare `data/runtime_cache/v2_data_lab` to match JSON Schema.
- [x] Expert C Strategy/Product/Governance returned PASS.
- [x] Dashboard reader remains HOLD.
- [x] G9 remains context-only and non-actionable.
- [x] Reconciled verdict exists at `docs/handover/MULTI_EXPERT_RECONCILED_VERDICT_20260602.md`.
- [x] SAW report exists at `docs/saw_reports/saw_v2_d0_multi_expert_reconciliation_20260602.md`.
- [x] Focused V2-D0 tests pass with 20 tests.
- [ ] Non-secret WRDS entitlement evidence exists. PENDING user/source evidence.
- [ ] Read-only WRDS permission probe is approved. BLOCKED.
- [ ] Any PIT snapshot is generated. BLOCKED.
- [ ] Any dashboard reader is opened. HOLD / BLOCKED for main stream.
- [ ] Any SafeBoot or BootReady claim is made. BLOCKED.

## Latest Addendum - V2-D0 WRDS Permission + Snapshot Provenance Contract

- [x] RoundID recorded: `ROUND-20260601-V2-D0-WRDS-PERMISSION-SNAPSHOT`.
- [x] ScopeID recorded: `V2-D0_WRDS_PERMISSION_AND_SNAPSHOT_PROVENANCE_CONTRACT`.
- [x] G9 FINRA signal-card packet recorded as context-only ADVISORY_PASS.
- [x] Dashboard reader recorded as HOLD.
- [x] `v2_discovery/data_lab/permission_matrix.py` exists.
- [x] `v2_discovery/data_lab/wrds_probe.py` exists.
- [x] `v2_discovery/data_lab/snapshot_manifest.py` exists.
- [x] `v2_discovery/data_lab/schema_registry.py` exists.
- [x] `contracts/data_snapshot/wrds_permission_matrix.schema.json` exists.
- [x] `contracts/data_snapshot/wrds_snapshot_manifest.schema.json` exists.
- [x] Permission matrix validates through dataclass and JSON Schema.
- [x] WRDS probe contract records offline-only mode and no connection attempt.
- [x] Snapshot manifest validates through dataclass and JSON Schema.
- [x] Snapshot manifest rejects `data/processed/`, `data/registry/`, runtime boot-status, and docs/context boot-status storage targets.
- [x] Snapshot manifest rejects absolute, drive-letter, UNC, URI-scheme, and non-approved sandbox storage paths.
- [x] Dataclass payload validators and JSON Schema registry validation reject constant drift, denied-action drift, missing approval refs, and extra PIT policy fields.
- [x] Root false flags reject falsey non-bool values such as `0`, `None`, and empty string.
- [x] No provider, Streamlit, alert, broker, candidate promotion, parquet/CSV write, manifest write, or atomic write primitive exists in the new data-lab modules.
- [x] Source guard covers every `v2_discovery/data_lab/*.py` module.
- [x] Direct `jsonschema==4.26.0` dependency is declared in `pyproject.toml` and mirrored in `requirements.txt`.
- [x] Focused V2-D0 tests pass.
- [ ] Actual WRDS permission truth is approved. PENDING user/source evidence.
- [ ] Any read-only WRDS probe is implemented or run. BLOCKED until explicit approval.
- [ ] Any PIT snapshot is generated. BLOCKED until separate explicit approval.
- [ ] Any SafeBoot or BootReady claim is made. BLOCKED and forbidden for this round.

## Latest Addendum - V2 Alpha Factory Immediate Todo Directive

- [x] RoundID recorded: `ROUND-20260601-V2-ALPHA-FACTORY-DIRECTIVE`.
- [x] ScopeID recorded: `SCOPE-DOCS-ONLY-IMMEDIATE-TODO-FIRSTS`.
- [x] Directive packet exists at `docs/architecture/v2_alpha_factory_immediate_todo_directive_20260601.md`.
- [x] Directive is labeled as idea/directive intake, not a decision.
- [x] Immediate TODO-first order is recorded: WRDS/PIT/provenance first; PEAD variants second; corporate actions third; meta-labeling fourth; Orbis/BvD fifth.
- [x] Deferred/blocked directions are recorded: LLM market-news agents, DRL allocator, and live routing.
- [x] SQLite is explicitly not approved and remains forbidden without explicit approval.
- [x] No code, data, runtime, provider, boot, candidate scoring/ranking, or promotion behavior changed in this docs-only round.
- [ ] WRDS read-only permission probe scope is approved. PENDING.
- [ ] PIT snapshot generation scope, manifest policy, storage path, and rollback rule are approved. PENDING.
- [ ] Candidate registry storage design is approved. PENDING; SQLite requires explicit approval.
- [ ] Any PEAD/corporate-actions/meta-labeling/Orbis implementation has started. NOT STARTED and not authorized by this directive.
- [ ] SafeBoot or BootReady is claimed as passing. BLOCKED and forbidden for this directive.

## Latest Addendum - Governed Data Source Provenance Intake

- [x] RoundID recorded: `ROUND-20260528-GOVERNED-DATA-SOURCE-PROVENANCE-INTAKE`.
- [x] ScopeID recorded: `SCOPE-APPROVE-RAW-SOURCES-BEFORE-ARTIFACT-GENERATION`.
- [x] Source-provenance intake packet exists at `docs/architecture/governed_data_source_provenance_intake_20260528.md`.
- [x] StartingVerdict recorded as `BLOCK`.
- [x] Current state recorded: GovernanceGateV0 PASS; BootStatusPathContract PASS; GovernedDataAuthorizationPacket PASS; DataSourceAcquisitionPacket PASS; DataReadyStrict BLOCKED_MISSING_GOVERNED_ARTIFACTS; SafeBoot false; BootReady BLOCKED.
- [x] Packet states it does not close data readiness and does not authorize generation yet.
- [x] Correct sequence recorded: approve source provenance first; then bounded offline regeneration; then manifests/hashes; then strict data-readiness validation; then strict `--require-github`; then regenerate runtime boot status only after strict PASS.
- [x] Intake lines cover prices, ticker/security master, WRDS/R3000 membership, and Rule100 history source/generator.
- [x] Each line requires source location, owner/approval, date/as-of coverage, license/access note, schema, generator command, output path, manifest path, SHA256 policy, validation command, and rollback/removal rule.
- [x] Known static generator state is recorded without approving generation.
- [x] Forbidden actions are recorded: no boot_preflight.py patch; no DataReadyStrict weakening; no data/processed generation from incomplete provenance; no placeholder parquet/CSV; no runtime/boot_status_current.json edit; no ignored/local-governed data commit unless policy changes; no BootReady claim.
- [ ] Approved source provenance exists for all lines. BLOCKED until user/source authorization.
- [ ] Bounded offline regeneration is approved. BLOCKED and not authorized by this packet.
- [ ] Any required data artifact is generated or intaken. BLOCKED and not approved by this round.
- [ ] Strict data readiness is proven as passing. BLOCKED.
- [ ] Safe boot or boot readiness is claimed as passing. BLOCKED and forbidden for this round.

## Latest Addendum - Governed Data Source Acquisition / Bounded Regeneration Planning

- [x] RoundID recorded: `ROUND-20260528-GOVERNED-DATA-SOURCE-ACQUISITION`.
- [x] ScopeID recorded: `SCOPE-SOURCE-INPUTS-AND-GENERATORS-FOR-STRICT-DATA-READINESS`.
- [x] Source-acquisition planning packet exists at `docs/architecture/governed_data_source_acquisition_20260528.md`.
- [x] StartingVerdict recorded as `BLOCK`.
- [x] Current state recorded: GovernanceGateV0 PASS; BootStatusPathContract PASS; GovernedDataAuthorizationPacket PASS; StrictProof PASS / DEGRADED; DataReadyStrict BLOCKED_MISSING_GOVERNED_ARTIFACTS; SafeBoot false; BootReady BLOCKED; RuntimeBootStatus local / ignored / not commit evidence.
- [x] BlockingReason records absent/ignored/local-governed artifacts without approved source manifests or generators.
- [x] Correct next decision records options A trusted external governed bundle, B source acquisition + bounded offline regeneration planning, or C quarantine BootReady.
- [x] Recommendation records B unless a trusted governed bundle already exists.
- [x] Packet states planning/source acquisition only, not generation.
- [x] All five artifacts are documented in dependency order with source input, generator/gap status, approval, output schema, manifest/hash, validation command, rollback/removal, storage policy, and blocked-until condition.
- [x] Forbidden actions are recorded: no boot_preflight.py patch; no DataReadyStrict weakening; no placeholder parquet/CSV; no generation during boot; no runtime/boot_status_current.json edit; no data/processed commit unless policy changes; no BootReady claim.
- [ ] Trusted external governed bundle is approved and accepted. BLOCKED until user/source authorization.
- [ ] Source acquisition + bounded offline regeneration execution is approved. BLOCKED until explicit authorization.
- [ ] Any required data artifact is generated or intaken. BLOCKED and not approved by this round.
- [ ] Strict data readiness is proven as passing. BLOCKED.
- [ ] Safe boot or boot readiness is claimed as passing. BLOCKED and forbidden for this round.

## Latest Addendum - Governed Data Artifact Authorization

- [x] RoundID recorded: `ROUND-20260528-GOVERNED-DATA-ARTIFACT-AUTHORIZATION`.
- [x] ScopeID recorded: `SCOPE-APPROVE-INTAKE-OR-REGENERATION-FOR-STRICT-DATA-READINESS`.
- [x] Authorization packet exists at `docs/architecture/governed_data_artifact_authorization_20260528.md`.
- [x] Gate truth recorded: GovernanceGateV0 PASS; BootStatusPathContract PASS; StrictProof PASS/degraded.
- [x] Blocked boot truth recorded: DataReadyStrict BLOCKED_MISSING_GOVERNED_ARTIFACTS; SafeBoot false; BootReady BLOCKED.
- [x] Missing artifact paths are explicitly listed: `data/processed/prices_tri.parquet`, `data/processed/prices.parquet`, `data/processed/tickers.parquet`, `data/processed/universe_r3000_daily.parquet`, `data/processed/rule100_softmax_v1_history.csv`.
- [x] Local artifacts and dirty context are recorded as not clean GitHub truth and not BootReady evidence.
- [x] Forbidden actions are recorded: no boot_preflight.py patch; no DataReadyStrict weakening; no generation during boot; no placeholder parquet/CSV; no data/processed commit unless policy changes; no runtime/boot_status_current.json edit; no BootReady claim.
- [ ] Governed offline regeneration is approved and executed, or an approved external bundle is accepted. BLOCKED until user authorization.
- [ ] Missing governed artifacts are generated or intaken with manifest/hash/provenance approval. BLOCKED.
- [ ] Strict data readiness is proven through the approved read-only gate path. BLOCKED by missing governed artifacts.
- [ ] Safe boot or boot readiness is claimed as passing. BLOCKED and forbidden for this round.

## Latest Addendum - Research Validity Runner v0 Commit Anchor

- [x] Research-validity runner v0 exists in a local isolated commit.
- [x] Commit SHA recorded: `8716c51781d8524de4147cf42f17e52466913de4`.
- [x] Commit message: `Add research-validity runner v0 evidence gate`.
- [x] No boot-preflight, dashboard, optimizer/lifecycle, packet zip, or unrelated dirty files were staged into that commit.
- [x] Research/engine suite passed with 45 tests.
- [x] Affected replay/lifecycle/optimizer suite passed with 186 tests.
- [x] Context-builder test passed with 21 tests.
- [x] Context rebuild and validation passed.
- [x] SAW report block validation passed.
- [x] Commit is pushed to GitHub and remote branch resolves to `8716c51781d8524de4147cf42f17e52466913de4`.

## Latest Addendum - Portfolio Replay Role Contract

- [x] `REPLAY_COLUMNS` includes `context_role` and `row_role`.
- [x] `REPLAY_CONTEXT_COLUMNS` includes `context_role` and `row_role`.
- [x] `SELECTED_METHOD_REPLAY_ARTIFACT_COLUMNS` includes `context_role` and `row_role`.
- [x] Legacy selected-method artifacts missing role columns hydrate default roles on read.
- [x] Unrelated selected-method artifact schema drift still fails closed.
- [x] Dashboard context normalization delegates to `normalize_context_frame_for_replay(...)`.
- [x] Latest snapshot display uses `Replay Weight`, not generic `Weight`.
- [x] Allocation snapshot display uses `Current Weight`, not generic `Weight`.
- [x] Decision tables expose `Context Role` plus replay target and audit weight.
- [x] Diagnostics are computed from existing `DashboardReplayContext`.
- [x] Diagnostic payload includes replay identity and cache-signature hash.
- [x] Scoped compile passes.
- [x] Targeted role/compat/diagnostic hardening regressions pass after reviewer suggestions.
- [x] Affected replay/dashboard suite passes.
- [x] Real dashboard route AppTest smoke passes with role-aware table assertions.
- [x] SAW Implementer and Reviewer A/B/C passes complete.

## Latest Addendum - Optimizer History Diagnostics Split

- [x] Backend fail-closed `insufficient_history` semantics remain unchanged.
- [x] Missing local history is counted separately from stale local endpoints.
- [x] Universe Audit visible metrics include `Missing History`.
- [x] Universe Audit visible metrics include `Stale Endpoint`.
- [x] Universe Audit table includes `Latest Price Date`.
- [x] Allocation explanation uses split price-readiness labels.
- [x] Focused backend/UI regressions pass.
- [ ] Stale local price endpoint repair remains a separate data follow-up.
- [ ] Pre-2025 Rule100 candidate/decision artifact rebuild remains a separate backend/data follow-up.

## Latest Addendum - Dashboard Replay Aux Weight Semantics + Stacked Timeline

- [x] Event/decision context rows carry replay-derived `target_weight`.
- [x] Original auxiliary event/decision weight is preserved as `audit_weight`.
- [x] Saved-artifact context rows are aligned to replay target weights before render.
- [x] Transitional backend context rows are aligned to replay target weights before render.
- [x] Strategy Replay Timeline renders stacked step-area allocation from replay `target_weight`.
- [x] Strategy Replay Timeline has an executable Plotly trace regression for stacked `hv` allocation areas.
- [x] Timeline remains display-only and does not feed Portfolio Performance.
- [x] Partial event rows missing `action` render as no trade events instead of crashing.
- [x] Partial latest snapshot rows missing display columns render unavailable instead of crashing.
- [x] Focused compile passes.
- [x] Targeted aux/timeline/fail-soft regressions pass.
- [x] Affected backend replay suite passes.
- [x] Affected frontend replay suite passes.
- [ ] Backend producers emitting `dashboard_cache_signature` for production saved-artifact UI hits remains a coordination follow-up.

## Latest Addendum - Dashboard Replay Horizon-Aware Asset Universe Fix

- [x] Current allocation still validates against signed `PortfolioReplaySelection`.
- [x] Dashboard replay request assets include current signed assets.
- [x] Dashboard replay request assets include mapped ENTER/EXIT context tickers inside the selected replay window.
- [x] Dashboard replay request assets include mapped BUY/SELL decision tickers inside the selected replay window.
- [x] Rule100 replay request assets can include mapped Rule100 history tickers inside the selected replay window.
- [x] Dashboard `allocation_assets` remain current signed assets and drive selected PIT price loading.
- [x] Coverage-plan unavailable row emission is filtered to allocation assets before backend replay construction.
- [x] History-only horizon assets are added as zero-weight `context_only` rows after backend bundle construction.
- [x] Replay cache signatures distinguish widened `replay_assets` from current-only `allocation_assets`.
- [x] `_normalize_context_frame(...)` remains strict and is not loosened to display non-replay tickers.
- [x] Regression proves MU BUY/SELL rows stay in the bundle decision context while MU is not a latest positive-weight holding.
- [x] Focused compile passes.
- [x] Focused Portfolio/YTD dashboard test file passes.
- [x] Optimizer/replay follow-up tests pass.
- [ ] Durable saved-artifact horizon-aware superset/subset policy remains a future backend/dashboard coordination follow-up.

## Latest Addendum - Replay Selected Price Loading + MU/SNDK Eligibility Trace

- [x] Batched replay loader builds full-window `r3000_pit` membership index before price loading.
- [x] Batched replay loader accepts `selected_permnos` and limits price/return reads to selected PIT members.
- [x] Batched replay metadata records `pit_membership_proof = "full_window_membership_index"`.
- [x] Dashboard passes signed numeric replay assets into the batched loader.
- [x] Dashboard still filters replay inputs to signed replay assets before backend replay execution.
- [x] MU/SNDK diagnostic is separate from dashboard replay request construction.
- [x] MU/SNDK diagnostic answers pinned universe, ticker-map, PIT membership, local price/return rows, Rule100 history, sizing/current-hold state, and latest gate.
- [x] MU/SNDK local price/return diagnostics reject non-finite `total_ret` rows.
- [x] Executable dashboard regression proves selected numeric replay assets are passed into the batched loader while non-selected PIT members stay out of the raw price load.
- [x] Local evidence JSON records selected-loader metadata and MU/SNDK trace result.
- [x] Focused compile passes.
- [x] Targeted selected-loader/source/trace regressions pass.
- [x] Broader affected suite passes with 112 tests.
- [ ] Separate Strategy/Data remediation for MU/SNDK Rule100 history/candidate-frame gaps remains optional follow-up.

## Latest Addendum - Dashboard Replay Horizon Superset Cache Fix

- [x] `_ensure_daily_portfolio_replay_context(...)` checks existing daily replay cache before entering the build spinner path.
- [x] In-session superset reuse ignores only `replay_dates` while requiring method, cap, controls, signed assets, sampling, and data signature to match.
- [x] Exact cache matches still prove actual replay rows cover requested dates.
- [x] Superset reuse proves requested dates are present in both `context.replay_dates` and `replay_df["date"]`.
- [x] Reused contexts are scoped to the selected horizon before rendering allocation/performance/timeline/events/decisions.
- [x] Saved replay artifacts still require exact `dashboard_cache_signature`.
- [x] Focused compile passes.
- [x] Targeted superset-cache regressions pass.
- [x] Focused Portfolio/YTD dashboard test file passes.
- [x] Optimizer/replay coverage follow-up tests pass.
- [ ] Durable saved-artifact superset/subset policy remains a future backend/dashboard coordination follow-up.

## Latest Addendum - Max Replay Timeline Sampling Fix

- [x] Max-window Strategy Replay timeline sampling does not call `Series.normalize()`.
- [x] Weekly grouped keep-dates normalize through the pandas Series `.dt` accessor.
- [x] The final daily replay date is retained in the sampled timeline.
- [x] Timeline sampling remains display-only from daily replay rows.
- [x] Focused compile passes.
- [x] Targeted max-window sampler regression passes.
- [x] Focused Portfolio/YTD dashboard test file passes.
- [ ] Backend producers emitting `dashboard_cache_signature` for production saved-artifact UI hits remains a coordination follow-up.

## Latest Addendum - Portfolio Replay Selection Identity Hardening

- [x] `PortfolioReplaySelection` exists as the explicit replay-universe handoff.
- [x] Selection signature binds method, max-weight, risk-free rate, typed replay assets, current price-frame identity, and selected price content hash.
- [x] Dashboard replay cache signatures distinguish integer and string asset IDs.
- [x] Dashboard replay request construction validates signed selection before replay build/read.
- [x] Missing signed selection fails closed with `portfolio_replay_selection_unavailable`.
- [x] Stale/mismatched signed selection clears replay selection and replay/YTD caches.
- [x] Optimizer builder errors clear replay selection and replay/YTD caches.
- [x] Runtime replay request no longer reads `optimizer_universe`.
- [x] Runtime replay request no longer falls back to first 10 price columns.
- [x] Focused compile passes.
- [x] Focused replay-selection/advisory regressions pass.
- [x] Focused optimizer-selection AppTests pass.
- [ ] Backend producer ownership for aux event/decision rows remains a follow-up.

## Latest Addendum - Portfolio Single-Source Replay Page

- [x] Portfolio page builds one daily `DashboardReplayContext` before replay-facing surfaces render.
- [x] Top allocation display uses latest daily replay snapshot.
- [x] Optimizer panel is controls-only in the Portfolio single-source page flow.
- [x] Portfolio Performance consumes daily replay `portfolio_return`.
- [x] Portfolio Performance refuses non-daily replay.
- [x] Portfolio Performance does not fall back to optimizer weights, local/live weighted price paths, or equal-weight local performance.
- [x] Strategy Replay Timeline sampling is display-only from daily replay rows.
- [x] ENTER/EXIT Events uses the selected Portfolio horizon.
- [x] Duplicate Trade Event Log table is removed.
- [x] Latest Buys/Sells is derived from `bundle.decision_rows` / Buy/Sell Decision Log.
- [x] Render-path source guard rejects direct JSONL lifecycle/trade reads outside the bundle-building boundary.
- [x] Focused compile passes.
- [x] Focused Portfolio/replay/optimizer suite passes with 178 tests.
- [ ] SAW reviewer gate remains pending for implementation closure.

## Latest Addendum - Saved Artifact Single-Source Aux Surface Fix

- [x] Saved-artifact adapter preserves artifact event rows exactly, including empty frames.
- [x] Saved-artifact adapter preserves artifact decision rows exactly, including empty frames.
- [x] Saved artifacts with daily portfolio rows but empty event/decision rows do not backfill from separately loaded dashboard fallback frames.
- [x] Regression covers non-empty fallback event/decision frames while saved artifact aux frames remain empty.
- [x] Focused saved-artifact regression passes.
- [x] Focused frontend pytest suite passes with 106 tests.
- [x] Frontend/UI SAW report exists at `docs/saw_reports/saw_frontend_ui_saved_replay_source_selector_20260514.md`.
- [ ] Backend producers emitting `dashboard_cache_signature` for production saved-artifact UI hits remains a coordination follow-up.

## Latest Addendum - Backend Replay Reader Identity Hardening

- [x] Manifest-level `run_id` must be a non-empty string after trimming.
- [x] Manifest-level `source_id` must be a non-empty string after trimming.
- [x] Manifest-level `method_id` must be a non-empty string after trimming.
- [x] Blank manifest identity is rejected before optional caller expected `run_id` / `source_id` checks.
- [x] Regression covers matching blank manifest and parquet identity with no expected IDs supplied by the caller.
- [x] Valid saved artifact reads remain accepted.
- [x] Focused compile passes.
- [x] Focused replay artifact/strategy/coverage suite passes with 79 tests and durations under budget.
- [x] Backend SAW report artifact exists at `docs/saw_reports/saw_backend_replay_reader_identity_hardening_20260514.md`.
- [ ] Backend producers emitting `dashboard_cache_signature` for production saved-artifact UI hits remains a coordination follow-up.

## Latest Addendum - Frontend/UI Saved Replay Source Selector

- [x] Pure dashboard replay request construction is extracted from `_build_dashboard_strategy_replay_context(...)`.
- [x] Saved artifact read path uses backend `read_selected_method_replay_artifact(...)`.
- [x] Saved artifact UI consumption requires exact `dashboard_cache_signature`.
- [x] Dashboard cache signature binds method, max-weight cap, controls, assets, replay dates, sampling, and dashboard data signature.
- [x] Valid saved artifact maps to `DashboardReplayContext.source_mode = "saved_artifact"`.
- [x] Transitional backend build remains available only as labeled fallback when allowed.
- [x] Unavailable/stale/over-budget saved artifacts can return unavailable without rebuilding when fallback is disabled.
- [x] Stale saved artifact clears replay/YTD latest weights and cached replay context.
- [x] YTD latest weights, latest snapshot, Strategy Replay rows, ENTER/EXIT annotations, and Buy/Sell Decision Log consume one `DashboardReplayContext`.
- [x] `_render_strategy_replay_section()` does not directly call `read_lifecycle_log()`.
- [x] `_render_strategy_replay_section()` does not directly read `data/portfolio_lifecycle_buy_sell_log.jsonl`.
- [x] Executable saved-artifact context test asserts replay rows, latest snapshot, event rows, decision rows, source mode, and cache signature.
- [x] Focused compile passes.
- [x] Requested focused frontend pytest suite passes.
- [ ] Backend producers emitting `dashboard_cache_signature` for production saved-artifact UI hits remains a coordination follow-up.

## Latest Addendum - Saved Replay Artifact Reader + Budget

- [x] Saved selected-method replay artifact reader exists.
- [x] Reader validates parquet and manifest as one bundle.
- [x] Reader validates `run_id`, `source_id`, `method_id`, `artifact_type`, row counts, status counts, date window, input signatures, timing, and schema.
- [x] Reader rejects stale method context.
- [x] Reader rejects stale controls context.
- [x] Reader rejects same-shape/date Rule100 candidate-frame content drift.
- [x] Reader rejects stale replay date/window context.
- [x] Reader rejects stale input signatures.
- [x] Reader rejects stale source file signatures when supplied.
- [x] Reader rejects schema and manifest field drift.
- [x] Reader rejects null/blank parquet identity fields for run id, source id, artifact scope, method, and row type.
- [x] Reader rejects malformed timing payloads.
- [x] Manifest/parquet row/status/date-window mismatches fail closed.
- [x] `ReplayBudgetPolicy` exists with cold-start, rerun/cache, max rows, max dates, and max elapsed fields.
- [x] Saved reads enforce row/date/elapsed/cache budgets.
- [x] Budget-wrapped builds enforce cold-start/row/date/elapsed budgets.
- [x] Over-budget reads/builds return unavailable typed results with empty replay output.
- [x] Existing `build_selected_method_replay(...)` semantics and `REPLAY_COLUMNS` are preserved.
- [x] Selected-method output CLI exposes budget row/date/elapsed flags and uses the budget wrapper.
- [x] Focused compile passes.
- [x] Focused replay artifact/strategy/coverage suite passes with durations under budget.
- [ ] Frontend/dashboard saved-reader consumption remains a separate coordination slice.

## Latest Addendum - Overlay Overlap Anchor Fix

- [x] `scale_live_overlay_to_local(...)` has no public permissive no-overlap evidence flag.
- [x] Selected-price live overlays require same-column local/live overlap.
- [x] Selected no-overlap stale assets are dropped before optimizer evidence.
- [x] Benchmark live overlays require same-ticker local/live overlap.
- [x] Benchmark no-overlap stale tickers are dropped while fresh peers remain available.
- [x] Focused affected stale-data suite passes.
- [x] SAW Implementer and Reviewer A/B/C passes complete.

## Latest Addendum - Portfolio Market-Data Freshness Endpoint Cache

- [x] `PriceEndpointFreshness` exists as a reusable endpoint snapshot.
- [x] `build_price_endpoint_freshness(...)` computes per-column endpoints and required endpoint in one chunked pass.
- [x] Dashboard computes one cached snapshot for loaded `prices_wide`.
- [x] Snapshot cache key includes unified data source signatures, loader arguments, and matrix shape.
- [x] Portfolio YTD uses the cached required endpoint instead of rescanning all columns.
- [x] Optimizer default ordering reuses the supplied per-column endpoints.
- [x] Optimizer selected-price prep reuses the supplied required endpoint.
- [x] Optimizer universe construction reuses the supplied snapshot for endpoint checks.
- [x] Direct callers without a supplied snapshot build one fallback snapshot.
- [x] Weighted portfolio YTD fails closed when live fallback omits a nonzero weighted asset.
- [x] Replay latest weights are signature-bound to current method/cap/assets/data before YTD can reuse them.
- [x] Cached full replay/YTD contexts are signature-bound before Portfolio Performance can reuse them.
- [x] Failed or non-ready replay contexts clear stale replay/YTD session weights.
- [x] Focused correctness regressions pass.
- [x] Actual local performance probe records endpoint match and reduced scan cost.
- [x] Reviewer A targeted recheck passes after weighted-YTD reconciliation.
- [ ] Reviewer B second targeted recheck passes after full-context signature reconciliation.

## Latest Addendum - Portfolio Market-Data Freshness Fail-Closed Fix

- [x] Per-column price endpoint helper exists.
- [x] Generic endpoint/tolerance predicate is centralized in `core.data_orchestrator`.
- [x] `strategies.portfolio_universe` imports shared endpoint helpers and passes policy tolerance explicitly.
- [x] Source guard rejects private endpoint/tolerance helper clones in `strategies.portfolio_universe`.
- [x] Price-frame freshness filtering keeps only columns that reach the required endpoint.
- [x] Benchmark YTD drops stale benchmark columns that cannot be refreshed.
- [x] Benchmark YTD reports a common endpoint for remaining benchmark curves.
- [x] Portfolio YTD local fallback returns unavailable when a nonzero weighted leg is stale.
- [x] Optimizer selected-price prep passes the global price endpoint into live-overlay stitching.
- [x] Optimizer selected-price prep drops stale selected assets that cannot be refreshed.
- [x] Optimizer selected-price overlay requires same-column local/live overlap before treating live rows as allocation evidence.
- [x] Scaled overlays require same-column local/live overlap; no permissive no-overlap evidence mode remains.
- [x] Optimizer default ordering demotes stale endpoint assets before trailing-return ranking.
- [x] Optimizer universe eligibility checks endpoint freshness in addition to history observation count.
- [x] Focused stale-data regressions pass.
- [x] Broader affected dashboard/replay suite passes.
- [x] Formal SAW Implementer and Reviewer A/B/C rerun passes; governance PASS is claimed for this endpoint-centralization round.

## Latest Addendum - Dashboard Backend Bundle Integration Verification

- [x] Dashboard consumes backend `build_selected_method_replay(...)` through `_build_dashboard_strategy_replay_context(...)`.
- [x] Dashboard backend-bundle call uses a per-date PIT `input_loader` backed by `load_strategy_replay_inputs(..., end_date=as_of_date, universe_mode="r3000_pit")`.
- [x] Dashboard Strategy Replay rows, latest snapshot, ENTER/EXIT annotations, Buy/Sell Decision Log rows, and YTD latest-weight preference share `DashboardReplayContext`.
- [x] Source-guard tests prove the dashboard context calls `build_selected_method_replay(...)` and does not pass raw `prices_wide` replay frames.
- [x] Focused replay/dashboard suite passes.
- [x] Full repository pytest passes.
- [x] Runtime smoke passes for `/portfolio-and-allocation` on a fresh Streamlit process.
- [x] No promotion claim is made; same-window/same-cost/same-engine baseline delta evidence remains required before any future promotion claim.
- [ ] Saved artifact-reader consumption and explicit cold-start/rerun performance budget remain future architecture work.

## Latest Addendum - Replay Coverage Contract Audit Fix

- [x] Replay metadata writes contiguous `coverage_segments`.
- [x] Uncovered replay rows preserve specific `input_unavailable:<coverage_reason>` values.
- [x] Adapter fallback metadata includes coverage warnings for pre-coverage replay rows.
- [x] Uncovered-date replay emission is batched before performance attachment.
- [x] Duplicate shadowed coverage/perf test definitions are removed.
- [x] Row-heavy `no_priced_members` unavailable windows stay under the daily-scale budget with explicit per-member rows.
- [x] Replay performance aligns allocation-date weights to next tradable returns, not same-date returns.
- [x] Loader-based replay performance is recomputed once after combined output so portfolio equity is run-level continuous.
- [x] Tiny PIT replay frames avoid stack/merge performance attachment overhead.
- [x] Bound-feasible inverse-volatility targets skip SLSQP with diagnostics.
- [x] Context bootstrap selects replay-audit current truth instead of the older Rule100/YTD handover.
- [x] Context validation fails if the selected current truth packet drifts after bootstrap generation.
- [x] Focused replay coverage suite passes.
- [x] Affected replay/optimizer suite passes.
- [x] Full pytest passes.
- [x] Formal SAW Implementer and Reviewer A/B/C rechecks pass.
- [x] Dashboard consumes backend `build_selected_method_replay(...)` through the transitional dashboard bundle builder.
- [x] Runtime smoke passes for phase-close proof on `/portfolio-and-allocation`.

## Latest Addendum - Selected-Method Replay Source Evidence Handoff

- [x] Backend `build_selected_method_replay(...)` bundle API exists.
- [x] Backend replay bundle uses `build_strategy_replay(...)` as the shared target-weight frame source.
- [x] Rule of 100 and optimizer methods share the `REPLAY_COLUMNS` schema.
- [x] Replay output includes a `CASH` row per replay date.
- [x] Replay output includes `asset_return`, `weight_for_return`, `return_contribution`, `portfolio_return`, and `portfolio_equity`.
- [x] Backend event annotation and decision contexts filter to replay window/method/tickers or return explicit empty status/reason.
- [x] Dashboard `DashboardReplayContext` feeds Strategy Replay rows, latest snapshot, ENTER/EXIT annotations, and Buy/Sell Decision Log rows.
- [x] Portfolio Performance primes latest selected-method replay weights before legacy optimizer fallback.
- [x] Timeframe/PIT rule is documented: UI horizons do not weaken per-date PIT loading with `end_date=as_of_date` and `universe_mode="r3000_pit"`.
- [x] Latest-trades-default UX rule is documented: Buy/Sell Decision Log sorts latest first and remains replay-audit-only.
- [x] Durable saved replay-output artifact/run id is implemented for selected-method replay output.
- [x] Saved replay-output artifact writes parquet rows plus manifest with run id, method id, source id, input signatures, date window, row/status counts, and timing.
- [x] Selected-method replay artifact path is confined to `data/runtime_cache/strategy_replay` for repo data writes.
- [x] Selected-method replay artifact parquet+manifest promotion is rollback-safe; manifest promotion failure cannot leave orphan parquet evidence.
- [x] Focused backend replay suite passes.
- [x] Focused dashboard replay/YTD/optimizer/lifecycle suite passes.
- [x] Dashboard consumes backend `build_selected_method_replay(...)` end to end through the transitional dashboard context builder rather than a dashboard-local direct `build_strategy_replay(...)` call.
- [x] Full repository pytest and runtime smoke pass for phase-close proof.
- [x] No promotion claim is made; same-window/same-cost/same-engine baseline delta evidence remains required before any future promotion claim.

## Latest Addendum - Frontend/UI Shared Replay Bundle

- [x] Dashboard has one selected-method `DashboardReplayContext` for Strategy Replay surfaces.
- [x] Strategy Replay latest snapshot reads from `DashboardReplayContext.latest_snapshot`.
- [x] Portfolio YTD primes and prefers the latest selected-method replay snapshot before legacy optimizer fallback.
- [x] ENTER/EXIT annotations are supplied by replay context, not direct calls in `_render_strategy_replay_section()`.
- [x] Buy/Sell Decision Log is supplied by replay context, not direct JSONL reads in `_render_strategy_replay_section()`.
- [x] Cheap Buy/Sell audit display remains before heavy full replay build.
- [x] Source-guard tests prove no direct split-source calls remain in the main replay render path.
- [x] Focused dashboard/optimizer replay suite passes.
- [x] Durable backend replay-output artifact/run id is implemented.

## Latest Addendum - Urgent Ultra-Modular Replay Architecture Enforcement

- [x] Docs state the non-negotiable invariant: one selected-method replay run/source feeds YTD, current allocation/latest snapshot, Strategy Replay, ENTER/EXIT annotations, Buy/Sell Decision Log, and saved evidence.
- [x] Docs state that independent recomputation, stale allocation-state reuse, separate overlay artifacts, and separate decision tapes cannot be treated as the selected-method replay source.
- [x] Docs distinguish the architecture goal from temporary transitional bridges.
- [x] Docs state transitional bridges must be labeled, bounded, non-canonical, and forbidden from becoming a second replay stack.
- [x] Guardrails include no future-data leakage.
- [x] Guardrails include no stale-data carry-forward.
- [x] Guardrails include no fake improvements without same-window/same-cost/same-engine baseline deltas and saved evidence.
- [x] Guardrails include no overfitting or unchecked promotion.
- [x] Guardrails include no broker/live trading.
- [x] Guardrails include no alerts, rankings, recommendations, candidate scoring, or autonomous capital allocation.
- [x] Shared replay source implemented with one run/artifact identifier per selected method.
- [ ] Selected-method adapters use the shared replay source for all in-scope methods.
- [ ] Shared YTD/performance consumes shared daily portfolio output.
- [ ] Current allocation/latest snapshot consumes the same latest daily portfolio row used by YTD.
- [ ] Strategy Replay rows and ENTER/EXIT annotations consume the shared event/annotation source.
- [ ] Buy/Sell Decision Log consumes the same shared event/annotation source.
- [x] Saved evidence artifact records run id, method id, input signatures, date window, output row counts, status counts, and timing.
- [ ] Performance budget documented and enforced for cold-start replay, rerun/cache path, max rows/dates, and fail-closed timeout behavior.
- [x] SAW-style report exists for the docs-only enforcement round.
- [x] This Worker 3 round edits docs only and no code files.

## Latest Addendum - Visible Rule100 / QQQ / Buy-Sell Replay Audit

- [x] Default Portfolio Optimizer method is `Rule of 100`.
- [x] Default optimizer asset ordering uses trailing 1-year return rather than YTD.
- [x] Backend benchmark builder returns both SPY and QQQ for current YTD display.
- [x] Runtime browser DOM shows SPY and QQQ metrics together.
- [x] Buy/Sell Decision Log is visible before heavy forward-walk replay output.
- [x] Buy/Sell Decision Log is labeled replay audit only, not live orders or trade signals.
- [x] Focused YTD/optimizer/portfolio/lifecycle/policy timeline tests pass.
- [x] Context packet validation passes.
- [ ] Full YTD forward-walk replay cold-start optimization completed.

## Latest Addendum - Urgent Ultra-Modular Replay Architecture Milestone Note

- [x] Current focused patch is documented as visible Portfolio & Allocation QQQ/YTD/default-method/Rule100 parity work.
- [x] Larger urgent ultra-modular replay architecture milestone is documented as separate next-step work.
- [x] Milestone note states the loop is endless AI-assisted research evidence generation, not unchecked optimization.
- [x] Target contract names one replay engine.
- [x] Target contract names one strategy plug-in contract.
- [x] Target contract names one daily portfolio output format.
- [x] Target contract names one event/annotation format.
- [x] Target contract names one YTD/performance path.
- [x] Target contract names one saved evidence artifact.
- [x] Guardrails include no future-data leakage.
- [x] Guardrails include stale data handling / fail-closed behavior.
- [x] Guardrails include overfitting controls.
- [x] Guardrails include fake improvement rejection.
- [x] Guardrails include no broker/live trading.
- [x] Rule100 visible sizing fixes remain acceptance tests.
- [x] QQQ/YTD stale-overlay fixes remain acceptance tests.
- [x] Planner/bridge next step points to the modular replay milestone after QQQ/default-method visible fixes.
- [x] This architecture note makes no code changes.

## Latest Addendum - Rule100 Dynamic UI/Replay Sizing + Benchmark Stale Overlay

- [x] `Rule100SoftmaxConfig()` audit defaults remain `gross_budget_per_name=0.10` and `max_single_name_weight=0.15`.
- [x] `rule100_config_from_max_weight(max_weight)` exists.
- [x] Dynamic Rule100 UI/replay config sets `gross_budget_per_name=max_weight`.
- [x] Dynamic Rule100 UI/replay config sets `max_single_name_weight=max_weight`.
- [x] Direct Rule100 UI path passes `controls.max_weight` into softmax sizing.
- [x] Strategy Replay Rule100 path uses the same dynamic config as direct UI.
- [x] One eligible Rule100 name at 35% can target 35%.
- [x] Two equal eligible Rule100 names at 35% target 35%/35%/30% cash.
- [x] Direct Rule100 UI state and Strategy Replay agree for the same candidate frame and cap.
- [x] Frozen audit default still produces 10%/10%/80% cash for two equal names.
- [x] Benchmark freshness is evaluated per ticker.
- [x] Stale/missing QQQ attempts live overlay while fresh local SPY remains local.
- [x] Stale QQQ does not forward-fill into a visible fresh curve when live overlay returns empty.
- [x] Dashboard benchmark source can report `local+live_overlay`.
- [x] Focused Rule100/replay/YTD/AppTest suite passes.
- [x] Broader affected replay/data/dashboard/lifecycle suite passes.
- [x] Full pytest passes.
- [x] Streamlit readiness smoke passes.
- [x] Independent SAW subagent Implementer and Reviewer A/B/C passes complete for PASS governance closure.

## Latest Addendum - Data/PIT Strategy Replay Hardening + UI Wiring

- [x] `build_strategy_replay_cache_signature(...)` defaults to `universe_mode="r3000_pit"`.
- [x] `build_strategy_replay_cache_signature(...)` rejects non-`r3000_pit` universe modes.
- [x] `load_strategy_replay_inputs(...)` rejects non-`r3000_pit` universe modes.
- [x] `write_strategy_replay_artifact_atomic(...)` rejects repo `data/` output paths outside `data/runtime_cache/strategy_replay`.
- [x] `write_strategy_replay_artifact_atomic(...)` rejects `cache_dir=data/processed`.
- [x] Dashboard Strategy Replay loads per-date `StrategyReplayInputs`.
- [x] Dashboard Strategy Replay passes `prices=replay_inputs` to `build_strategy_replay(...)`.
- [x] Empty PIT selected-asset slices render explicit cash-closed rows instead of dropping dates.
- [x] Per-date PIT input failures render explicit cash-closed rows instead of aborting the full replay section.
- [x] Focused replay/data/dashboard suite passes.
- [x] Broader affected replay/portfolio/lifecycle/DASH suite passes.
- [ ] Independent SAW subagent Implementer and Reviewer A/B/C passes complete for PASS governance closure.

## Latest Addendum - Rule100 Softmax v1.1 Contract Fix

- [x] `scripts/rule100_softmax_v1_1_audit.py` active artifact contract is comparison CSV + summary JSON only.
- [x] `data/processed/rule100_softmax_v1_1_history.csv` is absent after audit refresh.
- [x] Stale v1.1 history bytes are retained only as `data/processed/rule100_softmax_v1_1_history.retired.csv`.
- [x] `factor_present_count` and `factor_positive_count` count approved factor groups, not raw columns.
- [x] `capital_cycle_score` and `quality_composite` cannot double-count the capital-discipline group.
- [x] Missing v1.1 factor strength shrinks toward neutral `0.50` by coverage.
- [x] Real dashboard `AppTest.from_file("dashboard.py")` captures the Policy Target Timeline TSM 2026-05-11 regression.
- [x] Focused v1.1, v1 history, lifecycle renderer, and route tests pass.
- [x] Full pytest passes after the v1.1 contract fix.
- [x] Independent SAW subagent Implementer and Reviewer A/B/C passes complete for PASS governance closure.

## Latest Addendum - Rule of 100 Method Label

- [x] `data/processed/rule100_softmax_v1_history.csv` exists as a derived v1 history overlay.
- [x] Historical overlay preserves immutable lifecycle `event_weight`.
- [x] Historical overlay writes `softmax_v1_target_weight` and `softmax_v1_cash_residual`.
- [x] Position Lifecycle Replay transaction log labels Event Weight separately from Softmax v1 Target.
- [x] Regression proves 2026-05-11 TSM remains event weight 10% but softmax v1 target is 0% and cash is 80%.
- [x] Focused softmax/history/lifecycle renderer tests pass.
- [ ] Independent SAW subagent Implementer and Reviewer A/B/C passes complete for PASS governance closure.

## Previous Addendum - Rule of 100 Method Label

- [x] `OptimizationMethod.RULE_OF_100` exists.
- [x] Dropdown label is exactly `Rule of 100`.
- [x] `Rule of 100` is included in `OPTIMIZATION_METHOD_OPTIONS`.
- [x] `Rule of 100` is not a mean-variance method.
- [x] Selecting `Rule of 100` routes to lifecycle holdings plus residual cash.
- [x] Empty lifecycle state under `Rule of 100` renders cash-only session state.
- [x] Focused compile passes.
- [x] Focused optimizer view and portfolio universe tests pass.
- [x] Runtime manual audit on port 8509 confirms visible dropdown label after restart.
- [ ] Independent SAW subagent Implementer and Reviewer A/B/C passes complete for PASS governance closure.

## Latest Addendum - Rule100 Softmax v1 Audit

- [x] `strategies/rule100_softmax.py` exists and exposes pure softmax v1 sizing helpers.
- [x] `kelly_ablation_weights(...)` stays comparator-only and does not become a second stack.
- [x] `scripts/rule100_softmax_v1_audit.py` exists and writes versioned summary/comparison/sample/cash artifacts.
- [x] `Rule of 100` UI writes `portfolio_allocation_state.source = rule100_softmax_v1`.
- [x] Explicit `Rule of 100` UI target weights come from softmax v1 rather than lifecycle `last_weight`.
- [x] Regression proves TSM drops from stale 10% current weight to 0% target and residual cash rises to 80%.
- [x] Regression proves all-ineligible Rule100 candidate state renders cash-only instead of stale lifecycle weights.
- [x] Focused softmax/Kelly/audit harness tests pass.
- [x] Shared audit script runs successfully on the current PIT lifecycle state.
- [x] Full pytest completed after the audit harness round.
- [ ] Independent SAW subagent Implementer and Reviewer A/B/C passes complete for PASS governance closure.

## Latest Addendum - Rule100 Lifecycle Policy v0

- [x] `Rule100State` adapter exists and exposes demand/supply/pricing/margin with proxy provenance.
- [x] v0 BUY requires Rule100 3/4 confirmation, technical entry zone, and 3-day confirmation.
- [x] v0 HOLD tolerates one weak factor with 2/4 positives.
- [x] v0 TIGHTEN emits audit-only lifecycle rows for <2/4 factor state.
- [x] v0 TRIM emits audit-only lifecycle rows for `0.12 < dist_sma20 <= 0.20`.
- [x] v0 EXIT requires hard stop `dist_sma20 > 0.20` or confirmed trend veto.
- [x] v0 entry sizing uses `min(0.10 + 0.025 * max(0, factor_positive_count - 3), 0.15)`.
- [x] Runtime lifecycle log promoted to v0 and has 29 events with open AMAT/LRCX/TSM.
- [x] Decision audit compares v0 against the 33-event baseline.
- [x] Focused Rule100/lifecycle/portfolio tests pass.
- [ ] Independent SAW subagent Implementer and Reviewer A/B/C passes complete for PASS governance closure.

## Latest Addendum - Lifecycle Decision Export

- [x] `export_lifecycle_decision_log(...)` exports PIT daily decision rows without mutating the lifecycle event log.
- [x] Export rows include `BUY`/`SELL`/`HOLD`/`NO_ACTION`, `primary_reason`, `reason_codes`, gate state, streaks, hold days, cooldown, and Rule-of-100 proxy fields.
- [x] Compact buy/sell JSONL exists at `data/portfolio_lifecycle_buy_sell_log.jsonl`.
- [x] Full decision JSONL exists at `data/portfolio_lifecycle_decision_log.jsonl`.
- [x] Audit summary exists at `docs/context/e2e_evidence/lifecycle_decision_audit_20260512.json`.
- [x] Export buy/sell rows match `run_pit_replay(...)` emitted ENTER/EXIT events in regression coverage.
- [x] Export run shows 5424 decision rows, 33 BUY/SELL rows, 18 BUY, 15 SELL, and open AMAT/LRCX/TSM.
- [x] Focused export tests pass.
- [ ] Independent SAW subagent Implementer and Reviewer A/B/C passes complete for PASS governance closure.

## Latest Addendum - Lifecycle Replay Churn + Weight Policy

- [x] `scripts.pit_lifecycle_replay.replay_entry_weight()` defaults to `0.10`.
- [x] ENTER weights no longer use `1 / len(replay_tickers)`.
- [x] `lifecycle_factor_confirmation(...)` exists and requires at least 3 present and positive PIT vectors.
- [x] ENTER requires a 3-day confirmation streak.
- [x] EXIT requires 20-day minimum hold plus 2-day confirmation unless `dist_sma20 > 0.20`.
- [x] Re-entry cooldown blocks a ticker until 10 calendar days after EXIT.
- [x] Replay CLI accepts `--log-path` and runs from repo root.
- [x] Final lifecycle log has 33 events, all ENTER weights at 0.10, and open AMAT/LRCX/TSM positions.
- [x] Final lifecycle log has no `<=5` day round trips.
- [x] Focused lifecycle/portfolio/YTD test suite passes.
- [x] Full pytest passes.
- [x] Browser smoke completed after reboot on port 8509 for this final replay.
- [x] `UnifiedDataPackage.prices` holds TRI/price levels, not daily returns.
- [x] Portfolio YTD uses local TRI history before live overlay.
- [x] Port 8509 smoke shows Portfolio `+14.25%` and does not show `7645112.18%`.
- [x] SAW report exists and validates for this churn/weight policy round.
- [ ] Independent SAW subagent Implementer and Reviewer A/B/C passes complete for PASS governance closure.

## Latest Addendum - Pinned Strategy Universe Hardening

- [x] `data/universe/pinned_thesis_universe.yml` exists with ≥10 thesis tickers.
- [x] `data/universe/loader.py` raises FileNotFoundError on missing manifest.
- [x] `data/universe/loader.py` raises ValueError on empty/malformed/duplicate entries.
- [x] `data/feature_store.py run_build()` aborts when pinned loader fails (unless `allow_missing_pinned_universe=True`).
- [x] `data/feature_store.py run_build()` unions pinned permnos into feature universe.
- [x] `scripts/pit_lifecycle_replay._default_replay_tickers()` raises on loader failure (no silent fallback).
- [x] `scripts/pit_lifecycle_replay.is_pit_eligible()` is the single shared gate for replay and diagnostics.
- [x] `scripts/pit_lifecycle_replay.diagnose_pinned_exclusions()` reports every pinned ticker with status OK/DATA_BLOCKED/FAILED_GATE.
- [x] All 10 pinned tickers have yahoo_patch coverage from 2025-01-02.
- [x] All 10 pinned tickers have features.parquet rows with non-null price-derived columns.
- [x] 27 regression tests in `tests/test_pinned_universe.py` pass.

## Latest Addendum - Portfolio Lifecycle Current Holds Fix

- [x] `data.portfolio_lifecycle_log.get_open_lifecycle_positions` exists.
- [x] Open lifecycle positions use latest ENTER/EXIT event at or before `as_of`.
- [x] Future-dated lifecycle rows are ignored for current holdings.
- [x] Malformed lifecycle JSONL rows fail closed with a visible error.
- [x] Lifecycle JSONL appends use temp-file replacement instead of direct append.
- [x] Lifecycle sell-all overrides stale JSON position memory.
- [x] `strategies.portfolio_universe.load_current_position_memory` prefers lifecycle replay state when replay evidence exists.
- [x] `build_optimizer_universe` includes open lifecycle holdings as `included_current_hold`.
- [x] Open lifecycle holdings can remain included even when today's scanner row is EXIT/KILL.
- [x] Portfolio Optimizer renders lifecycle holds plus residual cash when there are open holds and no fresh PIT ENTER candidates.
- [x] Portfolio performance session weights preserve residual cash unless weights exceed 100%.
- [x] Live ticker-mapped YTD weights preserve residual cash unless mapped weights exceed 100%.
- [x] Focused compile passes.
- [x] Focused lifecycle/universe/optimizer/YTD tests pass.
- [x] Browser smoke completed for `/portfolio-and-allocation` after this fix.
- [x] Full pytest completed for this focused bug round.
- [x] SAW report exists and validates for this focused bug round.

## Latest Addendum - Dashboard Unified Data Cache Performance Fix

- [x] `dashboard.py::_load_unified_data_cached` exists.
- [x] `_load_unified_data_cached` is decorated with `st.cache_resource`.
- [x] Dashboard unified package load includes `data_signature=build_unified_data_cache_signature(...)`.
- [x] `core.data_orchestrator.build_unified_data_cache_signature` exists.
- [x] Cache signature tracks source parquet path, mtime_ns, and size.
- [x] File add/remove/rewrite changes signature in focused tests.
- [x] Dashboard source guard confirms cached unified load path.
- [x] Focused compile passes.
- [x] Focused data-orchestrator/dashboard tests pass.
- [x] Portfolio YTD and optimizer view regressions pass.
- [x] Streamlit HTTP smoke reaches dashboard with status 200.
- [x] Context validation passes.
- [x] Full pytest completed in this round.
- [x] SAW independent Implementer and Reviewer A/B/C passes completed in this round.
- [x] Stale quick-slice closure evidence reconciled after full pytest.
- [x] `docs/saw_reports/saw_dashboard_unified_data_cache_performance_20260511.md` exists and records SAW PASS.
- [x] SAW closure packet validation passes.
- [x] SAW report block validation passes.

## Latest Addendum - Dashboard Scanner Testability Hardening

- [x] `strategies/scanner.py` exists and owns deterministic scanner math.
- [x] `dashboard.py` preserves yfinance/provider calls and delegates scanner enrichment to `strategies.scanner.enrich_scan_frame`.
- [x] Macro score, breadth, price technicals, cluster, entry/support, tactics, proxy signal, rating, leverage, and scan-frame enrichment have focused tests.
- [x] Non-finite macro and breadth inputs fail closed to unknown/neutral behavior with regression coverage.
- [x] `tests/conftest.py` includes shared price/return/macro/ticker-map fixtures.
- [x] `InvestorCockpitStrategy` quality-cap coverage exists.
- [x] `AdaptiveTrendStrategy` regime transition coverage exists.
- [x] `ProductionConfig` invariant coverage exists.
- [x] `core.etl` temp-directory parquet build coverage exists.
- [x] Process guardrail test still passes.
- [x] Focused affected pytest passes.
- [x] Scoped compile passes.
- [x] Full pytest completed for this scanner hardening addendum.
- [x] SAW Reviewer C final recheck passes after latest invalid credit denominator reconciliation.
- [x] `docs/saw_reports/saw_dashboard_scanner_testability_hardening_20260511.md` records SAW PASS.

## Latest Addendum - Dashboard Architecture Safety Slice

- [x] `utils/process.py` exists and exposes `pid_is_running`.
- [x] Dashboard backtest PID probing delegates to `pid_is_running`.
- [x] Updater, parameter-sweep, release-controller, and phase16 optimizer lock probes delegate through shared helper or compatibility wrappers.
- [x] Source guard test rejects `os.kill(pid, 0)` and `os.kill(int(pid), 0)` in runtime lock callers.
- [x] `dashboard.py::spawn_backtest` does not terminate an unverified PID-file owner.
- [x] Dashboard strategy matrix initialization uses `_build_strategy_matrix` / `_ensure_modular_strategy_state`.
- [x] `dashboard.py::_clean_portfolio_price_frame` delegates to `core.data_orchestrator.clean_price_frame`.
- [x] Focused compile passes.
- [x] Affected focused tests pass.
- [x] HTTP smoke reaches dashboard with status 200.
- [ ] Full pytest completed in this round. It timed out after 304 seconds and requires a longer follow-up window for phase closure.
- [x] SAW independent Implementer and Reviewer A/B/C passes complete.
- [x] Reviewer B High finding on unverified PID termination was fixed and rechecked PASS.

## Latest Addendum - Portfolio Optimizer View Test and Performance Hardening

- [x] `tests/test_optimizer_view.py` exists.
- [x] `tests/test_optimizer_view.py` uses `streamlit.testing.v1.AppTest`.
- [x] Optimizer view renders without Streamlit exceptions in focused AppTest coverage.
- [x] Mean-variance selection and sector-cap controls are exercised in AppTest coverage.
- [x] UI-derived max-weight and risk-free-rate controls are tested through the real SLSQP optimizer path.
- [x] Sector caps remain post-solver soft constraints and are tested as such.
- [x] Recent close display overlays use a display-only Parquet cache in `core/data_orchestrator.py`.
- [x] Cold display-overlay cache misses schedule background refresh and return without synchronous provider blocking.
- [x] Parquet cache writes use temp-file then `os.replace`.
- [x] Overlay scaling cache returns copy-safe dataframes.
- [x] Optimizer runs are cached by method, selected price frame, max-weight, and risk-free-rate.
- [x] Focused optimizer view, optimizer core policy, and DASH-2 tests pass.
- [x] Full pytest passes after implementation.
- [x] Runtime smoke passes for `/portfolio-and-allocation`.
- [x] `docs/saw_reports/saw_portfolio_optimizer_view_perf_hardening_20260511.md` exists and records SAW PASS.
- [x] Independent Implementer and Reviewer A/B/C SAW passes complete.

## Latest Addendum - Portfolio Data Boundary Refactor

- [x] `core/data_orchestrator.py` owns selected-stock display-refresh close extraction.
- [x] `core/data_orchestrator.py` owns local TRI overlay scaling and selected-price stitching.
- [x] `core/data_orchestrator.py` owns `data/backtest_results.json` strategy-metrics parsing.
- [x] `views/optimizer_view.py` does not import yfinance.
- [x] `views/optimizer_view.py` does not parse `data/backtest_results.json` directly.
- [x] `data/providers/legacy_allowlist.py` does not require `views/optimizer_view.py`.
- [x] Partial live overlays merge cell-wise and preserve local TRI values for missing live cells.
- [x] Duplicate local/live anchor dates are deduped before overlay scaling.
- [x] Stale display overlay cache behavior is explicit stale-while-revalidate and display-only.
- [x] Background overlay scheduler submit failures fail soft and clear the inflight key.
- [x] Focused data-orchestrator, dashboard sprint, DASH-2, provider-port, and portfolio regression tests pass.
- [x] Scoped compile passes for touched runtime/test files.

## Latest Addendum - Optimizer Core Structured Diagnostics Implementation

- [x] `strategies/optimizer_diagnostics.py` exists.
- [x] `OptimizerFeasibilityReport`, `OptimizerBoundDiagnostics`, `OptimizerConstraintDiagnostics`, `OptimizerSolverDiagnostics`, and `OptimizerDiagnosticSeverity` exist outside UI code.
- [x] Pre-solver upper-bound infeasibility is rejected without fallback.
- [x] Lower-bound and required-minimum infeasibility diagnostics exist without approving lower-bound allocation policy.
- [x] Equal-weight boundary pressure is reported.
- [x] Active upper and lower bounds are diagnosed directly from weights.
- [x] SLSQP failure reports solver status/message and labels equal-weight fallback as not optimized.
- [x] Optimizer UI includes status, feasibility, active constraints, assets at max cap/lower bound, equal-weight forced, and fallback labels.
- [x] Non-finite diagnostic weights fail closed as errors and cannot be reported as optimized.
- [x] Focused optimizer policy tests pass with no strict xfails.
- [x] Scoped compile passes for optimizer diagnostics, optimizer core, optimizer UI, and dashboard.
- [x] Full pytest passes after SAW reconciliation.
- [x] Browser smoke passes on `/portfolio-and-allocation`.
- [x] `docs/saw_reports/saw_optimizer_core_structured_diagnostics_20260511.md` exists and records SAW PASS.

## Latest Addendum - Optimizer Core Policy Audit

- [x] `docs/architecture/optimizer_core_policy_audit.md` exists.
- [x] `docs/architecture/optimizer_constraints_policy.md` exists.
- [x] `docs/architecture/optimizer_lower_bound_slsqp_policy.md` exists.
- [x] `tests/test_optimizer_core_policy.py` exists.
- [x] `docs/saw_reports/saw_optimizer_core_policy_audit_20260510.md` exists.
- [x] Audit rejects the quarantined lower-bound/SLSQP diff as-is.
- [x] No optimizer implementation changes are made in this audit round.
- [x] Focused optimizer policy tests pass with expected strict xfails for known policy debt.

## Latest Addendum - Portfolio Universe Quarantine Closure

- [x] Dirty `strategies/optimizer.py` lower-bound/SLSQP diff was inspected.
- [x] Dirty optimizer-core diff was saved to `docs/quarantine/optimizer_core_lower_bounds_slsqp_diff_20260510.patch`.
- [x] Quarantine note exists at `docs/quarantine/optimizer_core_lower_bounds_slsqp_diff_note_20260510.md`.
- [x] `strategies/optimizer.py` was reverted to baseline for this closure.
- [x] `git diff -- strategies/optimizer.py` is empty.
- [x] Focused portfolio universe, DASH-2, and DASH-1 tests pass.
- [x] Full pytest passes after quarantine and hygiene repair.
- [x] Scoped compile passes.
- [x] Context validation passes.
- [x] Browser smoke confirms Portfolio Optimizer, Universe Audit, fail-closed no-eligible message, and YTD Performance render on port `8503`.
- [x] SAW closure packet records `ChecksTotal=9`, `ChecksPassed=9`, `ChecksFailed=0`, `Verdict=PASS`.

## Latest Addendum - Portfolio Universe Construction Fix

- [x] `strategies/portfolio_universe.py` exists and owns optimizer universe eligibility.
- [x] `dashboard.py` no longer passes `selected_tickers[:20]` from display-sorted `df_scan` into the optimizer.
- [x] `EXIT`, `KILL`, `AVOID`, and `IGNORE` are excluded by default.
- [x] Generic `WATCH` is research-only by default.
- [x] Missing local ticker mapping is reported.
- [x] Insufficient local price history is reported.
- [x] Max-weight feasibility and equal-weight boundary diagnostics exist.
- [x] Misleading `Auto (Best Sharpe)` label is removed from runtime.
- [x] MU hard floor and conviction mode remain absent.
- [x] Focused portfolio universe and DASH-2 tests pass.
- [x] Scoped compile passes.
- [x] Browser smoke confirms Portfolio Optimizer, Universe Audit, fail-closed no-eligible message, and YTD Performance render on port `8503`.

## Latest Addendum - DASH-2 Portfolio Allocation Runtime Slice

- [x] Portfolio Optimizer renders top-level on `Portfolio & Allocation`.
- [x] Optimizer expander/toggle is removed from the Portfolio page.
- [x] YTD Performance renders below the optimizer.
- [x] Portfolio YTD return uses current optimizer weights when available.
- [x] SPY/QQQ YTD comparison metrics render.
- [x] Selected stock and benchmark prices refresh in-memory for display freshness without canonical writes.
- [x] Focused DASH-2 tests pass.
- [x] DASH-1 navigation regression passes.
- [x] Scoped compile passes.
- [x] Browser check confirms optimizer-before-YTD order and prices through `2026-05-08`.

## Header

- `CHECKLIST_ID`: `20260510-d383-phase65-g8-2-system-scouted-candidate-card`
- `DATE_UTC`: `2026-05-10`
- `SCOPE`: `Phase 65 G8.2 System-Scouted Candidate Card`
- `STATUS`: `current`
- `OWNER`: `PM / Architecture Office`

## Done Criteria

### Artifact Completeness

- [x] `data/candidate_cards/MSFT_supercycle_candidate_card_v0.json` exists.
- [x] `data/candidate_cards/MSFT_supercycle_candidate_card_v0.manifest.json` exists.
- [x] `tests/test_g8_2_system_scouted_candidate_card.py` exists.
- [x] `docs/architecture/g8_2_system_scouted_candidate_card_policy.md` exists.
- [x] `docs/handover/phase65_g82_system_scouted_candidate_card_handover.md` exists.
- [x] `docs/saw_reports/saw_phase65_g8_2_system_scouted_candidate_card_20260510.md` exists after SAW publication.

### Source-Intake Completeness

- [x] Existing `LOCAL_FACTOR_SCOUT` output exists.
- [x] Existing scout output contains exactly one item.
- [x] Existing scout output ticker is `MSFT`.
- [x] MSFT card ticker matches the scout output ticker.
- [x] MSFT card references `data/discovery/local_factor_scout_output_tiny_v0.manifest.json`.
- [x] MSFT card manifest hash matches card bytes.

### Card Completeness

- [x] `candidate_status = candidate_card_only`.
- [x] `discovery_origin = LOCAL_FACTOR_SCOUT`.
- [x] `scout_model_id = LOCAL_FACTOR_EQUAL_WEIGHT_V0`.
- [x] `source_intake_item_id` is present.
- [x] `source_intake_manifest_uri` is present.
- [x] `candidate_card_manifest_uri` is present.
- [x] `primary_alpha` records thesis summary, driver, present evidence, missing evidence, and thesis breakers.
- [x] `secondary_alpha` records relevant modules, observed signal availability, later estimated signals, and provider gaps.
- [x] `state_mapping` forbids action states and direct action jumps.
- [x] `governance` records not validated, not actionable, no score, no rank, no buy/sell signal, no alert, and no broker action.

### Scope Completeness

- [x] No card is created for `DELL`, `AMD`, `LRCX`, `ALB`, or any other user-seeded intake item.
- [x] No new `LOCAL_FACTOR_SCOUT` output is added.
- [x] No factor score is displayed.
- [x] No rank is displayed.
- [x] No buy/sell/hold output is emitted.
- [x] No thesis validation is claimed.
- [x] No actionability is claimed.
- [x] No buying range is claimed.
- [x] No alert or broker action is emitted.
- [x] No dashboard runtime behavior is added.

### Validation Status

- [x] Focused G8.2 tests: PASS.
- [x] G8/G8.1B/G8.2 regression: PASS.
- [x] Scoped compile: PASS.
- [x] Context-builder tests: PASS.
- [x] Context rebuild and validation: PASS.
- [x] SAW report validation: PASS.
- [x] Closure packet validation: PASS.

## Machine-Checkable Rules

```text
.venv\Scripts\python -m pytest tests\test_g8_2_system_scouted_candidate_card.py -q
.venv\Scripts\python -m pytest tests\test_g8_supercycle_candidate_card.py tests\test_g8_1b_pipeline_first_discovery_scout.py tests\test_g8_2_system_scouted_candidate_card.py -q
.venv\Scripts\python -m pytest tests\test_build_context_packet.py -q
.venv\Scripts\python -m py_compile opportunity_engine\candidate_card_schema.py opportunity_engine\candidate_card.py tests\test_g8_2_system_scouted_candidate_card.py
.venv\Scripts\python scripts\build_context_packet.py --validate
```

## Open Risks

- yfinance migration remains future debt.
- S&P sidecar freshness remains stale.
- Reg SHO policy gap remains future work.
- GodView provider, options license, ownership, insider, and market-behavior gaps remain open.
- Dashboard runtime list still contains legacy action-shaped labels; G8.2 does not merge into that runtime surface.
- Factor model validation remains open before any predictive or ranked use.
- Broad dirty worktree and inherited compileall hygiene remain out of scope.

## Latest Addendum - Portfolio Allocation State Split + Route Smoke

- [x] `portfolio_allocation_state` exists and records mode/source/weights/cash_only/latest_price_date.
- [x] Legacy mirrors `optimizer_weights`, `optimizer_cash_only`, and `optimizer_price_latest_date` remain available.
- [x] `Rule of 100` and current-hold replay write explicit replay state instead of blending into optimizer output.
- [x] Portfolio page copy separates optimizer output from replay output.
- [x] `views.page_registry.build_dashboard_navigation(...)` keeps `Portfolio & Allocation` as the default visible page and assigns the explicit `portfolio-and-allocation` url path.
- [x] Focused compile passes for dashboard, page registry, optimizer view, and route/smoke tests.
- [x] Focused dashboard/navigation/optimizer/universe tests pass.
- [x] AppTest smoke for `dashboard.py` with `query_params["page"]="portfolio-and-allocation"` passes without exception and renders Portfolio + current-hold replay output.
