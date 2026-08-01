## 2026-07-21 Round Entry (Observation Is Not Product Value; Mutable Bytes Are Not Evidence)
- Date: 2026-07-21
- Mistake or miss: the E0B repair correctly hardened publication authority, but repeated concurrent writes meant passing tests were not bound to one candidate; generated context and SAW counts drifted; an unreported remote push advanced PR #5 to hosted-green `b7a24d3`; and `e0b_close_eligible` silently conflated a methodologically valid observed comparison with successful decision-value proof.
- Root cause: local worktree state was treated as candidate custody; remote branch movement was not reconciled before planning the reconstruction base; a managed Git worktree was treated as the only clean-checkout mechanism; and the experiment’s evidence-admission predicate was reused as the product-success predicate after causal-overclaim wording was removed.
- Fix applied: classified remote `b7a24d3` as hosted-green C0, required C1 to descend from it in a fresh approved-root clone or standalone checkout, bounded transfer to exactly 15 source files, retained the security repair, deleted the conflated close term without compatibility, separated `comparison_observed_eligible` from `decision_value_disposition`, froze a measurable `IMPROVED` rule with targeted gains and safety non-regression, and added honest `NOT_IMPROVED` publication/falsification coverage.
- Guardrail for next time: fetch and reconcile remote authority before naming a reconstruction base; establish one local and one remote writer; prefer a clean approved-root clone when worktree metadata is broken; freeze candidate bytes before acceptance; regenerate derived truth only after source stabilization; distinguish evidence validity from hypothesis success; publish valid negative/zero evidence; never repeat an experiment merely to obtain a desired sign; push reversible candidate custody early and parallelize hosted proof with independent review.
- Evidence paths: `core/gv_e0b_dv1_contradiction.py`, `scripts/gv_e0b_g08_capture.py`, `tests/gv_fs0_product/test_e0b_dv1_contradiction.py`, `docs/notes.md`, `docs/phase_brief/gv-e0b-dv1-contradiction-brief.md`, and current truth surfaces.

## 2026-07-20 Round Entry (Verified Evidence Must Own Publication Authority)
- Date: 2026-07-20
- Mistake or miss: E0B reloaded and verified `result.json`, but publication still accepted the original comparison plus caller-controlled `close_eligible=True`; public decision/book/certification helpers and a public imported generic publisher allowed the same fixture-publication route to be recomposed after deleting only the wrapper; writable path parameters could also alias and let a successful publication overwrite its own verified result evidence.
- Root cause: verification was treated as a pre-publication check rather than the sole authority-bearing object; Python's module surface was not audited as a composable capability boundary; path-identity uncertainty could fail open; and individually atomic writes were mistaken for a failure-atomic artifact pair.
- Fix applied: removed all official comparison-only E0B build/certification/publication helpers without compatibility; imported the generic publisher privately; made `run_e0b_dv1_case()` the sole official entry; pinned result schema/case/run class; reconstructed the complete embedded comparison from verified sealed records; certified and published only from that reloaded result with exact close `true`, exact integer count `1`, and embedded comparison-hash rationale binding; made path-identity errors fail closed; added pairwise lexical/symlink/hard-link alias rejection; and staged both canonical artifacts before replacement with restoration of both prior paths on either replacement failure.
- Guardrail for next time: every publication gate must identify one verified authority-bearing object and consume only that object; hash validity is insufficient unless identity, types, and all derived projections are reconstructed from primary sealed evidence; every caller-controlled input, evidence, lock, and publication path must be pairwise disjoint before the first write, and uncertainty must block; multi-file canonical outputs require explicit paired commit/rollback semantics rather than individually atomic writes; audit every public helper and imported capability for equivalent composition, not just the top-level wrapper; require a result-bearing hosted gate after any real experiment before merge.
- Evidence paths: `core/gv_e0b_dv1_contradiction.py`, `tests/gv_fs0_product/test_e0b_dv1_contradiction.py`, `docs/phase_brief/gv-e0b-dv1-contradiction-brief.md`, `docs/saw_reports/saw_gv_e0b_publication_authority_20260720.md`.

## 2026-07-20
- Mistake or miss: after staged-seal repair, capture authority still accepted caller timestamps, asserted 60m budget without measurement, treated REAL_HUMAN labels as close evidence, and rehashed summary comparison without replaying complete sealed bodies; V1 nineteen-case gate still framed as default post-G08 path.
- Root cause: authorship strings and self-stamped times were mistaken for observation; close eligibility lived inside comparison summary instead of attestation + full seal replay.
- Fix applied: system-stamped arm start/end + measured 60m budget; session nonce + append-only chain; result embeds complete seals and re-verifies them; human IDs attribution-only; external independent attestation required for close; post-G08 direction = V2 BLOCK-ONLY REAL ADMISSION superseding V1-19.
- Guardrail for next time: never grant close from REAL_HUMAN strings alone; never accept caller timing fields; never display observed count without full seal replay + attestation; do not schedule a second synthetic comparison as default after G08.
- Evidence paths: `core/gv_e0b_dv1_contradiction.py`, `tests/gv_fs0_product/test_e0b_dv1_contradiction.py`, `docs/architecture/top_level_roadmap.md`.

## 2026-07-20
- Mistake or miss: PR #5 repair still hardcoded packet `generated_at`, auto-sealed unsealed loads during comparison, allowed fixture publish to current authority, trusted mutated result fields for observed count, left ~9/100 in active context/roadmap, and omitted the frozen nineteen-case MU entry gate.
- Root cause: seal recompute was treated as sufficient observed truth; chronology/authorship remained self-asserted at compare-time; publication authority was not gated on close eligibility; display trusted payload fields without full re-verify.
- Fix applied: staged capture (baseline→packet with real timestamp→post→rubric→compare); load paths reject unsealed; publish requires e0b_close_eligible; UI/count recompute result+comparison seals; CI path includes core/gv_e0b_dv1_contradiction.py; retire ~9/100 remnants; document nineteen-case gate + post-G08 V2 choice.
- Guardrail for next time: never seal on load for observed paths; never hardcode capture timestamps; never publish fixture comparisons as current portfolio authority; never display observed count without re-verified result hash.
- Evidence paths: `core/gv_e0b_dv1_contradiction.py`, `tests/gv_fs0_product/test_e0b_dv1_contradiction.py`, `.github/workflows/gv-fs0-product.yml`, `docs/architecture/top_level_roadmap.md`.

## 2026-07-19
- Mistake or miss: PR #5 hardcoded baseline/post/rubric in the same module as G08 detection so the “delta” was predetermined; seals not recomputed; comparison only referenced E0A cert; no result.json/decision_packet/Streamlit; roadmap demanded causal improvement and used unofficial maturity scores; context still said finish E0A-R1 after PR #4 merge.
- Root cause: comparison machinery was shipped as decision evidence; endgame “observed within-case” was narrated as causal win; additive/unofficial scores masked zero real comparisons.
- Fix applied: delete hardcoded human/rubric APIs; external seals with recompute; atomic artifacts; E0B:CMP comparison-bound cert; Streamlit/AppTest; fixtures cannot close E0B; retire unofficial decision-value/conjunctive scores for observed-comparison count=0; strip causal-superiority roadmap language.
- Guardrail for next time: never invent baseline/post/rubric in engine code; same real operator for baseline+post and different real reviewer for rubric required for observed count; positive/zero/negative deltas all valid; no stage promotion without real seals.
- Evidence paths: `core/gv_e0b_dv1_contradiction.py`, `tests/gv_fs0_product/test_e0b_dv1_contradiction.py`, `docs/phase_brief/gv-e0b-dv1-contradiction-brief.md`.

## 2026-07-19
- Mistake or miss: treating E0A operable (custody/cert/publish plumbing + hardcoded HOLD_FOR_EVIDENCE→NO_POSITION) as product maturity; additive score (39) masked missing observed comparisons; E0A acquired roadmap weight beyond endgame contribution; risk of auto-canonizing dirty-root cockpit files for path-existence; E0B planned with causal-improvement language that drifts from frozen endgame.
- Root cause: substrate success was narrated as GodView intelligence; single additive score compensated zero baseline-comparison; missing authority refs invited “copy local file” shortcuts; shipment optional framing for decision value.
- Fix applied: reclassify E0A-R1 as hard-capped merge-safety repair tax; bank E0A as substrate only; report observed-comparison count instead of unofficial maturity percentages; provenance-before-track rule; E0B reports observed within-case difference only.
- Guardrail for next time: never promote plumbing to intelligence; never auto-canonize dirty-root authority bytes; close repair gates immediately after smoke; product gates must measure observed comparisons, not fabricated deltas.
- Evidence paths: `docs/phase_brief/gv-e0a-r1-merge-safety-brief.md`, `docs/architecture/top_level_roadmap.md`, `docs/context/planner_packet_current.md`.

## 2026-07-19
- Mistake or miss: terminal E0A truth surfaces still left historical PEAD `## New Context Packet` as the first bootstrap-selectable block, so validated `current_context` imported terminated PEAD direction into cutover planning.
- Root cause: context builder selects the first machine-shaped New Context Packet; Active Addendum prose is not parseable as bootstrap sections.
- Fix applied: lead planner with machine-shaped E0A terminal packet; reconcile cutover surfaces; regenerate context; add regression that E0A wins over later PEAD packet; Option A cutover then E0B (not indefinite hold, not FS1).
- Guardrail for next time: every terminal product close must bank a leading machine context packet before merge-to-main; never treat indefinite hold after certification as the endgame next step.
- Evidence paths: `docs/context/planner_packet_current.md`, `tests/test_build_context_packet.py`, `docs/context/current_context.md`.

## 2026-07-19
- Mistake or miss: multi-active-gate drift (F1C closed + still active + still blocked + implement next stacked simultaneously); dual-fixture Certified Portfolio UI overclaimed as operator product endpoint; score conflated with functional maturity (pressure to uplift 39 without rubric).
- Root cause: addendum-stacking left contradictory `Active` sections live; demo evidence was treated as shipment/operability; single numeric score used for both claim ceiling and stage maturity.
- Fix applied: hard-recut active canon to one gate GV-E0A-OPERABLE; demote F1C to CLOSED_SUBSTRATE; implement operable vertical (custody→HOLD_FOR_EVIDENCE→NO_POSITION→cert→current publish→one UI); split SHIPPED_PRODUCT_SCORE 39/100 from FUNCTIONAL_STAGE CERTIFIED_SINGLE_DECISION_OPERABLE (stage-only).
- Guardrail for next time: never leave two `Active` next gates; never promote score from stage alone; default UI shows one current decision only; operator publish is CLI not presentation-layer mutation.
- Evidence paths: core/gv_e0a_operable.py, views/gv_fs0_portfolio_adapter.py, scripts/publish_gv_e0a_current.py, docs/architecture/top_level_roadmap.md, tests/gv_fs0_product/test_e0a_operable.py.
## 2026-07-19
- Mistake or miss: ordering commit→hosted→review→push is causally impossible; Windows CRLF also broke 55774 identity.
- Root cause: hosted CI needs pushed workflow/commit; reviews need immutable SHA; Git autocrlf on Windows without attributes.
- Fix applied: two-SHA pattern (C transport → hosted+A/B/C → T closeout); .gitattributes 	ext eol=lf for permanent bundle; workflow_dispatch on C2.
- Guardrail: never claim shipment before push+hosted+A/B/C; pin exact-byte product artifacts with ol=lf; path-filters must include identity pins or use dispatch.
- Evidence: 48ad053dc21d7dda3c8280dcbd3c332584cc184a / 91b9bf1459439443298886ad6acc4a6181154431 / CI 29651784244 / terminal SAW.

# lessonss.md

Last updated: 2026-07-18

## 2026-07-18 Round Entry (A Visible Route Is Not Shipped Without Artifact Custody)
- Date: 2026-07-18
- Mistake or miss: component certification and even a locally passing default screen could be overread as shipment while the permanent tracked bundle, immutable commit, hosted parity, independent review, and push were absent.
- Root cause: runtime construction, repository artifact custody, hosted reproducibility, review identity, and remote delivery are separate authorities.
- Fix applied: implemented one F1C-SHIP vertical, kept the tracked-artifact assertion red, compared the entire suite to exact `c37db09`, and reconciled truth to BLOCK rather than inflating the 39/100 score.
- Guardrail for next time: never move a shipped-product score from local runtime proof; require one exact artifact/commit/hosted-review/push chain and reject intermediate publication-only or compatibility milestones.
- Evidence paths: `docs/context/e2e_evidence/gv_fs0_f1c_ship_local_validation_20260718.md`, `core/gv_fs0_bundle.py`, `core/gv_fs0_publish.py`, and `tests/gv_fs0_product/test_bundle_publication_and_default.py`.

## 2026-07-18 Round Entry (Bank Before Review and Preserve Dirty Sibling Custody)
- Date: 2026-07-18
- Mistake or miss: F1B was locally green in a detached worktree while the named branch was registered to a separate dirty worktree, so ordinary branch switching would have risked disturbing unrelated user changes or reviewing mutable bytes.
- Root cause: implementation custody, branch-ref custody, and dirty sibling worktree custody were separate facts that the local validation run could not reconcile.
- Fix applied: committed the exact detached F1B bytes, atomically fast-forwarded only the named branch ref from `e156c66` to `4359f35`, left the dirty sibling files untouched, refreshed generated context, and ran distinct read-only Reviewer A/B/C against the immutable commit.
- Guardrail for next time: when a target branch is checked out in a dirty sibling worktree, never force checkout or overwrite it; commit in the clean detached worktree, prove a fast-forward ref update, and pin every reviewer to the resulting commit.
- Evidence paths: `docs/context/e2e_evidence/gv_fs0_f1b_local_validation_20260718.md`, `docs/saw_reports/reviewer_{a,b,c}_gv_fs0_f1b_20260718.md`, `docs/saw_reports/saw_gv_fs0_f1b_terminal_close_20260718.md`, and commit `4359f35`.

## 2026-07-18 Round Entry (Verify Latest Git Authority Before Acting on Stale Local Reports)
- Date: 2026-07-18
- Mistake or miss: the supplied context contained both a pre-bank F1A local BLOCK report and a later claim that F1A was banked and independently closed, while the primary checkout itself had broken worktree metadata.
- Root cause: narrative status can lag object-store truth, and a broken checkout can make ordinary Git commands falsely suggest custody is unavailable.
- Fix applied: resolved `e156c66` directly from the repository object store, verified branch containment and terminal closure, created a clean managed worktree from a healthy sibling repository worktree, and opened only F1B.
- Guardrail for next time: when status artifacts conflict, verify the newest claimed commit, tree, branch containment, and active truth before planning; never repair a dirty/broken primary checkout when an exact clean worktree can isolate the authorized slice.
- Evidence paths: `docs/context/e2e_evidence/gv_fs0_f1b_local_validation_20260718.md`, `docs/phase_brief/gv-fs0-f1-product-slice-brief.md`, and Git inspection evidence for `e156c66`.

## 2026-07-18 Round Entry (Identical Path Means Shared Functions Plus Action-Specific Preconditions)
- Date: 2026-07-18
- Mistake or miss: F1A runtime and certification code encoded OPEN assumptions directly, so adding NO_POSITION by copying code would have created parallel truth paths and silent drift risk.
- Root cause: the first functional slice optimized for one role rather than separating shared mechanics from role-specific source/decision preconditions.
- Fix applied: generalized fixture/decision construction and certification orchestration while keeping one event builder, reducer, snapshot, verifier, certification, result, and adapter path; NO_POSITION now rejects any non-valuation intent and any non-null quantity.
- Guardrail for next time: extend a certified state machine by sharing mechanics and making role differences explicit at input gates; never duplicate accounting, certification, or presentation paths for a second role.
- Evidence paths: `core/gv_fs0_book.py`, `core/gv_fs0_certify.py`, `views/gv_fs0_portfolio_adapter.py`, and `tests/gv_fs0_product/test_no_position_vertical.py`.

## 2026-07-18 Round Entry (Schema PASS Does Not Prove Cross-Artifact Binding)
- Date: 2026-07-18
- Mistake or miss: F1A reached correct NAV 1044 and schema-valid CERTIFIED output while identity-bearing source tokens were nonconforming, raw verifier semantic fields were discarded during formalization, presentation rows were not bound to injected truth, and unexpected infrastructure errors could skip the second attempt.
- Root cause: happy-path schema validity and numeric equality were treated as sufficient without adversarially checking every authority token and every boundary between raw verifier output, formal result, certification, and presentation.
- Fix applied: enforced frozen source tokens, full raw economic/hash equality, exact two-attempt normalization, presentation projection/hash equality, legacy replay revocation, duplicate semantics, inherited-pipe deadline, and combined-suite module identity.
- Guardrail for next time: before claiming certification, mutate each independently supplied field and each identity-bearing token; require every mutation to fail closed while the exact required attempt count still executes.
- Evidence paths: `core/gv_fs0_book.py`, `core/gv_fs0_certify.py`, `views/gv_fs0_portfolio_adapter.py`, `tests/gv_fs0_product/test_open_vertical.py`, and `docs/saw_reports/se_gv_fs0_f1a_reconciliation_20260718.md`.

## 2026-07-14 Round Entry (PEAD Strict-PIT Program Terminal Close)
- Date: 2026-07-14
- Mistake or miss: The original 2015–2019 dollar-neutral Q5−Q1 strict-PIT PEAD objective was not achieved. The shipped outcome is a bounded 2019 long-only future-informed diagnostic (M7F4-v8) with research validity ~30/100.
- Root cause: Strict-PIT EPS data requires first-public/unrestated vintage with genuine effective-dated identifiers (CRSP/CCM PERMNO↔GVKEY date-ranged links). The available Compustat security master has only current-snapshot identifiers, and the CCM linktable has all-null PERMNO join keys. No data-owner approval for historical source acquisition was obtained.
- Fix applied: Formally terminated the strict-PIT program. Merged M7F4-v8 to main as DIAGNOSTIC_ONLY at commit `150d322` with tag `pead-v8-diagnostic-terminal`. Closed all PEAD phase briefs. Prohibited strategy/UI promotion.
- Guardrail for next time: Before starting a multi-phase strict-PIT research program, verify that the required historical data provenance (effective-dated identifiers, committed data-owner approval, non-null join keys) is obtainable. Do not proceed past M1 without proving the data authority path.
- Evidence paths: merge commit `150d322`, tag `pead-v8-diagnostic-terminal` at `076f26b`, `docs/context/bridge_contract_current.md`.

## 2026-07-13 Round Entry (Clean Success Does Not Prove Transactional Recovery)
- Date: 2026-07-13
- Mistake or miss: The first Slice 2 attempt left four partial outputs after an OOM-adjacent failure, and the later clean rerun could be overread as proving generalized recovery.
- Root cause: Individual writes are atomic, but the map, ledger, scenario legs, evidence, and manifests are not committed as one transaction; the full-panel plus dual-Shapley path also has no enforced memory cap or checkpoint.
- Fix applied: Removed all failed-run partials, reran from a clean committed checkout, reconciled every available artifact hash and row count, and recorded the transactionality/memory limits in independent Reviewer B and terminal SAW evidence.
- Guardrail for next time: Before any large rerun, require a clean-output preflight and post-run complete-package hash audit; never infer transactionality, bounded memory, or resumability from one successful rerun.
- Evidence paths: `scripts/pead_m7f4_v8_2019_crsp_vertical.py`, `tests/test_pead_m7f4_v8_2019_crsp_vertical.py`, `docs/saw_reports/reviewer_b_c0x_m7f4_v8_commit_b_20260713.md`, `docs/saw_reports/saw_c0x_m7f4_v8_terminal_commit_c_20260713.md`.

## 2026-07-12 Round Entry (Self-Financing Truth Before Score Close)
- Date: 2026-07-12
- Mistake or miss: M7F2-v6 claimed diagnostic 70–74 close while residual exposure used event-count share (0.163% vs ~0.72% first-bad), turnover ignored drift/equity-cash transitions (identical leg costs), bridge lacked price/RET parity, and A/B/C identities were unproven while truth still said Commit C pending.
- Root cause: Portfolio mechanics and governance closure were treated as hash/test PASS rather than self-financing path + independent review pins.
- Fix applied: M7F3-v7 locked drifted-prior→equity trade→RET→close sequence; first-bad residual metric; dead write-down sleeves; equity-only turnover; 16-state Shapley; selection-set hash; v6 CLI retired; Commit B evidence-only; Commit C after distinct A/B/C.
- Guardrail for next time: Never score a portfolio diagnostic close without (1) explicit daily trade sequence, (2) residual exposure defined as first-bad weight sum when that is the audit metric, (3) non-identical leg costs when residual paths differ, (4) distinct reviewer agent IDs, (5) seven-surface reconcile only after reviewers.
- Evidence paths: `scripts/pead_m7f3_v7_2019_crsp_vertical.py`, `docs/context/e2e_evidence/pead_m7f3_v7_2019_crsp_vertical.json`, `docs/saw_reports/saw_c0x_m7f3_v7_self_financing_20260712.md`.


## 2026-07-11 Round Entry (Payload Identity Must Use a Detached Envelope)
- Date: 2026-07-11
- Mistake or miss: Dispatch and reviewer PASS were claimed against commit `e470137` even though the four current 20260701 request artifacts were untracked and absent from that commit; the dispatch Markdown also labeled the JSON hash as its own.
- Root cause: Artifact identity was treated as narrative metadata inside or beside the payload instead of an exact object-store binding. Embedding a payload's final commit/tree in that payload is self-referential, and one ambiguous packet hash cannot identify separate Markdown and JSON bytes.
- Fix applied: Restored truth to BLOCK, quarantined the false dispatch outputs and dependent PASS report, banked the exact four request payloads unchanged in Commit 1 `a86c3a0fcc34d29e8d76cded5616c6cbe77f500e`, and created a tracked detached envelope binding its remote/root/commit/tree plus distinct path/hash pairs with `PREPARED_NOT_SENT`. Both preflights and A/B/C technical checks pass; terminal SAW remains BLOCK because distinct-agent ownership is unavailable.
- Guardrail for next time: Bank payload bytes first, then bind them from a detached envelope. Reject legacy, divergent, reconstructed, redirected, cherry-picked, self-referential, ambiguously hashed, or otherwise unbound artifacts. `PREPARED_NOT_SENT` is never dispatch proof.
- Evidence paths: `docs/phase_brief/v2-pead-m6b-request-artifact-identity-repair-v1.md`, `docs/quarantine/request_artifact_identity_repair_v1/QUARANTINE_MANIFEST.md`, the four 20260701 request artifacts, and the tracked identity envelope created in Commit 2.

## 2026-07-11 Round Entry (Planning Preflight Hard Dirty Is Path-Classified, Not Every Dirty File)
- Date: 2026-07-11
- Mistake or miss: Early planning treated boot-core dirty files as the hard dirty blocker; the real hard fail was the untracked Path A source/test pair. Separately, GOV-002 failed PEAD *denial* copy that contained the token `recommendation`, and GOV-008 failed on stale candidate-card manifest hashes. Locked PEAD evidence JSON had CRLF bytes under assume-unchanged, breaking SHA verification without showing as ordinary git dirty.
- Root cause: Dirty classification is code-path severity, not “any modified file.” UI scanners match substrings regardless of negation. Manifest hashes drift silently if card bytes change without rebinding. Windows line-ending + assume-unchanged can desync content hashes from Git’s dirty view.
- Fix applied: Banked Path A pair; reworded PEAD denial UI without forbidden tokens; moved M1B schema claim-boundary names to non-UI core; rebound MSFT/MU manifests to current card SHA-256; restored locked evidence LF blobs from HEAD; acceptance governance+planning preflight PASS at commit `e470137`.
- Guardrail for next time: When preflight fails dirty, list `severity=fail` paths only before planning work. Rebind manifests mechanically when cards change. Never put product-action tokens in UI-scanned string literals even in denials—use allowed wording or non-UI schema modules. Clear assume-unchanged and restore LF when evidence SHA verification drifts without porcelain dirt.
- Evidence paths: `core/pead_evidence_claim_boundary.py`, `views/pead_validation_evidence.py`, `data/candidate_cards/*manifest.json`, Path A script/tests, `scripts/governance_preflight.py` PASS, `scripts/boot_preflight.py --mode planning --no-tests` PASS, commit `e470137`.

## 2026-07-11 Round Entry (Authority Identity Requires an Unambiguous Parser and Object Store)
- Date: 2026-07-11
- Mistake or miss: Approval/evidence JSON accepted duplicate members under Python's last-key-wins default, while Git ancestry checks could be affected by replacement refs and did not reject their presence.
- Root cause: Repository identity and JSON syntax were treated as ordinary input details rather than authority preconditions.
- Fix applied: Sanitized Git identity subprocesses, disabled replacement objects, rejected loose/packed replacement refs, required raw HEAD/upstream commit objects plus a verified HEAD tree, and added all-depth duplicate-key rejection to strict evidence and authorization JSON parsing before output creation. Fresh A/B/C review passed after the repair.
- Guardrail for next time: An authority packet is valid only when Git redirection is sanitized, raw commit/tree identity and replacement state are verified, and every JSON object member is unique; unavailable/non-commit identity, any replacement ref, or any duplicate key blocks the packet with no compatibility bypass.
- Evidence paths: `scripts/boot_preflight.py`, `tests/test_boot_preflight.py`, `scripts/pead_m6b_strict_path_a_data_gate.py`, `tests/test_pead_m6b_strict_path_a_data_gate.py`, focused P0 test output, final Reviewer A/B/C evidence, and this round's SAW report.

## 2026-07-02 Round Entry (Repository Identity Must Be a Packet Gate, Not a Narrative Rule)
- Date: 2026-07-02
- Mistake or miss: An R0.1 approval/denial packet was evaluated against Quant even though its claimed commit and root plan did not resolve here; the active M6b phase brief also retained stale language implying a restated-EPS exception could satisfy strict Gate A.
- Root cause: Repository identity was described as an operational principle rather than required fields and verification evidence in the canonical approval/request template; active and historical wording were not separated tightly enough.
- Fix applied: Added a repository remote/root, commit, tree, artifact path, and artifact hash gate to `docs/templates/ship_fast_decision_gate.md`; corrected only the active M6b phase brief so first-public/unrestated EPS is the sole strict Gate A pass route.
- Guardrail for next time: Deny any approval/request packet whose declared repository, commit, tree, artifact path, or artifact hash cannot resolve exactly; never repair a missing external governance chain by importing it into the wrong repository. Preserve historical addenda while correcting active truth.
- Evidence paths: `docs/templates/ship_fast_decision_gate.md`, `docs/phase_brief/v2-pead-m6b-strict-data-path-a.md`, current truth surfaces, and this round's Thin SAW report.

## 2026-06-30 Round Entry (Windows Sandbox Failure Requires an Explicit WSL Repo Guard)
- Date: 2026-06-30
- Mistake or miss: Reinstalling Codex did not repair the Windows sandbox helper, and a malformed WindowsApps-based working directory could have redirected validation away from the intended repository.
- Root cause: The Windows sandbox setup executable had a missing-module failure, while the WSL handoff inherited an invalid composite cwd instead of the mounted E: workspace.
- Fix applied: Bound every command to `/mnt/e/Code/Quant`, confirmed the working path before validation, used the repo `.venv` through WSL interop, and preserved the canonical brief and unrelated dirty files.
- Guardrail for next time: On WSL recovery, hard-stop unless `pwd` is exactly `/mnt/e/Code/Quant`; never accept a cwd containing `WindowsApps` or a composite `resources/E:/...` path.
- Evidence paths: `scripts/pead_m6b_strict_path_a_data_gate.py`, `tests/test_pead_m6b_strict_path_a_data_gate.py`, `docs/context/e2e_evidence/pead_m6b_strict_path_a_readiness.json`, focused pytest/compile/CLI output from this round.

## 2026-06-30 Round Entry (Evidence Content Must Never Carry Its Own Authority)
- Date: 2026-06-30
- Mistake or miss: The current-evidence payload could set its own authorization boolean, malformed authorization was silently downgraded to `NOT_AUTHORIZED`, and structurally passing gates could report `PASS` without detached authority or complete source-byte verification.
- Root cause: Authorization schema validity, authorization outcome, evidence content, byte provenance, and gate status were evaluated as separable local checks instead of global current-evidence prerequisites.
- Fix applied: Made malformed authorization JSON/schema and synthetic-test-plus-authorization CLI input errors; retained fail-closed JSON for structurally valid unapproved/mismatched current-evidence authorization; and required detached authorization plus all four verified source hashes before any current gate can pass.
- Guardrail for next time: Never emit a current gate `PASS` unless detached authority and the complete source-byte set are verified; never convert malformed control artifacts into ordinary authorization denials or accept authorization flags in synthetic validation.
- Observed state: A/B/C/D are `BLOCKED`; the restated-EPS exception is `NOT_AUTHORIZED`; `strict_vintage_pit=false`; `m6b_data_contract_ready=false`. Inherited exception wording is superseded on current truth surfaces and cannot satisfy strict Gate A.
- Evidence: strict-gate tests PASS 68/68; M6a tests PASS 12/12; malformed and synthetic-test authorization combinations exit 2 without output; mismatched current-evidence authorization exits 0 with A-D blocked; canonical context build/validation passes; readiness JSON SHA-256 `0ef4b2504f7f573eab734614054e3c3e9ffa746b02522a6ef00a51453010574a`.
- Next action: obtain authorized, verifiable evidence for the smallest blocked strict-data gate.

## 2026-06-25 Round Entry (Bounded B Runs Need Eligibility and Commit Atomicity Together)
- Date: 2026-06-25
- Mistake or miss: Reviewer A/C terminal-window repair and Reviewer B commit-path repair could have been split into separate regenerations of the same B artifact.
- Root cause: The prior path treated "which events are eligible" and "how B outputs are committed" as separable even though both converge on regenerating the same JSON/parquet pair.
- Fix applied: Repaired in one ordered round: full-window event eligibility first, then gate-first rollback-protected `--commit-bestavail-run`, followed by one B regeneration through the new path.
- Guardrail for next time: For any bounded diagnostic that emits paired data artifacts, fix selection eligibility before output commit semantics, then regenerate once through the final commit path.
- Evidence paths: `scripts/pead_m6b_bestavail_illustrative_2015_2019.py`, `tests/test_pead_m6b_bestavail_illustrative_2015_2019.py`, `docs/context/e2e_evidence/pead_m6b_bestavail_illustrative_2015_2019.json`, `data/processed/pead_m6b_bestavail_illustrative_2015_2019_daily_returns.parquet`, `docs/saw_reports/saw_v2_pead_m6b_bestavail_option1_repair_20260625.md`.

## 2026-06-25 Round Entry (Illustrative B Curves Still Need Terminal Window Completeness)
- Date: 2026-06-25
- Mistake or miss: A best-available illustrative curve passed flag/hash/parquet checks while still including terminal cohorts that could not complete the configured 60-session holding rule inside the declared 2015-2019 return frame.
- Root cause: The standalone B selection capped return rows at 2019-12-31 but did not also cap eligible events by `exit_idx <= max(return_idx)` before the sparse engine call.
- Fix applied: Reviewer C blocked closure and recorded the exact data-integrity failure: 1,796 / 29,737 selected events exceeded the return-calendar max index.
- Guardrail for next time: Every future bounded-window diagnostic must verify full holding-window completeness before emitting or accepting curve metrics, even when the artifact is illustrative-only and hard-flagged as non-alpha/non-tradable.
- Evidence paths: `docs/saw_reports/saw_v2_pead_m6b_bestavail_option1_reviewer_c_20260625.md`, `scripts/pead_m6b_bestavail_illustrative_2015_2019.py`, `docs/context/e2e_evidence/pead_m6b_bestavail_illustrative_2015_2019.json`, `data/processed/pead_m6b_bestavail_illustrative_2015_2019_daily_returns.parquet`.

## 2026-06-25 Round Entry (Review Evidence Must Match Current Revision)
- Date: 2026-06-25
- Mistake or miss: A prior reviewer artifact did not match the current revision.
- Root cause: Revision matching was not rechecked before using the artifact as terminal evidence.
- Fix applied: Published an independent current revision review and kept the unmatched reviewer rerun open.
- Guardrail for next time: Confirm reviewed implementation identity before accepting terminal review evidence.
- Evidence paths: `docs/saw_reports/saw_v2_pead_m6a_reviewer_b_rerun_20260625.md`, `docs/context/planner_packet_current.md`.

## 2026-06-25 Round Entry (Reviewer-Only PASS Must Leave Remaining Reviewers Explicit)
- Date: 2026-06-25
- Mistake or miss: A reviewer-only terminal PASS can be overread as full SAW closure if current truth surfaces still say all reviewers are pending or if the report omits the remaining reviewer boundary.
- Root cause: Reviewer A/B/C evidence is collected independently, while the prior status language grouped them together as one unresolved gate.
- Fix applied: Published a separate Reviewer A rerun artifact, validated its closure and SAW blocks, and updated current truth surfaces to show Reviewer A PASS while Reviewer B/C remain pending.
- Guardrail for next time: When only one terminal reviewer reruns, publish a distinct reviewer artifact and update planner/bridge/impact/done surfaces to name exactly which reviewers remain.
- Evidence paths: `docs/saw_reports/saw_v2_pead_m6a_reviewer_a_rerun_20260625.md`, `docs/context/planner_packet_current.md`, `docs/context/bridge_contract_current.md`, `docs/context/impact_packet_current.md`, `docs/context/done_checklist_current.md`.

## 2026-06-24 Round Entry (PIT Timing Alignment Must Not Be Overclaimed as EPS Vintage PIT)
- Date: 2026-06-24
- Mistake or miss: An M6 equity-curve runner could have treated RDQ/release-date timing alignment as full PIT safety and emitted a fake tradable curve from current-vintage EPS plus non-delisting-adjusted Compustat returns.
- Root cause: Prior PEAD evidence used the broad word PIT while the data contract actually has two layers: timing availability and unrevised/first-public vintage availability. M5a also labelled net output even though the cost parameter was zero.
- Fix applied: Implemented M6a as a fail-closed input-contract and framework runner that labels current EPS as `release_date_aligned_but_restated`, requires nonzero explicit costs, and refuses `--run` curve output when strict vintage, delisting-adjusted tradable returns, or full as-of tradability screens are missing.
- Guardrail for next time: Every future PIT/backtest claim must separately state `timing_pit_status`, `eps_vintage_status`, return-source/tradability status, delisting status, and whether net costs are nonzero before emitting CAGR or equity curves.
- Evidence paths: `scripts/pead_m6_pit_walk_forward_equity_curve.py`, `tests/test_pead_m6_pit_walk_forward_equity_curve.py`, `docs/context/e2e_evidence/pead_m6_pit_walk_forward_equity_curve.json`, `.venv\Scripts\python.exe -m pytest tests/test_pead_m6_pit_walk_forward_equity_curve.py -q`, `.venv\Scripts\python.exe scripts/pead_m6_pit_walk_forward_equity_curve.py --run`.

## 2026-06-24 Round Entry (Lineage Validation Errors Due to Sample vs Full Universe Manifest Mismatch)
- Date: 2026-06-24
- Mistake or miss: `pead_m5a_net_multifactor_alpha_test.py` failed with a `ValueError: D2B manifest path drift` because the loaded `d3` manifest expected the full universe manifest, while the default loaded `d2b` was the sample manifest.
- Root cause: The daily benchmark `pead_d3_ken_french_daily_benchmark` on the system was built against the full universe manifest `pead_d2b_event_windows.parquet.manifest.json` during the M4B phase, whereas the M5a factor builder and diagnostic script defaulted to the sample manifest `pead_d2b_event_windows_sample.parquet.manifest.json`.
- Fix applied: Ran both scripts explicitly passing the full universe D2B manifest (`--d2b-manifest data/processed/pead_d2b_event_windows.parquet.manifest.json`) and bypassed counts check using `--no-enforce-counts` on the diagnostic runner.
- Guardrail for next time: Always verify whether the active benchmark artifact is aligned with the sample or the full universe manifest, and pass the corresponding `--d2b-manifest` and count enforcement flags explicitly to keep the lineage consistent.
- Evidence paths: `scripts/pead_m5a_multifactor_factors.py`, `scripts/pead_m5a_net_multifactor_alpha_test.py`, `docs/context/e2e_evidence/pead_m5a_net_multifactor_alpha_test.json`, `data/processed/pead_d3m_ken_french_daily_multifactor.parquet.manifest.json`.

## 2026-06-23 Round Entry (Context Hygiene Tests Enforce Historical Sub-Milestone Presence)
- Date: 2026-06-23
- Mistake or miss: Context hygiene test failed due to missing "M4A" string in `current_context.json`'s `what_was_done` field.
- Root cause: The previous round's status update replaced the "M4A" string with M4B.1 reclassification details, violating the test's `assert "M4A" in joined_done` constraint.
- Fix applied: Restored the M4A status reference to the `what_was_done` array in `docs/context/current_context.json` and validated all tests passed cleanly.
- Guardrail for next time: Ensure historical sub-milestone references within the active phase are not completely removed from context files during status updates unless the test assertions are explicitly modified or retired.
- Evidence paths: `docs/context/current_context.json`, `tests/test_phase61_context_hygiene.py::test_current_context_promotes_latest_active_phase`.

## 2026-06-22 Round Entry (Full-Universe Inference Requires Memory-Conscious DataFrame Lifecycle)
- Date: 2026-06-22
- Mistake or miss: Full-universe calendar-time portfolio regressions failed with a `numpy.core.exceptions._ArrayMemoryError` during groupby and copy operations.
- Root cause: Pandas DataFrames containing 13.6M+ rows were duplicated and cast repeatedly, and unneeded columns (e.g. `issuer_id`, `coverage_reason`, `handoff_eligible`) were retained in memory, exceeding local RAM limits.
- Fix applied: Updated `scripts/pead_real_data_validation.py` to drop unused columns from `d2b.frame` before subset filtering, pre-compute lineage metadata records early to allow immediate deletion of `d1` and `d2b` snapshots, and invoke explicit garbage collection (`gc.collect()`) prior to running the inference estimator.
- Guardrail for next time: For large-scale datasets (10M+ rows), proactively prune columns before filtering, clear objects early, call garbage collection, and avoid deep copies or string type castings of large columns.
- Evidence paths: `scripts/pead_real_data_validation.py`, `docs/context/e2e_evidence/pead_calendar_time_inference_m1b_full_universe.json`, `docs/context/e2e_evidence/pead_real_data_validation_full_universe.json`.

## 2026-06-22 Round Entry (Clean-Exit Failures Need Process-Liveness Proof Before Code Changes)
- Date: 2026-06-22
- Mistake or miss: The M4A execution_microstructure/full-suite blocker was initially treated as a possible teardown/status code defect even though stale pytest and Streamlit smoke processes were still alive.
- Root cause: The first full-suite clean-exit rerun used an insufficient timeout and did not prove process liveness before classifying the failure.
- Fix applied: Stopped the stale pytest/Streamlit smoke processes after verifying their command lines, reran targeted execution_microstructure/status checks, reran the full repository pytest with a longer timeout, and confirmed no lingering Python processes remained.
- Guardrail for next time: Before editing code for a pytest hang or missing exit code, enumerate active Python processes with command lines, clear only verified stale test/smoke processes, rerun a targeted teardown matrix, then rerun full pytest with a timeout long enough for the current suite size.
- Evidence paths: `docs/saw_reports/saw_v2_pead_m4a_clean_exit_rerun_20260622.md`, `docs/saw_reports/se_v2_pead_m4a_clean_exit_rerun_20260622.md`, `.venv\Scripts\python -m pytest tests\test_execution_microstructure.py -q`, `.venv\Scripts\python -m pytest tests\test_execution_microstructure.py tests\test_phase61_context_hygiene.py tests\test_policy_target_timeline_apptest.py -q`, `.venv\Scripts\python -m pytest -q`.

## 2026-06-22 Round Entry (Terminal Reviewer Capacity Must Be Reserved Before Implementation)
- Date: 2026-06-22
- Mistake or miss: M4A implementation reached passing focused and PEAD regression tests, but the implementer subagent hit the usage limit before returning a report and before terminal Reviewer A/B/C capacity could be reserved.
- Root cause: Reviewer capacity was acknowledged as a known closure dependency but not preflighted before starting the final implementation loop.
- Fix applied: Kept M4A terminal SAW at BLOCK, recorded the usage-limit blocker, and separated local implementation evidence from closure authority.
- Guardrail for next time: Before starting any code round that requires full Reviewer A/B/C SAW, reserve or preflight terminal reviewers first; if capacity is unavailable, publish BLOCK immediately or ask the user whether to proceed with local-only implementation evidence.
- Evidence paths: scripts/pead_d2_return_contract.py, scripts/pead_d2b_event_window_contract.py, tests/test_pead_d2_returns.py, tests/test_pead_d2b_event_window_contract.py, docs/saw_reports/saw_v2_pead_m4a_memory_bounded_full_universe_20260622.md.

## 2026-06-21 Round Entry (Read-Only Evidence UI Must Not Become Approval UI)
- Date: 2026-06-21
- Mistake or miss: A frontend status surface for closed M1B evidence could either imply alpha approval or overcorrect by leading with hashes/manifests instead of PM-readable readiness.
- Root cause: Evidence integrity and product readiness are related but different surfaces; showing audit plumbing can obscure the approval boundary, while showing inference status without blocked states can imply promotion.
- Fix applied: M2 verifies validation and M1B JSON hashes internally, renders locked evidence and blocked alpha/promotion states, sanitizes fail-closed UI errors, and tests that successful rendering exposes no SHA/path/manifest strings.
- Guardrail for next time: Read-only evidence dashboards must separate internal verification from visible readiness and always show blocked approval/action states when evidence is not an authorization.
- Evidence paths: `views/pead_validation_evidence.py`, `views/strategy_view.py`, `tests/test_pead_validation_evidence.py`, `docs/context/observability_pack_current.md`.

## 2026-06-21 Round Entry (Cross-Artifact Invariants Must Precede Estimation)
- Date: 2026-06-21
- Mistake or miss: The first M1B implementation validated D2B and D3 separately but did not reject off-spine D2B return dates, and its CLI/schema boundaries allowed alternate output targets and underconstrained count/null fields.
- Root cause: Artifact-local schema checks were treated as sufficient without enumerating cross-artifact set invariants and protected output identities.
- Fix applied: Added the D2B-to-D3 date-subset gate, canonical M1B output lock, exact HAC correction flag, reconciled nonnegative count/rate validation, zero-session null semantics, and negative regressions.
- Guardrail for next time: Before publishing derived evidence, enumerate and test source-to-source set relationships, protected output paths, empty-state representation, and every arithmetic identity in the evidence schema.
- Evidence paths: `scripts/pead_real_data_validation.py`, `strategies/pead_event_study.py`, `tests/test_pead_real_data_validation.py`, `docs/context/e2e_evidence/pead_calendar_time_inference_m1b.json`, `AGENTS.md`.

## 2026-06-21 Round Entry (Reserve Terminal Review Capacity Before Final Repair)
- Date: 2026-06-21
- Mistake or miss: M1B reached repaired code, deterministic evidence, and technical Reviewer A/B/C approval before the final hierarchy-only Reviewer C confirmation again hit the subagent usage limit.
- Root cause: Terminal reviewer capacity was still consumed reactively after reconciliation instead of reserved before the last repair loop.
- Fix applied: Kept terminal SAW at BLOCK, recorded the exact unavailable check, and promoted reviewer-capacity preflight into `AGENTS.md`.
- Guardrail for next time: Preflight and reserve all required terminal reviewers before the final repair loop; if capacity is unavailable, publish BLOCK immediately rather than performing closure work that cannot be independently sealed.
- Evidence paths: `AGENTS.md`, `docs/saw_reports/saw_v2_pead_calendar_time_inference_m1b_20260621.md`, Reviewer C hierarchy-audit usage-limit result.

## 2026-06-21 Round Entry (Terminal Review Must Recheck Corrected Counts)
- Date: 2026-06-21
- Mistake or miss: The first M1A feasibility text recorded null-`return_date` exclusions as 327 and treated the methodology gate as approved before final Reviewer C could rerun after the count correction.
- Root cause: Event/skeleton count language was conflated with row-count schema language, and reviewer capacity was discovered only after local reconciliation.
- Fix applied: Reran the parent-side count check, corrected the contract to 19,812 null-`return_date` rows, 226,772 extreme expected rows, and 1,519 missing rows, then published a BLOCK SAW status instead of starting M1B.
- Guardrail for next time: For every future evidence schema field named `*_rows_*`, rerun a parent-side exact row-count command and require independent Reviewer C terminal recheck before approval or implementation starts.
- Evidence paths: `docs/phase_brief/v2-pead-alpha-inference-methodology-gate.md`, `docs/saw_reports/saw_v2_pead_alpha_inference_methodology_gate_20260621.md`, `docs/context/planner_packet_current.md`.

## 2026-06-20 Round Entry (Name the Product Surface, Then Execute the Approval)
- Date: 2026-06-20
- Mistake or miss: The first response treated the approved D4 work as another status/approval handoff and retained the ambiguous phrase `status-only dashboard`.
- Root cause: Execution-state language was allowed to replace the product-surface contract even though the user had already bounded and authorized implementation.
- Fix applied: Implemented the slice directly, renamed it `read-only evidence dashboard`, and used status language only for artifact integrity fields inside the panel.
- Guardrail for next time: After explicit bounded approval, execute without inserting another approval packet; name a surface by user-visible capability and forbidden actions, not by internal workflow state.
- Evidence paths: `views/pead_validation_evidence.py`, `views/strategy_view.py`, `dashboard.py`, `tests/test_pead_validation_evidence.py`, `docs/phase_brief/v2-pead-read-only-evidence-dashboard-brief.md`.

## 2026-06-20 Round Entry (Historical BLOCK Evidence Needs Separate PASS Rerun Artifact)
- Date: 2026-06-20
- Mistake or miss: Terminal closure could be overread if the prior BLOCK SAW were edited in place after reviewer capacity returned.
- Root cause: The D2B technical state was already repaired, but the missing proof was reviewer availability, so the terminal state changed because of new review evidence rather than a new implementation.
- Fix applied: Left `docs/saw_reports/saw_v2_d2b_session_spine_repair_20260619.md` intact and published `docs/saw_reports/saw_v2_d2b_session_spine_repair_rerun_20260620.md` as a separate PASS artifact.
- Guardrail for next time: When reviewer capacity returns after a BLOCK caused by unavailable reviewers, publish a new rerun artifact and update current truth surfaces instead of mutating the historical BLOCK report.
- Evidence paths: `docs/saw_reports/saw_v2_d2b_session_spine_repair_rerun_20260620.md`, `docs/context/planner_packet_current.md`, `docs/context/bridge_contract_current.md`, `.venv\Scripts\python -m pytest tests\test_pead_d2_returns.py tests\test_pead_d2b_event_window_contract.py tests\test_pead_d3_benchmark_artifact.py tests\test_pead_event_study.py -q`.

## 2026-06-20 Round Entry (Reviewer Capacity Is a Closure Dependency)
- Date: 2026-06-20
- Mistake or miss: The D2B session-spine repair reached code, artifact, test, and smoke evidence before confirming that final independent Reviewer A/B/C capacity was available for the post-fix state.
- Root cause: Reviewer capacity was treated as a terminal action instead of a closure dependency that can block after local reconciliation fixes are already complete.
- Fix applied: Published a terminal BLOCK SAW report with `ChecksFailed=1`, refreshed current truth surfaces to say final Reviewer A/B/C is unavailable rather than merely pending, and kept D3 publication separate.
- Guardrail for next time: Before the final code-fix loop, preflight reviewer availability; if final A/B/C cannot run, publish BLOCK immediately and do not imply milestone closure from machine evidence alone.
- Evidence paths: `docs/saw_reports/saw_v2_d2b_session_spine_repair_20260619.md`, `docs/context/planner_packet_current.md`, `docs/context/bridge_contract_current.md`, `docs/context/done_checklist_current.md`, `docs/context/observability_pack_current.md`.

## 2026-06-19 Round Entry (Filter Before Full-Frame Strategy Normalization)
- Date: 2026-06-19
- Mistake or miss: The first repaired strategy handoff deep-copied and sorted all 1.49 million D2A rows before filtering selected securities, causing a reproducible active-scale `ArrayMemoryError`.
- Root cause: Input validation, canonical normalization, and selected-security projection were coupled in one full-frame operation.
- Fix applied: Added bounded chunk validation across all D2A rows, retained only selected-security return columns with a shared categorical identity dtype, and derived event metadata from one eligible row per event.
- Guardrail for next time: At large dataframe boundaries, validate globally in bounded chunks and project/filter before normalization or sorting; synthetic adapter tests must be paired with one active-scale memory smoke.
- Evidence paths: `scripts/pead_d2b_event_window_contract.py`, `tests/test_pead_d2b_event_window_contract.py`, `docs/phase_brief/v2-pead-d2b-session-spine-repair-brief.md`, active-scale smoke output for `ROUND-20260619-V2-D2B-SESSION-SPINE-REPAIR`.

## 2026-06-19 Round Entry (Source Row Dates Are Not Calendar Authority)
- Date: 2026-06-19
- Mistake or miss: D2B treated every distinct D2A source row date as a market session, allowing 52 exchange-closed dates to enter liquidity lookbacks and `+1..+60` event windows.
- Root cause: D2A observation availability and market-calendar authority were collapsed into one date union.
- Fix applied: Added an explicit source-backed Ken French daily session spine, recorded its release/hash and excluded dates in the D2B manifest, rebuilt D2B, and made D3 validate the same upstream source/session hash.
- Guardrail for next time: Every event-study window builder must receive an explicit authoritative calendar; never infer market sessions solely from security-row dates.
- Evidence paths: `scripts/pead_d2b_event_window_contract.py`, `scripts/pead_d3_benchmark_artifact.py`, `tests/test_pead_d2b_event_window_contract.py`, `tests/test_pead_d3_benchmark_artifact.py`, `data/processed/pead_d2b_event_windows_sample.parquet.manifest.json`.

## 2026-06-18 Round Entry (Closure References Must Resolve Before PASS)
- Date: 2026-06-18
- Mistake or miss: The first parent-closure bridge addendum referenced a SAW filename that did not exist while a concurrent worker had already published the authoritative full D1 SAW under a different path.
- Root cause: Closure drafting began from an earlier truth snapshot and did not re-resolve the evidence path after concurrent context updates.
- Fix applied: Re-read current truth, retained the existing full D1 SAW as authoritative, published only a thin reconciliation report, corrected the bridge paths, and disclosed untracked local D1 ownership.
- Guardrail for next time: Immediately before closure PASS, resolve every evidence path on disk, distinguish authoritative implementation SAW from reconciliation SAW, and never duplicate promotion ownership after concurrent publication.
- Evidence paths: `docs/saw_reports/saw_v2_d1_repair_20260618.md`, `docs/saw_reports/saw_v2_d1_parent_closure_reconciliation_20260618.md`, `docs/context/bridge_contract_current.md`, `docs/context/impact_packet_current.md`.

## 2026-06-18 Round Entry (Identity Dedup Must Precede Stateful Transforms)
- Date: 2026-06-18
- Mistake or miss: RDQ deduplication was applied after lag computation, allowing rows that were later removed to make events appear lag-valid.
- Root cause: Stage-order review missed upstream-row contamination in stateful lag and rolling transforms.
- Fix applied: Moved `(gvkey, rdq)` identity deduplication before exact t-4 lag and rolling calculations, rebuilt D1, and removed 1,447 contaminated lag-valid events.
- Guardrail for next time: Resolve identity duplicates before any stateful lag or rolling transform and require a duplicate-key counterexample regression test.
- Evidence paths: `scripts/pead_d1_sue_builder.py`, `tests/test_pead_d1_sue.py`, `docs/phase_brief/v2-pead-d1-repair-brief.md`, `data/processed/pead_d1_sue_signal.parquet`, `data/processed/pead_d1_sue_signal.parquet.manifest.json`.

## 2026-06-18 Round Entry (Empty D1 Output Must Preserve Existing Bundle)
- Date: 2026-06-18
- Mistake or miss: The first D1 repair write path could promote an empty Parquet before later summary code failed.
- Root cause: Atomic publication was verified for normal writes, but the all-filtered edge case did not have a pre-write fail-closed gate.
- Fix applied: Added a pre-write empty-output guard and tests for dry-run and production paths, plus temp/manifest failure-order regressions.
- Guardrail for next time: Any data builder that publishes a replace bundle must prove empty-output preservation before production rebuild evidence can count.
- Evidence paths: `scripts/pead_d1_sue_builder.py`, `tests/test_pead_d1_sue.py`, `.venv\Scripts\python -m pytest tests\test_pead_d1_sue.py tests\test_pead_event_study.py -q`, `data/processed/pead_d1_sue_signal.parquet.manifest.json`.

## Purpose
Track mistakes, root causes, and guardrails so repeated errors are prevented.

## Entry Template
| Date | Scope | Mistake/Miss | Root Cause | Fix Applied | Guardrail | Evidence |
|---|---|---|---|---|---|---|
| YYYY-MM-DD | `<task/phase>` | `<one line>` | `<one line>` | `<one line>` | `<one line>` | `<paths/tests>` |

## Entries
| Date | Scope | Mistake/Miss | Root Cause | Fix Applied | Guardrail | Evidence |
|---|---|---|---|---|---|---|
| 2026-06-18 | V2 PEAD strategy SAW rerun | Promotion evidence could be confused with the earlier BLOCK report or a pasted 4-check ClosurePacket | The original implementation round had valid code/tests but incomplete reviewer rerun, and later audit found reporting drift between pasted status and saved artifact | Published a separate rerun SAW PASS artifact, kept the old BLOCK report as historical evidence, refreshed current truth, and recorded exact reviewer/test/validator gates | Never rewrite historical BLOCK evidence into PASS; promotion after reviewer capacity returns must use a new artifact with its own closure packet and validator output | `docs/saw_reports/saw_v2_pead_strategy_contract_rerun_20260618.md`, `docs/saw_reports/saw_v2_pead_strategy_contract_20260618.md`, `docs/context/planner_packet_current.md`, `.venv\Scripts\python -m pytest tests\test_pead_event_study.py tests\test_statistics.py tests\test_phase56_pead_runner.py -q` |
| 2026-06-18 | V2 PEAD strategy contract | A strategy skeleton could silently treat raw compounded return as CAR or accept partial `+60` windows while the data contract is still under repair | Return semantics and future-window coverage were implicit in upstream artifacts instead of enforced at the strategy boundary | Added explicit raw/CAR/BHAR formulas, strict post-event indexing, complete-window eligibility, cohort quantiles, HAC spread inference, and synthetic failure-path tests | Never label raw returns as CAR; require an explicit benchmark and complete event window before abnormal-return analysis, and keep strategy tests separate from real-alpha evidence | `strategies/pead_event_study.py`, `tests/test_pead_event_study.py`, `docs/phase_brief/v2-pead-strategy-contract-brief.md`, `.venv\Scripts\python -m pytest tests\test_pead_event_study.py -q` |
| 2026-06-03 | V2-D0.4C probe approval fast gate | A fast unblock approval artifact could be misread as permission for Codex/subagents to run WRDS or capture provider output | D0.4C approves a future local human probe, but the operational vocabulary includes access checks and table names | Created D0.4C as docs-only approval with exact five-row scope, allowed output shape only, D0.4D queued but not run, and explicit blocks on credentials, discovery, row counts, samples, snapshots, data output, runtime writes, and formal approval_ref changes | Keep approval, execution, and outcome recording in separate packets; D0.4C approves future local human execution only, while D0.4D is the first packet that may record redacted outcomes | `docs/authorization/V2_D0_4C_LOCAL_READ_ONLY_PERMISSION_PROBE_APPROVAL.md`, `docs/authorization/V2_D0_4C_LOCAL_READ_ONLY_PERMISSION_PROBE_APPROVAL.json`, `docs/saw_reports/saw_v2_d0_4c_local_read_only_permission_probe_20260603.md` |
| 2026-06-03 | V2-D0.4B WRDS local auth correction | Overbroad `WRDS/provider access blocked` language could hide a user-attested local auth method while still not proving login or permissions | Prior docs collapsed auth-method availability, credential handling, provider execution, and formal table permission truth into one blocked label | Added V2-D0.4B correction artifacts and refreshed current truth/product docs with local-auth-available, login-unverified, credentials-unread, permission-not-closed states | Split local auth availability from actual login verification and table-level permission truth; never read or use `secret.txt`/credentials, and keep rows not_approved until separate approval_ref evidence exists | `docs/authorization/V2_D0_4B_WRDS_LOCAL_AUTH_METHOD_CONFIRMED.md`, `docs/authorization/V2_D0_4B_WRDS_LOCAL_AUTH_METHOD_CONFIRMED.json`, `docs/context/planner_packet_current.md`, `PRD.md`, `PRODUCT_SPEC.md` |
| 2026-05-28 | Governed data source provenance intake `ROUND-20260528-GOVERNED-DATA-SOURCE-PROVENANCE-INTAKE` / `SCOPE-APPROVE-RAW-SOURCES-BEFORE-ARTIFACT-GENERATION` | Source acquisition planning could still be mistaken for permission to generate processed artifacts | The previous packet named source/generator gaps but did not require explicit raw source ownership, access, as-of coverage, license, manifest path, and SHA256 policy before generation | Added a source-provenance intake packet and refreshed truth surfaces with a no-generation boundary and per-line provenance fields | Before any governed regeneration, approve raw/source provenance first; generator argv and artifact writes stay blocked until provenance, manifests, hashes, and validation commands are documented | `docs/architecture/governed_data_source_provenance_intake_20260528.md`, `docs/context/bridge_contract_current.md`, `docs/context/impact_packet_current.md`, `docs/context/done_checklist_current.md`, `docs/context/planner_packet_current.md`, `docs/context/multi_stream_contract_current.md`, `docs/context/post_phase_alignment_current.md`, `docs/context/observability_pack_current.md`, `docs/decision log.md`, `docs/notes.md`, `docs/phase_brief/phase65-brief.md` |
| 2026-05-28 | Governed data source acquisition planning | Source/generator approval could be conflated with the prior governed artifact authorization PASS | The prior packet approved the next decision surface but did not enumerate source inputs and generator gaps per strict-readiness artifact in dependency order | Added a source-acquisition planning packet and refreshed truth surfaces with BLOCK state, explicit A/B/C decision, no-generation boundary, and per-artifact source/schema/manifest/rollback rules | Before any data-readiness recovery, split authorization, source acquisition, generator approval, data generation, and BootReady proof into separate docs/check gates | `docs/architecture/governed_data_source_acquisition_20260528.md`, `docs/context/bridge_contract_current.md`, `docs/context/impact_packet_current.md`, `docs/context/done_checklist_current.md`, `docs/context/planner_packet_current.md`, `docs/context/multi_stream_contract_current.md`, `docs/context/post_phase_alignment_current.md`, `docs/context/observability_pack_current.md`, `docs/decision log.md`, `docs/notes.md`, `docs/phase_brief/phase65-brief.md` |
| 2026-05-26 | Boot status path contract SAW | Executable code and tests could be corrected to runtime while docs/context contracts still snapped back to docs/context as canonical | The path contract lived in multiple docs and JSON policy surfaces, so code-only sentinels did not catch stale docs-as-code authority | Patched BOOT.md, boot/data-readiness architecture docs, taxonomy, and route contract to runtime canonical and reran focused tests plus stale-authority grep | Path contract rounds must run both import sentinels and stale-authority grep over docs/context policy JSON before SAW closure | `BOOT.md`, `docs/architecture/boot_preflight_contract.md`, `docs/architecture/data_readiness_gate_v0.md`, `docs/context/data_artifact_taxonomy_current.json`, `docs/context/portfolio_allocation_route_contract_v0.json`, `.venv\Scripts\python -m pytest tests\test_boot_preflight.py tests\test_boot_preflight_governance.py tests\test_boot_status_contract.py tests\test_data_readiness_gate.py tests\test_data_readiness_gate_write_guard.py -q`, `.venv\Scripts\python -c "from core import boot_status as b; from scripts import boot_preflight as p; import core.data_readiness_gate as d; ..."` |
| 2026-05-26 | Data Readiness Gate v0 recovery | The boot-status path was patched to docs/context by subagents and briefly passed, then snapped back to runtime after the agents closed | Multiple live Codex/app-server streams in the shared workspace could still rewrite the same root files, and no safe single writer PID was identifiable | Stopped broad implementation, closed subagents, preserved BLOCK evidence, and did not stage or claim boot readiness | When a path sentinel flips after all patch lanes report PASS, stop immediately, keep BLOCK, and require a fresh isolated workspace or explicit process freeze before another path-lock attempt | `core/boot_status.py`, `tests/test_boot_status_contract.py`, `docs/saw_reports/saw_data_readiness_gate_v0_recovery_20260526.md`, `.venv\Scripts\python -c "from core.boot_status import BOOT_STATUS_CURRENT_PATH, DEFAULT_BOOT_STATUS_PATH; ..."` |
| 2026-05-26 | Boot status path contract | A stale `docs/context/boot_status_current.json` snapshot still claimed docs/context was canonical after runtime code had moved to `runtime/boot_status_current.json` | Snapshot evidence was treated like current runtime truth during earlier boot-control streams | Deleted the stale noncanonical snapshot, locked runtime-only reader/writer tests, and integrated Governance Gate v0 into boot preflight so GOV-000 proves root application | Never generate or preserve `docs/context/boot_status_current.json` as safe-boot evidence; runtime truth is `runtime/boot_status_current.json`, and docs/context snapshots must be explicit exports only | `core/boot_status.py`, `scripts/boot_preflight.py`, `tests/test_boot_status_contract.py`, `tests/test_boot_preflight.py`, `tests/test_boot_preflight_governance.py`, `.venv\Scripts\python scripts\governance_preflight.py --repo-root . --json`, `.venv\Scripts\python -m pytest tests\test_boot_preflight.py tests\test_boot_preflight_governance.py tests\test_boot_status_contract.py tests\test_data_readiness_gate_write_guard.py -q` |
| 2026-05-26 | Boot control stabilization | The boot-status canonical path flipped during verification after an attempted runtime-path patch, so targeted tests could pass against one contract while the live sentinel reported another | Multiple dirty boot-control streams and parked patches/artifacts were still influencing the same root files, leaving `core/boot_status.py`, docs, and tests out of sync | Stopped implementation, preserved governance/data/preflight evidence, closed subagents, and published a SAW BLOCK instead of claiming boot-ready | If the boot-status sentinel changes during a round, stop coding, freeze competing writers, choose one path contract in a single clean slice, and rerun sentinel before and after every focused suite | `core/boot_status.py`, `tests/test_boot_status_contract.py`, `tests/test_data_readiness_gate_write_guard.py`, `docs/saw_reports/saw_boot_control_stabilization_20260526.md`, `.venv\Scripts\python scripts\governance_preflight.py --repo-root . --json`, `.venv\Scripts\python scripts\run_data_readiness_gate.py --strict`, `.venv\Scripts\python -m pytest tests\test_boot_status_contract.py tests\test_data_readiness_gate_write_guard.py tests\test_boot_preflight.py tests\test_boot_preflight_governance.py tests\test_data_readiness_gate.py -q`, `.venv\Scripts\python scripts\boot_preflight.py --repo-root . --strict --json --no-tests` |
| 2026-05-15 | Strategy Replay Timeline visualization QA | The stacked replay timeline was guarded by source text but did not yet prove the actual Plotly traces were stacked step areas | The first visualization check locked the implementation string instead of exercising the rendered `go.Figure` contract | Added an executable Plotly trace regression that captures the chart and asserts stacked `weights`, `hv` line shape, marker-free traces, fixed 0-100% y-axis, and muted last `CASH` trace | Visualization behavior should have at least one rendered-figure assertion when the user-visible fix depends on trace semantics, not just source text | `dashboard.py`, `tests/test_dash_2_portfolio_ytd.py`, `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py::test_replay_timeline_uses_stacked_replay_targets tests\test_dash_2_portfolio_ytd.py::test_replay_timeline_stacked_chart_traces_are_allocation_areas -q`, `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py -q` |
| 2026-05-15 | Dashboard replay horizon asset universe | The page was mechanically single-source but the single replay source was scoped only to current signed holds, so MU was dropped from 1Y trade history after becoming flat | Replay identity hardening correctly removed broad fallbacks but did not distinguish current allocation assets from horizon lifecycle/history assets | Added horizon-aware `replay_assets`, current-only `allocation_assets`, cache identity for both, zero-weight context-only rows for history tickers, coverage pre-gate filtering, and MU/coverage/cache regressions | Single-source replay must prove its bundle universe covers the selected horizon while optimizer/PIT allocation, cache identity, and coverage emission remain current-selection-aware | `dashboard.py`, `tests/test_dash_2_portfolio_ytd.py`, `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py -q`, `.venv\Scripts\python -m pytest tests\test_optimizer_view.py tests\test_strategy_replay.py tests\test_strategy_replay_coverage.py -q` |
| 2026-05-15 | Dashboard selected-method replay runtime | YTD replay was scoped to the YTD date list but still felt like a full-history replay because each date loaded a PIT input slice from the full history start | The dashboard transitional build reused the safe per-date PIT loader pattern after the batched replay loader existed, so correctness was preserved but runtime paid repeated wide data loads | Switched the dashboard transitional replay path to one cached `load_batched_pit_replay_data(...)` call per selected window, wrapped by `build_batched_pit_input_loader(...)`, and filtered each PIT input to the signed replay assets | Forward-walk dashboard replay should bulk-load PIT source data once per selected window, then slice per date; keep signed asset filtering after any broad PIT source load | `dashboard.py`, `tests/test_dash_2_portfolio_ytd.py`, `tests/test_optimizer_view.py`, `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py -q`, `.venv\Scripts\python -m pytest tests\test_strategy_replay_coverage.py -q` |
| 2026-05-14 | Saved artifact replay aux surfaces | Saved-artifact mode could still show separately loaded ENTER/EXIT or Buy/Sell rows when the artifact had daily portfolio rows but empty event/decision rows | The adapter treated empty artifact aux frames as missing data and backfilled from fallback dashboard frames, weakening `source_mode="saved_artifact"` | Removed aux-frame fallback in `_dashboard_context_from_artifact_read(...)`, added a regression with empty saved aux rows and non-empty fallback rows, and mirrored SAW evidence under `docs/saw_reports/` | In saved-artifact mode, empty artifact surfaces are valid evidence and must be preserved exactly; any mixed-source fallback must be explicitly labeled outside `source_mode="saved_artifact"` | `dashboard.py`, `tests/test_dash_2_portfolio_ytd.py`, `docs/saw_reports/saw_frontend_ui_saved_replay_source_selector_20260514.md`, `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_position_lifecycle.py tests\test_policy_target_timeline_apptest.py -q` |
| 2026-05-14 | Saved selected-method replay artifact reader | Saved replay-output artifacts could be written but not safely consumed, leaving future readers to risk trusting stale manifest/parquet pairs or carrying prior weights on budget misses | Writer tests covered bundle atomicity, but there was no reader-side context signature, source-file signature, schema, identity, timing, or performance-budget gate | Added `read_selected_method_replay_artifact(...)`, `ReplayBudgetPolicy`, `SelectedMethodReplayResult`, DataFrame control content hashes, strict parquet identity checks, timing validation, budget-wrapped build support, CLI budget flags, and stale/mismatch/over-budget regressions | Any saved replay artifact consumer must validate parquet+manifest as a bundle, match method/controls/date/input/source signatures including DataFrame content, enforce row/date/time budgets, and return unavailable instead of stale replay output | `strategies/strategy_replay.py`, `scripts/build_strategy_replay_artifact.py`, `tests/test_strategy_replay_artifact.py`, `tests/test_strategy_replay_coverage.py`, `.venv\Scripts\python -m pytest tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py tests\test_strategy_replay_coverage.py -q --durations=12` |
| 2026-05-14 | Replay coverage contract audit | Initial closeout framed a 31s daily replay path as a timing flake and suggested threshold relaxation before proving the hot path | The audit looked only at one loaded-machine timing and missed per-date DataFrame/performance/concat work, row-heavy unavailable windows, same-date return alignment, and duplicate shadowed tests | Batched uncovered-date cash-closed rows, added fast row-heavy unavailable emission, shifted replay performance to next tradable returns, recomputed loader equity once per run, added a small-frame performance lookup, added a bound-feasible inverse-volatility fast path, removed duplicate tests, and reran focused/affected/full pytest | Performance-budget misses must be profiled before relaxing thresholds; replay performance must prove no same-date lookahead; duplicate pytest definitions are test debt and must be removed in the same audit fix | `strategies/strategy_replay.py`, `strategies/optimizer.py`, `tests/test_strategy_replay.py`, `tests/test_strategy_replay_coverage.py`, `tests/test_optimizer_core_policy.py`, `.venv\Scripts\python -m pytest tests\test_strategy_replay_coverage.py -q --durations=12`, `.venv\Scripts\python -m pytest -q` |
| 2026-05-14 | Scaled live overlay anchor | Initial freshness regressions covered stale selected-asset dropping only when another asset had overlap; they did not pin local ending `2026-02-27` and live starting `2026-05-01` for selected or benchmark overlay paths | The overlay scaler still allowed no-overlap display scaling, and evidence paths could reuse that synthetic stitch | Made `scale_live_overlay_to_local(...)` require same-column overlap by default with no permissive public flag, made benchmark overlays use the same invariant, and added no-overlap/drop regressions | Any scaled overlay that can feed allocation, YTD, optimizer, or benchmark evidence must prove a same-ticker overlap anchor; no overlap means unavailable/dropped, not synthetic continuity | `core/data_orchestrator.py`, `tests/test_data_orchestrator_portfolio_runtime.py`, `tests/test_dash_2_portfolio_ytd.py`, `.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_portfolio_universe.py -q` |
| 2026-05-13 | Selected-method replay artifact atomicity | Initial artifact tests proved temp cleanup but still allowed an orphan parquet if manifest promotion failed after parquet promotion | Writer treated parquet and manifest as two independent atomic writes instead of one evidence bundle | Staged parquet and manifest first, added rollback promotion, and added a regression that fails manifest replace after parquet replace | Saved evidence must be bundle-atomic: parquet and manifest promote together or neither remains as current evidence | `strategies/strategy_replay.py`, `tests/test_strategy_replay_artifact.py`, `.venv\Scripts\python -m pytest tests\test_strategy_replay_artifact.py -q` |
| 2026-05-13 | Selected-method replay evidence/docs handoff | Runtime patches existed, but the current docs still split backend replay, dashboard context, timeframe/PIT, and latest-trades UX rules into separate fragments | Evidence was recorded per worker lane instead of as one cross-surface selected-method source invariant | Added a combined evidence handoff across phase brief, notes, decision log, context packets, done checklist, observability, alignment, and SAW report | After parallel replay workers land, publish one docs/evidence handoff that states the source invariant, timeframe/PIT rule, latest-trades default, rollback, and open risks before claiming closure | `docs/phase_brief/phase65-brief.md`, `docs/notes.md`, `docs/context/*.md`, `docs/saw_reports/saw_backend_shared_replay_source_20260513.md`, `.venv\Scripts\python -m pytest tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py tests\test_replay_non_cash_closed.py -q`, `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_position_lifecycle.py tests\test_policy_target_timeline_apptest.py -q` |
| 2026-05-13 | Rule100 dynamic UI/replay sizing | First plan risked regenerating frozen Rule100 history at the new 35% visible UI cap | Audit/history and UI/replay paths shared softmax sizing, making default mutation or artifact rewrite look simpler than caller-specific policy | Preserved `Rule100SoftmaxConfig()` defaults, added `rule100_config_from_max_weight(max_weight)` for UI/replay only, and left `data/processed/rule100_softmax_v1_history.csv` untouched unless a versioned artifact is approved | If an artifact says audit/history/frozen, never rewrite it to match live UI controls; add a runtime adapter or versioned policy artifact and test both semantics | `strategies/rule100_softmax.py`, `strategies/strategy_replay.py`, `views/optimizer_view.py`, `tests/test_rule100_softmax.py`, `tests/test_optimizer_view.py`, `docs/saw_reports/saw_rule100_dynamic_ui_replay_ytd_20260513.md` |
| 2026-05-12 | Rule100 history overlay | Buy/sell and lifecycle history still looked like stale 10% sizing after the live Rule of 100 UI switched to softmax v1 | The history table displayed the immutable v0 event `weight` column from the lifecycle ledger, while softmax v1 existed only as current target allocation and PIT audit artifacts | Added `data/processed/rule100_softmax_v1_history.csv`, wired the transaction log to show `Event Weight` beside `Softmax v1 Target` and `Softmax v1 Cash`, and added current TSM regression coverage | Historical execution/event ledgers must not be silently repurposed as target-weight histories; add explicit overlay columns and source labels for new sizing policies | `scripts/rule100_softmax_v1_audit.py`, `dashboard.py`, `tests/test_rule100_softmax.py`, `tests/test_position_lifecycle.py`, `data/processed/rule100_softmax_v1_history.csv` |
| 2026-05-12 | Rule100 softmax v1 UI wiring | Softmax v1 artifacts existed but the live Rule of 100 UI still rendered lifecycle `last_weight`, so the screen stayed at AMAT/LRCX/TSM 10% and YTD +14.25% | The audit stack was not connected to `views/optimizer_view.py`, and docs still framed softmax as artifacts-only | Routed explicit `Rule of 100` to `softmax_v1_weights(...)`, stored `source=rule100_softmax_v1`, and added regressions proving TSM drops to 0% while cash rises to 80% | Any sizing artifact intended for a visible method must have a UI/session-state regression that proves the method consumes the new weight source, not only artifact tests | `views/optimizer_view.py`, `tests/test_optimizer_view.py`, `data/processed/rule100_softmax_v1_comparison.csv`, `.venv\Scripts\python -m pytest tests\test_optimizer_view.py tests\test_rule100_softmax.py tests\test_portfolio_universe.py tests\test_dash_2_portfolio_ytd.py -q`, `.venv\Scripts\python -m pytest -q` |
| 2026-05-12 | Rule100 softmax v1 audit | Kelly comparator initially redistributed leftover budget into zero-edge names, which made the comparator look like a second full stack instead of a thin ablation | Generic cap-and-redistribute logic was reused for Kelly without preserving the positive-edge subset boundary | Restricted Kelly to the positive-edge candidate subset and let residual cash remain explicit; kept softmax as the primary sizing path | Kelly-style comparators must never backfill cash into names with zero edge; if the comparator cannot fund only positive-edge names, the leftover stays cash | `strategies/rule100_softmax.py`, `scripts/rule100_softmax_v1_audit.py`, `tests/test_rule100_softmax.py`, `.venv\Scripts\python -m pytest tests\test_rule100_softmax.py -q`, `.venv\Scripts\python scripts\rule100_softmax_v1_audit.py --as-of-date 2026-05-12`, `.venv\Scripts\python -m pytest -q` |
| 2026-05-11 | Dashboard scanner testability hardening | Core scanner formulas lived as dashboard runtime closures and had no focused boundary tests | Streamlit orchestration, provider calls, row math, and label rules were coupled in one large `run_and_save_scan` path | Extracted deterministic scanner math to `strategies/scanner.py`, kept provider calls in `dashboard.py`, and added boundary tests plus strategy/config/ETL coverage | Scanner formula changes must land in `strategies/scanner.py` with `tests/test_scanner.py` boundary coverage before dashboard wiring is accepted | `strategies/scanner.py`, `dashboard.py`, `tests/test_scanner.py`, `tests/test_adaptive_trend.py`, `tests/test_production_config.py`, `tests/test_core_etl.py`, `.venv\Scripts\python -m pytest tests\test_scanner.py tests\test_strategy.py tests\test_phase15_integration.py tests\test_adaptive_trend.py tests\test_production_config.py tests\test_core_etl.py tests\test_process_utils.py -q` |
| 2026-03-20 | Post-phase GitHub alignment | Repo fell 30+ phases behind public GitHub; CEO handover links would 404 | No git-sync checkpoint in phase closeout SAW template | Added `CHK-PH-07` Git sync gate to SAW protocol and milestone review checklist | `git status --porcelain` empty AND `git log origin/main..HEAD --oneline` empty before phase-close SAW verdict PASS | `docs/checklist_milestone_review.md`, `.codex/skills/saw/SKILL.md` |
| 2026-02-18 | Governance bootstrap | No persistent self-learning log existed | Process control gap | Added mandatory feedback-loop policy | Append one lesson after each execution/review round | `AGENTS.md`, `docs/lessonss.md` |
| 2026-02-18 | SAW round reconciliation | Reviewer-independence proof was implied but not explicit | Missing ownership-check line item | Added explicit implementer/reviewer agent-separation check in SAW protocol | Always include ownership check in SAW report before verdict | `AGENTS.md` |
| 2026-02-19 | Interactive review governance | Review guidance from external prompt was being reapplied ad hoc | Missing standardized review-mode contract in project policy | Added Section 14 interactive review protocol to `AGENTS.md` and decision-log record | For review tasks, force mode gate + per-issue option analysis + confirmation checkpoint before implementation | `AGENTS.md`, `docs/decision log.md`, `N/A (docs-only round; no test run)` |
| 2026-02-19 | PM hierarchy and iteration loop | Top-down snapshot remained generic and leaked table formatting under mixed-width content | Snapshot contract lacked project-based hierarchy and stage-specific loop controls | Added project-based `L1/L2/L3` contract, stage-specific rows, one-stage expansion rule, and trigger-based optional skills | Keep main table at active stage level, expand only one stage when triggered, and collapse when certainty stabilizes | `AGENTS.md`, `docs/spec.md`, `docs/templates/plan_snapshot.txt`, `.codex/skills/` |
| 2026-02-19 | SAW scope deadlock prevention | Pre-existing out-of-scope High findings could block unrelated governance rounds | Reconciliation rule lacked in-scope vs inherited-scope distinction | Updated SAW/AGENTS to block only on in-scope Critical/High and carry inherited out-of-scope High findings in Open Risks | Prevent process deadlock while preserving milestone-close risk acceptance requirements | `AGENTS.md`, `.codex/skills/saw/SKILL.md`, `docs/decision log.md` |
| 2026-02-19 | Phase 17.1 scoping | No ready map of repo locations for the double-sort evaluator | Phase 17.1 requirements hadn’t been traced to concrete helpers earlier | Ran targeted repo scans, documented candidate modules, and flagged missing components before coding | Always verify that each required capability (fundamentals, returns, grouping, sorting, inference) has a documented owner before implementation | `docs/lessonss.md`, `AGENTS.md` |
| 2026-02-19 | Phase 17.1 data foundation | Legacy feature/cache schema can silently keep missing columns even after logic updates | Incremental/cache flows trusted existing artifact schema without required-column validation | Added required-column guards for cache and incremental upsert, plus forced full rewrite on schema drift; rebuilt features artifact | For factor-column migrations, always enforce schema contract before incremental writes and invalidate stale cache artifacts | `data/feature_store.py`, `scripts/evaluate_cross_section.py`, `tests/test_feature_store.py`, `tests/test_evaluate_cross_section.py`, `python data/feature_store.py --full-rebuild`, `pytest tests/test_evaluate_cross_section.py tests/test_feature_store.py -q` |
| 2026-02-19 | Phase 17.2 validation | Initial pytest run used system Python and failed import resolution for local packages | Environment discipline miss (`python` vs repo `.venv`) during fast validation loop | Standardized all test/script verification commands on `.venv\Scripts\python -m ...` | Always run build/test/smoke commands through the project venv to preserve dependency and path consistency | `tests/test_statistics.py`, `tests/test_parameter_sweep.py`, `.venv\Scripts\python -m pytest -q`, `.venv\Scripts\python scripts/parameter_sweep.py --cscv-blocks 6` |
| 2026-02-19 | Phase 17.3 checkpoint hardening | Frequent checkpoint rewrites on Windows can intermittently fail with `PermissionError` during atomic replace | Transient file-lock contention on rapid successive writes | Added atomic replace retry wrapper in sweep checkpoint writers and validated with repeated resume runs | For high-frequency artifact checkpoints on Windows, always add short retry/backoff around `os.replace` | `scripts/parameter_sweep.py`, `tests/test_parameter_sweep.py`, `.venv\Scripts\python scripts/parameter_sweep.py --output-prefix phase17_3_prep_smoke2 --keep-checkpoint` |
| 2026-02-19 | Phase 17 closeout lock crash | Lock liveness probe could hard-abort pytest/sweep process on Windows | Used POSIX-style `os.kill(pid, 0)` as a cross-platform existence check | Replaced Windows path with WinAPI liveness probe and added corrupt-lock mtime TTL fallback + regression tests | For cross-platform lock ownership checks, never use `os.kill(pid, 0)` on Windows; require OS-native process query and corrupt-metadata recovery path | `scripts/parameter_sweep.py`, `tests/test_parameter_sweep.py`, `.venv\Scripts\python -m pytest tests\test_parameter_sweep.py -k sweep_lock -vv -s`, `.venv\Scripts\python -m pytest -q` |
| 2026-02-19 | Phase 18 Day 1 baseline | Initial implementation charged turnover on synthetic cash-leg moves, overstating transaction costs | Modeling cash as an explicit traded asset under gross sum(abs(delta_w)) turnover without checking control-case economics | Refactored baseline execution to trade only SPY allocation in engine on excess-return sleeve and add cash return separately | For benchmark portfolios with residual cash, validate turnover semantics against a one-asset toggle test before accepting cost outputs | `scripts/baseline_report.py`, `tests/test_baseline_report.py`, `.venv\\Scripts\\python -m pytest tests\\test_baseline_report.py -q`, `.venv\\Scripts\\python scripts\\baseline_report.py` |
| 2026-02-19 | Phase 18 Day 1 protocol alignment | Initial Day 1 delivery used custom metric wiring and artifact names that diverged from operator contract | Scope was delivered before locking final operator interface/schema contract | Extracted SSOT metrics to `utils/metrics.py`, refactored FR-050 wrappers, and aligned baseline CLI/output schema exactly to operator spec | Before closing a milestone, run a strict contract check for CLI names, artifact naming, and schema columns against signed operator inputs | `utils/metrics.py`, `backtests/verify_phase13_walkforward.py`, `scripts/baseline_report.py`, `tests/test_metrics.py`, `tests/test_baseline_report.py`, `.venv\Scripts\python -m pytest tests\test_metrics.py tests\test_verify_phase13_walkforward.py tests\test_baseline_report.py tests\test_verify_phase15_alpha_walkforward.py -q`, `.venv\Scripts\python scripts\baseline_report.py` |
| 2026-02-19 | Phase 18 Day 2 TRI validation | Initial split continuity rule used a fixed absolute-move threshold and incorrectly failed real split-day moves | Validation logic checked raw daily move magnitude instead of consistency with causal return input | Updated split continuity test to compare `tri_pct_change` against same-day `total_ret` and regenerated Day 2 validation outputs | For corporate-action checks, validate continuity against causal return stream (`total_ret`) instead of arbitrary absolute move cutoffs | `data/build_tri.py`, `tests/test_build_tri.py`, `data/processed/phase18_day2_tri_validation.csv`, `.venv\Scripts\python -m pytest tests\test_build_tri.py -q` |
| 2026-02-20 | Phase 18 Day 3 cash overlay | Runtime crashed while building FR-050 context in Day 3 report (`TypeError` sorting mixed `Timestamp`/`int` index) | `_load_inputs` reset macro index to integer rows before calling FR-050 `_build_context`, causing index-type mismatch when liquidity frame was present | Preserved datetime index in macro context handoff and added regression test to enforce datetime-index contract | For cross-module DataFrame handoffs, assert index type before union/reindex operations and add focused regression coverage for index-shape assumptions | `scripts/cash_overlay_report.py`, `tests/test_cash_overlay.py`, `.venv\Scripts\python -m pytest tests\test_cash_overlay.py -q`, `.venv\Scripts\python scripts\cash_overlay_report.py --start-date 2015-01-01 --end-date 2024-12-31 --cost-bps 5 --target-vol 0.15 --vol-lookbacks 20,60,120` |
| 2026-02-20 | Phase 18 Day 3 hypothesis closure | Treated CHK-26 Sharpe miss as an implementation-blocking failure initially | Weak separation between execution defects and design-constraint discoveries during exploration loops | Reclassified Day 3 closure to `ADVISORY_PASS` with explicit FR-041 architectural validation and locked reference overlay | In exploration sprints, if tests/runtime pass and misses are design constraints, document as informative negative results and advance critical path instead of parameter-salvage tuning | `docs/saw_phase18_day3_round1.md`, `docs/phase18-brief.md`, `docs/decision log.md`, `data/processed/phase18_day3_overlay_metrics.csv` |
| 2026-02-20 | Phase 18 Day 4 scorecard engine | Initial scorecard pseudocode grouped/looped by date, which would scale poorly on multi-year universes | Starting template was correctness-first but not aligned with existing vectorized feature-store patterns | Implemented vectorized cross-sectional normalization/contribution pipeline and kept control toggles configurable but default OFF | For cross-sectional models over large universes, avoid per-date loops by default; loop over factor families only and use groupby/transform primitives | `strategies/factor_specs.py`, `strategies/company_scorecard.py`, `scripts/scorecard_validation.py`, `tests/test_company_scorecard.py`, `.venv\Scripts\python -m pytest tests/test_company_scorecard.py tests/test_feature_store.py -q` |
| 2026-02-20 | Phase 18 Day 4 coverage gate hardening | Validation initially over-reported score coverage because score accumulation defaulted to non-null even when contributions were absent | Coverage metric was coupled to numeric score presence rather than explicit contribution-valid mask | Added `score_valid` gating, wired validation to that mask, and added low-coverage regression test | Coverage checks must be driven by explicit validity masks, not implied non-null arithmetic outputs | `strategies/company_scorecard.py`, `scripts/scorecard_validation.py`, `tests/test_company_scorecard.py`, `.venv\Scripts\python -m pytest tests/test_company_scorecard.py tests/test_feature_store.py -q` |
| 2026-02-20 | Phase 18 Day 5 ablation execution | Initial Day 5 run exposed hidden active-return gaps and an off-by-one quantile boundary in portfolio selection | Backtest wiring assumed missing returns could be zero-filled and used inclusive percentile cutoff semantics | Added active-return fail-fast with explicit override flag, exact `ceil(q*n)` selector logic, and dense-matrix safety cap; reran full ablation and regression suite | For cross-sectional backtests, validate selected-name cardinality and active-return completeness before computing performance metrics | `scripts/day5_ablation_report.py`, `tests/test_day5_ablation_report.py`, `.venv\Scripts\python scripts/day5_ablation_report.py --allow-missing-returns`, `.venv\Scripts\python -m pytest tests/test_metrics.py tests/test_verify_phase13_walkforward.py tests/test_baseline_report.py tests/test_verify_phase15_alpha_walkforward.py tests/test_build_tri.py tests/test_feature_store.py tests/test_strategy.py tests/test_phase15_integration.py tests/test_alpha_engine.py tests/test_cash_overlay.py tests/test_company_scorecard.py tests/test_day5_ablation_report.py` |
| 2026-02-20 | Phase 18 Day 6 recovery-speed gate | First Day 6 run produced `NaN` for CHK-47 because recovery-speed computation was clipped to the 2022 test window end | Recovery metric definition required post-window observation but implementation truncated series at `test_end` | Extended recovery-speed series to continue after 2022 boundary and reran Day 6 validator | For walk-forward recovery diagnostics, allow observation horizon to extend beyond test-window end when the metric explicitly measures time-to-recovery | `scripts/day6_walkforward_validation.py`, `tests/test_day6_walkforward_validation.py`, `.venv\Scripts\python scripts/day6_walkforward_validation.py --allow-missing-returns`, `.venv\Scripts\python -m pytest tests/test_day6_walkforward_validation.py` |
| 2026-02-20 | Phase 18 closure evidence discipline | Closure drafts initially risked copying target numbers from directives instead of artifact outputs | Human instruction payload included values that diverged from generated Day 5/Day 6 files | Locked closure docs to CSV/JSON evidence and recorded any unresolved checks as accepted advisory risks | For closure rounds, treat generated artifacts as source of truth and never promote unverified narrative metrics into final records | `docs/saw_phase18_day6_final.md`, `docs/phase18_closure_report.md`, `docs/production_deployment.md`, `data/processed/phase18_day5_ablation_metrics.csv`, `data/processed/phase18_day6_summary.json` |
| 2026-02-20 | Phase 21 Day 1 stop-loss module | First trailing-activation test fixture accidentally used a price path that never became profitable after entry | Test scenario design assumed a profit transition that the deterministic fixture did not provide | Reworked test inputs to explicitly force underwater then profitable updates without relying on incidental series shape | For stage-transition tests, drive state transitions with explicit inputs rather than implicit assumptions from broad fixture trends | `tests/test_stop_loss.py`, `.venv\Scripts\python -m pytest tests/test_stop_loss.py -q` |
| 2026-02-20 | Phase 19 Alignment Sprint + Phase 21 Day 1 Governance Gate | Risk-layer implementation momentum can outrun evidence governance if delta gates are not codified first | Governance rule existed implicitly in discussion but not locked as a repo-level non-negotiable | Added explicit AGENTS rule requiring same-window/same-cost/same-engine delta metrics vs latest C3 baseline before shipping risk/execution layers | Before enabling any risk/execution layer, enforce quantified deltas and publish SAW gate verdict in the same round | `AGENTS.md`, `docs/phase19-brief.md`, `docs/saw_phase21_day1.md` |
| 2026-02-20 | Phase 21 Day 1 risk layer | Fixed ATR stops (2.0/1.5) destroyed Sharpe and exploded turnover 4.3× on current scorecard | Weak/noisy signal edge (Phase 18 advisory-pass coverage 52 %, spread 1.80) | ABORT + pivot to signal-strengthening sprint | No risk/execution layer ships without same-window/same-cost/same-engine delta gate vs C3 baseline (Sharpe ≥ -0.03, turnover ≤1.15×, MaxDD neutral, crisis reduction ≥70 %) | `scripts/phase21_day1_stop_impact.py`, `data/processed/phase21_day1_delta_metrics.csv`, `data/processed/phase21_day1_crisis_turnover.csv`, `docs/saw_phase21_day1.md` |
| 2026-02-20 | Phase 19.5 scorecard sprint | New factors + partial validity lifted coverage but regressed spread (1.80 → 1.56) and reversed crisis turnover protection | Factor correlation / regime-blind normalization / diluted quality signal in partial mode | ABORT_PIVOT + pivot to deep diagnostics | Every signal sprint must improve both coverage and spread simultaneously; crisis turnover must stay ≥70 % reduction in all windows or block | `scripts/scorecard_strengthening_sprint.py`, `data/processed/phase19_5_delta_vs_c3.csv`, `data/processed/phase19_5_crisis_turnover.csv`, `docs/saw_phase19_5_round1.md` |
| 2026-02-20 | Phase 19.6 diagnostics sprint | Regime-adaptive norm + rank-4F lifted coverage/spread but destroyed Sharpe (-1.63 delta) and crisis turnover protection | Factors/normalization not enforcing RED/AMBER governor veto (positions stay on in stress) | ABORT_PIVOT + pivot to regime-fidelity forensics | Every factor change must be audited for per-regime behavior; crisis reduction must stay ≥75 % in all windows or block | `scripts/scorecard_diagnostics_sprint.py`, `data/processed/phase19_6_delta_vs_c3.csv`, `data/processed/phase19_6_crisis_turnover.csv`, `docs/saw_phase19_6_round1.md` |
| 2026-02-20 | Phase 20 aggressive variant | Top-12 + leverage destroyed Sharpe and reversed crisis protection | Core signal insufficient for heavy concentration + leverage | ABORT_PIVOT + pivot to Minimal Viable (no leverage, Top-20) | After 5+ failed runs, relax to Minimal Viable before advancing user priorities | `data/processed/phase20_full_delta_vs_c3.csv`, `docs/saw_phase20_round2.md` |
| 2026-02-20 | Phase 20 closure | 6 consecutive runs failed to improve on C3 | Linear scorecard structural ceiling reached | Permanent lock of C3 + conviction + cash governor; pivot to advanced math track | After 6+ heuristic failures, lock safe baseline and move to first-principles models | `data/processed/phase19_5_delta_vs_c3.csv`, `data/processed/phase19_6_delta_vs_c3.csv`, `data/processed/phase19_7_delta_vs_c3.csv`, `data/processed/phase20_full_delta_vs_c3.csv`, `data/processed/phase20_round3_delta_vs_c3.csv`, `docs/saw_phase19_5_round1.md`, `docs/saw_phase19_6_round1.md`, `docs/saw_phase19_7_round1.md`, `docs/saw_phase20_round2.md`, `docs/saw_phase20_round3.md` |
| 2026-02-20 | Phase 21.1 ticker pool slice | Strict style gate generated zero long candidates on sparse daily fundamentals coverage | Method-B style constraints were valid but too sparse when both EBITDA and ROIC acceleration had to be positive simultaneously | Added deterministic fallback long selection (top-K by compounder probability) while preserving strict style gate telemetry | Keep strict style gate as audit signal, but require a documented deterministic fallback path when gate cardinality is zero | `strategies/ticker_pool.py`, `strategies/company_scorecard.py`, `scripts/phase21_1_ticker_pool_slice.py`, `tests/test_ticker_pool.py`, `data/processed/phase21_1_ticker_pool_sample.csv` |
| 2026-02-20 | Phase 21.1 hardening (round1.2) | Static centroid drift and ad-hoc probability mapping weakened archetype stability across quarters | Centroid update lacked explicit quarterly seed anchoring and probability mapping lacked explicit eCDF contract | Implemented Ledoit-Wolf/manual constant-correlation shrinkage, quarterly dynamic centroid (seed + top-30 KNN expansion), and daily average-rank eCDF probability with audit summary JSON | For archetype layers, lock deterministic quarterly centroid rules and eCDF mapping, then gate with explicit archetype checks (TZA/PLUG out + seed presence when available) | `strategies/ticker_pool.py`, `scripts/phase21_1_ticker_pool_slice.py`, `tests/test_ticker_pool.py`, `data/processed/phase21_1_ticker_pool_sample.csv`, `data/processed/phase21_1_ticker_pool_summary.json` |
| 2026-02-20 | Phase 21.1 final hardening (round1.3) | Dense-cluster gravity still pulled centroid toward defensives despite quarterly KNN expansion | Unweighted KNN centroid treated all top-30 neighbors equally, allowing high-density defensive cluster to dominate seed intent | Added distance-weighted centroid (`exp(-3.0 * dist_to_seed)`) over top-30 neighbors with fixed seed-anchor reference and explicit defensive-share gate in summary | When dynamic centroids are used, require weighted anchor retention plus explicit dominance checks (seed presence threshold + defensive share <50%) before advancing | `strategies/ticker_pool.py`, `scripts/phase21_1_ticker_pool_slice.py`, `data/processed/phase21_1_ticker_pool_sample.csv`, `data/processed/phase21_1_ticker_pool_summary.json`, `docs/saw_phase21_round1_3.md` |
| 2026-02-20 | Phase 21.1 final hardening attempt (round1.4) | Stronger anchoring (`lambda=8.0`) and cyclical feature upweighting (2.5x) improved anchor retention but failed strict dominance gate | Defensive cluster remained persistent in late-2024 cross-section and available seed set was only MU/CIEN (COHR/TER missing), limiting style concentration in top longs | Applied lambda=8.0 + cyclical feature re-weighting + stricter archetype checks in summary/SAW; preserved PIT-safe pipeline and reran full validations | Before advancing to new phase, require both strict dominance metrics to pass together (`defensive <35%` and `MU-style >=4 in top-12`), otherwise pivot direction explicitly | `strategies/ticker_pool.py`, `strategies/company_scorecard.py`, `scripts/phase21_1_ticker_pool_slice.py`, `data/processed/phase21_1_ticker_pool_sample.csv`, `data/processed/phase21_1_ticker_pool_summary.json`, `docs/saw_phase21_round1_4.md` |
| 2026-02-20 | Phase 21 final leverage run | Binary leverage path lacked auditable risk accounting (beta cap visibility, net/gross contract, borrow-cost traceability) | Prior implementation focused on entry heuristics and did not expose leverage risk controls as first-class outputs | Replaced leverage path with target-vol + sigmoid jump veto + EMA10 + pre/post beta capping and strict net/gross + daily borrow-cost accounting columns | Any leverage change must ship with explicit artifact columns (`leverage_multiplier`, `portfolio_beta`, `gross_exposure`, `net_exposure`, `borrow_cost_daily`) plus range/cap/accounting checks in the slice summary | `strategies/company_scorecard.py`, `scripts/phase21_1_ticker_pool_slice.py`, `tests/test_company_scorecard.py`, `data/processed/phase21_1_ticker_pool_sample.csv`, `data/processed/phase21_1_ticker_pool_summary.json`, `docs/saw_phase21_round2_1.md` |
| 2026-02-20 | Phase 21 final odds fix (round2.2) | Posterior-odds hard gate removed defensive names but still failed archetype intent (PLUG entered top-8; MU-style remained 2/12) | Odds vs defensive alone over-favored names far from defensive cluster without enforcing seed-style proximity | Implemented odds score + hard gate + posterior integrity checks, then blocked round at decision gate due archetype failure | Odds-only ranking is not sufficient acceptance evidence; require explicit archetype checks (`TZA/PLUG out`, seed presence, MU-style >=4/12`) to pass together before promotion | `strategies/ticker_pool.py`, `strategies/company_scorecard.py`, `scripts/phase21_1_ticker_pool_slice.py`, `data/processed/phase21_1_ticker_pool_sample.csv`, `data/processed/phase21_1_ticker_pool_summary.json`, `docs/saw_phase21_round2_2.md` |
| 2026-02-20 | Phase 21 final odds-vs-junk fix (round2.2 rerun) | Odds-vs-junk cleaned defensive/TZA-PLUG gate but still failed core archetype (seed presence false, MU-style 0/12) | Current feature space and centroid geometry still prioritize non-seed tech names under hard `S>0` gate | Added junk-aware posterior odds, resilient integrity telemetry, and blocked promotion at gate | Even with mathematically cleaner odds, promotion requires simultaneous pass on seed-presence + MU-style breadth; no Phase 22 until both are green | `strategies/ticker_pool.py`, `strategies/company_scorecard.py`, `scripts/phase21_1_ticker_pool_slice.py`, `data/processed/phase21_1_ticker_pool_sample.csv`, `data/processed/phase21_1_ticker_pool_summary.json`, `docs/saw_phase21_round2_2.md` |
| 2026-02-21 | Phase 21 final finetune (round2.3) | Quality-triplet fallback initially treated all-NaN preferred columns as valid sources and collapsed long selection (`0 LONG`) | Candidate-selection logic checked column existence instead of non-null availability before fallback | Switched to first non-empty source selection (`gm_accel_q -> operating_margin_delta_q -> ebitda_accel`, `revenue_growth_q -> revenue_growth_yoy -> revenue_growth_lag`) and reran slice/tests | For ordered fallback fields, always select by non-null coverage, not schema presence; add telemetry gates (`min_odds_ratio_top8`) before promotion | `strategies/ticker_pool.py`, `strategies/company_scorecard.py`, `scripts/phase21_1_ticker_pool_slice.py`, `data/processed/phase21_1_ticker_pool_sample.csv`, `data/processed/phase21_1_ticker_pool_summary.json`, `.venv\\Scripts\\python -m pytest tests/test_ticker_pool.py tests/test_company_scorecard.py -q` |
| 2026-03-05 | Phase 33B escalation | Integration tests recreated dashboard initialization logic instead of calling actual production code | Test fidelity gap - tests validated reimplementation not production runtime path | Extracted dashboard escalation init to shared function (core/dashboard_escalation.py) callable by both dashboard.py and tests | For dashboard lifecycle features, extract initialization to shared module and call from both runtime and tests to ensure test fidelity | `core/dashboard_escalation.py`, `dashboard.py:1002`, `tests/test_dashboard_integration.py`, 43 tests passing |
| 2026-02-21 | Phase 21.1 anchor centroid injection | Anchor centroid update alone did not guarantee anchor names surfaced in top-long ranks under raw odds ordering | Ranking score prioritized high posterior odds from non-anchor lookalikes despite anchor-centered geometry | Added anchor-injected daily centroid, explicit pre-pool `score_col` guard, and anchor-priority bonus in `odds_score` while keeping MahDist hard ceiling and odds telemetry | When an archetype basket is the explicit target, enforce ranking alignment explicitly and regression-test forbidden circular score columns | `strategies/ticker_pool.py`, `tests/test_ticker_pool.py`, `scripts/phase21_1_ticker_pool_slice.py`, `scripts/phase21_1_odds_diagnostic.py`, `data/processed/phase21_1_ticker_pool_sample.csv`, `data/processed/phase21_1_diagnostic_odds_2024-12-24.csv` |
| 2026-02-21 | Phase 21.1 Path1 directive telemetry | Sector/industry context existed in static map but was not guaranteed inside conviction frame before pool ranking, leaving Path1 audit fields implicit | Context merge responsibility sat outside scorecard conviction builder and output schema lacked explicit directive fields | Added deterministic permno-first/ticker-fallback sector map attach before `rank_ticker_pool` and emitted `DICTATORSHIP_MODE` + Path1 telemetry in sample/summary artifacts | For any directive-driven ranking path, enforce pre-rank context attachment in the same module and ship explicit mode/directive telemetry fields in exported artifacts | `strategies/company_scorecard.py`, `scripts/phase21_1_ticker_pool_slice.py`, `docs/notes.md`, `docs/decision log.md`, `.venv\\Scripts\\python -m py_compile strategies/company_scorecard.py scripts/phase21_1_ticker_pool_slice.py` |
| 2026-02-21 | Phase 22 Path1 reconciliation hardening | Deterministic sector-balanced resampling could be disabled by `UNKNOWN` context rows and projection fallback could continue with unneutralized geometry | Resample depth check counted `UNKNOWN` bucket and residualization fallback did not fail closed | Excluded `UNKNOWN` from known-sector resample depth, added critical skip on projection non-finite fallback, added explicit sparse-slice warning logs, and exposed `--dictatorship-mode on/off` for controlled de-anchor runs | For geometry-gated models, ensure fallback paths cannot silently continue with untrusted transforms and keep mode toggles externally controllable for OOS experiments | `strategies/ticker_pool.py`, `strategies/company_scorecard.py`, `scripts/phase21_1_ticker_pool_slice.py`, `data/processed/phase21_1_ticker_pool_summary.json`, `.venv\\Scripts\\python -m pytest tests/test_ticker_pool.py tests/test_company_scorecard.py -q` |
| 2026-02-21 | Phase 22 separability harness | Initial silhouette telemetry came back all-NaN on most days | Runtime had `sklearn.metrics` unavailable while score path only attempted sklearn silhouette | Added deterministic manual silhouette fallback + posterior argmax NA-safe labeling and reran baseline telemetry | For diagnostics that depend on optional deps, always ship deterministic fallback math and keep one-class days as explicit NaN coverage events | `scripts/phase22_separability_harness.py`, `tests/test_phase22_separability_harness.py`, `data/processed/phase22_separability_daily.csv`, `data/processed/phase22_separability_summary.json`, `.venv\\Scripts\\python -m pytest tests/test_phase22_separability_harness.py -q` |
| 2026-02-22 | Phase 23 Step 1 ingest scaffold | Initial ingest write path would overwrite output parquet with empty datasets on total fetch/mapping failure | Output writes were unconditional after fetch loop without empty-result safety gate | Added fail-safe guards to skip writes when `raw` or `processed` is empty and log explicit failure context; added PIT and mapping tests | For external API ingests, never overwrite last-known-good artifacts when fetch/mapping cardinality collapses to zero; fail closed and preserve prior data | `scripts/ingest_fmp_estimates.py`, `tests/test_ingest_fmp_estimates.py`, `.venv\\Scripts\\python -m pytest tests/test_ingest_fmp_estimates.py -q` |
| 2026-02-22 | Phase 23 Step 1.1 rate-aware ingestion | Cache-first + scoped-universe behavior was missing, making API-credit and rate-limit failure paths brittle | Initial implementation focused on schema correctness but not quota-aware orchestration | Added per-ticker JSON cache, scoped universe (`--tickers-file` + cap), 429 backoff strategy, crosswalk prefilter, and deterministic merge override for new rows | For paid/API-limited ETL, design cache-first and rate-limit control paths in the first implementation round, not as a later patch | `scripts/ingest_fmp_estimates.py`, `tests/test_ingest_fmp_estimates.py`, `data/raw/fmp_target_tickers.txt`, `.venv\\Scripts\\python -m pytest tests/test_ingest_fmp_estimates.py tests/test_ticker_pool.py tests/test_company_scorecard.py -q` |
| 2026-02-22 | Phase 23 Step 2 SDM assembler | `merge_asof` failed with `left keys must be sorted` after sorting by `gvkey` first | Assumed group-first sort was sufficient for `merge_asof(..., by=...)`; pandas requires global monotonic order on the timeline key | Reordered joins to timeline-first sort (`published_at_dt/pit_date` then `gvkey`) and added explicit sortedness assertions + regression tests | For every `merge_asof`, enforce global monotonic key assertions before join and include a test fixture with interleaved entity timelines | `scripts/ingest_compustat_sdm.py`, `scripts/assemble_sdm_features.py`, `tests/test_ingest_compustat_sdm.py`, `tests/test_assemble_sdm_features.py`, `.venv\\Scripts\\python -m pytest tests/test_ingest_compustat_sdm.py tests/test_assemble_sdm_features.py -q` |
| 2026-02-22 | Phase 23 Step 2.1 feed-horizon gate | Configurable asof tolerance let stale macro/factor data bleed into newer fundamentals when operator args drifted | Tolerance policy was parameterized instead of pinned to operational risk budget | Locked assembler to strict `14d` tolerance, added stale-null warning telemetry, and removed CLI override | For feed-conditioned asof joins, lock tolerance in code and emit explicit nulled-row counts against no-tolerance baseline every run | `scripts/assemble_sdm_features.py`, `tests/test_assemble_sdm_features.py`, `.venv\\Scripts\\python scripts/assemble_sdm_features.py --dry-run`, `.venv\\Scripts\\python -m pytest tests/test_assemble_sdm_features.py -q` |
| 2026-02-22 | Phase 23 Step 6 manifold swap | Dual-read adapter merge failed at runtime due timezone mismatch on `date` key (`datetime64[us]` vs tz-aware dtype) | Loader normalized date after merge path instead of before join, so parquet sources with mixed tz metadata conflicted | Normalized both sides to UTC-naive timestamps before `[date, permno]` merge and added loader regression tests | For any cross-artifact key merge, normalize datetime keys to UTC-naive before dedupe/sort/merge; add a targeted loader test for mixed-source timestamps | `scripts/phase20_full_backtest.py`, `tests/test_phase20_full_backtest_loader.py`, `.venv\\Scripts\\python scripts/phase21_1_ticker_pool_slice.py --start-date 2024-01-01 --as-of-date 2024-12-24 --top-longs 5 --short-excerpt 5 --dictatorship-mode on --output-csv data/processed/phase23_action2_smoke_sample.csv --output-summary-json data/processed/phase23_action2_smoke_summary.json`, `.venv\\Scripts\\python -m pytest tests/test_phase20_full_backtest_loader.py tests/test_ticker_pool.py tests/test_company_scorecard.py -q` |
| 2026-02-22 | Phase 23 Step 6.1 geometry stability | Sparse SDM features caused universe collapse because geometry path required complete-case non-null rows | Implicit `notna().all(axis=1)` filter acted like hidden `dropna` on mixed-frequency inputs (quarterly/annual/daily) | Added hierarchical PIT imputation (industry median then neutral zero) before robust scaling and aligned harness geometry reconstruction to same path | In mixed-frequency manifolds, never allow complete-case filtering to gate universe eligibility; always impute in a documented hierarchy and publish before/after universe telemetry | `strategies/ticker_pool.py`, `scripts/phase22_separability_harness.py`, `tests/test_ticker_pool.py`, `.venv\\Scripts\\python -m pytest tests/test_ticker_pool.py tests/test_phase22_separability_harness.py tests/test_company_scorecard.py -q`, `.venv\\Scripts\\python scripts/phase22_separability_harness.py --start-date 2024-12-01 --as-of-date 2024-12-24 --dictatorship-mode off --output-csv data/processed/phase22_separability_daily_action2.jsonfix.csv --output-summary-json data/processed/phase22_separability_summary_action2.jsonfix.json` |
| 2026-02-22 | Phase 23 closeout robustness | Outlier-heavy industry cross-sections and dense covariance coupling can mask true cyclical trough geometry despite broad universe recovery | Peer baselines and covariance assumptions were not robust enough to mega-cap skew and fat-tail overlap | Locked median peer-neutralization and diagonal covariance mode, then validated with positive mean silhouette before phase close | For phase-close promotion gates, require outlier-robust peer baselines + stable covariance mode and freeze manifold/ranker/hyperparameters immediately after approval | `strategies/ticker_pool.py`, `strategies/company_scorecard.py`, `docs/phase_brief/phase23-brief.md`, `docs/decision log.md`, `data/processed/phase22_separability_summary_action2_outlierskewfix.json` |
| 2026-02-22 | Governance phase-end closeout | Phase completion steps were partially implied across SAW/checklists but not codified into one enforceable protocol | Closure requirements existed in multiple files without a single hard-gated phase-end contract | Added mandatory SAW phase-end protocol with full-suite test checks, subagent E2E replay, PM handover template, and `/new` confirmation packet gate | Before closing any phase, require `CHK-PH-01..CHK-PH-05`, `docs/handover/phase<NN>_handover.md`, and `ConfirmationRequired: YES` before next-phase execution | `.codex/skills/saw/SKILL.md`, `.codex/skills/saw/references/phase_end_handover_template.md`, `.codex/skills/saw/agents/openai.yaml`, `docs/checklist_milestone_review.md`, `docs/decision log.md` |
| 2026-02-22 | Core module refactor Stage 2 | Moving core modules out of root can silently break imports across scripts/backtests/tests if migration skips one path | High fan-out dependency graph around `engine` and mixed import styles (`import engine` vs `from engine import ...`) | Applied shim-first migration (`core/` move -> import rewrite -> scan -> shim removal) and verified entrypoint dry-run + full test run evidence | For high fan-out refactors, require explicit shim lifecycle and a zero-root-import grep gate before shim destruction | `core/__init__.py`, `core/engine.py`, `core/etl.py`, `core/optimizer.py`, `app.py`, `backtests/verify_phase15_alpha_walkforward.py`, `backtests/optimize_phase16_parameters.py`, `scripts/*.py`, `tests/test_engine.py`, `.venv\\Scripts\\python launch.py --help`, `.venv\\Scripts\\python -m pytest -q` |
| 2026-02-22 | Phase 20 closure package | Closure narrative and runtime ranker diverged after exploratory sweeps (supercycle formula still active during wrap prep) | Lock-state governance gap between experiment branches and milestone-close checklist | Restored Option A ranker in `strategies/ticker_pool.py`, then published explicit lock formulas in brief/notes/handover | Before phase close, run a lock-state parity check: code formula, brief formula, and handover formula must match exactly | `strategies/ticker_pool.py`, `docs/phase_brief/phase20-brief.md`, `docs/notes.md`, `docs/handover/phase20_handover.md` |
| 2026-02-23 | Context bootstrap governance | Phase-close `/new` packet could drift because generated context artifacts were not explicitly refreshed/validated | Context bootstrap steps were implied in handover flow but missing as a hard closure gate | Added explicit SAW/checklist/runbook contracts for context artifact refresh + build-script validation and documented schema/markdown packet contracts | At every phase close, require `docs/context/current_context.json` + `docs/context/current_context.md` regeneration and `.venv\Scripts\python scripts/build_context_packet.py --validate` pass before verdict | `.codex/skills/saw/SKILL.md`, `docs/checklist_milestone_review.md`, `docs/runbook_ops.md`, `docs/decision log.md`, `docs/notes.md`, `docs/lessonss.md`, `N/A (docs-only round; no test run)` |
| 2026-02-23 | Context bootstrap implementation | Parser originally broke round-trip when canonical markdown (`## What Was Done`...) was pasted back into handover docs | Extraction logic stopped context block on first heading after `New Context Packet` | Updated parser to allow canonical section headings inside the block; added tests for markdown-style source parsing + markdown/json parity validation | When generating canonical context artifacts, enforce bidirectional compatibility tests (source->artifact and artifact-style->source parse) before closing the round | `scripts/build_context_packet.py`, `tests/test_build_context_packet.py`, `docs/context/current_context.json`, `docs/context/current_context.md` |
| 2026-02-23 | Phase 23 Round 7 macro gates | Initial hard-gate draft used fixed drawdown cutoffs for slow-bleed/deep-drawdown flags, violating adaptive-rule intent | First implementation blended legacy fixed thresholds with adaptive labels during fast delivery | Replaced fixed drawdown thresholds with rolling/adaptive z-score labels and updated tests/docs to the z-score contract | For regime labels, enforce adaptive-statistic-only trigger checks in code review (no absolute drawdown cutoffs unless explicitly approved) | `data/macro_loader.py`, `tests/test_macro_loader.py`, `docs/spec.md`, `docs/notes.md`, `.venv\\Scripts\\python -m pytest tests/test_macro_loader.py tests/test_updater_parallel.py tests/test_regime_manager.py -q` |
| 2026-02-23 | Phase 23 Round 8 gate consumption | First consumption draft risked treating gate outputs as same-day controls by omission in strategy path comments/tests | Existing regime loader had shift discipline for regime state only, not explicit gate control bundle | Added explicit shifted control contract for `state/scalar/cash_buffer/momentum_entry` in loader + tests and validated with 5-year baseline run | For any new gate/control artifact, enforce a single function that shifts every control field together and regression-test the warmup defaults | `scripts/phase20_full_backtest.py`, `tests/test_phase20_macro_gates_consumption.py`, `tests/test_regime_manager.py`, `data/processed/phase23_baseline_macro_summary.json` |
| 2026-02-23 | Phase 23 Round 9 softmax sizing | `tests/test_ticker_pool.py` drifted to legacy matrix/anchor contracts after raw-geometry rollback, masking true behavior | Tests were not updated when production ranker contract was simplified | Rewrote ticker-pool tests to assert raw-geometry score/telemetry contract and added GREEN softmax sizing (`temperature=1.0`) in Phase 20 planner | When ranker contracts are intentionally simplified, update tests to the active production contract in the same round and re-run targeted plus full-suite health checks | `tests/test_ticker_pool.py`, `scripts/phase20_full_backtest.py`, `data/processed/phase23_softmax_sizing_summary.json`, `pytest -q tests/test_ticker_pool.py tests/test_company_scorecard.py`, `pytest -q` |
| 2026-02-23 | Phase 23 Round 10 WFO temperature | Re-running OOS candidates during parameter search can silently leak selection bias | Backtest wrappers often blend train/test loops when optimizing one hyperparameter | Added dedicated IS grid loop (`2020-2022`), selected `T*` by IS Sharpe only, then executed exactly one OOS run (`2023-2024`) and wrote combined artifact | For WFO sweeps, hard-code train/test windows and enforce a single final OOS pass for the selected parameter | `scripts/optimize_softmax_temperature.py`, `data/processed/phase23_wfo_temperature_summary.json`, `.venv\\Scripts\\python scripts/optimize_softmax_temperature.py` |
| 2026-02-23 | Phase 23 Round 11 starvation/cap overlay | Single-day PM diagnostics can mislead when requested date falls outside local feature coverage window | Diagnostic script initially picked nearest available date mechanically, which landed on a low-breadth edge day and obscured gate breadth behavior | Restored bounded fundamental continuity fill, added explicit softmax breadth/cap guards, and updated diagnostic dump to report closest valid day with hard-gate universe and capped weights | For PM one-day telemetry requests, always emit requested date plus resolved valid date and include explicit coverage constraint notes when source panel does not contain the requested period | `strategies/company_scorecard.py`, `scripts/phase20_full_backtest.py`, `scripts/diagnostic_softmax_weights.py`, `.venv\\Scripts\\python scripts/diagnostic_softmax_weights.py`, `.venv\\Scripts\\python -m pytest -q` |
| 2026-02-23 | Phase 23 wrap freeze | No `.git` metadata in workspace makes rollback fragile after phase pivot | Revert path depended on memory/manual file hunting instead of deterministic snapshot state | Added manifest-backed freeze/restore scripts with SHA256 integrity and latest-pointer index, then generated a full Phase 23 snapshot | For every phase wrap in no-git environments, generate a manifest snapshot + dry-run restore proof before pivoting to new data domain | `scripts/phase23_freeze_pack.py`, `scripts/phase23_restore_from_freeze.py`, `data/processed/phase23_freeze_latest.json`, `data/processed/phase23_freeze/phase23_freeze_20260223_131534Z/manifest.json`, `.venv\\Scripts\\python scripts/phase23_freeze_pack.py --top-results-limit 12`, `.venv\\Scripts\\python scripts/phase23_restore_from_freeze.py --dry-run --code-only` |
| 2026-02-24 | Phase 25B Osiris macro semantics | Initial interpretation risked sign confusion between inventory level and inventory turnover | Signal hypothesis was phrased in inventory-bloat terms while implementation metric used turnover ratio | Locked explicit semantic mapping in docs and notes (`low turnover = glut = bearish`; `high turnover = efficient = bullish`) and recorded IC evidence in pivot decision | For ratio-based macro proxies, always document numerator/denominator sign physics and expected IC sign before validation review | `data/osiris_loader.py`, `scripts/align_osiris_macro.py`, `docs/notes.md`, `docs/spec.md`, `docs/decision log.md` |
| 2026-02-26 | P0-2 execution hardening | Non-interactive console path could auto-generate broker payloads without explicit human confirmation and payload safety used `assert` guards | Safety checks relied on interpreter-dependent assertions and permissive non-TTY defaults | Added explicit non-TTY confirmation contract (`TZ_EXECUTION_CONFIRM=YES`), replaced payload assertions with fail-closed validation, added deterministic batch/idempotency metadata, and added duplicate-symbol/order-size protections + tests | For production-impacting order generation, require explicit confirmation in non-interactive sessions and enforce risk checks via explicit exceptions (never `assert`) | `execution/confirmation.py`, `main_console.py`, `scripts/execution_bridge.py`, `execution/rebalancer.py`, `execution/broker_api.py`, `tests/test_execution_controls.py`, `.venv\\Scripts\\python -m pytest tests/test_execution_controls.py -q` |
| 2026-02-26 | P1 dependency/control-plane lock | Runtime checks could pass in `.venv` but fail in system Python because dependency manifests and operator commands were not uniformly enforced | Manifest drift (`pyproject.toml` vs `requirements.txt`) and legacy bare `python` runbook commands allowed interpreter ambiguity | Unified dependency pins across manifests, enforced `.venv\Scripts\python` in operational docs/governance commands, and moved pytest cache to `.venv/.pytest_cache` to bypass root ACL failure path | For every environment/governance round, enforce manifest parity plus venv-only command examples and add a cache-dir control-plane path that is writable in CI/local shells | `pyproject.toml`, `requirements.txt`, `docs/runbook_ops.md`, `AGENTS.md`, `docs/decision log.md`, `.venv\\Scripts\\python -m pytest -q tests/test_phase20_macro_gates_consumption.py tests/test_phase20_full_backtest_loader.py tests/test_regime_manager.py tests/test_execution_controls.py` |
| 2026-02-26 | P1 control-plane test coverage | Orchestrator safety/scheduling behavior was previously validated by manual runs but not locked by direct tests | Test coverage focused on downstream execution modules and missed top-level control-plane entrypoints (`main_console.py`, `main_bot_orchestrator.py`) | Added dedicated orchestrator test suites with monkeypatched control seams and deterministic branch assertions for abort/confirm/schedule paths | For each production control-plane script, require direct branch coverage for non-interactive safety, subprocess failure tolerance, and scheduler disarm behavior before declaring milestone complete | `tests/test_main_console.py`, `tests/test_main_bot_orchestrator.py`, `.venv\\Scripts\\python -m pytest -q tests/test_main_console.py tests/test_main_bot_orchestrator.py tests/test_execution_controls.py`, `docs/decision log.md` |
| 2026-02-26 | P2 app thin-layer slice | `app.py` accumulated data-access and control-state logic, making UI changes risky and hard to test in isolation | Early architecture mixed Streamlit presentation with heavy loading/orchestration code paths in one file | Extracted non-UI responsibilities into `data/dashboard_data_loader.py` and `core/dashboard_control_plane.py`, then left `app.py` as cached wrappers + routing/rendering | For each future `app.py` reduction step, first define a pure service boundary with direct tests, then replace in-app logic with a thin wrapper to preserve behavior | `app.py`, `data/dashboard_data_loader.py`, `core/dashboard_control_plane.py`, `tests/test_dashboard_control_plane.py`, `tests/test_dashboard_data_loader.py`, `.venv\\Scripts\\python -m pytest -q tests/test_dashboard_control_plane.py tests/test_dashboard_data_loader.py tests/test_main_console.py tests/test_main_bot_orchestrator.py tests/test_execution_controls.py` |
| 2026-02-28 | P0 execution-safety remediation | Critical safety gaps were split across multiple write/execution paths (secrets in source, fail-open subprocess behavior, and non-serialized patch writes) | Control-plane hardening had been incremental, so critical guardrails were not enforced as one fail-closed boundary | Removed hardcoded secrets, enforced live break-glass in broker init, added subprocess timeout+non-zero hard-stop semantics, and routed JIT/update patch writes through a single lock+atomic facade with targeted tests | For any production-adjacent execution round, enforce a P0 bundle gate: `secrets scrub + live break-glass + subprocess hard-stop + single atomic write facade` before any strategy/feature work | `scripts/scout_drone.py`, `main_bot_orchestrator.py`, `execution/broker_api.py`, `data/updater.py`, `views/jit_patch.py`, `tests/test_main_bot_orchestrator.py`, `tests/test_execution_controls.py`, `tests/test_updater_parallel.py`, `.venv\\Scripts\\python -m pytest tests/test_updater_parallel.py tests/test_main_bot_orchestrator.py tests/test_execution_controls.py -q`, `docs/runbook_ops.md`, `docs/decision log.md` |
| 2026-02-28 | P1 closeout implementer validation | P1 safety hardening existed in code/tests, but closure evidence was fragmented and not packaged into one operator-facing validation path | Verification focus drifted across modules (`engine`, `execution`, `fundamentals`) without a single checklist-driven closeout artifact | Built one docs-as-code validation bundle: targeted proof commands in runbook, decision-log closeout entry, formula mapping in notes, and SAW report skeleton with explicit CHK IDs/scope split | For milestone closeout, always publish one consolidated evidence map tying each target behavior to file:line proof and reproducible `.venv` commands in the same round | `docs/runbook_ops.md`, `docs/decision log.md`, `docs/notes.md`, `docs/saw_reports/saw_p1_closeout_impl_validation_skeleton.md`, `.venv\\Scripts\\python -m pytest tests/test_engine.py tests/test_execution_controls.py tests/test_fundamentals_updater_checkpoint.py -q` |
| 2026-02-28 | P1 reconciliation hardening | First reconciliation pass fixed headline defects but missed semantic-corruption edge cases in checkpoint metadata/rows until second reviewer deep-dive | Initial verification focused on syntax/branch paths and did not include malformed-but-valid-JSON or semantically invalid checkpoint-row probes | Added semantic checkpoint payload validation, checkpoint-row integrity gates, and dedicated corruption-path tests; reran full targeted matrix | For checkpointed state machines, always test three corruption classes: invalid JSON, valid JSON with invalid field types, and semantically invalid data rows before closure | `data/fundamentals_updater.py`, `tests/test_fundamentals_updater_checkpoint.py`, `.venv\\Scripts\\python -m pytest tests/test_fundamentals_updater_checkpoint.py tests/test_updater_parallel.py -q`, `.venv\\Scripts\\python -m pytest tests/test_execution_controls.py tests/test_fundamentals_updater_checkpoint.py tests/test_missing_returns_cli_defaults.py tests/test_missing_returns_execution_masks.py tests/test_engine.py tests/test_day5_ablation_report.py tests/test_day6_walkforward_validation.py tests/test_updater_parallel.py tests/test_phase20_full_backtest_loader.py tests/test_phase20_macro_gates_consumption.py tests/test_main_console.py tests/test_main_bot_orchestrator.py -q` |
| 2026-02-28 | P2 auto-backtest infrastructure UI | Initial extraction pass persisted only \"finished\" cache status and used a fixed temp-file name, which could lose failure observability and create concurrent temp-file collision risk | First implementation focused on functional split parity and underweighted multi-writer/failure-path semantics for cache persistence | Added explicit failed-state transition write on simulation exceptions and switched atomic cache temp path to unique `target.pid.epoch_ms.tmp`; extended tests for failed status/invalid status guard | For any new cache/control-plane path, require failure-state persistence and collision-safe temp-file naming in the first patch, then validate both with targeted tests before closure | `core/auto_backtest_control_plane.py`, `views/auto_backtest_view.py`, `tests/test_auto_backtest_control_plane.py`, `.venv\\Scripts\\python -m pytest -q tests/test_auto_backtest_control_plane.py`, `.venv\\Scripts\\python -m py_compile core/auto_backtest_control_plane.py views/auto_backtest_view.py app.py` |
| 2026-02-28 | P2 auto-backtest SAW reconciliation | Cost-unit interpretation between UI and control-plane remained ambiguous under edge inputs and required reviewer-driven rework | `cost_bps` normalization accepted mixed units implicitly, while UI exposed bps labels; seam-level contract was not explicitly tested | Added explicit `cost_bps_unit` contract (`rate`/`bps`), wired UI to pass decimal rate + explicit unit token, and added dedicated view seam test for bps conversion | For any user-entered numeric control with units, codify unit tokens in payload contracts and add at least one seam-level test that validates label-to-runtime conversion | `core/auto_backtest_control_plane.py`, `views/auto_backtest_view.py`, `tests/test_auto_backtest_control_plane.py`, `tests/test_auto_backtest_view.py`, `.venv\\Scripts\\python -m pytest -q tests/test_auto_backtest_control_plane.py tests/test_auto_backtest_view.py` |
| 2026-02-28 | Phase 25 orchestrator SAW closure | First orchestration reconciliation closed one High path but left malformed-row and intent-anchor edge cases open until second reviewer deep dive | Retry-loop validation initially focused on happy-path/timeout branches and under-tested downstream row-shape and row-order drift adversarial cases | Added CID-completeness reconciliation, duplicate-symbol preflight guard, intent anchoring to original pending payload, malformed-row filtering (`non-dict result`), and targeted adversarial tests; reran reviewer A/B/C rechecks to PASS | For execution control-plane retries, always run adversarial tests for partial batches, malformed rows, and downstream order-echo drift before SAW close | `main_bot_orchestrator.py`, `tests/test_main_bot_orchestrator.py`, `.venv\\Scripts\\python -m pytest -q tests/test_main_bot_orchestrator.py tests/test_auto_backtest_view.py tests/test_auto_backtest_control_plane.py tests/test_main_console.py tests/test_execution_controls.py`, `docs/saw_reports/saw_phase25_round1.md` |
| 2026-02-28 | Phase 26 runtime debt burn-down | Initial runtime debt patch addressed core risks but still missed container/schema malformed edge paths and daemon fail-dead behavior until reviewer-driven recheck | First patch validated happy-path timeout wiring but not all malformed downstream shapes and scheduler exception survivability | Added non-list batch guard, missing-`ok` malformed-result guard, scheduler exception containment, Windows `taskkill` return-code validation, rebalance non-zero exit signaling, and script-level regression tests | For orchestration control planes, enforce both structural-fault tests (container/schema corruption) and daemon-liveness tests (loop survives run failures) before closure | `main_bot_orchestrator.py`, `tests/test_main_bot_orchestrator.py`, `scripts/test_rebalance.py`, `tests/test_test_rebalance_script.py`, `.venv\\Scripts\\python -m pytest -q tests/test_main_bot_orchestrator.py tests/test_test_rebalance_script.py tests/test_main_console.py tests/test_execution_controls.py tests/test_auto_backtest_view.py tests/test_auto_backtest_control_plane.py`, `docs/saw_reports/saw_phase26_round1.md` |
| 2026-02-28 | Phase 27 conditional-block remediation | Initial remediation pass over-tightened universal parity and exposed a false-negative risk for sparse `ok=True` payloads; qty typing also remained partially coercive via Python bool/int behavior | First implementation enforced parity directly from `result` fields and relied on generic numeric coercion before adversarial reviewer replay | Added row-order fallback parity for sparse success payloads, introduced explicit bool-qty rejection in normalization/recovery matcher, and added dedicated regression tests for sparse success + bool qty edge paths | For fail-closed reconciliation layers, always combine strict typing with sparse-payload fallback semantics and run adversarial reviewer sweeps before closure | `main_bot_orchestrator.py`, `tests/test_main_bot_orchestrator.py`, `scripts/test_rebalance.py`, `execution/rebalancer.py`, `.venv\\Scripts\\python -m pytest tests/test_main_bot_orchestrator.py tests/test_test_rebalance_script.py tests/test_main_console.py tests/test_execution_controls.py tests/test_auto_backtest_view.py tests/test_auto_backtest_control_plane.py`, `docs/saw_reports/saw_phase27_round1.md` |
| 2026-02-28 | Phase 28 entrypoint contract remediation | First pass fixed core High risks but left a subtle recovery null-semantics inconsistency (`limit_price` coercion) that triggered a late SAW BLOCK | Recovery lookup normalized raw broker `limit_price` too early (`\"null\" -> 0.0`), diverging from matcher semantics | Preserved raw recovered `limit_price`, aligned market null-semantics matcher, and added explicit regression coverage for numeric vs text-null market recovery values | For recovery contracts, avoid lossy normalization before parity matching; enforce semantics first, then normalize only where mathematically required | `execution/broker_api.py`, `tests/test_execution_controls.py`, `.venv\\Scripts\\python -m pytest tests/test_execution_controls.py tests/test_main_console.py tests/test_main_bot_orchestrator.py`, `.venv\\Scripts\\python -m pytest tests/test_main_bot_orchestrator.py tests/test_test_rebalance_script.py tests/test_main_console.py tests/test_execution_controls.py tests/test_auto_backtest_view.py tests/test_auto_backtest_control_plane.py`, `docs/saw_reports/saw_phase28_round1.md` |
| 2026-03-01 | DevSecOps stream | Secret handling relied on fallback defaults and cache URLs persisted live API keys | Security controls were distributed and incomplete across ingest/cache/execution seams | Enforced env-only secret ingestion, redacted cache URL secrets, removed broker dotenv path, and added deny-by-default egress + HMAC key-version/legal-hold rotation contract | For any execution-adjacent change, run a pre-close scrub gate: `no hardcoded secrets`, `no key-bearing artifacts`, `egress allowlist enforced`, `rotation metadata present` | `core/security_policy.py`, `execution/broker_api.py`, `scripts/ingest_fmp_estimates.py`, `scripts/execution_bridge.py`, `scripts/high_freq_data.py`, `tests/test_security_policy.py`, `tests/test_execution_controls.py`, `tests/test_ingest_fmp_estimates.py` |
| 2026-03-01 | Phase 29 microstructure telemetry | Execution path initially optimized for idempotency/safety but lacked arrival/fill-quality observability | Control-plane hardening prioritized submit integrity over post-trade analytics contracts | Added command-time arrival midpoint anchor, partial-fill VWAP aggregation, deterministic IS/slippage formulas, latency decomposition, and Parquet/DuckDB telemetry sink with local-submit fail-closed write guard | For every execution-path change, require an explicit telemetry contract (`arrival`, `fills`, `cost`, `latency`, `sink`) in the same milestone before considering the path production-complete | `main_console.py`, `execution/broker_api.py`, `execution/microstructure.py`, `tests/test_execution_microstructure.py`, `tests/test_execution_controls.py`, `tests/test_main_console.py`, `docs/spec.md`, `docs/notes.md`, `docs/runbook_ops.md`, `docs/decision log.md` |
| 2026-03-01 | Stream 2 risk interceptor | First implementation sketch assumed richer broker risk-context methods and risked false blocks on minimal stubs | Optional context contracts were not explicitly modeled as soft dependencies | Added immutable/stateless interceptor with ordered context fallbacks, fail-closed block behavior, atomic breach-audit writes, and explicit regression tests for stubs missing optional risk methods | For execution risk layers, treat broker context methods as optional inputs and require one regression test that proves baseline broker stubs still execute when optional context is absent | `execution/risk_interceptor.py`, `execution/rebalancer.py`, `tests/test_execution_controls.py`, `tests/test_main_console.py`, `.venv\\Scripts\\python -m pytest tests/test_execution_controls.py tests/test_main_console.py -q` |
| 2026-03-01 | Area 4 release pipeline wiring | Initial release-freeze approach tracked files and config locks but did not enforce deployable immutable artifact identity or startup-fault auto-rollback | Release controls lived at file/metadata level without container deployment-controller coupling | Added digest-locked release metadata schema, docker-mode promotion controller with startup watch and automatic N-1 rollback, and bound UI cache key to runtime release digest | For every release stream round, require digest lock (`@sha256`), atomic metadata state transitions (`pending_probe -> active/rolled_back`), and one startup-fault rollback simulation before closure | `Dockerfile`, `.dockerignore`, `core/release_metadata.py`, `scripts/release_controller.py`, `tests/test_release_controller.py`, `dashboard.py`, `docs/production_deployment.md`, `docs/runbook_ops.md`, `docs/spec.md`, `docs/notes.md`, `docs/decision log.md`, `.venv\\Scripts\\python -m pytest tests/test_release_controller.py -q` |
| 2026-03-01 | Stream 1 truth-layer hardening | First patch partitioning implementation changed updater internals and broke two contract tests that assumed a root-level atomic write event | New partitioned write path removed legacy event shape used by compatibility tests | Added one-time root bootstrap write for first publish and kept partitioned migration/upsert path; reran full targeted data suite | For storage migrations, preserve seam-level compatibility contracts during first-write bootstrap while still moving steady-state writes to partitioned incremental path | `data/updater.py`, `data/fundamentals.py`, `data/feature_store.py`, `docs/notes.md`, `docs/decision log.md`, `.venv\\Scripts\\python -m pytest tests/test_bitemporal_integrity.py tests/test_feature_store.py tests/test_updater_parallel.py tests/test_fundamentals_updater_checkpoint.py -q` |
| 2026-03-01 | Stream 1 truth-layer SAW reconciliation | First resilience patch still left fail-open/ownership edge paths (self-owner recovery blocked, tokenless lock-release ambiguity, and swallowed Yahoo transport failures misclassified as success) | Recovery/lock assumptions were correct in isolated paths but not end-to-end under adverse failure sequencing | Added self-owner recovery allowance, token-owned lock release, chunk-failure sentinel accounting, fail-closed updater abort gates, and dedicated regression tests for partial/full chunk failures plus backup recovery | For data-layer resilience rounds, require explicit failure-path tests for lock ownership, crash-recovery restore, and provider transport errors before SAW close | `data/updater.py`, `data/feature_store.py`, `tests/test_updater_parallel.py`, `tests/test_feature_store.py`, `docs/notes.md`, `docs/decision log.md`, `.venv\\Scripts\\python -m pytest tests/test_bitemporal_integrity.py tests/test_feature_store.py tests/test_updater_parallel.py tests/test_fundamentals_updater_checkpoint.py tests/test_fundamentals_daily.py -q` |
| 2026-03-01 | Stream 1 manifest-v2 upgrade | First manifest-pointer draft broke direct `pd.read_parquet(features.parquet)` compatibility and created duplicate rows because root partition cache files were not normalized after commit/bootstrap | Metadata-plane design was correct, but current-view cache hygiene for legacy readers was under-specified | Moved `CURRENT` pointer under `_manifests/`, added root cache normalization to `part-000.parquet` per touched partition, and purged stale extra parquet files in partition dirs; added hash-seal + rollback tests | For lakehouse-style upgrades, preserve legacy reader compatibility explicitly: keep metadata files out of root parquet scan paths and enforce single-file current-view cache per partition | `data/feature_store.py`, `tests/test_feature_store.py`, `.venv\\Scripts\\python -m pytest tests/test_feature_store.py -q`, `.venv\\Scripts\\python -m pytest tests/test_bitemporal_integrity.py tests/test_feature_store.py tests/test_updater_parallel.py tests/test_fundamentals_updater_checkpoint.py tests/test_fundamentals_daily.py -q` |
| 2026-03-01 | Stream 2 risk interceptor reconciliation | Initial risk checks trusted order-row metadata precedence and did not enforce long-only projection at interceptor boundary | Risk-input trust model and projection semantics were not fully normalized to broker-authoritative data and fail-stop behavior | Inverted precedence to broker-first (`price/sector/vix/vol`), added explicit `invalid_order_projection` long-only block, committed risk state only on submit success, and added audit-write fail-stop regressions | For execution risk gates, enforce authoritative-source precedence and include adversarial spoof tests (`sector/vix/vol`) plus post-submit state-commit assertions before SAW closure | `execution/risk_interceptor.py`, `execution/rebalancer.py`, `tests/test_execution_controls.py`, `tests/test_main_bot_orchestrator.py`, `.venv\\Scripts\\python -m pytest -q tests/test_execution_controls.py tests/test_main_console.py tests/test_main_bot_orchestrator.py`, `docs/notes.md`, `docs/decision log.md` |
| 2026-03-01 | Stream 2 SAW reconciliation round 2 | Batch validation lived inside the submit loop and one sector resolver path could downgrade known broker classifications to `UNKNOWN` | Validation and precedence checks were partially correct but not guarded against side-effect ordering and downgrade edge cases | Added full-batch preflight normalization before first submit, removed risk-context bypass path, protected known sectors from `UNKNOWN` overwrite, made malformed broker position quantities fail-closed, and added targeted regressions | For execution batches, validate all rows before side effects and add one adversarial test per precedence edge (`known -> UNKNOWN` downgrade, malformed broker state) before closure | `execution/rebalancer.py`, `execution/risk_interceptor.py`, `tests/test_execution_controls.py`, `tests/test_main_bot_orchestrator.py`, `.venv\\Scripts\\python -m pytest -q tests/test_execution_controls.py tests/test_main_console.py tests/test_main_bot_orchestrator.py`, `docs/notes.md`, `docs/decision log.md` |
| 2026-03-01 | Stream 2 SAW reconciliation round 3 | Late reviewer pass found canonicalization gaps in position-key handling and non-finite broker quantities could still crash order sizing path | Canonicalization was hardened in execution submit path but not fully mirrored in rebalance sizing ingestion from broker state | Trimmed broker position symbols in `calculate_orders`, rejected non-finite position quantities with explicit fail-closed error, and added regression tests for whitespace-padded and NaN position keys | For risk-critical symbol pipelines, enforce one shared canonicalization rule (`upper+strip`) across sizing, validation, and projection paths, plus explicit NaN/inf ingestion tests | `execution/rebalancer.py`, `tests/test_execution_controls.py`, `.venv\\Scripts\\python -m pytest -q tests/test_execution_controls.py tests/test_main_console.py tests/test_main_bot_orchestrator.py`, `docs/notes.md`, `docs/decision log.md` |
| 2026-03-01 | Area 4 release-controller reconciliation | Initial Area-4 rollout marked rollback success in metadata even when rollback verification failed/unknown and lock release semantics allowed ownership races | Rollback truth-state and single-flight lock ownership were under-specified in first controller version | Added explicit `rollback_failed` terminal state, propagated `rollback_ok` verification into probe/result metadata, hardened lock owner-token semantics with stale-lock live-pid checks, gated external-probe promotion with explicit acknowledgement, and expanded regression tests | For deployment controllers, never serialize `rolled_back` unless rollback verification is explicit; require lock-owner identity checks and stale-lock liveness validation in the same milestone | `scripts/release_controller.py`, `core/release_metadata.py`, `tests/test_release_controller.py`, `docs/runbook_ops.md`, `docs/production_deployment.md`, `docs/spec.md`, `docs/phase_brief/phase30-brief.md`, `docs/decision log.md`, `.venv\\Scripts\\python -m pytest tests/test_release_controller.py -q`, `.venv\\Scripts\\python -m py_compile scripts/release_controller.py core/release_metadata.py dashboard.py` |
| 2026-03-01 | DevSecOps SAW reconciliation | Initial DevSecOps pass left policy bypass/outage footguns (HTTP egress acceptance, future-dated HMAC anchor masking, and post-submit webhook hard-fail) | Security controls were implemented but not adversarially validated for transport semantics, timestamp tampering, and post-commit notification resilience | Enforced HTTPS-only egress by default, added HMAC future-skew fail-closed check, switched allowlist env to additive-by-default, and added post-submit webhook degraded mode with new regression tests | For every security-policy round, run a dedicated adversarial gate for `transport scheme`, `timestamp skew`, and `post-commit failure semantics` before SAW close | `core/security_policy.py`, `scripts/high_freq_data.py`, `scripts/execution_bridge.py`, `main_console.py`, `tests/test_security_policy.py`, `tests/test_high_freq_data.py`, `tests/test_execution_controls.py`, `docs/runbook_ops.md`, `docs/notes.md`, `docs/decision log.md` |
| 2026-03-01 | Stream 5 Option 1 test hardening | Failure-path tests can look green while silently writing live telemetry sinks when persistence mocks are missing | Local-submit failure scenarios were not fully hermetic and one fallback path lacked explicit snapshot-fill coverage | Added sink isolation in risk-blocked local-submit test, added no-activity snapshot-fill fallback test, and tightened no-notify assertion on save-failure abort path | For execution fail-path tests, always stub telemetry sink writes and require one explicit `downstream_not_called` assertion per abort branch | `tests/test_main_console.py`, `tests/test_execution_controls.py`, `tests/test_execution_microstructure.py`, `.venv\\Scripts\\python -m pytest -q tests/test_execution_microstructure.py tests/test_execution_controls.py tests/test_main_console.py`, `docs/saw_reports/saw_stream5_option1_tests_round1.md` |
| 2026-03-01 | Stream 5 Option 2 production patch | Initial Stream-5 logic treated terminal unfilled statuses as accepted submits and left recovery latency anchors sparse, which could hide fail-closed intent and produce negative decomposed latency under clock drift | Submit success was keyed on transport acceptance (`ok=True`) without explicit terminal-unfilled normalization and latency decomposition trusted raw timestamp ordering | Added terminal-unfilled fail-closed normalization in broker/orchestrator paths, added recovery submit/ack timestamp backfill from broker lifecycle fields, clamped latency decomposition with `max(0, computed_ms)`, and added signed slippage regression tests for negative/zero invariants | For execution telemetry/control seams, enforce three explicit gates in one patch: terminal-unfilled non-acceptance, lifecycle-anchor backfill for recovered rows, and non-negative latency math with favorable/zero slippage assertions | `execution/broker_api.py`, `main_bot_orchestrator.py`, `execution/microstructure.py`, `tests/test_execution_controls.py`, `tests/test_main_bot_orchestrator.py`, `tests/test_execution_microstructure.py`, `docs/spec.md`, `docs/notes.md`, `docs/decision log.md`, `.venv\\Scripts\\python -m pytest -q tests/test_execution_microstructure.py tests/test_execution_controls.py tests/test_main_console.py tests/test_main_bot_orchestrator.py` |
| 2026-03-01 | Stream 1 manifest-v2 SAW reconciliation (round 2) | Initial manifest-v2 upgrade left fail-open metadata edges (non-v2 downgrade fallback and partition-key/file drift acceptance) and publish-token enforcement only at outer build entry | Read/write acceptance gates were validated at a high level but not adversarially tested at manifest-primitive boundaries | Enforced token-validated publish checks in feature-store commit/pointer paths, required v2 manifests on partitioned reads, added partition key/file congruence validation, and expanded regression tests for downgrade/mismatch/token-missing scenarios; reran targeted Stream 1 suite to PASS (`53 passed`) | For lakehouse-style commits, require explicit adversarial tests for manifest downgrade, partition-key drift, and lock-token ownership at publish primitives before SAW close | `data/feature_store.py`, `tests/test_feature_store.py`, `docs/notes.md`, `docs/decision log.md`, `.venv\\Scripts\\python -m py_compile data/feature_store.py tests/test_feature_store.py`, `.venv\\Scripts\\python -m pytest tests/test_bitemporal_integrity.py tests/test_feature_store.py tests/test_updater_parallel.py tests/test_fundamentals_updater_checkpoint.py tests/test_fundamentals_daily.py -q` |

## 2026-03-01 Round Entry (Phase 31 Option 1 Medium-Risk Reconciliation)
- Date: 2026-03-01
- Mistake or miss: First medium-risk patch cycle solved immediate duplication/accounting defects but still left a silent durability-loss path on shutdown under lock contention.
- Root cause: Shutdown semantics were treated as best-effort background behavior instead of a fail-closed boundary with explicit pending-data rejection.
- Fix applied: Added bounded synchronous drain on spooler stop and explicit fail-closed shutdown error when pending telemetry remains; also added deterministic retry identity, malformed-ledger fail-closed replay behavior, and corresponding regression tests.
- Guardrail for next time: For any async-buffered durability path, include an explicit shutdown-state contract (`pending_bytes == 0` or hard-fail) and test it before SAW close.
- Evidence paths: `execution/microstructure.py`, `execution/signed_envelope.py`, `core/dashboard_control_plane.py`, `app.py`, `tests/test_execution_microstructure.py`, `tests/test_signed_envelope_replay.py`, `tests/test_dashboard_control_plane.py`, `.venv\Scripts\python -m pytest -q tests/test_execution_microstructure.py tests/test_signed_envelope_replay.py tests/test_dashboard_control_plane.py`, `.venv\Scripts\python -m pytest -q tests/test_main_console.py tests/test_main_bot_orchestrator.py tests/test_execution_controls.py tests/test_execution_microstructure.py tests/test_auto_backtest_control_plane.py tests/test_dashboard_control_plane.py tests/test_ticker_pool.py tests/test_alpha_engine.py tests/test_engine.py tests/test_statistics.py tests/test_signed_envelope_replay.py`
## Philosophy Sync (2026-03-01)
- PhilosophySyncID: 2026-03-01-top-level-philosophy-6-8
- LocalFirstStatus: COMPLETED
- Source: top_level_PM.md
- AppliedSections: 6,7,8

### Synced Sections
```markdown
## 6. Theory of Constraints (Eliyahu M. Goldratt)
Core concept:
- Every system is limited by a very small number of bottlenecks (often one).
- Optimizing non-bottlenecks creates the illusion of progress.

Application pattern:
- Continuously identify the current throughput bottleneck and align optimization there.
- In data pipelines, prioritize eliminating O(N) staging/copy bottlenecks before micro-optimizing compute.


## 7. Cynefin Framework (Dave Snowden)
Core concept:
- Problems belong to domains: Clear, Complicated, Complex, Chaotic, Confusion.
- Decision method must match domain type.

Application pattern:
- For Complex/Chaotic domains, use probe-sense-respond instead of rigid best-practice scripts.
- Keep QoS and ingestion control policies adaptive and evidence-driven.


## 8. Ergodicity and Survival Logic (Ole Peters)
Core concept:
- Ensemble average is not time average.
- Non-zero ruin probability destroys long-term compounding for a single entity.

Application pattern:
- Place survival constraints ahead of nominal expected return.
- Keep fail-closed data/update controls and strict lock discipline to minimize ruin pathways.
```

## 2026-03-01 Round Entry (Phase 31 SAW Reconciliation)
- Date: 2026-03-01
- Mistake or miss: First implementation closure attempt was made after one green matrix while second-wave SAW reviewer checks still had in-scope Critical/High defects.
- Root cause: Reconciliation loop stopped at first successful patch cycle instead of enforcing an additional independent adversarial reviewer pass.
- Fix applied: Executed a second SAW reconciliation round, closed all in-scope Critical/High findings, added targeted regressions, and re-ran the integrated matrix.
- Guardrail for next time: For reliability hardening rounds, require a reviewer recheck pass after reconciliation patches; do not finalize unless in-scope Critical/High count is zero.
- Evidence paths: `execution/microstructure.py`, `main_console.py`, `strategies/alpha_engine.py`, `strategies/ticker_pool.py`, `tests/test_execution_microstructure.py`, `tests/test_main_console.py`, `tests/test_alpha_engine.py`, `tests/test_ticker_pool.py`, `.venv\Scripts\python -m pytest -q tests/test_main_console.py tests/test_main_bot_orchestrator.py tests/test_execution_controls.py tests/test_execution_microstructure.py tests/test_auto_backtest_control_plane.py tests/test_dashboard_control_plane.py tests/test_ticker_pool.py tests/test_alpha_engine.py tests/test_engine.py tests/test_statistics.py tests/test_signed_envelope_replay.py`
| 2026-03-01 | Stream 5 Option 2 SAW reconciliation | SAW recheck exposed three missed adversarial edges: terminal-partial-fill retry thrash, summary-only fill aggregates producing empty fill rows, and legacy parquet append dedupe collapsing rows without spool UIDs | Reconciliation validation focused on previously known failures and under-covered mixed-shape telemetry/legacy-schema paths | Added terminal-status fail-closed handling for partial-fill outcomes (no retry), synthesized `summary_fallback` fill row when only order-level fill summary is present, hardened legacy parquet dedupe to preserve rows lacking `_spool_record_uid`, and added dedicated regression tests plus Alpaca v2 quote-field coverage | Before SAW close on execution telemetry rounds, require adversarial checks for `terminal+filled`, `summary-only fills`, and `legacy parquet without UID` in addition to nominal batch tests | `main_bot_orchestrator.py`, `execution/microstructure.py`, `tests/test_main_bot_orchestrator.py`, `tests/test_execution_microstructure.py`, `tests/test_execution_controls.py`, `.venv\Scripts\python -m pytest -q tests/test_execution_microstructure.py tests/test_execution_controls.py tests/test_main_console.py tests/test_main_bot_orchestrator.py`, `.venv\Scripts\python -m py_compile main_bot_orchestrator.py execution/microstructure.py tests/test_main_bot_orchestrator.py tests/test_execution_microstructure.py tests/test_execution_controls.py` |

## 2026-03-01 Round Entry (Stream 5 Adaptive Heartbeat + Runner Pack)
- Date: 2026-03-01
- Mistake or miss: Initial execution of the targeted Stream 5 matrix hit a transient Windows `PermissionError` on atomic cursor-file replace during parquet export cursor updates.
- Root cause: Atomic replace path in microstructure write helpers lacked bounded retry/backoff for short-lived file locks on Windows.
- Fix applied: Added `_atomic_replace_with_retry(...)` and routed `_atomic_write_text(...)` / `_atomic_write_parquet(...)` through it, then re-ran the full targeted Stream 5 matrix to green.
- Guardrail for next time: For execution telemetry persistence on Windows, wrap every critical `os.replace` path with bounded retry/backoff and keep retry policy explicit in code constants.
- Evidence paths: `execution/microstructure.py`, `scripts/backfill_execution_latency.py`, `scripts/evaluate_execution_slippage_baseline.py`, `tests/test_execution_microstructure.py`, `tests/test_execution_stream5_scripts.py`, `.venv\Scripts\python -m pytest -q tests/test_execution_microstructure.py tests/test_execution_stream5_scripts.py tests/test_execution_controls.py tests/test_main_console.py`, `.venv\Scripts\python -m py_compile execution/microstructure.py scripts/backfill_execution_latency.py scripts/evaluate_execution_slippage_baseline.py tests/test_execution_microstructure.py tests/test_execution_stream5_scripts.py`
| 2026-03-01 | DevSecOps Track 3 follow-through | First-pass DevSecOps closure left operator visibility gap for degraded HF proxy signals and did not explicitly lock malformed non-rate-limit FMP payload classes | Initial hardening prioritized transport/secret boundaries and under-scoped operator-facing health observability plus payload-shape adversarial tests | Added in-memory binary Data Health derivation + dashboard badge/expander and expanded malformed payload regressions for dict/scalar/invalid-JSON classes | For DevSecOps follow-through rounds, require both `operator-visible degradation telemetry` and `malformed payload class matrix` before final SAW close | `dashboard.py`, `core/dashboard_control_plane.py`, `tests/test_dashboard_control_plane.py`, `tests/test_ingest_fmp_estimates.py`, `.venv\Scripts\python -m pytest -q tests/test_dashboard_control_plane.py tests/test_ingest_fmp_estimates.py`, `.venv\Scripts\python -m py_compile dashboard.py core/dashboard_control_plane.py tests/test_dashboard_control_plane.py tests/test_ingest_fmp_estimates.py` |
| 2026-03-01 | Stream 1 fail-loud bootstrap + Stream 4 strict container draft | Missing/ambiguous manifest lineage still had residual bootstrap ambiguity risk and cross-filesystem/tombstone contracts lacked explicit adversarial proofs | Recovery and integrity contracts were mostly implemented but not fully stress-tested at deterministic boundary conditions; immutable image policy needed a stricter orchestrator draft | Replaced mtime inference with explicit AmbiguousFeatureStoreStateError, added EXDEV/cross-device and tombstone-priority/retention adversarial tests, and drafted Dockerfile.orchestrator.strict with digest-pinned base, snapshot apt pins, and checksum gate | For truth-layer state engines, never infer commit lineage from filesystem timestamps; require fail-loud lineage checks plus adversarial EXDEV/tombstone tests, and pair data hardening with immutable release artifact drafts in parallel tracks | data/feature_store.py, tests/test_feature_store.py, Dockerfile.orchestrator.strict, docs/production_deployment.md, docs/notes.md, docs/decision log.md, .venv\\Scripts\\python -m py_compile data/feature_store.py tests/test_feature_store.py, .venv\\Scripts\\python -m pytest tests/test_feature_store.py tests/test_bitemporal_integrity.py tests/test_fundamentals_daily.py tests/test_updater_parallel.py tests/test_fundamentals_updater_checkpoint.py -q |
| 2026-03-01 | Stream 1 Option 1 isolated inherited-high closure | Initial fail-closed spec patch handled explicit exceptions but still allowed dependency-bypass and non-DataFrame return edge paths to leak raw runtime errors | The first pass focused on direct exception swallowing and under-scoped dependency/type contracts inside `_execute_feature_specs` | Added dependency gate against snapshot/derived outputs, enforced DataFrame-type/post-processing fail-closed wrapping, added patch-overlay PIT selector test, and expanded targeted regressions before final SAW close | For feature-spec executors, enforce fail-closed contracts at three layers (`inputs`, `dependencies`, `result type/post-processing`) and require one regression per layer in the same round | `data/feature_store.py`, `tests/test_feature_store.py`, `docs/spec.md`, `docs/notes.md`, `docs/decision log.md`, `.venv\\Scripts\\python -m py_compile data/feature_store.py tests/test_feature_store.py`, `.venv\\Scripts\\python -m pytest tests/test_feature_store.py tests/test_bitemporal_integrity.py tests/test_fundamentals_daily.py tests/test_updater_parallel.py tests/test_fundamentals_updater_checkpoint.py -q` |
| 2026-03-01 | Stream 5 execution receipt gate pivot | Existing sparse `ok=True` guard only required intent-shape fields (`symbol/side/qty`), allowing success acceptance without definitive execution receipt fields | Earlier hardening prioritized idempotency and intent parity, not authoritative execution telemetry completeness at acceptance boundary | Enforced authoritative success gate in orchestrator (`filled_qty`, `filled_avg_price`, `execution_ts`) with reconciliation polling and `AmbiguousExecutionError` on unresolved ambiguity; added reconciliation success/failure regressions | For execution acceptance paths, never emit `ok=True` unless authoritative receipt fields are present; every sparse-success path must include an explicit reconciliation test and an ambiguity-fail-closed test | `main_bot_orchestrator.py`, `execution/broker_api.py`, `tests/test_main_bot_orchestrator.py`, `tests/test_execution_controls.py`, `.venv\\Scripts\\python -m py_compile main_bot_orchestrator.py execution/broker_api.py tests/test_main_bot_orchestrator.py tests/test_execution_controls.py`, `.venv\\Scripts\\python -m pytest -q tests/test_main_bot_orchestrator.py tests/test_execution_controls.py tests/test_execution_microstructure.py tests/test_main_console.py` |
| 2026-03-01 | Stream 1 PiT reconciliation (dual-time gate + t-1 universe) | First reconciliation left fallback valid-time leakage and strict-binding runtime break risk under `T0_STRICT_SIMULATION_TS_BINDING=1` | Initial patch hardened primary loader paths but under-covered fallback daily broadcast semantics and strict-mode integration through feature-store call chain | Added release-date valid-time masking across fallback matrices, non-negative age gate, strict binding token plumbing from feature-store to fundamentals loaders, deterministic dedupe tie-break `_row_hash`, and regression tests for fallback no-leak / strict binding / equal-ingested tie determinism | For PiT rounds, always test both primary and fallback data paths plus strict-env integration seams (`loader -> feature-store`) before SAW closure | `data/fundamentals.py`, `data/feature_store.py`, `tests/test_bitemporal_integrity.py`, `tests/test_fundamentals_daily.py`, `tests/test_feature_store.py`, `.venv\\Scripts\\python -m pytest -q tests/test_bitemporal_integrity.py tests/test_fundamentals_daily.py tests/test_feature_store.py`, `.venv\\Scripts\\python -m py_compile data/fundamentals.py data/feature_store.py tests/test_bitemporal_integrity.py tests/test_fundamentals_daily.py tests/test_feature_store.py` |
| 2026-03-01 | Stream 1 cleanup helper retirement | Legacy annual-liquidity helper remained callable after runtime migration and could reintroduce historical yearly-block semantics in future refactors | Prior rounds hardened active runtime behavior but retained obsolete helper/test surface for compatibility | Removed `_select_permnos_from_annual_liquidity`, replaced helper tests with active-dispatch regression, and preserved t-1/no-same-day/patch-precedence coverage on live selector path | After behavior migrations, schedule a dedicated cleanup slice to remove obsolete helper surfaces and bind tests only to active runtime entrypoints | `data/feature_store.py`, `tests/test_feature_store.py`, `docs/decision log.md`, `docs/phase_brief/phase31-brief.md`, `.venv\\Scripts\\python -m pytest -q tests/test_feature_store.py tests/test_bitemporal_integrity.py tests/test_fundamentals_daily.py`, `.venv\\Scripts\\python -m py_compile data/feature_store.py tests/test_feature_store.py` |

## 2026-03-01 Round Entry (Stream 5 Final Cleanup)
- Date: 2026-03-01
- Mistake or miss: Heartbeat history bootstrap still depended on append/capture order assumptions, and slippage baseline aggregates were measured on observed-only rows.
- Root cause: Initial hardening optimized sink pagination stability and signed-metric correctness, but denominator/event-time invariants were not fully closed in baseline/bootstrap layers.
- Fix applied: Enforced explicit event-time ordering in heartbeat history bootstrap and backfill sorting, removed unordered fallback history query, aligned slippage baseline math to full intended cohort with explicit zero-imputed counters, and sanitized non-finite numeric inputs before aggregation.
- Guardrail for next time: For execution telemetry analytics, require two invariants in the same round: `event-time ordering proof` and `cohort denominator proof` (including missing-observation rows).
- Evidence paths: `execution/microstructure.py`, `scripts/backfill_execution_latency.py`, `scripts/evaluate_execution_slippage_baseline.py`, `tests/test_execution_microstructure.py`, `tests/test_execution_stream5_scripts.py`, `.venv\Scripts\python -m pytest -q tests/test_execution_microstructure.py tests/test_execution_stream5_scripts.py`, `.venv\Scripts\python -m py_compile execution/microstructure.py scripts/backfill_execution_latency.py scripts/evaluate_execution_slippage_baseline.py tests/test_execution_microstructure.py tests/test_execution_stream5_scripts.py`

## 2026-03-01 Round Entry (Stream 5 Option 2 Fail-Loud Source Contract)
- Date: 2026-03-01
- Mistake or miss: Script loaders still silently downgraded to parquet when DuckDB failed, masking primary sink outages.
- Root cause: Loader behavior favored continuity over observability and lacked an explicit operator-mode gate for fallback reads.
- Fix applied: Enforced strict default source mode (`duckdb_strict`) with fatal `PrimarySinkUnavailableError`, removed implicit fallback paths, and added explicit parquet override mode (`parquet_override`) only via CLI/env token.
- Guardrail for next time: Any execution-adjacent source loader must define default source-of-truth mode plus explicit override token; implicit fallback in exception handlers is forbidden.
- Evidence paths: `scripts/backfill_execution_latency.py`, `scripts/evaluate_execution_slippage_baseline.py`, `tests/test_execution_stream5_scripts.py`, `.venv\Scripts\python -m pytest -q tests/test_execution_stream5_scripts.py`

## 2026-03-01 Round Entry (Stream 5 Sprint+1 Telemetry Constraints Hardening)
- Date: 2026-03-01
- Mistake or miss: First hardening pass still allowed row-order-dependent outcomes for duplicate broker rows with the same `client_order_id` because ambiguity could raise before duplicate handling executed.
- Root cause: Duplicate CID detection happened during row iteration instead of a deterministic pre-scan phase, so first-row control flow dominated behavior.
- Fix applied: Added duplicate CID pre-scan fail-closed gate before row processing, hardened reconciliation with per-poll timeout and issue propagation, enforced timezone-valid `execution_ts` parsing, and enforced fill bound `filled_qty <= order.qty`.
- Guardrail for next time: For execution acceptance loops, always pre-scan batch identity collisions before evaluating any single-row success/ambiguity branch; then run adversarial row-order permutation tests in the same round.
- Evidence paths: `main_bot_orchestrator.py`, `tests/test_main_bot_orchestrator.py`, `docs/decision log.md`, `docs/phase_brief/phase31-brief.md`, `docs/saw_reports/saw_stream5_sprintplus1_round6_20260301.md`, `.venv\Scripts\python -m pytest -q tests/test_main_bot_orchestrator.py tests/test_execution_controls.py tests/test_execution_microstructure.py tests/test_main_console.py`, `.venv\Scripts\python -m py_compile main_bot_orchestrator.py tests/test_main_bot_orchestrator.py`

## 2026-03-01 Round Entry (Stream 5 D-209 SAW Reconciliation)
- Date: 2026-03-01
- Mistake or miss: First Stream 5 receipt-gate patch still allowed a local `client_order_id` backfill path to satisfy `ok=True` acceptance without broker-origin identity proof.
- Root cause: Acceptance checks emphasized fill/timestamp authority but under-specified broker identity authority on non-recovery success rows.
- Fix applied: Required broker `client_order_id` in the authoritative `ok=True` gate, forced reconciliation when broker CID is missing, canonicalized terminal taxonomy fields, and added batch exception retry/exhaustion fail-closed handling with regression tests.
- Guardrail for next time: For execution receipt acceptance, lock identity and fill authority together in one invariant (`broker_cid + qty + price + execution_ts`) and add at least one adversarial missing-CID success test in the same round.
- Evidence paths: `main_bot_orchestrator.py`, `tests/test_main_bot_orchestrator.py`, `docs/notes.md`, `docs/decision log.md`, `docs/phase_brief/phase31-brief.md`, `.venv\Scripts\python -m py_compile main_bot_orchestrator.py tests/test_main_bot_orchestrator.py`, `.venv\Scripts\python -m pytest -q tests/test_main_bot_orchestrator.py tests/test_execution_controls.py tests/test_execution_microstructure.py tests/test_main_console.py`

## 2026-03-01 Round Entry (Phase 31 Closeout Protocol)
- Date: 2026-03-01
- Mistake or miss: Stream-focused validation passed, but full-repo closeout gate still surfaced one inherited strategy-path regression that had not been exercised in the Stream 1/5 isolated matrix.
- Root cause: Closeout relied on scoped confidence before running an unconditional repo-wide matrix gate.
- Fix applied: Executed full-repo matrix (`pytest --maxfail=1`), isolated the inherited Phase 15 integration regression explicitly, executed orchestrator init/shutdown smoke, and published Phase 31 handover + refreshed context packet artifacts.
- Guardrail for next time: Do not mark phase-end governance ready until full-repo matrix is executed and logged, even when active-stream matrices are green.
- Evidence paths: `docs/handover/phase31_handover.md`, `docs/context/current_context.json`, `docs/context/current_context.md`, `docs/decision log.md`, `docs/phase_brief/phase31-brief.md`, `.venv\Scripts\python -m pytest --maxfail=1`, `.venv\Scripts\python -m pytest tests/test_phase15_integration.py::test_phase15_weights_respect_regime_cap -q -vv`

## 2026-03-02 Round Entry (Phase 31 Final Governance Promotion)
- Date: 2026-03-02
- Mistake or miss: Initial promotion attempts treated scheduler-level execution (`schtasks`) as the primary isolation path, but this host held scheduled payloads in non-advancing `Running` state and produced non-deterministic interruption signatures.
- Root cause: The execution environment applied process-control and filesystem constraints that interacted with repo-local temp paths and Windows replace semantics; governance gate logic needed immutable artifacts from a truly stable detached path.
- Fix applied: Promoted detached wrapper execution with immutable status/log artifacts, moved pytest `--basetemp` to OS temp, embedded status/log checksums in handover + SAW closeout, and flipped Phase 31 governance to PASS only after status file returned `0` with `597 passed` summary.
- Guardrail for next time: For phase-end governance on Windows, require artifact-first detached runs with `status` as source-of-truth, unique temp roots outside repo worktree, and checksum-backed evidence embedding before promotion.
- Evidence paths: `docs/context/e2e_evidence/phase31_full_matrix_final.status`, `docs/context/e2e_evidence/phase31_full_matrix_final.log`, `docs/context/e2e_evidence/phase31_full_matrix_wrapper.py`, `docs/handover/phase31_handover.md`, `docs/saw_reports/saw_phase31_closeout_round8_20260301.md`, `docs/phase_brief/phase31-brief.md`, `docs/decision log.md`, `.venv\Scripts\python scripts/build_context_packet.py --repo-root .`, `.venv\Scripts\python scripts/build_context_packet.py --repo-root . --validate`

## 2026-03-02 Round Entry (Phase 31 Governance Promotion SAW Reconciliation)
- Date: 2026-03-02
- Mistake or miss: Initial governance-promotion doc pass introduced cross-section ordering drift for Phase 32 backlog priorities and left residual legacy wording in archival-adjacent Phase 31 entries.
- Root cause: Multi-document state rewrite was performed quickly from blocker-removal intent, but canonical ordering/risk registry normalization was not enforced as one synchronized invariant across handover, brief, SAW, decision log, and lessons entries.
- Fix applied: Ran independent implementer + reviewer A/B/C passes, normalized one canonical Phase 32 sequence across all Phase 31 canonical docs, removed residual `BLOCK/carryover` governance wording in promoted sections, and revalidated SAW closure/blocks validators.
- Guardrail for next time: For governance-state flips, require a post-edit consistency sweep with fixed-order token checks and SAW validator passes before publishing final closeout.
- Evidence paths: `docs/handover/phase31_handover.md`, `docs/phase_brief/phase31-brief.md`, `docs/saw_reports/saw_phase31_closeout_round8_20260301.md`, `docs/decision log.md`, `docs/lessonss.md`, `.venv\Scripts\python .codex/skills/_shared/scripts/validate_closure_packet.py --packet "<ClosurePacket>" --require-open-risks-when-block --require-next-action-when-block`, `.venv\Scripts\python .codex/skills/_shared/scripts/validate_saw_report_blocks.py --report-file docs/saw_reports/saw_phase31_closeout_round8_20260301.md`, `.venv\Scripts\python scripts/build_context_packet.py --repo-root . --validate`

## 2026-03-02 Round Entry (Phase 32 Step 1 Timeout Soak Reconciliation)
- Date: 2026-03-02
- Mistake or miss: First implementation preserved timeout/cancel behavior but allowed lookup taxonomy downgrade across polls and did not harden concurrent quarantine append semantics.
- Root cause: Initial pass optimized single-path success criteria; adversarial reviewer checks exposed multi-poll precedence and concurrent-writer integrity gaps.
- Fix applied: Added sticky lookup issue precedence, uncooperative-timeout early return to avoid repeated hanging lookup workers, lock-serialized durable quarantine append path, schema-versioned quarantine payload, and concurrency regression coverage.
- Guardrail for next time: For timeout/cancellation rounds, always require at least one mixed-poll precedence test and one concurrent evidence-writer integrity test before SAW closure.
- Evidence paths: `main_bot_orchestrator.py`, `tests/test_main_bot_orchestrator.py`, `docs/phase_brief/phase32-brief.md`, `docs/decision log.md`, `.venv\Scripts\python -m pytest -q tests/test_main_bot_orchestrator.py`, `.venv\Scripts\python -m py_compile main_bot_orchestrator.py tests/test_main_bot_orchestrator.py`

## 2026-03-02 Round Entry (Phase 32 Step 2 UTF-8 Decode Wedge Reconciliation)
- Date: 2026-03-02
- Mistake or miss: Quarantine JSONL replay used unsafe `.read_text(encoding="utf-8")` which wedges with `UnicodeDecodeError` if broker responses or external sources introduce malformed UTF-8 bytes.
- Root cause: No deterministic malformed-byte test fixture existed to prove robustness against corruption; ingestion/replay boundaries assumed all JSONL data would be well-formed UTF-8.
- Fix applied: Added `_read_quarantine_jsonl_safe()` helper with `errors='replace'` decode policy converting invalid bytes to U+FFFD replacement character, created deterministic malformed-byte test fixture (0xFF,0xFE sequence), and retrofitted all 5 existing quarantine read calls to use safe reader.
- Guardrail for next time: For forensic evidence ingestion (JSONL, logs, telemetry), always require fail-closed decode error handling (`errors='replace'`) and at least one deterministic malformed-byte fixture proving graceful recovery instead of wedge.
- Evidence paths: `main_bot_orchestrator.py`, `tests/test_main_bot_orchestrator.py`, `docs/phase_brief/phase32-brief.md`, `docs/decision log.md`, `docs/saw_reports/saw_phase32_step2_round1_20260302.md`, `.venv\Scripts\python -m pytest -q tests/test_main_bot_orchestrator.py`, `.venv\Scripts\python -m py_compile main_bot_orchestrator.py tests/test_main_bot_orchestrator.py`

## 2026-03-02 Round Entry (Phase 32 Step 2 SAW Recheck Hardening)
- Date: 2026-03-02
- Mistake or miss: Initial UTF-8 wedge regression asserted replacement-character presence but under-covered full metadata round-trip and malformed-JSON skip recovery.
- Root cause: First test fixture optimized decode failure proof and did not include full quarantine schema fields or explicit malformed-JSON-line branch coverage.
- Fix applied: Expanded malformed-byte fixture to include full quarantine metadata keys, added explicit metadata preservation assertions (`client_order_id`, `schema_version`, `attempt`, `source`, `order`), and added `test_read_quarantine_jsonl_safe_skips_malformed_json_lines()` to cover JSON parse-recovery skip path.
- Guardrail for next time: For corruption-tolerance readers, pair decode-level tests with schema-level metadata assertions and at least one malformed-JSON branch test in the same round.
- Evidence paths: `tests/test_main_bot_orchestrator.py`, `docs/phase_brief/phase32-brief.md`, `docs/decision log.md`, `docs/saw_reports/saw_phase32_step2_round1_20260302.md`, `.venv\Scripts\python -m pytest tests/test_main_bot_orchestrator.py --disable-warnings`, `.venv\Scripts\python -m py_compile main_bot_orchestrator.py tests/test_main_bot_orchestrator.py`

## 2026-03-02 Round Entry (Phase 32 Step 3 DuckDB Flush Reconciliation)
- Date: 2026-03-02
- Mistake or miss: First Step 3 pass left two reliability regressions: EOF export cursor rewind delayed new-tail export by one cycle, and shutdown fail-closed gate only checked `pending_bytes`, allowing sink errors to pass if buffers were drained.
- Root cause: Initial optimization focused on removing `COUNT(*)` scans and throughput, but EOF cursor semantics and shutdown error-propagation invariants were under-covered by targeted regression tests.
- Fix applied: Removed EOF cursor rewind in `_export_duckdb_table_to_parquet`, added EOF-then-append regression, hardened `_TelemetrySpooler.stop` to raise `MicrostructureFlushError` when `pending_bytes > 0` or `buffer_drop_count > 0` or `last_flush_error` is present, and added synthetic disk-full shutdown propagation regression.
- Guardrail for next time: For spool/export optimizations, require paired regressions for `EOF tail continuity` and `shutdown error propagation` in the same round before SAW close.
- Evidence paths: `execution/microstructure.py`, `tests/test_execution_microstructure.py`, `docs/phase_brief/phase32-brief.md`, `docs/decision log.md`, `docs/notes.md`, `.venv\Scripts\python -m pytest tests/test_execution_microstructure.py --disable-warnings`, `.venv\Scripts\python -m py_compile execution/microstructure.py tests/test_execution_microstructure.py`

## 2026-03-02 Round Entry (Phase 32 Step 4 Exception Taxonomy Split Reconciliation)
- Date: 2026-03-02
- Mistake or miss: Initial Step 4 pass left a hidden timeout stall seam (`timeout<=0` synchronous lookup), taxonomy schema drift across terminal branches, and terminal-precedence leakage where mixed-token errors could route through retry path.
- Root cause: First implementation prioritized batch exception routing but under-covered edge branches where row-level broker errors and defensive exhaustion paths used non-canonical result shapes and token-order-sensitive routing.
- Fix applied: Added minimum bounded lookup timeout clamp (`0.01s`), removed synchronous zero-timeout lookup path, centralized canonical transient/terminal builders, routed non-retryable terminal row errors to `FAILED_REJECTED`, enforced terminal classification precedence before retry-token checks, and expanded tests for zero-timeout and mixed-token terminal cases.
- Guardrail for next time: For taxonomy migrations, enforce one canonical builder per terminal state plus explicit `terminal-precedence-over-retry-token` regressions in the same round before SAW close.
- Evidence paths: `main_bot_orchestrator.py`, `tests/test_main_bot_orchestrator.py`, `docs/phase_brief/phase32-brief.md`, `docs/decision log.md`, `docs/notes.md`, `.venv\Scripts\python -m pytest tests/test_main_bot_orchestrator.py --disable-warnings`, `.venv\Scripts\python -m py_compile main_bot_orchestrator.py tests/test_main_bot_orchestrator.py`

## 2026-03-17 Round Entry (Phase 55 Allocator Governance Hardening)
- Date: 2026-03-17
- Mistake or miss: The first Phase 55 implementation pass fixed the nested CPCV shape but still allowed silent row coercion, same-fold duplicate averaging, and path-based CLI import failure, and the SAW closeout briefly stalled while the original Reviewer B lane failed to return.
- Root cause: Input-surface hardening and runtime invocation were under-specified up front, and reviewer-lane continuity was treated as incidental instead of being planned as part of the closeout path.
- Fix applied: Added fail-closed validation for malformed `fold`, `snapshot_date`, `variant_id`, and `period_return` rows, blocked duplicate/fold leakage before matrix construction, normalized numeric `variant_id` values to the string contract, restored direct script-path execution, added focused regressions plus SPA benchmark-alignment coverage, and completed SAW with an independent replacement Reviewer B pass instead of inferring runtime sign-off locally.
- Guardrail for next time: For bounded governance wrappers, lock the input contract before the first coding pass, add direct script-path smoke coverage in the same round, and predefine a replacement reviewer path so SAW does not stall when one reviewer lane drops.
- Evidence paths: `scripts/phase55_allocator_governance.py`, `utils/spa.py`, `tests/test_phase55_allocator_governance.py`, `tests/test_spa.py`, `docs/notes.md`, `docs/saw_reports/saw_phase55_allocator_governance_20260317.md`, `.venv\Scripts\python -m pytest tests/test_spa.py tests/test_phase55_allocator_governance.py -q --tb=no`, `.venv\Scripts\python scripts/phase55_allocator_governance.py --help`

## 2026-03-17 Round Entry (Critical Git Recovery / Stash-Untracked Split)
- Date: 2026-03-17
- Mistake or miss: The repo cleanup round treated later-phase docs and Phase 53 read-only inputs as safely recoverable from the main stash entry, but those files were untracked and therefore disappeared from the worktree after `git reset --hard` plus `git clean -fd`, leaving `docs/phase_brief` truncated at `phase35-brief.md` and hiding the Phase 53 CPCV input surface.
- Root cause: Git stash structure was not verified before cleanup. The work assumed `stash@{0}` contained the missing files, but untracked artifacts were actually stored in the stash's untracked-files parent (`stash@{0}^3`), and directory-level restore assumptions were made before proving file-level recovery semantics.
- Fix applied: Diagnosed the issue with `git ls-files docs/phase_brief` and `git ls-tree -r --name-only 'stash@{0}^3'`, confirmed Phase 36-55 briefs and the read-only research inputs existed only in `stash@{0}^3`, restored the missing docs and research surface from that stash parent, and recorded the recovery path instead of regenerating any locked artifacts.
- Guardrail for next time: Before any cleanup touching a dirty tree, prove whether critical files are tracked or untracked, inspect stash topology explicitly (`stash@{n}`, `stash@{n}^3`), and never assume `git checkout <stash> -- <dir>` will recover untracked content without validating the result at file level.
- Evidence paths: `docs/lessonss.md`, `docs/phase_brief/phase36-brief.md`, `docs/phase_brief/phase55-brief.md`, `allocator_cpcv.sql`, `research_data/alloc_cpcv_splits`, `data/research_connector.py`, `git ls-files docs/phase_brief`, `git ls-tree -r --name-only 'stash@{0}'`, `git ls-tree -r --name-only 'stash@{0}^3'`, `git checkout 'stash@{0}^3' -- docs/phase_brief`

## 2026-03-17 Round Entry (Phase 55 Gate-Miss Governance Wording)
- Date: 2026-03-17
- Mistake or miss: The Phase 55 SSOT briefly described `D-311` as execution authorization even after the first bounded evidence packet had already failed the allocator gate.
- Root cause: Execution approval and post-evidence disposition were not recast as separate governance states once the summary artifact landed.
- Fix applied: Recomputed the locked gate from `data/processed/phase55_allocator_cpcv_summary.json`, recorded `D-311` as gate miss / no promotion, updated the Phase 55 brief wording, and kept artifact staging on `data/processed/phase55_*` only.
- Guardrail for next time: After every evidence packet, recompute the canonical gate from the published summary JSON in the same round and update SSOT docs before any further planning or promotion language.
- Evidence paths: `data/processed/phase55_allocator_cpcv_summary.json`, `data/processed/phase55_allocator_cpcv_evidence.json`, `docs/phase_brief/phase55-brief.md`, `docs/decision log.md`

## 2026-03-17 Round Entry (Phase 55 D-312 Repo-Verified Closeout)
- Date: 2026-03-17
- Mistake or miss: A thread-level claim treated `D-312` as already published before the repo SSOT actually contained the decision-log, brief, context-packet, and SAW updates.
- Root cause: Conversation state was treated as authoritative before file-system verification of the governance artifacts.
- Fix applied: Verified that `docs/decision log.md` still ended at `D-311`, then published `D-312` through synchronized updates to the Phase 55 brief, decision log, lessons log, context packet, and closeout SAW report.
- Guardrail for next time: Do not accept any governance transition as complete until `docs/decision log.md`, the active phase brief, and the current context packet all reflect the new state in the repo.
- Evidence paths: `docs/decision log.md`, `docs/phase_brief/phase55-brief.md`, `docs/context/current_context.md`, `docs/context/current_context.json`, `docs/saw_reports/saw_phase55_d312_closeout_20260317.md`

## 2026-03-18 Round Entry (Phase 56 Planning Kickoff Requires Repo Publication)
- Date: 2026-03-18
- Mistake or miss: A thread-level claim asserted that Phase 56 planning-only kickoff artifacts had already been published even though the repo still had no `phase56` brief, memo, or decision record.
- Root cause: Approval intent was conflated with completed repo publication.
- Fix applied: Verified the absence of `phase56` artifacts in the workspace, then published `D-313`, the Phase 56 kickoff brief, the kickoff memo, the refreshed context packet, and the docs-only SAW report in one synchronized round.
- Guardrail for next time: Treat an approval token as permission to publish the next-phase packet, not proof that the packet already exists; verify artifact presence in the repo before accepting the transition as complete.
- Evidence paths: `docs/decision log.md`, `docs/phase_brief/phase56-brief.md`, `docs/handover/phase56_kickoff_memo_20260318.md`, `docs/context/current_context.md`, `docs/context/current_context.json`, `docs/saw_reports/saw_phase56_d313_kickoff_20260318.md`

## 2026-03-18 Round Entry (Phase 56 Execution Token Must Match Published Contract)
- Date: 2026-03-18
- Mistake or miss: Thread-level language again tried to treat an execution-open claim as sufficient before checking whether the exact published token contract had actually been satisfied.
- Root cause: Execution intent and execution authorization were not separated tightly enough from the explicit `approve next phase` gate in the active brief.
- Fix applied: Verified `docs/phase_brief/phase56-brief.md` still required the exact token, waited for the literal `approve next phase` reply, then published `D-314` and refreshed the context packet in the same round.
- Guardrail for next time: Do not open execution from paraphrase or delegated summary; require the exact token string in-thread, then update repo SSOT immediately before any implementation work begins.
- Evidence paths: `docs/phase_brief/phase56-brief.md`, `docs/decision log.md`, `docs/context/current_context.md`, `docs/context/current_context.json`

## 2026-03-18 Round Entry (Phase 56 PEAD Slice Must Start From Repo-Verified Hooks)
- Date: 2026-03-18
- Mistake or miss: The thread narrative claimed a bounded PEAD slice and brief updates already existed before the repo had any on-disk implementation packet or evidence artifacts.
- Root cause: Thread-level execution intent was treated as if it were equivalent to inspected hook inventory and actual artifact publication.
- Fix applied: Re-read `backtests/event_study_csco.py`, the Phase 56 brief, and the PEAD-related data hooks; then implemented `scripts/phase56_pead_runner.py`, added focused tests, and published the first bounded evidence artifacts from repo-truth only.
- Guardrail for next time: Before coding a new phase slice, inspect the actual hook files and artifact availability on disk first; never let a thread claim substitute for repo-local proof of the current implementation surface.
- Evidence paths: `backtests/event_study_csco.py`, `scripts/phase56_pead_runner.py`, `tests/test_phase56_pead_runner.py`, `data/processed/phase56_pead_summary.json`, `data/processed/phase56_pead_evidence.csv`, `.venv\Scripts\python -m pytest tests/test_phase56_pead_runner.py -q --tb=no`, `.venv\Scripts\python scripts/phase56_pead_runner.py --start-date 2000-01-01 --end-date 2022-12-31 --max-date 2022-12-31 --cost-bps 5.0`

## 2026-03-18 Round Entry (Phase 56 Review Packets Must Quote the Real Summary Schema)
- Date: 2026-03-18
- Mistake or miss: Thread-level review language drifted into invented Phase 56 summary fields and implied dispositions that were not actually present in `data/processed/phase56_pead_summary.json`.
- Root cause: The review packet was being narrated from memory instead of reopening the on-disk summary artifact and constraining the wording to its actual schema.
- Fix applied: Re-read `data/processed/phase56_pead_summary.json`, anchored `D-316` to the exact published keys/metrics (`strategy_id`, `same_engine`, date clamp, Sharpe/CAGR/drawdown/ulcer/turnover/positions), and kept comparator or promotion language blocked.
- Guardrail for next time: Before publishing any review/closeout packet, open the actual summary artifact and quote only keys that exist on disk; if a field is absent, state that it is absent instead of inferring it.
- Evidence paths: `data/processed/phase56_pead_summary.json`, `docs/decision log.md`, `docs/phase_brief/phase56-brief.md`, `docs/context/current_context.md`, `docs/context/current_context.json`, `docs/saw_reports/saw_phase56_d316_review_20260318.md`

## 2026-03-18 Round Entry (Streamlit Test Contamination Cleanup)
- Date: 2026-03-18
- Mistake or miss: Dashboard integration tests mocked `sys.modules['streamlit']` without restoring full module state, which contaminated later tests and triggered `DeltaGeneratorSingleton instance already exists!`.
- Root cause: Only the top-level `streamlit` module was deleted/replaced, leaving `streamlit.*` submodules and singleton state alive in the shared pytest process.
- Fix applied: Removed Streamlit module mocking from `tests/test_dashboard_integration.py` and used a plain `session_state` dict, so tests no longer alter global import state.
- Guardrail for next time: Do not mock Streamlit via `sys.modules` in shared pytest runs; if isolation is required, snapshot/restore the full `streamlit*` module tree or use subprocess isolation.
- Evidence paths: `tests/test_dashboard_integration.py`, `tests/test_auto_backtest_view.py`, `tests/test_dashboard_sprint_a.py`, `.venv\Scripts\python -m pytest tests/test_auto_backtest_view.py tests/test_dashboard_integration.py tests/test_dashboard_sprint_a.py::test_metrics_source -q --tb=short`

## 2026-03-18 Round Entry (Phase 56 Closeout Gate Requires Uninterrupted Evidence)
- Date: 2026-03-18
- Mistake or miss: An initial closeout regression run was interrupted, leaving a misleading status artifact and an incomplete evidence trail.
- Root cause: Full-suite regression runs were not treated as atomic evidence captures; interruption yielded partial logs.
- Fix applied: Re-ran `.venv\Scripts\python -m pytest -q` and `launch.py --help` into `docs/context/e2e_evidence/` with status files, then captured a bounded PEAD replay artifact set.
- Guardrail for next time: Treat phase-end evidence captures as atomic; if interrupted, delete partial artifacts and rerun to produce clean status + log pairs.
- Evidence paths: `docs/context/e2e_evidence/phase56_closeout_full_pytest_20260318.*`, `docs/context/e2e_evidence/phase56_launch_smoke_20260318.*`, `docs/context/e2e_evidence/phase56_pead_replay_20260318.*`

## 2026-03-18 Round Entry (Phase 57 Kickoff Must Stay Planning-Only and Repo-Verified)
- Date: 2026-03-18
- Mistake or miss: A Phase 57 kickoff claim could have been published as if comparator approval or a Corporate Actions implementation surface already existed on disk.
- Root cause: Phase-transition intent arrived immediately after a closeout round, which makes it easy to blur a docs-only kickoff with executed hooks or reopened predecessor scope.
- Fix applied: Re-read the locked Phase 53 roadmap, the Phase 56 closeout packet, and the repo-local Corporate Actions reuse hooks (`data/build_tri.py`, `tests/test_build_tri.py`, `core/instrument_mapper.py`, `scripts/generate_instrument_mapping.py`, `backtests/event_study_csco.py`, `scripts/phase56_pead_runner.py`), then published `D-318` as planning-only with execution still blocked.
- Guardrail for next time: Before publishing any next-phase kickoff, reopen the roadmap and the real hook files first; never imply that missing hooks exist, that the predecessor phase reopened, or that execution is authorized before the repo SSOT says so.
- Evidence paths: `docs/phase_brief/phase53-brief.md`, `docs/phase_brief/phase56-brief.md`, `docs/phase_brief/phase57-brief.md`, `docs/handover/phase57_kickoff_memo_20260318.md`, `docs/decision log.md`, `docs/context/current_context.md`, `docs/context/current_context.json`, `docs/saw_reports/saw_phase57_d318_kickoff_20260318.md`

## 2026-03-18 Round Entry (Sparse Event Sleeves Must Reindex the Full Trading Calendar)
- Date: 2026-03-18
- Mistake or miss: A first draft of the Phase 57 Corporate Actions runner risked simulating only sparse event dates, which would have let the engine carry positions until the next event date instead of executing a bounded next-day / one-day hold.
- Root cause: Event-driven candidate selection was treated as if it were the execution calendar, but `core.engine.run_simulation` shifts exposures over the index actually provided to it.
- Fix applied: Reindexed the Phase 57 target-weight matrix to the full trading calendar from `prices.parquet`, forced zero weights on non-event dates, and added focused tests for the full-calendar contract before publishing the first bounded evidence packet.
- Guardrail for next time: Any sparse event sleeve must build target weights on the full trading calendar before calling `core.engine.run_simulation`; never pass an event-only index unless the intended holding period is explicitly that sparse schedule.
- Evidence paths: `scripts/phase57_corporate_actions_runner.py`, `tests/test_phase57_corporate_actions_runner.py`, `data/processed/phase57_corporate_actions_summary.json`, `data/processed/phase57_corporate_actions_evidence.csv`

## 2026-03-18 Round Entry (Long Closeout Evidence Captures Must Escape the Interactive Shell Host)
- Date: 2026-03-18
- Mistake or miss: A monolithic interactive-shell capture of the full pytest closeout evidence for Phase 57 repeatedly died near completion and left partial logs.
- Root cause: The interactive shell host was the unstable layer (`powershell.exe` AppHang / interruption), not a proven pytest or memory failure.
- Fix applied: Re-ran the full-suite closeout capture through a detached file-backed invocation and accepted only the atomic stdout / stderr / status artifact set once it completed successfully.
- Guardrail for next time: For long phase-end evidence captures, prefer detached or file-backed invocations over one monolithic interactive shell command; if a partial evidence file appears without a terminal status, delete it and rerun atomically.
- Evidence paths: `docs/context/e2e_evidence/phase57_closeout_full_pytest_20260318.stdout.log`, `docs/context/e2e_evidence/phase57_closeout_full_pytest_20260318.stderr.log`, `docs/context/e2e_evidence/phase57_closeout_full_pytest_20260318.status.txt`

## 2026-03-18 Round Entry (Governance Packets Must Separate Comparable Sleeves From Reference-Only Families)
- Date: 2026-03-18
- Mistake or miss: A first instinct for the Phase 58 Governance Layer packet could have mixed allocator-governance artifacts directly into the same-window / same-cost event-sleeve comparator surface.
- Root cause: All governance artifacts are related conceptually, but not all of them are comparable on the same execution surface.
- Fix applied: Kept the first bounded Phase 58 packet on the comparable event-sleeve family only (`Phase 56`, `Phase 57`) and carried the Phase 55 allocator summary as explicit `reference_only` context rather than inventing false comparability.
- Guardrail for next time: When building a governance packet, separate `comparable same-window/same-cost/same-engine` families from `reference_only` families explicitly; never force a mixed packet to look uniform if the source surfaces are not truly comparable.
- Evidence paths: `scripts/phase58_governance_runner.py`, `tests/test_phase58_governance_runner.py`, `data/processed/phase58_governance_summary.json`, `data/processed/phase58_governance_evidence.csv`, `data/processed/phase58_governance_delta_vs_c3.csv`

## 2026-03-18 Round Entry (Phase 59 Kickoff Must Inventory Live Shadow Hooks, Not Historical Path Assumptions)
- Date: 2026-03-18
- Mistake or miss: The historical Phase 53 roadmap pointed to several Shadow Portfolio hook paths that no longer exist at those exact locations in the current repo.
- Root cause: Roadmap lineage and current code layout drifted over time, so a planning packet could have overstated live implementation surfaces by trusting the old path list literally.
- Fix applied: Re-checked the repo-local shadow-related surfaces before publishing `D-327`, kept the kickoff inventory to the current read-only research connector/catalog surfaces plus historical `phase50_shadow_ship` artifacts that still exist on disk, and marked the missing query/alert/dashboard hooks explicitly as missing rather than implied.
- Guardrail for next time: Before any planning-only kickoff, verify every cited reuse hook exists at the current path; if a historical roadmap path is stale, record it as missing and do not imply the implementation surface is still live.
- Evidence paths: `docs/phase_brief/phase59-brief.md`, `docs/handover/phase59_kickoff_memo_20260318.md`, `data/research_connector.py`, `research_data/catalog.duckdb`, `data/processed/phase50_shadow_ship/gate_recommendation.json`

## 2026-03-18 Round Entry (Phase 59 Shadow Packet Must Split Research and Reference Lanes Explicitly)
- Date: 2026-03-18
- Mistake or miss: The first implementation instinct for Phase 59 could have implied that the read-only research lane and the historical shadow-reference lane shared one uniform holdings/turnover contract.
- Root cause: The Phase 53 research kernel exposes bounded return/state rows through `allocator_state`, while the Phase 50 shadow artifacts expose positions/turnover/telemetry; those surfaces are related but not identical.
- Fix applied: Implemented `phase59_shadow_portfolio` as two explicit lanes: a research-side Shadow NAV query and a reference-only Phase 50 alert contract, then carried the distinction into the summary/delta artifacts, brief, and notes.
- Guardrail for next time: When a packet combines historical monitoring artifacts with research-kernel artifacts, separate `research-comparable` and `reference-only operational` lanes explicitly; do not infer missing holdings/turnover fields from a return-only catalog.
- Evidence paths: `data/phase59_shadow_portfolio.py`, `scripts/phase59_shadow_portfolio_runner.py`, `views/shadow_portfolio_view.py`, `tests/test_phase59_shadow_portfolio.py`, `data/processed/phase59_shadow_summary.json`, `data/processed/phase59_shadow_delta_vs_c3.csv`

## 2026-03-18 Round Entry (Release Controller Reintroduced Windows os.kill PID Probe)
- Date: 2026-03-18
- Mistake or miss: `scripts/release_controller.py` reintroduced `os.kill(pid, 0)` for stale-lock owner liveness on Windows, repeating a previously logged cross-platform lock probe bug and destabilizing the pytest tail.
- Root cause: The earlier Windows lock-liveness guardrail lived in `docs/lessonss.md` but had not yet been promoted into repo-level engineering policy, so the anti-pattern resurfaced in a different lock implementation.
- Fix applied: Replaced the Windows path in `release_controller` with a WinAPI-based non-destructive process liveness query, reran the affected release-controller tests, and promoted the guardrail into `AGENTS.md`.
- Guardrail for next time: For any lock owner / stale-lock liveness check, never use `os.kill(pid, 0)` on Windows; require an OS-native query and treat any recurrence as a repo-policy violation.
- Evidence paths: `scripts/release_controller.py`, `tests/test_release_controller.py`, `AGENTS.md`, `docs/context/e2e_evidence/phase59_targeted_tests_20260318.status.txt`, `docs/context/e2e_evidence/phase59_full_pytest_20260318.status.txt`

## 2026-03-18 Round Entry (Phase 59 Review and Closeout Must Cite Artifact Truth Only)
- Date: 2026-03-18
- Mistake or miss: The first Phase 59 execution summary risked collapsing `implementation`, `review`, and `closeout` into one packet label, which weakened the explicit evidence-review gate expected by the repo governance pattern.
- Root cause: The bounded packet implementation completed in one round, but the repo governance contract still requires a separate evidence-only review state and a distinct closeout state even when the technical work is already done.
- Fix applied: Recast `D-329` as the formal evidence-only / no-promotion / no-widening review packet citing only on-disk Phase 59 artifact fields, then published `D-330` as the closeout packet with the same SSOT artifacts unchanged.
- Guardrail for next time: When a bounded packet finishes in one round, still publish a distinct `execution -> review -> closeout` governance sequence; the review packet must cite only artifact truth, and the closeout packet must reuse the same immutable SSOT artifacts.
- Evidence paths: `docs/decision log.md`, `docs/phase_brief/phase59-brief.md`, `docs/handover/phase59_handover.md`, `docs/saw_reports/saw_phase59_d329_d330_closeout_20260318.md`

## 2026-03-18 Round Entry (Phase 60 Planning-Only Kickoff Must Freeze Contracts Before Implementation Tokens)
- Date: 2026-03-18
- Mistake or miss: Stable-shadow follow-up discussion was close to carrying unresolved contracts (unified comparator surface, cost basis, post-2022 audit shape, allocator eligibility) as implied assumptions instead of explicit planning inputs.
- Root cause: The roadmap named Phase 60, but the four execution-critical contracts were not yet frozen in one planning-only artifact after the Phase 59 closeout.
- Fix applied: Published `D-331`, created `docs/phase_brief/phase60-brief.md`, created `docs/handover/phase60_kickoff_memo_20260318.md`, and refreshed `docs/context/bridge_contract_current.md` so the four contracts are explicit while implementation remains blocked.
- Guardrail for next time: Before any new phase spans multiple prior evidence surfaces, lock comparator surface, cost basis, audit spec, and eligibility rules in docs before any implementation token is allowed.
- Evidence paths: `docs/decision log.md`, `docs/phase_brief/phase60-brief.md`, `docs/handover/phase60_kickoff_memo_20260318.md`, `docs/context/bridge_contract_current.md`, `docs/context/current_context.md`, `docs/context/current_context.json`

## 2026-03-19 Round Entry (Execution Packets Must Refresh Bridge + SAW in the Same Round)
- Date: 2026-03-19
- Mistake or miss: The D-337 execution packet left the bridge on stale D-335 planning-only language and the D-337 SAW report outside the required validator-clean schema.
- Root cause: Governance artifacts were refreshed unevenly after the execution transition, so the decision log/brief/context moved to D-337 while bridge/SAW lagged behind.
- Fix applied: Published `D-338`, refreshed `docs/context/bridge_contract_current.md` to D-337 truth, rewrote `docs/saw_reports/saw_phase60_d337_first_packet_20260318.md` into the required schema, refreshed context artifacts, and held any code/cube start pending the next explicit packet.
- Guardrail for next time: When a phase transitions from planning to execution, refresh decision log, brief, bridge, context, and SAW in the same round; do not treat bridge/SAW as optional follow-up cleanup.
- Evidence paths: `docs/decision log.md`, `docs/context/bridge_contract_current.md`, `docs/saw_reports/saw_phase60_d337_first_packet_20260318.md`, `docs/context/current_context.md`, `docs/context/current_context.json`, `docs/context/e2e_evidence/phase60_d338_d337_saw_validate_20260319.txt`

## 2026-03-19 Round Entry (Validator Freshness Must Follow the Feature Builder's Governed Price Surface)
- Date: 2026-03-19
- Mistake or miss: The data-layer validator originally compared `features.parquet` against `prices.parquet + yahoo_patch.parquet`, even when the feature builder was operating in TRI mode on `prices_tri.parquet`.
- Root cause: Freshness validation was keyed to a generic latest-price surface instead of the actual governed input surface selected by `_price_source_config()`.
- Fix applied: Locked the validator to the feature builder's governed price surface, added regression tests for both lag and lead cases, verified live validator PASS, and published the bounded governed cube off the same same-window / same-cost sleeve surfaces.
- Guardrail for next time: Any freshness or integrity validator must reference the exact runtime-configured input surface of the builder it is validating; never compare to a broader surface the builder does not consume.
- Evidence paths: `scripts/validate_data_layer.py`, `tests/test_validate_data_layer.py`, `docs/context/e2e_evidence/phase60_validator_fix_20260319_validate_data_layer.txt`, `docs/context/e2e_evidence/phase60_validator_fix_20260319_full_pytest.status.txt`, `scripts/phase60_governed_cube_runner.py`, `tests/test_phase60_governed_cube_runner.py`

## 2026-03-19 Round Entry (Blocked Audit Reviews Must Stay Read-Only and SSOT-Bounded)
- Date: 2026-03-19
- Mistake or miss: A blocked audit packet can tempt follow-on work to rerun, widen, or “repair” the failed comparator path while claiming it is just a review.
- Root cause: Governance review scope can blur when the blocked packet and the remediation idea sit next to each other in the same phase.
- Fix applied: Published D-341 as a read-only review over the four immutable D-340 SSOT artifacts only, confirmed the exact `274` missing executed-exposure return cells, and emitted an evidence-only hold packet with every authorization flag still false.
- Guardrail for next time: Formal review packets must read the frozen SSOT artifacts only and fail if those artifacts drift; never reopen the comparator path, mutate research data, or widen scope under the label of review.
- Evidence paths: `scripts/phase60_d341_blocked_audit_review.py`, `tests/test_phase60_d341_blocked_audit_review.py`, `docs/context/e2e_evidence/phase60_d341_review_20260319_summary.json`, `docs/context/e2e_evidence/phase60_d341_review_20260319_findings.csv`, `docs/context/e2e_evidence/phase60_d341_review_20260319.status.txt`

## 2026-03-19 Round Entry (Active Briefs Must Not Carry Resolved Blockers Forward)
- Date: 2026-03-19
- Mistake or miss: The active Phase 60 brief still carried a resolved validator-failure block, and the bridge still cited the kickoff memo instead of the current execution handover.
- Root cause: Historical planning language and evidence references were not cleaned up after the validator gate was cleared and the execution-era handover became the active SSOT.
- Fix applied: Published `D-343`, removed the stale resolved-validator block from the active brief, refreshed the bridge evidence attribution to the execution handover, rebuilt the context packet, and added a focused regression to prevent recurrence.
- Guardrail for next time: When a blocker is resolved, remove it from active-state sections and keep it only in historical outcome sections; when a new handover supersedes a kickoff memo, update bridge evidence references in the same round.
- Evidence paths: `docs/phase_brief/phase60-brief.md`, `docs/context/bridge_contract_current.md`, `docs/handover/phase60_execution_handover_20260318.md`, `tests/test_phase60_d343_hygiene.py`, `docs/context/e2e_evidence/phase60_d343_hygiene_20260319_targeted_pytest.status.txt`

## 2026-03-19 Round Entry (Hold States Must Be Stamped Explicitly in the Active Brief Status)
- Date: 2026-03-19
- Mistake or miss: Even after the D-341 blocked-audit hold became the active Phase 60 reality, the brief status still read `EXECUTING_BOUNDED`, which understated the actual blocked-hold state.
- Root cause: Governance-close wording was updated in narrative sections, but the top-level status field lagged behind the true hold disposition.
- Fix applied: Published `D-344`, updated the active Phase 60 brief status to `BLOCKED_EVIDENCE_ONLY_HOLD`, refreshed the bridge/current-context surfaces, and kept all execution/remediation boundaries unchanged.
- Guardrail for next time: When a phase enters an evidence-only hold, update the active brief status line in the same round; do not leave the top-level status implying freer execution than the decision packet allows.
- Evidence paths: `docs/phase_brief/phase60-brief.md`, `docs/decision log.md`, `docs/context/bridge_contract_current.md`, `docs/context/current_context.md`, `docs/context/current_context.json`

## 2026-03-19 Round Entry (Formal Closeouts Must Stamp Closed State Without Inventing Exit Authority)
- Date: 2026-03-19
- Mistake or miss: After the blocked-hold state was already clear, the repo still lacked one final closeout packet explicitly marking Phase 60 as closed while preserving the blocked root cause and the lack of remediation authority.
- Root cause: The team had the correct hold state, but the formal closeout marker had not yet been added to the brief/bridge/handover stack.
- Fix applied: Published `D-345`, updated the active brief status to `CLOSED_BLOCKED_EVIDENCE_ONLY_HOLD`, refreshed the bridge/current-context/handover surfaces, and preserved the exact `274`-cell comparator gap as the formal closeout basis.
- Guardrail for next time: When a phase is being closed as a blocked hold, stamp the closed status explicitly and keep the blocked root cause verbatim; do not imply that closeout itself authorizes remediation or next-phase work.
- Evidence paths: `docs/phase_brief/phase60-brief.md`, `docs/decision log.md`, `docs/context/bridge_contract_current.md`, `docs/handover/phase60_execution_handover_20260318.md`, `docs/context/current_context.md`, `docs/context/current_context.json`

## 2026-03-20 Round Entry (Readonly Repair Extracts Must Persist the Frozen Missing-Cell Manifest)
- Date: 2026-03-20
- Mistake or miss: The frozen `D-341` review packet preserved the exact missing-cell count (`274`) but not the exact `(date, permno)` manifest needed for later readonly repair extracts, while the current live comparator reconstruction had already drifted to `275`.
- Root cause: The evidence-only blocked review locked count-level truth but did not publish the concrete missing-cell roster, which forced downstream extraction to infer the affected universe from a drifted live reconstruction.
- Fix applied: Generated additive-only readonly CUSIP output artifacts for the inferred single-name universe (`PERMNO 86544 -> CUSIP 095229100`), anchored the round to the D-341 count as the authority surface, and published an evidence summary that records the live `274` vs `275` drift explicitly.
- Guardrail for next time: Whenever a blocked evidence packet may feed a later repair or sidecar-prep step, persist the frozen `(date, permno)` manifest in the same round as the count-level review packet so later extracts do not have to infer scope from mutable live data.
- Evidence paths: `data/processed/d341_missing_executed_exposure_cusips.txt`, `data/processed/d341_missing_executed_exposure_permno_cusip.csv`, `data/processed/d341_missing_executed_exposure_permno_cusip.parquet`, `docs/context/e2e_evidence/phase60_d350_cusip_extract_20260320_summary.json`, `docs/saw_reports/saw_phase60_d350_cusip_extract_20260320.md`

## 2026-03-19 Round Entry (Phase 60 Kernel Mutation Blocked Reaffirmation)
- Date: 2026-03-19
- Mistake or miss: During Phase 60 review, a technical proposal attempted to remediate the exact 274-cell KS-03 gap by altering core engine defaults (`strict_missing_returns`) and snapshot hashing mechanisms.
- Root cause: Structural architecture fixes were being proposed to bypass a blocked comparator check, which violated the D-346/D-345 closeout boundary that prohibited direct remediation.
- Fix applied: Published `D-347`, explicitly blocked both Option A architecture changes, locked `core/engine.py` as immutable, preserved the 274-cell gap verbatim, and required a formal `approve next phase` token for any future kernel widening or Phase 61 work.
- Guardrail for next time: When a phase is formally blocked by governance on a gap, never remediate the underlying engine component without a brand new authorized execution phase; structural changes to bypass explicit hold states are kernel mutations.
- Evidence paths: `docs/decision log.md`, `docs/phase_brief/phase60-brief.md`, `docs/context/bridge_contract_current.md`, `docs/handover/phase60_execution_handover_20260318.md`

## 2026-03-19 Round Entry (Phase 61 Transition and Data-Level Completeness Rule)
- Date: 2026-03-19
- Mistake or miss: During Phase 60, a blocked C3 comparator gap (274 missing cells) led to proposed architecture mutations, which were rightly rejected by D-347. The resolution (Phase 61 D-348) must use data-level sidecar completeness instead of kernel changes.
- Root cause: Missing data on executed exposures was originally framed as a code-level engine/comparator defect instead of a data-completeness requirement matching the strict execution assumptions.
- Fix applied: Published `D-348`, consumed the CEO `approve next phase` token, closed Phase 60, and opened Phase 61 for a data-only patch preserving `strict_missing_returns=True` and `core/engine.py` immutability.
- Guardrail for next time: Resolve missing-return gaps on strict comparators via data-sidecar completeness patches or outer logic rather than mutating the core engine validation logic.
- Evidence paths: `docs/decision log.md`, `docs/phase_brief/phase60-brief.md`, `docs/handover/phase60_execution_handover_20260318.md`

## 2026-03-20 Round Entry (Prepare Downstream Ingest Before External Vendor Tape Arrives)
- Date: 2026-03-20
- Mistake or miss: The D-350 directive depended on a literal Capital IQ daily tape that is not currently producible on this workstation because the add-in is absent and the raw CSV does not exist yet.
- Root cause: The extraction step depended on an external vendor tool surface, while the local code path had not yet been hardened to ingest the tape immediately once it arrives.
- Fix applied: Upgraded `scripts/build_sp500_pro_sidecar.py` to prefer `data/raw/sp500_pro_avantax_tape.csv`, reject duplicate dates and floatless tapes, parse accounting-style negatives, and fail closed by default when the raw tape is missing.
- Guardrail for next time: When a repair round depends on an external vendor export, build and verify the downstream ingest path first, then report the local environment blocker explicitly instead of treating missing vendor data as if the remediation were complete.
- Evidence paths: `scripts/build_sp500_pro_sidecar.py`, `tests/test_build_sp500_pro_sidecar.py`, `docs/context/e2e_evidence/phase61_sp500_pro_tape_block_20260320.json`

## 2026-03-20 Round Entry (Strict Missing-Return Repairs Need Both Return Overlay and Pre-Execution Coverage Masking)
- Date: 2026-03-20
- Mistake or miss: The initial D-350 remediation framing assumed that publishing a sidecar file would patch KS-03 by itself.
- Root cause: The audit path was still loading returns from the base parquet only, and the comparator continued selecting AVTA after its last available return date, so strict `t -> t+1` execution would still fail even with a populated sidecar.
- Fix applied: Added sidecar return overlay logic to `scripts/phase60_governed_audit_runner.py`, added a sidecar-driven feature-date mask that drops sidecar permnos on and after their last available return date, and validated the repaired path with the real `2023-11-28` boundary return row from `data/processed/prices.parquet`.
- Guardrail for next time: For any strict missing-return repair, patch both interfaces explicitly:
  - the return surface the simulator consumes;
  - the feature/selection surface that can create next-day executed exposure after coverage ends.
- Evidence paths: `scripts/phase60_governed_audit_runner.py`, `scripts/ingest_d350_wrds_sidecar.py`, `tests/test_phase60_governed_audit_runner.py`, `tests/test_ingest_d350_wrds_sidecar.py`, `docs/context/e2e_evidence/phase61_d350_wrds_pivot_20260319_summary.json`, `docs/saw_reports/saw_phase61_d350_wrds_tape_20260319.md`

## 2026-03-20 Round Entry (Credential Presence Is Not Credential Validity)
- Date: 2026-03-20
- Mistake or miss: The Phase 61 blocker was initially tracked as missing WRDS environment variables, but a later live run showed that even with env vars supplied the login could still fail upstream.
- Root cause: Local environment readiness and remote authentication validity were treated as one gate instead of two separate checks.
- Fix applied: Executed the live extractor with supplied credentials, captured the WRDS PAM authentication failure explicitly, and updated the Phase 61 brief/evidence/SAW surfaces to reflect an auth blocker rather than a missing-env blocker.
- Guardrail for next time: For external authenticated data repairs, verify both gates separately:
  - local env variables present;
  - remote login succeeds.
- Evidence paths: `scripts/ingest_d350_wrds_sidecar.py`, `docs/phase_brief/phase61-brief.md`, `docs/context/e2e_evidence/phase61_d350_wrds_pivot_20260319_summary.json`, `docs/saw_reports/saw_phase61_d350_wrds_tape_20260319.md`

## 2026-03-22 Round Entry (Current Truth Surfaces Must Refresh in the Same Round as Phase-State Changes)
- Date: 2026-03-22
- Mistake or miss: The active Phase 61 brief and `D-351` evidence said `KS-03` was cleared, but `current_context`, planner, bridge, impact, alignment, observability, and README still advertised the older Phase 60 blocked-hold state.
- Root cause: `scripts/build_context_packet.py` still selected the latest phase doc with a `New Context Packet`, and the Phase 61 brief had not published one; the broader current packet set also was not refreshed in the same round as the newer phase-state evidence.
- Fix applied: Added a `New Context Packet` block to `docs/phase_brief/phase61-brief.md`, rebuilt `docs/context/current_context.*`, refreshed the stale `*_current.md` packet set plus `README.md`, and added regression tests for current-phase promotion and packet alignment.
- Guardrail for next time: Whenever a phase brief changes the active phase/status, publish or refresh the `New Context Packet` in that same phase doc, rerun `scripts/build_context_packet.py` and `--validate`, and run packet hygiene tests before closing the round.
- Evidence paths: `docs/phase_brief/phase61-brief.md`, `docs/context/current_context.md`, `docs/context/current_context.json`, `docs/context/planner_packet_current.md`, `docs/context/bridge_contract_current.md`, `README.md`, `tests/test_build_context_packet.py`, `tests/test_phase61_context_hygiene.py`

## 2026-05-09 Round Entry (Secret Hygiene Must Avoid Even Fragmentary Echoes)
- Date: 2026-05-09
- Mistake or miss: During the D-353 provenance closeout, a checklist draft briefly used literal credential fragments as examples for a secret scan, which could have persisted sensitive material even though the final implementation was env-only.
- Root cause: The scan proof was framed around specific pasted material instead of a generic scanner command and a no-match result.
- Fix applied: Replaced the checklist wording with a generic secret-scanner requirement, reran the milestone secret scan, and kept the broker integration env-only with no credential material in source, docs, tests, logs, or artifacts.
- Guardrail for next time: Never write pasted secrets or fragments of pasted secrets into docs, tests, comments, or evidence commands; prove hygiene with generic scanners and no-match status only.
- Evidence paths: `docs/context/done_checklist_current.md`, `execution/broker_api.py`, `data/provenance.py`, `docs/saw_reports/saw_phase64_d353_provenance_validation_20260509.md`, `tests/test_execution_controls.py`, `tests/test_provenance_policy.py`

## 2026-05-09 Round Entry (Dependency Closure Must Precede Experiment Multiplication)
- Date: 2026-05-09
- Mistake or miss: D-353 closed with `pip check` red, which would have let Candidate Registry start on an unstable dependency surface.
- Root cause: Functional tests passed, but dependency compatibility was treated as a carried risk instead of an entry gate for experiment multiplication.
- Fix applied: Migrated the main Alpaca SDK boundary to `alpaca-py==0.43.4`, removed the legacy Alpaca SDK from the main dependency files and venv, regenerated `requirements.lock`, added dependency hygiene tests, and reran `pip check`.
- Guardrail for next time: Before starting any candidate-generation or experiment-multiplication phase, require `pip check` to pass or explicitly isolate the conflicting package outside the main research environment.
- Evidence paths: `execution/broker_api.py`, `requirements.txt`, `requirements.lock`, `pyproject.toml`, `tests/test_dependency_hygiene.py`, `docs/phase_brief/phase65-brief.md`, `docs/saw_reports/saw_phase64_1_dependency_git_hygiene_20260509.md`

## 2026-05-09 Round Entry (Candidate Memory Must Precede Candidate Results)
- Date: 2026-05-09
- Mistake or miss: The project had many historical "candidate" references but no append-only identity ledger that records trial intent before results.
- Root cause: Prior phases optimized and validated bounded ideas without a dedicated pre-result registry, which would make future multiple-testing accounting too easy to reconstruct after seeing outcomes.
- Fix applied: Added the Phase 65 Candidate Registry kernel with frozen candidate specs, append-only JSONL events, hash-chain verification, rebuildable snapshots, dummy lifecycle evidence, and tests for required manifests/source quality/trial counts/parameters.
- Guardrail for next time: Do not start strategy search, parameter sweeps, alerts, or promotion packets until every candidate family and trial count is recorded in the registry before result generation.
- Evidence paths: `v2_discovery/schemas.py`, `v2_discovery/registry.py`, `tests/test_candidate_registry.py`, `scripts/run_candidate_registry_demo.py`, `data/registry/candidate_events.jsonl`, `data/registry/candidate_snapshot.json`, `docs/architecture/candidate_registry_policy.md`, `docs/saw_reports/saw_phase65_candidate_registry_20260509.md`

## 2026-05-09 Round Entry (Fast Proxy Outputs Must Stay Outside Canonical Truth)
- Date: 2026-05-09
- Mistake or miss: After Candidate Registry, the next likely drift risk was letting future fast proxy outputs look like official validation evidence.
- Root cause: A proxy simulator can become seductive infrastructure unless the boundary makes non-promotion and V1 rerun requirements executable before useful simulations exist.
- Fix applied: Added the Phase G0 V2 Proxy Boundary Harness with frozen proxy schemas, manifest/candidate/event validation, real registry note proof, no-op proxy round trip, forced `promotion_ready = false`, forced `canonical_engine_required = true`, and tests proving no alert/broker/search path is exposed.
- Guardrail for next time: Do not add a real fast simulator or strategy family until proxy outputs are already blocked from promotion, every promotion path requires `core.engine.run_simulation`, and proxy audit IDs resolve to append-only registry events.
- Evidence paths: `v2_discovery/fast_sim/schemas.py`, `v2_discovery/fast_sim/boundary.py`, `v2_discovery/fast_sim/noop_proxy.py`, `tests/test_v2_proxy_boundary.py`, `docs/architecture/v2_proxy_boundary_policy.md`, `docs/saw_reports/saw_phase65_v2_proxy_boundary_20260509.md`

## 2026-05-09 Round Entry (Same-Phase Handover Suffixes Must Not Regress Current Context)
- Date: 2026-05-09
- Mistake or miss: Phase G1 initially added a fresh handover, but the context packet builder still preferred the older same-phase `phase65_g0_handover.md` over `phase65_g1_handover.md`.
- Root cause: context source selection ranked only phase number, broad source type, and path order; it did not understand same-phase G-suffix progression.
- Fix applied: Added suffix-aware source ranking in `scripts/build_context_packet.py`, added a regression in `tests/test_build_context_packet.py`, rebuilt `docs/context/current_context.*`, and validated the context packet.
- Guardrail for next time: When closing subphases under the same numeric phase, add or validate a context-selection test that proves the newest suffix is the active source before refreshing planner packets.
- Evidence paths: `scripts/build_context_packet.py`, `tests/test_build_context_packet.py`, `docs/context/current_context.json`, `docs/context/current_context.md`

## 2026-05-09 Round Entry (Synthetic Proxy Mechanics Must Prove Hashes Before Accounting)
- Date: 2026-05-09
- Mistake or miss: The first G1 test harness copied fixture files through text writes, which changed bytes on Windows and made hash validation fail earlier than the intended invariant.
- Root cause: Fixture hashes are byte-level contracts, but the temporary-fixture test setup treated CSV copies as text-normalized content.
- Fix applied: Switched fixture-copy tests to byte-preserving writes, kept component hash validation in `v2_discovery/fast_sim/fixtures.py`, and added deterministic golden-file and accounting-property tests.
- Guardrail for next time: For manifest-backed fixtures, copy and mutate files at the byte/hash-contract level first, then test semantic invariants only after manifest hashes are intentionally aligned.
- Evidence paths: `v2_discovery/fast_sim/fixtures.py`, `tests/test_v2_fast_proxy_synthetic.py`, `tests/test_v2_fast_proxy_invariants.py`, `data/fixtures/v2_proxy/synthetic_manifest.json`

## 2026-05-09 Round Entry (Synthetic Proxy Evidence Must Fail Closed On Non-Finite And Sparse Inputs)
- Date: 2026-05-09
- Mistake or miss: G1 initially accepted some deterministic-looking bad evidence paths: non-finite numbers were not uniformly rejected, fixture manifests did not reconcile row count/date range/schema metadata, nullable symbols could become literal `<NA>`, and sparse target weights could be silently imputed to zero.
- Root cause: Hash validation proved file bytes, but semantic validation was spread across local checks and did not treat fixture metadata, symbol nulls, target-weight sparsity, and strict JSON numeric validity as one fail-closed boundary.
- Fix applied: Added reusable fast-proxy validators, finite guards across fixture/pre-ledger/post-ledger/result/proxy metadata boundaries, per-file manifest reconciliation, missing-symbol and sparse-weight regressions, and final Reviewer B/C rechecks.
- Guardrail for next time: For any simulator fixture, require a single validation layer that rejects `nan`, `+inf`, `-inf`, sparse required matrices, missing identifiers, and manifest metadata drift before simulation or golden comparison; never repair evidence with `nan_to_num`, `fillna(0)`, interpolation, or stringified nulls.
- Evidence paths: `v2_discovery/fast_sim/validation.py`, `v2_discovery/fast_sim/fixtures.py`, `v2_discovery/fast_sim/ledger.py`, `v2_discovery/fast_sim/schemas.py`, `tests/test_v2_fast_proxy_synthetic.py`, `tests/test_v2_fast_proxy_invariants.py`, `data/fixtures/v2_proxy/synthetic_manifest.json`, `docs/saw_reports/saw_phase65_g1_synthetic_proxy_20260509.md`

## 2026-05-09 Round Entry (Replay Closeout Needs Fresh Handover Source And Owned Errors)
- Date: 2026-05-09
- Mistake or miss: The first G3 focused test pass exposed two closure risks: duplicate fixture candidates could be hidden when a candidate ID was supplied, and lower-level proxy errors bubbled out without the G3 boundary type. Later, the context packet builder still selected the older G1 handover after the phase brief was updated.
- Root cause: The G3 selector narrowed by requested candidate before enforcing the global one-fixture invariant; the replay wrapper delegated to G2 without normalizing errors; context source ranking prefers latest phase handover over phase brief.
- Fix applied: Enforced global fixture-count validation before candidate-ID selection, wrapped lower-level proxy boundary errors as `G3ReplayError`, added `docs/handover/phase65_g3_handover.md`, and rebuilt/validated context packets.
- Guardrail for next time: For every same-phase G-suffix closeout, publish the newest suffix handover before running `scripts/build_context_packet.py`, and enforce cardinality invariants before optional selector filters.
- Evidence paths: `v2_discovery/replay/canonical_replay.py`, `tests/test_v2_canonical_replay_fixture.py`, `docs/handover/phase65_g3_handover.md`, `docs/context/current_context.md`, `scripts/build_context_packet.py --validate`

## 2026-05-09 Round Entry (Real Canonical Readiness Needs Its Own Tiny Manifest)
- Date: 2026-05-09
- Mistake or miss: The full `prices_tri.parquet` artifact was real and canonical, but it did not have a dedicated sidecar manifest suitable for a tiny first-contact readiness proof.
- Root cause: Prior readiness audits summarized large canonical artifacts, while G4 needed a small immutable fixture with exact hash, row-count, schema, date-range, key, and domain evidence.
- Fix applied: Created a tiny Tier 0 `prices_tri` fixture under `data/fixtures/g4/`, sealed it with a dedicated manifest, defaulted readiness execution to `report_path=None`, and removed contiguous forbidden metric/provider tokens from readiness implementation source scans.
- Guardrail for next time: For first-contact real data phases, derive the smallest clean canonical fixture, publish its own manifest, and run source-level forbidden-path scans so reject-list strings cannot masquerade as broker or performance behavior.
- Evidence paths: `data/fixtures/g4/prices_tri_real_canonical_tiny_slice.parquet`, `data/fixtures/g4/prices_tri_real_canonical_tiny_slice.parquet.manifest.json`, `v2_discovery/readiness/canonical_slice.py`, `v2_discovery/readiness/canonical_readiness.py`, `tests/test_g4_real_canonical_readiness_fixture.py`

## 2026-05-09 Round Entry (Real Canonical Replay Must Stay Mechanical)
- Date: 2026-05-09
- Mistake or miss: A real canonical replay can easily be misread as strategy evidence if the report exposes return-series or performance-style fields.
- Root cause: The official engine naturally computes return columns, but G5's purpose is proving replay plumbing and accounting controls, not evaluating edge.
- Fix applied: G5 calls `core.engine.run_simulation` for official-path proof, but the published report exposes only positions, cash, turnover, transaction cost, gross exposure, net exposure, manifest identity, and blocked promotion/alert/broker booleans.
- Guardrail for next time: For real-data replay phases before alpha authorization, keep engine return outputs internal, publish only mechanical accounting fields, default `report_path=None`, and run forbidden-field scans on implementation and artifact JSON.
- Evidence paths: `v2_discovery/replay/canonical_real_replay.py`, `v2_discovery/replay/canonical_replay_report.py`, `tests/test_g5_single_canonical_replay_no_alpha.py`, `data/registry/g5_single_canonical_replay_report.json`

## 2026-05-09 Round Entry (V1/V2 Real-Slice Match Still Is Not Promotion)
- Date: 2026-05-09
- Mistake or miss: A V1/V2 mechanical match on real canonical data could be misread as V2 promotion authority or strategy evidence if report fields or context surfaces are loose.
- Root cause: Mechanical equivalence and predictive edge are adjacent-looking artifacts unless the report explicitly separates equality fields, engine identity metadata, and promotion blockers.
- Fix applied: G6 compares only approved mechanical fields, records V1/V2 engine identity separately, keeps `promotion_ready = false` and `v2_promotion_ready = false`, defaults `report_path=None`, and publishes a dedicated mechanical-comparison policy.
- Guardrail for next time: When V2 matches V1 on real data, still require an explicit later decision before candidate-family definition, search, alerts, broker paths, paper trading, or promotion packets.
- Evidence paths: `v2_discovery/replay/real_slice_v1_v2_comparison.py`, `v2_discovery/replay/mechanical_comparison_report.py`, `tests/test_g6_v1_v2_real_slice_mechanical_comparison.py`, `data/registry/g6_v1_v2_real_slice_mechanical_report.json`

## 2026-05-09 Round Entry (Research Family Boundaries Must Exist Before Results)
- Date: 2026-05-09
- Mistake or miss: A future candidate could inherit a family label without a pre-result contract for allowed features, parameters, trial budget, and promotion data policy.
- Root cause: Candidate Registry records individual intent, but multiple-testing control needs the hypothesis family and trial budget fixed before outcomes exist.
- Fix applied: Added G7 candidate-family definition package, manifest-backed `PEAD_DAILY_V0` artifact, append-only/versioned behavior, finite parameter-space validation, trial-budget checks, and definition-only report hygiene.
- Guardrail for next time: Before generating even one candidate from a family, require the family JSON and manifest to reconcile, require `trial_budget_max`, and block all result, ranking, alert, broker, and promotion paths in the family-definition layer.
- Evidence paths: `v2_discovery/families/schemas.py`, `v2_discovery/families/registry.py`, `v2_discovery/families/validation.py`, `v2_discovery/families/trial_budget.py`, `tests/test_g7_candidate_family_definition.py`, `data/registry/candidate_families/pead_daily_v0.json`, `data/registry/candidate_families/pead_daily_v0.json.manifest.json`

## 2026-05-09 Round Entry (Roadmap Labels Must Match The Real Product Problem)
- Date: 2026-05-09
- Mistake or miss: After G7, the next default step still pointed toward PEAD candidate generation, which could make a tactical signal family look like the center of the product.
- Root cause: The technical governance roadmap was coherent, but the product framing had not been updated after the user clarified the real job: discretionary augmentation for de-risked asymmetric upside.
- Fix applied: Added G7.1 roadmap realignment docs, reclassified `PEAD_DAILY_V0` as tactical, named `SUPERCYCLE_GEM_DAILY_V0` as the primary product-family target, and refreshed current truth surfaces to hold G8 until a G7.2-or-hold decision.
- Guardrail for next time: Before candidate generation starts, verify that the roadmap label, family role, and dashboard mission match the current user problem; if not, run a docs/context realignment phase before implementation.
- Evidence paths: `docs/architecture/product_roadmap_discretionary_augmentation.md`, `docs/architecture/dashboard_signal_taxonomy.md`, `docs/architecture/supercycle_gem_family_policy.md`, `docs/handover/phase65_g71_handover.md`

## 2026-05-09 Round Entry (Streamlit Smoke Must Inspect Page Exceptions)
- Date: 2026-05-09
- Mistake or miss: A liveness-only `launch.py` smoke was treated as runtime evidence even though the legacy dashboard page had an uncaught `TypeError` in the promoted drift monitor tab.
- Root cause: The smoke checked whether the Streamlit process stayed alive but did not inspect stderr for `Uncaught app execution`, so a page-level failure looked like a pass.
- Fix applied: Passed the existing drift monitor dependencies into `render_drift_monitor_view`, added a focused dashboard integration regression, stopped stale smoke processes, and reran runtime smoke with stderr inspection.
- Guardrail for next time: Streamlit smoke evidence must check both process liveness and stderr/page-exception markers before being recorded as PASS.
- Evidence paths: `dashboard.py`, `tests/test_dashboard_drift_monitor_integration.py`, `tests/test_drift_monitor_view.py`, `docs/context/e2e_evidence/phase65_g7_1_launch_smoke_20260509_status.txt`, `docs/context/e2e_evidence/phase65_g7_1_launch_smoke_20260509_stderr.txt`

## 2026-05-09 Round Entry (Alpha-Suffix Handoffs Need Context-Builder Visibility)
- Date: 2026-05-09
- Mistake or miss: G7.1A first used `phase65_g71a_handover.md`, but the context packet builder ranks numeric G suffixes and could still select the older G7.1 packet if the alpha suffix is not made visible.
- Root cause: Same-phase source ranking parses `g<digits>` and ignores alphabetic suffix meaning; G7.1A is a product/planning label rather than a numeric suffix the builder understands.
- Fix applied: Added a docs-only selector alias `docs/handover/phase65_g71-1a_handover.md`, rebuilt `docs/context/current_context.*`, and validated context selection.
- Guardrail for next time: For same-phase alpha substeps, either update the context builder with explicit alpha-suffix ordering in a dedicated code phase or publish a clearly labeled selector alias that states it is not a new phase and does not authorize implementation.
- Evidence paths: `docs/handover/phase65_g71a_handover.md`, `docs/handover/phase65_g71-1a_handover.md`, `docs/context/current_context.md`, `scripts/build_context_packet.py --validate`

## 2026-05-09 Round Entry (Broad Compileall Can Surface Inherited Workspace Hygiene)
- Date: 2026-05-09
- Mistake or miss: The requested broad `.venv\Scripts\python -m compileall .` failed in a docs-only phase, even though the round did not edit code.
- Root cause: The broad workspace contains inherited hygiene issues: `scripts/wrds_schema_hunter.py` has null bytes, and some temp/cache directories have ACL-protected traversal.
- Fix applied: Isolated the null-byte source with a read-only scan, reran scoped compile checks over active packages/tests and current entry scripts, and recorded the broad compileall failure as inherited/out of scope in the impact and done surfaces.
- Guardrail for next time: For docs-only phases, run broad compileall when requested but distinguish inherited workspace traversal/source hygiene from the owned diff; keep a scoped compile check over active code paths as the actionable evidence.
- Evidence paths: `scripts/wrds_schema_hunter.py`, `docs/context/impact_packet_current.md`, `docs/context/done_checklist_current.md`, scoped `compileall`/`py_compile` outputs

## 2026-05-09 Round Entry (State Machines Must Wait For Data Reality)
- Date: 2026-05-09
- Mistake or miss: The next action after product canon could have jumped into G7.2 state-machine design before proving which GodView signals are actually available, delayed, licensed, estimated, or missing.
- Root cause: Product architecture vocabulary can make future capabilities sound present unless source readiness and provider gaps are mapped first.
- Fix applied: Ran G7.1B as docs/architecture/source mapping only, published signal-source matrix, provider roadmap, freshness policy, observed-vs-estimated policy, and Codex/Chrome SOP, and kept G7.2/G8 held.
- Guardrail for next time: Before designing any state machine that consumes a new data layer, require a source matrix with readiness, provider need, freshness, trust level, build priority, and observed/estimated/inferred labels for every signal family.
- Evidence paths: `docs/architecture/godview_data_infra_gap_assessment.md`, `docs/architecture/godview_signal_source_matrix.md`, `docs/architecture/godview_provider_roadmap.md`, `docs/architecture/godview_signal_freshness_policy.md`, `docs/architecture/godview_observed_vs_estimated_policy.md`, `docs/context/planner_packet_current.md`

## 2026-05-09 Round Entry (Research Capture Must Not Become Source Approval)
- Date: 2026-05-09
- Mistake or miss: A supplied API availability survey could be misread as audited source approval or as permission to start SEC/FINRA/CFTC provider work.
- Root cause: Source names and no-cost/public availability labels look implementation-ready unless the docs explicitly separate research capture, source audit, source policy, and provider implementation.
- Fix applied: Captured G7.1C as audit-pending research, added provider selection gates, marked no-cost paths as post-audit only, and refreshed truth surfaces to hold G7.2 and provider implementation.
- Guardrail for next time: Any external source survey must carry an audit queue, audit-pending status, and a no-provider/no-ingestion invariant before downstream planning can use it.
- Evidence paths: `docs/research/g7_1c_open_source_repo_data_api_availability_survey_20260509.md`, `docs/architecture/godview_provider_selection_policy.md`, `docs/architecture/godview_build_vs_borrow_decision.md`, `docs/context/planner_packet_current.md`

## 2026-05-09 Round Entry (Source Audit Must Not Become Ingestion Approval)
- Date: 2026-05-09
- Mistake or miss: Official public sources can look implementation-ready once terms and URLs are audited.
- Root cause: Source availability, fixture design, provider code, and dashboard/state-machine consumption are adjacent planning steps unless each is separated by explicit approval.
- Fix applied: Published G7.1C source audit, required-column terms matrix, tiny fixture schema plan only, provider priority note, refreshed context, and SAW report with no data downloads or provider files.
- Guardrail for next time: After source audit, require a one-source source policy and explicit tiny-fixture approval before any provider proof; keep observed, estimated, and inferred labels separate in every artifact.
- Evidence paths: `docs/architecture/godview_public_source_audit.md`, `docs/architecture/godview_source_terms_matrix.md`, `docs/architecture/godview_tiny_fixture_schema_plan.md`, `docs/saw_reports/saw_phase65_g7_1c_public_source_audit_20260509.md`

## 2026-05-09 Round Entry (Tiny Fixture Must Not Become Provider Code)
- Date: 2026-05-09
- Mistake or miss: Once a static SEC fixture exists, it can be mistaken for permission to build a live provider, expand tickers, or feed a state machine.
- Root cause: Static public-source samples and provider ingestion share endpoint vocabulary unless the fixture docs, manifests, and tests repeat the fixture-only boundary.
- Fix applied: Added G7.1D SEC policy, fixture plan, two static Apple Inc. fixtures, sidecar manifests, and fixture-only tests that validate provenance mechanics without adding a provider module.
- Guardrail for next time: Every tiny public-source fixture proof must state `fixture_only`, include allowed/forbidden use in manifests, validate static artifacts through tests, and keep provider/state-machine/scoring work behind a separate approval.
- Evidence paths: `docs/architecture/sec_tiny_fixture_policy.md`, `docs/architecture/sec_public_provider_fixture_plan.md`, `data/fixtures/sec/sec_companyfacts_tiny.json`, `data/fixtures/sec/sec_submissions_tiny.json`, `tests/test_g7_1d_sec_tiny_fixture.py`

## 2026-05-10 Round Entry (Short Interest Must Not Become A Squeeze Signal)
- Date: 2026-05-10
- Mistake or miss: FINRA short-interest fixtures can be mistaken for real-time squeeze evidence or mixed with Reg SHO short-sale-volume fields.
- Root cause: Short interest, short-sale volume, and squeeze pressure share similar vocabulary unless the fixture schema and policy make timing and measurement differences executable.
- Fix applied: Added the G7.1E FINRA short-interest policy, short-interest-vs-short-volume policy, a three-row static short-interest fixture, manifest allowed/forbidden use labels, and tests rejecting Reg SHO fields, duplicate primary keys, bad hashes, row-count drift, and non-finite/negative numeric values.
- Guardrail for next time: Treat FINRA short interest as delayed squeeze-base context only; require separate approval, separate fixture, and separate labels for Reg SHO or OTC/ATS data before any state-machine or scoring work.
- Evidence paths: `docs/architecture/finra_short_interest_tiny_fixture_policy.md`, `docs/architecture/finra_short_interest_vs_short_volume_policy.md`, `data/fixtures/finra/finra_short_interest_tiny.csv`, `data/fixtures/finra/finra_short_interest_tiny.manifest.json`, `tests/test_g7_1e_finra_short_interest_tiny_fixture.py`

## 2026-05-10 Round Entry (CFTC TFF Must Not Become Single-Name CTA Evidence)
- Date: 2026-05-10
- Mistake or miss: CFTC TFF broad futures-positioning rows can be mistaken for direct CTA buying evidence for a single stock.
- Root cause: `Leveraged Funds`, `systematic`, and `CTA pressure` vocabulary can sound stock-specific unless the fixture schema and policy force market-level, weekly, delayed interpretation.
- Fix applied: Added the G7.1F CFTC TFF fixture policy, usage policy, an eight-row static TFF fixture, manifest allowed/forbidden use labels, and tests rejecting single-name fields, duplicate primary keys, bad hashes, row-count drift, unknown trader categories, and non-finite/negative numeric values.
- Guardrail for next time: Treat CFTC TFF as broad regime/systematic-positioning context only; require separate approval, separate evidence, and explicit validation before any CTA score, state-machine input, ranking factor, alert, or single-name inference.
- Evidence paths: `docs/architecture/cftc_tff_tiny_fixture_policy.md`, `docs/architecture/cftc_cot_tff_usage_policy.md`, `data/fixtures/cftc/cftc_tff_tiny.csv`, `data/fixtures/cftc/cftc_tff_tiny.manifest.json`, `tests/test_g7_1f_cftc_tff_tiny_fixture.py`

## 2026-05-09 Round Entry (Macro / Factor Fixtures Must Not Become Scores)
- Date: 2026-05-09
- Mistake or miss: FRED macro rows and Ken French factor returns can be mistaken for permission to emit macro/factor regime scores or rank candidates.
- Root cause: Macro/factor language is naturally regime-oriented, so a tiny source fixture can sound like a model input unless manifests, policies, and tests forbid scoring/runtime fields.
- Fix applied: Added the G7.1G FRED / Ken French fixture policy, macro/factor usage policy, two static fixtures, manifest allowed/forbidden use labels, and tests rejecting score/runtime columns, duplicate primary keys, bad hashes, row-count/date-range drift, missing identifiers, and non-finite numeric values.
- Guardrail for next time: Treat public macro/factor rows as context-only until a separately approved state-machine or scoring phase; require real-time/vintage handling before any backtest or state-machine consumption.
- Evidence paths: `docs/architecture/fred_ken_french_tiny_fixture_policy.md`, `docs/architecture/macro_factor_context_usage_policy.md`, `data/fixtures/fred/fred_macro_tiny.csv`, `data/fixtures/ken_french/ken_french_factor_tiny.csv`, `tests/test_g7_1g_fred_ken_french_tiny_fixture.py`
## 2026-05-10 Round Entry (G7.2 Opportunity State Machine)
- Date: 2026-05-10
- Mistake or miss: State labels can be overread as trade instructions, and source classes can be overread as provider approval.
- Root cause: Opportunity-state vocabulary, source-policy vocabulary, and dashboard vocabulary are adjacent to execution language unless no-order/no-alert/no-score boundaries are explicit.
- Fix applied: Added finite opportunity states, transition evidence schemas, forbidden-jump register, and transition tests that fail closed on action metadata, estimated-only buying-range creation, and inferred-only winner-run creation.
- Guardrail for next time: Whenever introducing a state machine, define the no-order/no-alert boundary in the same round and test the forbidden jumps explicitly.
- Evidence paths: `opportunity_engine/states.py`, `opportunity_engine/schemas.py`, `opportunity_engine/transitions.py`, `tests/test_g7_2_opportunity_state_machine.py`

## 2026-05-10 Round Entry (G7.3 Signal-to-State Source Eligibility Map)
- Date: 2026-05-10
- Mistake or miss: Public fixture pillars and provider-gap families could be treated as available sources or action evidence.
- Root cause: Official, estimated, inferred, and provider-gap labels are easy to flatten unless source classes and confidence labels are explicit.
- Fix applied: Added source classes, signal-family policy maps, freshness requirements, and confidence labels that block estimated-only and provider-gap signals from action-state influence.
- Guardrail for next time: Whenever mapping signals to states, enforce source-class, freshness, and forbidden-influence checks before any dashboard or provider conversation.
- Evidence paths: `opportunity_engine/source_classes.py`, `opportunity_engine/signal_policy.py`, `tests/test_g7_3_signal_to_state_source_map.py`

## 2026-05-10 Round Entry (G7.4 Dashboard Wireframe / Product-State Spec)
- Date: 2026-05-10
- Mistake or miss: Dashboard section names can sound like runtime UI, and card fields can sound like candidate-card authority.
- Root cause: Product-spec language sits close to implementation language unless the no-runtime/no-alert/no-order boundary is repeated.
- Fix applied: Added state-first dashboard sections, watchlist card fields, daily brief sections, and focused tests that forbid orders, alerts, scores, rankings, provider calls, broker calls, and runtime dashboard code.
- Guardrail for next time: Whenever drafting dashboard specs, state explicitly that the artifact is product-spec only and test for forbidden runtime wording.
- Evidence paths: `docs/architecture/godview_dashboard_wireframe.md`, `docs/architecture/godview_watchlist_card_spec.md`, `docs/architecture/godview_daily_brief_spec.md`, `tests/test_g7_4_dashboard_state_spec.py`

## 2026-05-10 Round Entry (G8 Supercycle Candidate Card)
- Date: 2026-05-10
- Mistake or miss: A first real ticker card can be mistaken for candidate screening, alpha evidence, or a buying-range recommendation.
- Root cause: Once a human-nominated company appears in a structured object, product vocabulary can sound promotional unless source labels, missing evidence, and forbidden outputs are executable.
- Fix applied: Added one MU candidate-card schema, static card, manifest, and tests that require source-quality labels, restrict initial states, reject score/rank/signal/alert/broker fields, reject yfinance as canonical evidence, and require provider-gap labels for options/IV/gamma/whales.
- Guardrail for next time: Every candidate-card object must declare `candidate_card_only`, keep action states forbidden, and validate observed/estimated/inferred labels before any future signal-card or dashboard work can consume it.
- Evidence paths: `opportunity_engine/candidate_card_schema.py`, `opportunity_engine/candidate_card.py`, `data/candidate_cards/MU_supercycle_candidate_card_v0.json`, `data/candidate_cards/MU_supercycle_candidate_card_v0.manifest.json`, `tests/test_g8_supercycle_candidate_card.py`

## 2026-05-10 Round Entry (G8.1 Discovery Intake Must Not Become Ranking)
- Date: 2026-05-10
- Mistake or miss: A theme-to-candidate queue can be mistaken for alpha search, candidate ranking, or recommendations if the artifact only lists tickers.
- Root cause: Discovery vocabulary naturally sits close to screening vocabulary unless evidence requirements, provider gaps, and negated output flags are executable.
- Fix applied: Added a manifest-backed discovery intake schema, six-name static queue, theme taxonomy, and tests that reject score/rank fields, buy/sell/hold calls, validated status, action-state promotion, yfinance canonical evidence, and missing manifest evidence.
- Guardrail for next time: Every discovery queue must preserve intake-only status, require evidence-needed/thesis-breaker/provider-gap fields, and keep candidate-card promotion behind a separate approval.
- Evidence paths: `opportunity_engine/discovery_intake_schema.py`, `opportunity_engine/discovery_intake.py`, `data/discovery/supercycle_candidate_intake_queue_v0.json`, `tests/test_g8_1_supercycle_discovery_intake.py`

## 2026-05-10 Round Entry (Discovery Origin Must Not Drift Into System Scout)
- Date: 2026-05-10
- Mistake or miss: The G8.1 six-name queue could be read as system-discovered even though the names were user-seeded.
- Root cause: Intake artifacts had ticker/status fields but did not carry explicit discovery-origin provenance, so planner language could collapse user-seeded, theme-adjacent, factor-scouted, and system-scouted paths.
- Fix applied: Added `DiscoveryOrigin`, required origin fields, relabeled the six-name queue, blocked current seeds from `SYSTEM_SCOUTED`, held `LOCAL_FACTOR_SCOUT` until G8.1B, and added focused G8.1A tests.
- Guardrail for next time: Every discovery intake item must carry origin labels, origin evidence, scout path, and validation/action booleans before any planner treats it as discovered.
- Evidence paths: `opportunity_engine/discovery_intake_schema.py`, `data/discovery/supercycle_candidate_intake_queue_v0.json`, `tests/test_g8_1a_discovery_drift_policy.py`, `docs/architecture/discovery_drift_policy.md`

## 2026-05-10 Round Entry (Dashboard Redesign Must Start With IA)
- Date: 2026-05-10
- Mistake or miss: A dashboard redo can jump straight into Streamlit tabs and visual changes before the product page order is agreed.
- Root cause: The existing Sovereign Cockpit mixes operator cockpit, data health, drift ops, research lab, portfolio tools, and experiments as peer tabs.
- Fix applied: Approved DASH-0 as planning-only IA, mapped legacy tabs into state-first pages, moved Data Health/Drift Monitor to future Settings & Ops, and kept runtime shell work behind DASH-1 approval.
- Guardrail for next time: Dashboard runtime changes must start from an approved page map and migration plan; ops diagnostics and research tools should not crowd the main Command Center.
- Evidence paths: `docs/architecture/dashboard_information_architecture.md`, `docs/architecture/dashboard_page_registry_plan.md`, `docs/architecture/dashboard_redesign_migration_plan.md`, `docs/architecture/dashboard_ops_relocation_policy.md`

## 2026-05-10 Round Entry (Factor Scout Must Not Become Ranking)
- Date: 2026-05-10
- Mistake or miss: A local factor artifact can be overread as a discovery model with ranking or alpha meaning once it emits a system-scouted ticker.
- Root cause: Factor artifacts naturally contain internal numeric columns, and the word scout can collapse deterministic surfacing into recommendation language if manifests and validators do not block leakage.
- Fix applied: Wrapped the Phase 34 artifact as `LOCAL_FACTOR_SCOUT`, emitted exactly one intake-only item, selected by deterministic latest-date/local-metadata/ascending-permno rule, and validated no score, rank, action language, candidate-card creation, or yfinance canonical source.
- Guardrail for next time: Any future factor-scout output must keep numeric factor values quarantined, require a manifest-backed origin, and state that system-scouted means intake surfacing only until a separate validation phase approves model use.
- Evidence paths: `opportunity_engine/factor_scout_schema.py`, `opportunity_engine/factor_scout.py`, `data/discovery/local_factor_scout_output_tiny_v0.json`, `tests/test_g8_1b_pipeline_first_discovery_scout.py`, `docs/architecture/factor_scout_output_contract.md`

## 2026-05-10 Round Entry (Dashboard Shell Must Not Become Redesign)
- Date: 2026-05-10
- Mistake or miss: Moving from flat tabs to a page registry can accidentally become a page redesign or semantic expansion.
- Root cause: Streamlit navigation work sits next to visual layout, status badges, research tools, alerts, and scoring vocabulary unless the shell owns only routing and relocation.
- Fix applied: Added a DASH-1 page registry shell with approved IA pages, moved legacy content behind the mapped pages, kept new GodView pages as placeholders/status-only, and tested for no flat `st.tabs` navigation and no factor-scout/broker/action leakage.
- Guardrail for next time: Treat dashboard navigation changes as shell-only unless a later DASH phase explicitly approves page content redesign; keep old research and ops workflows grouped away from Command Center.
- Evidence paths: `dashboard.py`, `views/page_registry.py`, `tests/test_dash_1_page_registry_shell.py`, `docs/handover/dash_1_page_registry_shell_handover_20260510.md`

## 2026-05-10 Round Entry (System-Scouted Card Must Not Become Dashboard Action)
- Date: 2026-05-10
- Mistake or miss: MSFT can appear both as a legacy dashboard ticker-list row and as the new G8.2 candidate-card artifact, which can make the card look merged into dashboard action logic.
- Root cause: The legacy dashboard already contains MSFT runtime labels, tactical prices, trend labels, `COILED SPRING`, and `IGNORE`, while G8.2 introduces a file-backed MSFT research object with the same ticker.
- Fix applied: Documented the dashboard boundary in the G8.2 policy, bridge, planner packet, handover, PRD/spec notices, and tests; kept the card static and did not wire it into dashboard runtime.
- Guardrail for next time: Any future DASH card-reader lane must render candidate cards as status-only research objects and must explicitly avoid legacy action-shaped labels unless a later product state has separate approval.
- Evidence paths: `docs/architecture/g8_2_system_scouted_candidate_card_policy.md`, `data/candidate_cards/MSFT_supercycle_candidate_card_v0.json`, `tests/test_g8_2_system_scouted_candidate_card.py`, `dashboard.py`

## 2026-05-10 Round Entry (Portfolio Optimizer Should Stay Primary)
- Date: 2026-05-10
- Mistake or miss: The first DASH-2 pass hid Portfolio Optimizer behind an expander and placed it below the YTD comparison, making the primary allocation workflow feel secondary.
- Root cause: Cleanup pressure from removing Portfolio Builder marketing copy drifted into interaction hierarchy and treated the optimizer as optional instead of primary.
- Fix applied: Removed the optimizer expander/toggle, rendered optimizer above YTD Performance, calculated YTD portfolio return from current optimizer weights, and added live adjusted-close freshness overlays for selected stocks and SPY/QQQ.
- Guardrail for next time: When simplifying a page, preserve the primary operator workflow as top-level unless the user explicitly asks to demote it.
- Evidence paths: `dashboard.py`, `views/optimizer_view.py`, `tests/test_dash_2_portfolio_ytd.py`, browser check at `http://127.0.0.1:8502/portfolio-and-allocation`

## 2026-05-10 Round Entry (Display Order Must Not Become Portfolio Universe)
- Date: 2026-05-10
- Mistake or miss: The optimizer inherited `df_scan` display order and `selected_tickers[:20]`, which let EXIT/KILL rows enter the default portfolio universe and made a missing local price series look like a user-selected 19-name basket.
- Root cause: Discovery universe, dashboard display ranking, and allocation universe were collapsed into one handoff.
- Fix applied: Added `strategies/portfolio_universe.py`, wired `dashboard.py` to pass an audited universe to `views/optimizer_view.py`, default-excluded EXIT/KILL/AVOID/IGNORE, treated WATCH as research-only, reported ticker/price readiness, and added max-weight feasibility diagnostics.
- Guardrail for next time: Any capital-allocation handoff must use an explicit optimizer-universe contract and must show excluded names, missing mappings, price-history failures, and cap-bound warnings before optimization.
- Evidence paths: `strategies/portfolio_universe.py`, `dashboard.py`, `views/optimizer_view.py`, `tests/test_portfolio_universe.py`, `docs/architecture/portfolio_construction_contract.md`

## 2026-05-11 Round Entry (Dirty Optimizer Math Must Not Hide Inside Universe Closure)
- Date: 2026-05-11
- Mistake or miss: A dirty `strategies/optimizer.py` lower-bound/math diff was present while the Portfolio Universe Construction Fix was supposed to close only the mechanical universe handoff and diagnostics.
- Root cause: Broad dirty worktree state made it possible for out-of-scope optimizer-core edits to sit beside a narrow governance closure.
- Fix applied: Ran independent SAW reviewers; kept the round read-only for implementation; updated the SAW report to block on the unaccepted optimizer-core diff instead of silently passing governance.
- Guardrail for next time: Before portfolio closure, run a forbidden-scope diff scan across all dirty optimizer/scanner/runtime files and explicitly classify each dirty file as in-scope, inherited, or separately approved before claiming PASS.
- Evidence paths: `docs/saw_reports/saw_portfolio_universe_construction_fix_20260510.md`, `strategies/optimizer.py`, Reviewer B SAW finding, forbidden-scope scan output.

## 2026-05-11 Round Entry (Quarantine Before Pass)
- Date: 2026-05-11
- Mistake or miss: The universe-construction closure almost treated an optimizer-core lower-bound/SLSQP diff as a closure side issue instead of a separate model-policy change.
- Root cause: The closure gate checked focused portfolio behavior before isolating every dirty optimizer-core file in the worktree.
- Fix applied: Saved the dirty optimizer diff to `docs/quarantine/optimizer_core_lower_bounds_slsqp_diff_20260510.patch`, added a quarantine note, reverted `strategies/optimizer.py`, reran focused validation, and updated SAW to PASS only after the optimizer diff was gone.
- Guardrail for next time: A portfolio-universe PASS must require `git diff -- strategies/optimizer.py` to be empty unless an optimizer-core policy round explicitly owns that file.
- Evidence paths: `docs/quarantine/optimizer_core_lower_bounds_slsqp_diff_20260510.patch`, `docs/quarantine/optimizer_core_lower_bounds_slsqp_diff_note_20260510.md`, `docs/saw_reports/saw_portfolio_universe_construction_fix_20260510.md`, focused pytest/compile/context/browser evidence.

## 2026-05-11 Round Entry (Audit Tests Must Not Masquerade As Implementation)
- Date: 2026-05-11
- Mistake or miss: A docs/tests-first optimizer policy audit could be misread as approval to merge lower-bound/SLSQP implementation.
- Root cause: Test names for future required behavior can sound like current implementation proof unless strict xfails and audit wording clearly separate policy debt from accepted code.
- Fix applied: Added optimizer-core policy docs, preserved no `strategies/optimizer.py` diff, and marked current infeasibility/fallback/active-bound behavior as strict xfail audit debt.
- Guardrail for next time: Future optimizer-core acceptance must replace strict xfails with passing implementation tests in the same branch and SAW; audit xfails alone are not implementation approval.
- Evidence paths: `docs/architecture/optimizer_core_policy_audit.md`, `docs/architecture/optimizer_constraints_policy.md`, `docs/architecture/optimizer_lower_bound_slsqp_policy.md`, `tests/test_optimizer_core_policy.py`, `docs/saw_reports/saw_optimizer_core_policy_audit_20260510.md`.

## 2026-05-11 Round Entry (Diagnostics Must Fail Closed On Non-Finite Weights)
- Date: 2026-05-11
- Mistake or miss: The first optimizer diagnostics implementation could sanitize NaN/inf weights to zero for residual math and still classify a diagnostic envelope as fully invested or optimized if the remaining finite weights summed to one.
- Root cause: Constraint diagnostics reused cleanup logic suitable for display math instead of preserving the original non-finite state as a hard diagnostic failure.
- Fix applied: Detect non-finite values before fill, mark bound/constraint diagnostics as error, force `constraints_satisfied = false`, prevent `result_is_optimized`, and add NaN/inf regression tests.
- Guardrail for next time: Any diagnostic layer that cleans numeric inputs for reporting must separately preserve pre-clean invalidity and fail closed before emitting success status.
- Evidence paths: `strategies/optimizer_diagnostics.py`, `tests/test_optimizer_core_policy.py`, `docs/saw_reports/saw_optimizer_core_structured_diagnostics_20260511.md`, `.venv\Scripts\python -m pytest tests\test_optimizer_core_policy.py -q`.

## 2026-05-11 Round Entry (View Refactors Need Real Streamlit Coverage)
- Date: 2026-05-11
- Mistake or miss: The optimizer view had helper-level refactor work while the render body could still drift back to stale control code and runtime-only errors.
- Root cause: Existing checks were mostly source-text assertions and did not instantiate the Streamlit widget tree for `/portfolio-and-allocation`.
- Fix applied: Added dedicated `streamlit.testing.v1.AppTest` coverage, reconciled the optimizer render body to the helper path, cached optimizer runs, and moved recent display overlays behind a display-only Parquet cache with atomic writes.
- Guardrail for next time: Any optimizer view refactor must include at least one AppTest render, one widget-control rerun, and one focused UI-to-solver handoff test before claiming the route is stable.
- Evidence paths: `views/optimizer_view.py`, `core/data_orchestrator.py`, `tests/test_optimizer_view.py`, `tests/test_optimizer_core_policy.py`, `.venv\Scripts\python -m pytest tests\test_optimizer_view.py tests\test_optimizer_core_policy.py tests\test_dash_2_portfolio_ytd.py -q`.

## 2026-05-11 Round Entry (Display Freshness Must Not Live In The View)
- Date: 2026-05-11
- Mistake or miss: The approved DASH-2 display freshness overlay left yfinance fetching, local TRI scaling/stitching, and backtest-result JSON parsing inside `views/optimizer_view.py`.
- Root cause: The first runtime slice prioritized preserving Portfolio & Allocation behavior and did not immediately complete the data/UI boundary cleanup.
- Fix applied: Moved selected-stock display overlay fetching, adjusted-close extraction, local TRI scaling/stitching, and strategy metrics parsing into `core/data_orchestrator.py`; updated the view and focused tests.
- Guardrail for next time: Any runtime display-refresh path may be triggered by UI, but provider calls, price stitching, and repository file reads must live behind data orchestration/provider boundaries.
- Evidence paths: `core/data_orchestrator.py`, `views/optimizer_view.py`, `tests/test_data_orchestrator_portfolio_runtime.py`, `tests/test_dash_2_portfolio_ytd.py`, `.venv\Scripts\python -m pytest -q`.

## 2026-05-11 Round Entry (Optimizer View Refactors Must Fail Closed)
- Date: 2026-05-11
- Mistake or miss: Optimizer UI code carried method-label strings, audit-object coercion, cash-row manipulation, and render layout in one large procedural function; first refactor also left stale session weights on failure exits.
- Root cause: Dashboard velocity left view orchestration, typed source contracts, display-table assembly, and downstream session-state handoff coupled in `render_optimizer_view`.
- Fix applied: Moved optimizer method labels into a strategy-layer enum/registry, typed the universe audit boundary to `OptimizerUniverseResult`, moved cash-row injection into `_build_allocation_table`, split renderer responsibilities into focused helpers, cleared optimizer session state on all invalid exits, and treated future-dated overlay cache mtimes as stale.
- Guardrail for next time: Optimizer view changes should keep method labels source-owned, accept the universe dataclass contract directly, keep render functions declarative, and clear downstream session outputs before every fail-closed return.
- Evidence paths: `strategies/optimizer.py`, `views/optimizer_view.py`, `core/data_orchestrator.py`, `tests/test_portfolio_universe.py`, `tests/test_data_orchestrator_portfolio_runtime.py`, `docs/saw_reports/saw_optimizer_view_code_quality_20260511.md`, `.venv\Scripts\python -m pytest -q`, Streamlit smoke at `http://127.0.0.1:8506/portfolio-and-allocation`.

## 2026-05-11 Round Entry (SAW Resource Blocks Need Explicit Rerun Closure)
- Date: 2026-05-11
- Mistake or miss: The optimizer view hardening implementation had passing tests and runtime smoke, but the first SAW report stayed BLOCK because independent subagents were unavailable.
- Root cause: Closure depended on subagent availability and the report correctly refused to infer independent review from local verification alone.
- Fix applied: Reran SAW with distinct Implementer and Reviewer A/B/C agents, reconciled PASS outputs, carried only Low runtime hygiene follow-ups, and updated the SAW report plus current truth surfaces.
- Guardrail for next time: When SAW is blocked by resource availability rather than defects, keep the report BLOCK, then rerun independent agents and update closure packets only after concrete PASS outputs exist.
- Evidence paths: `docs/saw_reports/saw_portfolio_optimizer_view_perf_hardening_20260511.md`, `docs/context/done_checklist_current.md`, `docs/context/bridge_contract_current.md`, SAW rerun agent outputs.

## 2026-05-11 Round Entry (Display Overlays Must Merge Cell-Wise)
- Date: 2026-05-11
- Mistake or miss: The first data-boundary refactor could let a partial live overlay overwrite an overlapping local price row with `NaN` for tickers missing from the live response.
- Root cause: The stitch step used row concatenation plus duplicate-date `keep=last`, which was fine for full live rows but unsafe for sparse live frames.
- Fix applied: Changed selected-price stitching to `scaled_live_overlay.combine_first(local_TRI_prices)`, deduped duplicate anchor dates before scaling, fail-softened background refresh submission, and locked stale-while-revalidate behavior with focused tests.
- Guardrail for next time: Any display overlay that is allowed to be sparse must merge cell-wise and must prove missing live cells preserve canonical local values.
## 2026-05-13 Round Entry (Selected Method Replay Needs One Source)
- Date: 2026-05-13
- Mistake or miss: The architecture note named one replay engine and one evidence artifact, but did not yet make the cross-surface invariant machine-checkable for YTD, latest allocation, Strategy Replay, annotations, decision logs, and saved evidence.
- Root cause: The handoff was framed as a future architecture direction instead of an enforceable selected-method source contract with explicit temporary-bridge limits and performance gates.
- Fix applied: Updated the phase brief, notes, decision log, done checklist, bridge, planner, impact, multi-stream, observability, and SAW report to require one selected-method replay run/source and to mark shared source/adapters/YTD/annotations/decision-log/evidence/performance as incomplete until implemented.
- Guardrail for next time: Any replay architecture milestone must name every downstream consumer of the selected-method source and include a failure rule for stale, partial, over-budget, or non-PIT replay dates before code work starts.
- Evidence paths: `docs/phase_brief/phase65-brief.md`, `docs/notes.md`, `docs/decision log.md`, `docs/context/done_checklist_current.md`, `docs/context/bridge_contract_current.md`, `docs/context/planner_packet_current.md`, `docs/context/impact_packet_current.md`, `docs/context/multi_stream_contract_current.md`, `docs/context/observability_pack_current.md`, `docs/saw_reports/saw_ultra_modular_replay_architecture_note_20260513.md`.

## 2026-05-13 Round Entry (PIT Replay Safety Must Reach Public Helpers And UI Consumers)
- Date: 2026-05-13
- Mistake or miss: The replay input artifact slice fixed the happy-path loader but still left audit risk around public cache signatures, caller-controlled cache roots, and dashboard replay consuming raw global price matrices.
- Root cause: PIT safety was treated as a loader concern rather than an end-to-end contract across signature generation, artifact write roots, and replay output consumers.
- Fix applied: Made `build_strategy_replay_cache_signature(...)` default to and require `r3000_pit`, confined repo-local artifacts to `data/runtime_cache/strategy_replay`, wired dashboard Strategy Replay through per-date `StrategyReplayInputs` before `build_strategy_replay(...)`, and preserved empty/failed replay dates as explicit cash-closed rows.
- Guardrail for next time: Every replay path must prove PIT-safe universe membership at the public helper boundary and at the UI/output consumer boundary; source guards should reject raw global `prices_wide` replay calls and dropped replay dates.
- Evidence paths: `core/data_orchestrator.py`, `dashboard.py`, `tests/test_data_orchestrator_portfolio_runtime.py`, `tests/test_strategy_replay_artifact.py`, `tests/test_optimizer_view.py`, `tests/test_position_lifecycle.py`, `tests/test_policy_target_timeline_apptest.py`, `.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py tests\test_strategy_replay_artifact.py tests\test_strategy_replay.py tests\test_optimizer_view.py tests\test_position_lifecycle.py tests\test_policy_target_timeline_apptest.py tests\test_dash_1_page_registry_shell.py tests\test_dash_2_portfolio_ytd.py tests\test_portfolio_universe.py tests\test_pinned_universe.py -q`.

- Evidence paths: `core/data_orchestrator.py`, `tests/test_data_orchestrator_portfolio_runtime.py`, `docs/saw_reports/saw_portfolio_data_boundary_refactor_20260511.md`, `.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py -q`.

## 2026-05-11 Round Entry (PID Probes Must Be Shared And Windows-Safe)
- Date: 2026-05-11
- Mistake or miss: Dashboard and phase16 optimizer lock code still had direct `os.kill(pid, 0)` liveness probes while updater/parameter-sweep had copied Windows-safe implementations.
- Root cause: Process-liveness safety lived in local helpers instead of one shared utility, so later runtime paths drifted back to unsafe platform behavior.
- Fix applied: Added `utils/process.py::pid_is_running`, routed dashboard/updater/parameter-sweep/release-controller/phase16 optimizer wrappers through it, and added `tests/test_process_utils.py`.
- Guardrail for next time: New PID or lock-owner liveness checks must call `utils.process.pid_is_running`; direct `os.kill(pid, 0)` is allowed only inside that utility's non-Windows branch.
- Evidence paths: `utils/process.py`, `dashboard.py`, `data/updater.py`, `scripts/parameter_sweep.py`, `scripts/release_controller.py`, `backtests/optimize_phase16_parameters.py`, `tests/test_process_utils.py`, `.venv\Scripts\python -m pytest tests\test_process_utils.py tests\test_parameter_sweep.py tests\test_updater_parallel.py tests\test_release_controller.py tests\test_optimize_phase16_parameters.py tests\test_dash_1_page_registry_shell.py tests\test_dash_2_portfolio_ytd.py tests\test_data_orchestrator_portfolio_runtime.py tests\test_optimizer_view.py -q`.

## 2026-05-11 Round Entry (Dashboard Rerun Caches Need Source Signatures)
- Date: 2026-05-11
- Mistake or miss: The dashboard loaded the full unified parquet package on every Streamlit rerun even though the source parquet files usually had not changed.
- Root cause: The expensive DuckDB/pivot/concat load lived in top-level dashboard code without a Streamlit cache boundary or source-file invalidation key.
- Fix applied: Added `core.data_orchestrator.build_unified_data_cache_signature`, wrapped the dashboard unified-data load with `st.cache_resource`, and keyed the cache by source parquet path/mtime/size signatures.
- Guardrail for next time: Heavy top-level Streamlit data loads must either be behind a cache with explicit source invalidation or be moved out of rerun scope before dashboard UX is considered acceptable.
- Evidence paths: `dashboard.py`, `core/data_orchestrator.py`, `tests/test_data_orchestrator_portfolio_runtime.py`, `tests/test_dashboard_sprint_a.py`, pre-fix `.venv` timing of `load_unified_data(...)` at `8.802s` and `8.393s`.

## 2026-05-11 Round Entry (Lifecycle Replay Must Drive Current Holds)
- Date: 2026-05-11
- Mistake or miss: Portfolio & Allocation could show 100% cash while Position Lifecycle Replay still had open ENTER positions.
- Root cause: Universe construction used today's scanner labels and optional JSON memory, but did not treat PIT lifecycle replay as the authoritative current-holding state.
- Fix applied: Added PIT-safe open-position reconstruction, preferred lifecycle replay over stale JSON memory, included open positions as `included_current_hold`, preserved residual cash across allocation/live-YTD weight mapping, and made lifecycle JSONL append/fail-closed behavior stricter.
- Guardrail for next time: Any current-portfolio display must first reconcile latest lifecycle ENTER/EXIT state before declaring sell-all cash, and every performance path must preserve residual cash unless weights exceed 100%.
- Evidence paths: `data/portfolio_lifecycle_log.py`, `strategies/portfolio_universe.py`, `views/optimizer_view.py`, `dashboard.py`, `tests/test_position_lifecycle.py`, `tests/test_portfolio_universe.py`, `tests/test_optimizer_view.py`, `.venv\Scripts\python -m pytest tests\test_position_lifecycle.py tests\test_portfolio_universe.py tests\test_optimizer_view.py tests\test_dash_2_portfolio_ytd.py -q`.


## 2026-05-12: Pinned Strategy Universe — Silent Exclusion Class

**Mistake**: Thesis tickers (MU, SNDK, WDC) were silently excluded from features and PIT replay because they fell outside the top-N liquidity selector. No error, no warning, no diagnostic — just missing data.

**Root cause**: The feature_store universe selector is liquidity-ranked. Tickers with low recent dollar volume (delisted periods, consolidation phases) drop out. The PIT replay used a hardcoded ticker list that didn't auto-include manifest additions. Error handlers used `except: pass` patterns that swallowed failures.

**Fix applied**:
1. Pinned universe manifest (`data/universe/pinned_thesis_universe.yml`) — explicit named tickers.
2. Feature store unions pinned permnos after liquidity selection; aborts on loader failure unless `allow_missing_pinned_universe=True`.
3. PIT replay defaults to `SCANNER_TICKERS ∪ pinned manifest`; raises on loader failure.
4. Loader validates strictly: rejects empty groups, blank tickers, duplicates, unresolved permnos.
5. Incremental no-op checks pinned coverage before returning "up to date".

## 2026-05-13 Round Entry (Do Not Rewrite Frozen History For UI Policy)
- Date: 2026-05-13
- Mistake or miss: The first patch plan suggested regenerating the frozen Rule100 history artifact with the 35% UI cap, which would blur audit-baseline semantics with live UI policy.
- Root cause: I treated the cap/budget mismatch as a global sizing default problem instead of separating audit history defaults from dynamic UI/replay controls.
- Fix applied: Added `rule100_config_from_max_weight(max_weight)` and used it only in direct Rule100 UI allocation and Strategy Replay; left `Rule100SoftmaxConfig()` and `rule100_softmax_v1_history.csv` frozen unless a future labeled artifact is approved.
- Guardrail for next time: Any artifact with `history`, `audit`, or `comparison` in the name must preserve its existing policy defaults unless the patch explicitly creates a new versioned/labeled artifact and updates downstream labels.
- Evidence paths: `strategies/rule100_softmax.py`, `views/optimizer_view.py`, `strategies/strategy_replay.py`, `tests/test_rule100_softmax.py`, `tests/test_optimizer_view.py`, `.venv\Scripts\python -m pytest tests\test_rule100_softmax.py tests\test_strategy_replay.py tests\test_optimizer_view.py tests\test_dash_2_portfolio_ytd.py -q`.

## 2026-05-13 Round Entry (Benchmark Freshness Is Per Column)
- Date: 2026-05-13
- Mistake or miss: QQQ could be forward-filled flat through 2026-05-11 because benchmark fallback treated local SPY/QQQ data as one freshness unit.
- Root cause: `_build_benchmark_equity(...)` accepted the local benchmark frame if any local data existed, then forward-filled each column without checking that every ticker was current to the same local cutoff.
- Fix applied: Added `build_benchmark_equity_from_prices(...)` with per-ticker stale detection, stale-only live overlay, `local+live_overlay` source labeling, and a no-forward-fill guard for stale columns that cannot be refreshed.
- Guardrail for next time: Wide benchmark or comparison frames must compute freshness per column before any `ffill`; frame-level latest dates are insufficient when constituent histories can diverge.
- Evidence paths: `core/data_orchestrator.py`, `dashboard.py`, `tests/test_dash_2_portfolio_ytd.py`, `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py -q`.

## 2026-05-14 Round Entry (Freshness Is Per Asset, Not Per Matrix)
- Date: 2026-05-14
- Mistake or miss: Portfolio & Allocation could still treat stale ragged price columns as current because some paths used a shared matrix/benchmark max date, forward-filled stale weighted legs, or counted history rows without endpoint freshness.
- Root cause: Freshness metadata was not carried per asset through benchmark YTD, portfolio YTD, selected-price overlay prep, default optimizer ordering, and universe eligibility.
- Fix applied: Added per-column endpoint helpers, dropped or failed closed stale columns at benchmark/portfolio/optimizer boundaries, demoted stale default-order assets, and excluded stale universe assets even with sufficient history observations.
- Guardrail for next time: Any display or allocation surface that consumes a wide price matrix must prove each nonzero weighted/selected asset reaches the required endpoint; shared max dates are captions only, never asset freshness proof.
- Evidence paths: `core/data_orchestrator.py`, `dashboard.py`, `views/optimizer_view.py`, `strategies/portfolio_universe.py`, `tests/test_data_orchestrator_portfolio_runtime.py`, `tests/test_dash_2_portfolio_ytd.py`, `tests/test_optimizer_view.py`, `tests/test_portfolio_universe.py`, `.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_portfolio_universe.py -q`.

**Guardrail for next time**:
- Any universe selector that can silently exclude named strategy tickers must have a pinned override lane.
- `except: pass` on universe/manifest loaders is forbidden — use fail-closed with explicit override.
- Test the default fail-closed path, not just the override path.
- When adding a new ticker to the strategy, verify it appears in both features AND replay output before closing.

**Evidence**: `tests/test_pinned_universe.py` (27 tests), `tests/test_feature_store.py` (34 tests), PIT replay diagnostics showing all 10 pinned tickers accounted for.

## 2026-05-12 Round Entry (Lifecycle Replay Needs State, Not Raw Flips)
- Date: 2026-05-12
- Mistake or miss: Position Lifecycle Replay was too eager: raw PIT gate flips created frequent trading, and ENTER weights were stuck at 4% because sizing was derived from the full replay universe length.
- Root cause: Replay treated universe breadth as portfolio capacity and used one-day entry/exit predicates without entry confirmation, minimum holding period, exit confirmation, or cooldown state.
- Fix applied: Added 10% max-10 sizing, 3-of-4 PIT lifecycle factor confirmation, 3-day entry confirmation, 20-day minimum hold, 2-day exit confirmation, 20% hard-exit override, and 10-day re-entry cooldown.
- Guardrail for next time: Any lifecycle replay change must prove event count, ENTER weights, current open holds, and short-hold churn before publishing a runtime log.
- Evidence paths: `scripts/pit_lifecycle_replay.py`, `tests/test_pinned_universe.py`, `data/portfolio_lifecycle_log.jsonl`, `docs/context/e2e_evidence/optimal_lifecycle_replay_tmp.jsonl`, `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py tests\test_pinned_universe.py tests\test_position_lifecycle.py tests\test_portfolio_universe.py tests\test_optimizer_view.py -q`.

## 2026-05-13 Round Entry (Replay Output Must Carry Its Own Evidence Context)
- Date: 2026-05-13
- Mistake or miss: Strategy Replay had target-weight rows, but event annotations, buy/sell decisions, and performance derivation could still be pulled from separate dashboard-local paths.
- Root cause: The first replay helper stopped at weights plus cash and did not expose a typed backend bundle for context or per-date return/equity evidence.
- Fix applied: Added `build_selected_method_replay(...)` and typed replay context objects, kept `build_strategy_replay(...)` as the shared frame source, attached PIT-filtered event/decision frames, and added asset/portfolio return columns to the replay frame.
- Guardrail for next time: Any selected-method replay API must prove Rule100 and non-Rule100 methods share one schema, include CASH rows, attach explicit empty or PIT-filtered context, and derive YTD/performance without optimizer session weights.
- Evidence paths: `strategies/strategy_replay.py`, `tests/test_strategy_replay.py`, `.venv\Scripts\python -m pytest tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py -q`, `.venv\Scripts\python -m pytest tests\test_replay_non_cash_closed.py -q`.

## 2026-05-14 Round Entry (Bootstrap Packets Must Preserve Baseline Anchors)
- Date: 2026-05-14
- Mistake or miss: Fixing stale bootstrap selection initially replaced the older Rule100/YTD context packet with replay-audit truth but dropped the closed `R64.1` baseline token used by context hygiene tests.
- Root cause: The packet refresh focused on latest-round correctness and did not preserve legacy anti-regression anchors that still prove provenance/dependency hygiene is not being forgotten.
- Fix applied: Added current-truth packet selection in `scripts/build_context_packet.py`, added drift/heading regressions, rebuilt `docs/context/current_context.*`, and preserved the D-353/R64.1 baseline sentence in the replay-audit New Context Packet.
- Guardrail for next time: When a current context packet supersedes an older handover, include both the latest round truth and any closed baseline tokens that existing hygiene tests intentionally assert.
- Evidence paths: `scripts/build_context_packet.py`, `tests/test_build_context_packet.py`, `docs/context/planner_packet_current.md`, `docs/context/current_context.md`, `.venv\Scripts\python -m pytest tests\test_build_context_packet.py tests\test_phase61_context_hygiene.py -q`.

## 2026-05-15 Round Entry (Optimize Replay Prices, Not PIT Proof)
- Date: 2026-05-15
- Mistake or miss: Replay performance work could accidentally become watchlist-only replay if selected-asset filtering happens before PIT membership proof or if MU/SNDK diagnosis is folded into the hot path.
- Root cause: Full membership proof and selected price loading both use the word "universe", but only the price matrix needs shrinking for the dashboard replay hot path.
- Fix applied: Kept full-window `r3000_pit` membership index construction intact, limited batched price/return loading to selected permnos after membership proof, added a separate `trace_thesis_ticker_eligibility(...)` diagnostic for MU/SNDK gates, and reconciled the review finding so non-finite `total_ret` rows cannot count as local price/return evidence.
- Guardrail for next time: Performance slices may reduce loaded data only after PIT proof is already materialized; named-ticker disappearance investigations must report gate truth separately from replay asset selection and reject non-finite price/return evidence.
- Evidence paths: `core/data_orchestrator.py`, `dashboard.py`, `scripts/pit_lifecycle_replay.py`, `tests/test_data_orchestrator_portfolio_runtime.py`, `tests/test_optimizer_view.py`, `tests/test_pinned_universe.py`, `docs/context/e2e_evidence/replay_selected_price_loading_mu_sndk_trace_20260515.json`.

## 2026-05-14 Round Entry (Saved Replay Artifacts Need UI Signatures Too)
- Date: 2026-05-14
- Mistake or miss: It would be easy for Portfolio & Allocation to accept a backend-valid saved replay artifact that does not prove the current dashboard method/cap/assets/date/data context.
- Root cause: Backend artifact freshness and dashboard render freshness overlap but are not identical; the UI also needs the selected assets, replay dates, sampling, and loaded dashboard data signature.
- Fix applied: Added a pure `DashboardReplayRequest`, required exact `dashboard_cache_signature` for saved-artifact UI consumption, used backend `read_selected_method_replay_artifact(...)`, and added executable tests for valid saved-artifact consumption plus stale-artifact session clearing.
- Guardrail for next time: A saved replay artifact must pass both backend bundle validation and dashboard cache-signature validation before it can feed YTD/latest snapshot/events/decisions.
- Evidence paths: `dashboard.py`, `tests/test_dash_2_portfolio_ytd.py`, `tests/test_optimizer_view.py`, `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_position_lifecycle.py tests\test_policy_target_timeline_apptest.py -q`.

## 2026-05-14 Round Entry (Manifest Identity Must Be Semantic)
- Date: 2026-05-14
- Mistake or miss: Saved replay manifest validation checked that `run_id`, `source_id`, and `method_id` existed, but did not reject blank strings when the caller omitted expected run/source ids.
- Root cause: Identity validation relied on presence and parquet/manifest equality, so matching blank manifest and parquet values could pass before any caller-supplied identity check applied.
- Fix applied: Added non-empty trimmed string validation for manifest identity, added regressions where manifest and parquet identities are blank and expected ids are omitted, and published the backend SAW report artifact.
- Guardrail for next time: Durable artifact identity fields need semantic non-empty validation at the manifest boundary before equality checks or optional caller assertions.
- Evidence paths: `strategies/strategy_replay.py`, `tests/test_strategy_replay_artifact.py`, `docs/saw_reports/saw_backend_replay_reader_identity_hardening_20260514.md`, `.venv\Scripts\python -m pytest tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py tests\test_strategy_replay_coverage.py -q --durations=12`.

## 2026-05-12 Round Entry (Do Not Name Returns Prices)
- Date: 2026-05-12
- Mistake or miss: Portfolio Performance displayed `+7645112.18%` because daily returns were passed through the `prices` slot and then compounded with `pct_change`.
- Root cause: `core.data_orchestrator._load_historical_data()` unpacked `load_dashboard_data()` outputs in the wrong order: returns were assigned to `prices_wide`, and TRI levels were assigned to `returns_wide`.
- Fix applied: Corrected the unpacking order, added a regression test that `UnifiedDataPackage.prices` holds price levels and `.returns` holds returns, and made Portfolio/benchmark YTD prefer local TRI history before live yfinance fallback.
- Guardrail for next time: Any data package boundary must assert semantic ranges, not only shapes; price-like matrices should be positive levels, while return-like matrices should be small signed values.
- Evidence paths: `core/data_orchestrator.py`, `dashboard.py`, `tests/test_data_orchestrator_portfolio_runtime.py`, `tests/test_dash_2_portfolio_ytd.py`, `docs/context/e2e_evidence/portfolio_ytd_return_fix_8509_smoke.json`.

## 2026-05-14 Round Entry (Truth Surfaces Must Follow Verified Code)
- Date: 2026-05-14
- Mistake or miss: Current truth surfaces still claimed dashboard backend-bundle consumption was open even though `dashboard.py::_build_dashboard_strategy_replay_context(...)` already called `build_selected_method_replay(...)` with a PIT input loader.
- Root cause: The earlier Evidence/Docs handoff did not re-audit the source-guard tests and dashboard context function after follow-on implementation landed, so stale open-risk language survived.
- Fix applied: Verified the dashboard backend-bundle path, full pytest, and Streamlit readiness smoke, then refreshed planner, bridge, impact, done checklist, alignment, observability, notes, decision log, PRD/spec surfaces, and SAW report.
- Guardrail for next time: Before carrying an integration blocker forward, inspect the named function and the current source-guard tests; only keep the blocker if executable evidence still supports it.
- Evidence paths: `dashboard.py`, `tests/test_optimizer_view.py`, `tests/test_dash_2_portfolio_ytd.py`, `docs/context/e2e_evidence/backend_bundle_integration_streamlit_8520_status.json`, `.venv\Scripts\python -m pytest -q`.

## 2026-05-14 Round Entry (Freshness Tolerance Must Have One Owner)
- Date: 2026-05-14
- Mistake or miss: Endpoint freshness semantics were split between `core.data_orchestrator` and `strategies.portfolio_universe`, so strict display freshness and universe policy tolerance could drift apart.
- Root cause: The first stale-data fix moved endpoint checks into several call sites but left universe eligibility with private endpoint/tolerance helpers instead of consuming the core contract.
- Fix applied: Added shared `price_column_latest_date(...)` and `price_endpoint_is_fresh(..., max_staleness_days=0)` helpers in `core.data_orchestrator`, rewired `portfolio_universe` to import them, and added strict-vs-tolerant plus source-guard regressions.
- Guardrail for next time: When a freshness or PIT predicate differs only by caller policy, centralize the predicate and make the policy argument explicit; add a source guard if duplicate helpers caused the bug class.
- Evidence paths: `core/data_orchestrator.py`, `strategies/portfolio_universe.py`, `tests/test_data_orchestrator_portfolio_runtime.py`, `tests/test_portfolio_universe.py`, `.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_portfolio_universe.py -q`.

## 2026-05-14 Round Entry (Freshness Correctness Needs One Shared Endpoint Snapshot)
- Date: 2026-05-14
- Mistake or miss: The initial stale-data fail-closed fix preserved correctness but allowed dashboard YTD, optimizer prep/order, and universe eligibility to rescan the full price matrix independently on render paths.
- Root cause: Per-asset endpoint freshness was added as helper calls, not as a reusable loaded-matrix artifact tied to the dashboard data signature.
- Fix applied: Added `PriceEndpointFreshness`, cached one snapshot for the loaded `prices_wide` package, threaded it through dashboard YTD, optimizer rendering, and universe construction, and added reuse regressions.
- Guardrail for next time: Any freshness consumer added after a matrix load must accept the shared endpoint snapshot or build exactly one local snapshot at its boundary.
- Evidence paths: `core/data_orchestrator.py`, `dashboard.py`, `views/optimizer_view.py`, `strategies/portfolio_universe.py`, `tests/test_data_orchestrator_portfolio_runtime.py`, `tests/test_optimizer_view.py`, `tests/test_portfolio_universe.py`, `.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py tests\test_optimizer_view.py tests\test_portfolio_universe.py tests\test_dash_2_portfolio_ytd.py -q`.

## 2026-05-12 Round Entry (Decision Exports Must Match Replay Semantics)
- Date: 2026-05-12
- Mistake or miss: The first full lifecycle decision export falsely produced extra AMZN/MSFT/VRT buys because missing `dist_sma20` values were coerced to `0.0`.
- Root cause: The export path used a cleaner numeric coercion helper than the replay gate, accidentally changing NaN semantics; the replay treats NaN technical-entry distance as ineligible.
- Fix applied: Preserved NaN in gate inputs, added `technical_entry_zone_missing` reasons, regenerated the export, and added a regression that exported BUY/SELL rows exactly match `run_pit_replay(...)` ENTER/EXIT events.
- Guardrail for next time: Audit/export paths must be tested against the authoritative replay event sequence, not only against schema shape or row existence.
- Evidence paths: `scripts/pit_lifecycle_replay.py`, `tests/test_pinned_universe.py`, `data/portfolio_lifecycle_decision_log.jsonl`, `data/portfolio_lifecycle_buy_sell_log.jsonl`, `docs/context/e2e_evidence/lifecycle_decision_audit_20260512.json`.

## 2026-05-14 Round Entry (Sampled Views Are Not Replay Sources)
- Date: 2026-05-14
- Mistake or miss: The first Portfolio single-source plan allowed weekly sampled replay requests and legacy optimizer fallback to remain close enough to the replay-facing performance path that the page could still look coherent while mixing sources.
- Root cause: I treated sampling and fallback as performance optimizations instead of source-identity changes on a page whose product contract is one daily forward-walk replay source.
- Fix applied: Built one daily `DashboardReplayContext` before replay-facing surfaces render, made Portfolio Performance refuse non-daily replay and optimizer fallback, converted weekly timeline sampling into a display transform over daily rows, replaced the top allocation display with the latest daily replay snapshot, and derived latest buys/sells from `bundle.decision_rows`.
- Guardrail for next time: Any replay-facing Portfolio surface must accept the daily replay context explicitly; sampled views, latest-trade summaries, and allocation snapshots are views of that context, not loaders or fallback sources.
- Evidence paths: `dashboard.py`, `views/optimizer_view.py`, `tests/test_dash_2_portfolio_ytd.py`, `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_policy_target_timeline_apptest.py tests\test_position_lifecycle.py tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py -q`.

## 2026-05-15 Round Entry (Replay Selection Must Be Explicit)
- Date: 2026-05-15
- Mistake or miss: Portfolio replay identity still depended on hidden `optimizer_universe` session state and could fall back to the first 10 price columns.
- Root cause: Controls-only optimizer rendering wrote a side-effect key that dashboard replay treated as source truth, so skipped/error/stale controls could leave a plausible but wrong replay universe.
- Fix applied: Added signed `PortfolioReplaySelection`, made dashboard validate it before replay request construction, bound typed asset identities plus selected price content, removed first-10 fallback, and cleared selection/replay/allocation caches on optimizer builder errors.
- Guardrail for next time: Any replay-facing universe handoff must be an explicit signed state object or bundle field with typed asset identity and source/content binding; hidden widget/session mirrors are compatibility only and must fail closed when absent or stale.
- Evidence paths: `views/optimizer_view.py`, `dashboard.py`, `tests/test_optimizer_view.py`, `tests/test_dash_2_portfolio_ytd.py`.

## 2026-05-15 Round Entry (Replay Rows Need Durable Roles)
- Date: 2026-05-15
- Mistake or miss: Portfolio replay tables could still rely on generic `Weight` labels and `status=context_only` instead of a durable schema distinction between lifecycle audit intent and replay exposure truth.
- Root cause: Role semantics were spread across UI labels, `target_weight`, `audit_weight`, and `status`, while dashboard kept a private context normalizer that could drift from `strategies.strategy_replay`.
- Fix applied: Added `context_role` and `row_role` to replay/context/artifact schemas, hydrated defaults for legacy selected-method artifacts, delegated dashboard context normalization to `normalize_context_frame_for_replay(...)`, renamed visible replay/latest weights, and added diagnostics from `DashboardReplayContext`.
- Guardrail for next time: Replay-facing rows must carry machine-checkable role fields at the schema boundary; UI copy is not an adequate semantic contract, and diagnostics must bind to the same replay identity rendered on the page.
- Evidence paths: `strategies/strategy_replay.py`, `dashboard.py`, `tests/test_strategy_replay.py`, `tests/test_strategy_replay_artifact.py`, `tests/test_dash_2_portfolio_ytd.py`.

## 2026-05-15 Round Entry (Pandas Series Needs `.dt` For Replay Date Normalization)
- Date: 2026-05-15
- Mistake or miss: Max-window Strategy Replay timeline sampling grouped dates into a pandas `Series` and then called `.normalize()` directly, crashing the Portfolio page for long replay windows.
- Root cause: The sampler was written like it still had a `DatetimeIndex`; after `to_series().groupby(...).last()` the object was a `Series`, where datetime operations must go through `.dt`.
- Fix applied: Normalized grouped weekly keep-dates with `pd.to_datetime(...).dropna().dt.normalize()` and added a max-window regression with more than 160 business dates.
- Guardrail for next time: Any replay display sampler that changes pandas container type must have an executable long-window test, not only source-guard assertions.
- Evidence paths: `dashboard.py`, `tests/test_dash_2_portfolio_ytd.py`, `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py -q`.

## 2026-05-15 Round Entry (Horizon Cache Must Allow Proven Supersets)
- Date: 2026-05-15
- Mistake or miss: Switching from a wider replay horizon to a shorter one still rebuilt daily replay even when the wider in-session daily replay already covered the shorter window.
- Root cause: Replay cache validation bound exact `replay_dates`, and the page-level `_ensure_daily_portfolio_replay_context(...)` entered the build path before consulting reusable cached context.
- Fix applied: Added in-session superset reuse that ignores only `replay_dates` after method/cap/controls/signed assets/sampling/data signature match, verifies actual replay row coverage, and returns a horizon-scoped context before the spinner/build path.
- Guardrail for next time: Time-window cache keys should distinguish durable artifact identity from in-session superset reuse; never reuse a wider replay unless actual row coverage is proven and the returned context is scoped to the selected horizon.
- Evidence paths: `dashboard.py`, `tests/test_dash_2_portfolio_ytd.py`, `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py -q`.

## 2026-05-14 Round Entry (Scaled Live Overlays Need Anchors)
- Date: 2026-05-14
- Mistake or miss: The stale-data fail-closed fix still left a scaled live-overlay bridge that could connect a stale local endpoint to fresh live rows without any same-asset overlap date.
- Root cause: Overlay scaling treated first-live-to-last-local scaling as a display convenience, but selected-price and benchmark paths could use that stitched series as current evidence.
- Fix applied: Made `scale_live_overlay_to_local(...)` require same-column local/live overlap, made benchmark live overlays use the same anchor invariant, and added no-overlap regressions for selected assets and benchmark YTD.
- Guardrail for next time: Any scaled overlay that can feed allocation, YTD, optimizer, or benchmark evidence must prove a same-ticker overlap anchor; no overlap means unavailable/dropped, not synthetic continuity.
- Evidence paths: `core/data_orchestrator.py`, `tests/test_data_orchestrator_portfolio_runtime.py`, `tests/test_dash_2_portfolio_ytd.py`, `.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_portfolio_universe.py -q`.

## 2026-05-12 Round Entry (Do Not Abstract Before The Strategy Exists)
- Date: 2026-05-12
- Mistake or miss: The first planning answer suggested a generic replay/audit contract before the concrete Rule100 lifecycle policy was implemented.
- Root cause: Framework thinking was applied with only one strategy and before the actual lifecycle transitions, sizing, and trim/tighten semantics existed.
- Fix applied: Implemented the concrete Rule100 Lifecycle Policy v0 directly in `scripts/pit_lifecycle_replay.py`, kept TRIM/TIGHTEN audit-only, and produced a delta against the 33-event baseline.
- Guardrail for next time: Extract common strategy contracts only after at least two concrete strategies expose real shared shape; otherwise finish the strategy layer first.
- Evidence paths: `scripts/pit_lifecycle_replay.py`, `tests/test_pinned_universe.py`, `data/portfolio_lifecycle_log.jsonl`, `docs/context/e2e_evidence/rule100_v0_lifecycle_replay_tmp.jsonl`, `docs/context/e2e_evidence/lifecycle_decision_audit_20260512.json`.

## 2026-05-12 Round Entry (Method Labels Must Declare Their Execution Path)
- Date: 2026-05-12
- Mistake or miss: The Rule100 lifecycle policy existed, but the Portfolio Optimizer `Method` dropdown did not expose it under the user's intended `Rule of 100` label.
- Root cause: The lifecycle current-hold path was implemented as a fallback branch, not as a named method in the optimizer registry.
- Fix applied: Added `OptimizationMethod.RULE_OF_100 = "Rule of 100"` and routed that method directly to lifecycle holdings plus residual cash before optimizer execution.
- Guardrail for next time: A method label must map to one explicit execution path and declare whether it runs optimizer math, lifecycle replay state, or cash-only fallback.
- Evidence paths: `strategies/optimizer.py`, `views/optimizer_view.py`, `tests/test_optimizer_view.py`, `tests/test_portfolio_universe.py`, `.venv\Scripts\python -m pytest tests\test_optimizer_view.py tests\test_portfolio_universe.py -q`.

## 2026-05-12 Round Entry (Streamlit Page API Must Be Verified Before Using Extra Keywords)
- Date: 2026-05-12
- Mistake or miss: The first navigation patch used `st.Page(..., visibility="hidden")`, which is not supported in the Streamlit build in this workspace.
- Root cause: I assumed a newer page API than the installed runtime actually provides, so the route smoke failed with a `TypeError` before the app could render.
- Fix applied: Switched to the supported `st.Page(..., title=..., url_path=..., default=...)` contract and kept `Portfolio & Allocation` as the visible default page.
- Guardrail for next time: Before using navigation/page keywords, confirm the exact `st.Page` signature in the active environment and prefer the narrow supported contract.
- Evidence paths: `views/page_registry.py`, `tests/test_dash_1_page_registry_shell.py`, `dashboard.py`, `AppTest.from_file("dashboard.py")` route smoke.

## 2026-05-12 Round Entry (v1.1 Artifacts Must Match Their Contract)
- Date: 2026-05-12
- Mistake or miss: Rule100 softmax v1.1 looked current but kept a stale `rule100_softmax_v1_1_history.csv`, inflated factor coverage by counting alternate columns, and tested Policy Target Timeline through copied mini-apps.
- Root cause: The v1.1 contract changed to comparison/summary-only, but artifact cleanup and tests did not enforce the new boundary; factor coverage reused flattened column logic instead of group semantics.
- Fix applied: Retired the stale v1.1 history artifact, counted one value per approved factor group, added neutral missing-factor shrinkage toward `0.50`, and replaced copied AppTests with `AppTest.from_file("dashboard.py")` route coverage.
- Guardrail for next time: Every research artifact contract change must include an active-artifact source guard, stale-artifact cleanup, group-vs-column coverage tests, and one real app render test for dashboard-facing evidence.
- Evidence paths: `strategies/rule100_softmax_v1_1.py`, `scripts/rule100_softmax_v1_1_audit.py`, `tests/test_rule100_softmax_v1_1.py`, `tests/test_policy_target_timeline_apptest.py`, `data/processed/rule100_softmax_v1_1_summary.json`, `.venv\Scripts\python -m pytest tests\test_rule100_softmax_v1_1.py tests\test_policy_target_timeline_apptest.py tests\test_rule100_softmax.py tests\test_position_lifecycle.py tests\test_dash_1_page_registry_shell.py -q`.

## 2026-05-12 Round Entry (Rows Are Not The Whole PIT Boundary)
- Date: 2026-05-12
- Mistake or miss: The first replay artifact loader clamped rows to `as_of_date` but defaulted to the full-history `top_liquid` universe selector, which could leak future membership through columns.
- Root cause: I treated date slicing as sufficient PIT safety and did not account for the upstream universe-selection query semantics.
- Fix applied: Strategy replay inputs now default to and require `universe_mode="r3000_pit"`, the CLI uses the same default, and tests reject non-PIT universe mode.
- Guardrail for next time: Every replay input must validate both row-date availability and asset-universe availability as of the replay date.
- Evidence paths: `core/data_orchestrator.py`, `scripts/build_strategy_replay_artifact.py`, `tests/test_data_orchestrator_portfolio_runtime.py`, `tests/test_strategy_replay_artifact.py`, `.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py tests\test_strategy_replay_artifact.py -q`.

## 2026-05-12 Round Entry (Method Replay Must Fail Closed Per Date)
- Date: 2026-05-12
- Mistake or miss: Method-aware replay could accidentally be implemented as a carry-forward allocator, reusing a prior day's weights or optimizer fallback weights when one date failed.
- Root cause: Optimizer outputs and replay outputs share the same weight shape, so stale/fallback vectors look valid unless diagnostics and per-date status are checked explicitly.
- Fix applied: Added `strategies/strategy_replay.py::build_strategy_replay(...)` with PIT `<= as_of` price slicing, explicit CASH rows, per-date `cash_closed` status on optimizer fallback/failure, and Rule100 replay cap separation from the frozen audit default.
- Guardrail for next time: Any forward-walk allocation replay must test both PIT slice inputs and a two-day success-then-failure case proving failed days emit cash instead of stale or fallback weights.
- Evidence paths: `strategies/strategy_replay.py`, `tests/test_strategy_replay.py`, `.venv\Scripts\python -m pytest tests\test_strategy_replay.py tests\test_optimizer_core_policy.py -q`.

## 2026-05-13 Round Entry (Architecture Notes Must Separate Patch From Milestone)
- Date: 2026-05-13
- Mistake or miss: A focused visible UI/YTD patch can be overread as authorization to start a broad replay architecture rewrite.
- Root cause: Rule100, Strategy Replay, and YTD evidence share vocabulary with the future AI auto-research loop, so packet language can blur current patch scope and next milestone scope.
- Fix applied: Added a concise milestone note that separates QQQ/default-method visible fixes from the urgent ultra-modular replay architecture and locks the target contracts and guardrails.
- Guardrail for next time: Any architecture handoff after a tactical UI/data patch must explicitly name current scope, next milestone scope, non-goals, and acceptance tests before implementation starts.
- Evidence paths: `docs/phase_brief/phase65-brief.md`, `docs/context/bridge_contract_current.md`, `docs/context/planner_packet_current.md`, `docs/context/done_checklist_current.md`, `docs/context/impact_packet_current.md`.

## 2026-05-13 Round Entry (Audit UI Must Not Sit Behind Heavy Replay)
- Date: 2026-05-13
- Mistake or miss: The Buy/Sell Decision Log existed and was wired, but it rendered after the expensive forward-walk replay loop, so the user could still perceive it as missing while replay warmed.
- Root cause: The audit tape was placed at the end of `_render_strategy_replay_section()` with ENTER/EXIT annotations, coupling a cheap audit surface to the slowest replay computation.
- Fix applied: Moved `_render_buy_sell_decision_log()` directly under the Strategy Replay caption so it appears before PIT replay dates are loaded and target weights are built.
- Guardrail for next time: Cheap audit/context surfaces should render before expensive replay or data-refresh loops, especially when they are acceptance evidence for visible UI behavior.
- Evidence paths: `dashboard.py`, `docs/notes.md`, `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_portfolio_universe.py tests\test_policy_target_timeline_apptest.py tests\test_position_lifecycle.py -q`, browser DOM audit on `http://localhost:8509/`.

## 2026-05-13 Round Entry (Replay Surfaces Need One Bundle)
- Date: 2026-05-13
- Mistake or miss: Dashboard Strategy Replay rendered one replay output while latest allocation/YTD, ENTER/EXIT annotations, and Buy/Sell audit rows still came from separate dashboard reads.
- Root cause: The UI had grown surface-by-surface around `portfolio_allocation_state`, `read_lifecycle_log()`, and a direct compact JSONL read instead of one selected-method replay context.
- Fix applied: Added `DashboardReplayContext`, moved annotation/audit reads behind cached context loaders, made the render path consume context fields, and primed latest selected-method replay weights before Portfolio YTD.
- Guardrail for next time: Any new replay-facing dashboard surface must accept a replay context/bundle argument or explicitly label and test itself as a transitional fallback.
- Evidence paths: `dashboard.py`, `tests/test_dash_2_portfolio_ytd.py`, `tests/test_policy_target_timeline_apptest.py`, `tests/test_position_lifecycle.py`, `tests/test_optimizer_view.py`, `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py tests\test_policy_target_timeline_apptest.py tests\test_position_lifecycle.py tests\test_optimizer_view.py -q`.

## 2026-05-15 Round Entry (History Fail Is Not Endpoint Staleness)
- Date: 2026-05-15
- Mistake or miss: The optimizer UI mixed true missing local price history and stale local endpoints under one `History Fail` label, making GOOGL-style stale endpoint rows look like short-history rows.
- Root cause: The backend fail-closed bucket was correct but the visible diagnostic label collapsed multiple price-readiness failure modes.
- Fix applied: Split visible diagnostics into `Missing History` and `Stale Endpoint`, added `Latest Price Date` to the Universe Audit table, and added focused unit/AppTest regressions.
- Guardrail for next time: Any fail-closed data-readiness bucket that contains more than one operational cause must expose separate visible sub-buckets before users audit data repairs.
- Evidence paths: `strategies/portfolio_universe.py`, `views/optimizer_view.py`, `tests/test_portfolio_universe.py`, `tests/test_optimizer_view.py`, `.venv\Scripts\python -m pytest tests\test_portfolio_universe.py tests\test_optimizer_view.py -q`.

## 2026-05-26 Round Entry (Expert Packets Need Explicit GitHub vs Local Truth)
- Date: 2026-05-26
- Mistake or miss: A curated expert packet could be read as the clean GitHub state even though it intentionally includes local uncommitted truth surfaces and selected dirty-worktree context.
- Root cause: The repo's current planning truth is richer than the pushed commit, so packet portability creates a second interpretation risk unless GitHub alignment and dirty-worktree caveats are first-class packet fields.
- Fix applied: Added GitHub repo/branch/commit links, local HEAD/remote alignment notes, dirty-worktree snapshot, file manifest, and explicit "not a pure GitHub snapshot" caveats to the Data Engineering / Market-Data Integrity packet.
- Guardrail for next time: Every expert packet must include `GITHUB_ALIGNMENT.txt`, `GIT_STATUS_SHORT.txt`, a packet file manifest, and a question-packet caveat separating committed baseline from local review truth.
- Evidence paths: `docs/context/e2e_evidence/data_engineering_market_integrity_packet_20260526/PACKET_INDEX.md`, `docs/context/e2e_evidence/data_engineering_market_integrity_packet_20260526/DATA_ENGINEERING_QUESTIONS.md`, `docs/context/e2e_evidence/data_engineering_market_integrity_packet_20260526.zip`, `docs/saw_reports/saw_data_engineering_market_integrity_packet_20260526.md`.

## 2026-05-26 Round Entry (Boot-Status Snapback Means BLOCK, Not More Patching)
- Date: 2026-05-26
- Mistake or miss: The Data Readiness Gate recovery kept attempting to patch the canonical boot-status path while active root files and tests repeatedly snapped back to the rejected `runtime/boot_status_current.json` contract.
- Root cause: Multiple boot-status control-plane streams and stale tests were still asserting runtime-path semantics in the shared dirty workspace, so a local patch could pass an immediate read and then fail the next import/test window.
- Fix applied: Stopped the implementation loop, closed reviewer subagents, published a SAW BLOCK recovery report, and preserved the failed path sentinel plus focused pytest evidence.
- Guardrail for next time: If a canonical path, write guard, or default output flips during verification, stop source edits immediately; freeze competing streams first, then run a single path-lock slice with pre-suite and post-suite sentinels.
- Evidence paths: `core/boot_status.py`, `scripts/boot_preflight.py`, `tests/test_boot_status_contract.py`, `tests/test_boot_preflight.py`, `tests/test_data_readiness_gate_write_guard.py`, `docs/saw_reports/saw_data_readiness_gate_v0_recovery_20260526.md`.

## 2026-05-26 Round Entry (Governance Packets Must Separate Labels From Actions)
- Date: 2026-05-26
- Mistake or miss: Governance/risk review can become too generic if the packet only asks about compliance broadly instead of exposing the exact repo terms that may read as advice.
- Root cause: Terminal Zero uses research, replay, optimizer, and lifecycle vocabulary where labels such as BUY/SELL/ENTER/EXIT/WATCH/allocation can be audit semantics in code but action-shaped language to a reviewer or user.
- Fix applied: Created a dedicated Governance / Risk packet with GitHub alignment, local dirty-worktree caveat, label/action boundary questions, UI-language questions, alert/broker boundary questions, and focused files/tests for candidate-card, dashboard, optimizer, replay, and escalation review.
- Guardrail for next time: Any governance expert packet must list the risky terms and ask for term/context rules, not just a general policy review.
- Evidence paths: `docs/context/e2e_evidence/governance_risk_boundary_packet_20260526/PACKET_INDEX.md`, `docs/context/e2e_evidence/governance_risk_boundary_packet_20260526/GOVERNANCE_RISK_QUESTIONS.md`, `docs/context/e2e_evidence/governance_risk_boundary_packet_20260526.zip`, `docs/saw_reports/saw_governance_risk_boundary_packet_20260526.md`.

## 2026-05-26 Round Entry (Product UX Packets Need Boundary Rails)
- Date: 2026-05-26
- Mistake or miss: A Product / UX expert packet can drift into optimizer policy, ranking/scoring, alerts, or trading semantics if the question packet only asks for a better first screen.
- Root cause: Terminal Zero's dashboard, replay, candidate-card, and portfolio vocabulary share action-shaped terms, so UX review needs explicit product-boundary rails before asking workflow questions.
- Fix applied: Created a Product / UX ready-workflow packet with GitHub alignment, current truth, dashboard IA, view/test context, and explicit non-goals against recommendations, rankings, scoring, alerts, provider ingestion, and broker paths.
- Guardrail for next time: Any UX/product expert packet must ask for screen/workflow/copy decisions while explicitly forbidding product-authority expansion; include GitHub/local-truth caveats and focused UI tests.
- Evidence paths: `docs/context/e2e_evidence/product_ux_ready_workflow_packet_20260526/EXPERT_QUESTIONS.md`, `docs/context/e2e_evidence/product_ux_ready_workflow_packet_20260526/PACKET_INDEX.md`, `docs/context/e2e_evidence/product_ux_ready_workflow_packet_20260526.zip`, `docs/saw_reports/saw_product_ux_ready_workflow_packet_20260526.md`.

## 2026-05-26 Round Entry (Evidence Runners Need Output-Path and Completion Gates)
- Date: 2026-05-26
- Mistake or miss: Research-validity runner v0 initially focused on PIT/cost/benchmark math but did not fully prove evidence-output containment, atomic writes, or stale final-manifest cleanup.
- Root cause: The first implementation treated the evidence directory as a passive artifact sink, while reviewer runtime analysis correctly treated it as part of the research-validity boundary.
- Fix applied: Rejected unsafe `run_id` values, resolved evidence run directories under the cartridge output root, wrote JSON/CSV artifacts through same-directory temp files plus `os.replace`, removed stale `evidence_packet.json` before same-run rewrites, emitted final manifest last, and added focused regressions.
- Guardrail for next time: Any runner that emits evidence must test path confinement, temp-to-replace writes, final-manifest ordering, stale-manifest failure behavior, and malformed-input blocked paths before SAW closure.
- Evidence paths: `research/backtest_runner.py`, `research/evidence_schema.py`, `tests/test_research_backtest_runner.py`, `tests/test_research_evidence_schema.py`, `.venv\Scripts\python -m pytest tests\test_research_status.py tests\test_research_evidence_schema.py tests\test_research_benchmarks.py tests\test_research_backtest_runner.py tests\test_research_rule100_adapter.py tests\test_engine.py -q`.

## 2026-05-26 Round Entry (Route Smokes Need Fail-Closed Alternatives)
- Date: 2026-05-26
- Mistake or miss: The Portfolio route smoke required replay/current allocation tables even when the route rendered an explicit fail-closed replay-unavailable state.
- Root cause: The smoke contract only recognized the success table path and did not encode the page's valid unavailable-state copy.
- Fix applied: Updated the AppTest smoke to accept either role-aware replay/current allocation dataframes or the full explicit unavailable state, and restored strict preflight to run that smoke by default.
- Guardrail for next time: A boot smoke may accept a fail-closed state, but it must assert the exact visible unavailable messages; never downgrade to header-only, and never skip the route smoke in strict boot.
- Evidence paths: `tests/test_dash_1_page_registry_shell.py`, `scripts/boot_preflight.py`, `tests/test_boot_preflight.py`, `.venv\Scripts\python -m pytest tests\test_dash_1_page_registry_shell.py::test_dash_1_portfolio_allocation_route_renders_without_overlay -q`, `.venv\Scripts\python launch.py --preflight --strict`.

## 2026-05-26 Round Entry (Runtime Boot Truth Is Not Context Documentation)
- Date: 2026-05-26
- Mistake or miss: The first shared boot-status patch treated `docs/context/boot_status_current.json` as both canonical runtime artifact and legacy compatibility path.
- Root cause: BOOT-0A mixed context-packet truth with runtime preflight truth, so tests and docs accidentally preserved the old docs/context-only path.
- Fix applied: Set `core.boot_status.DEFAULT_BOOT_STATUS_PATH` to `runtime/boot_status_current.json`, kept `docs/context/boot_status_current.json` as `LEGACY_BOOT_STATUS_PATH`, updated preflight/data write guards, and added canonical-vs-legacy tests.
- Guardrail for next time: Runtime verdicts belong under `runtime/`; docs/context may provide schemas, context packets, or temporary compatibility fallbacks, but not the canonical generated boot verdict.
- Evidence paths: `core/boot_status.py`, `scripts/boot_preflight.py`, `core/data_readiness_gate.py`, `tests/test_boot_status_contract.py`, `tests/test_boot_preflight.py`, `tests/test_data_readiness_gate_write_guard.py`, `.venv\Scripts\python -m pytest tests\test_boot_status_contract.py tests\test_boot_preflight.py tests\test_data_readiness_gate.py tests\test_data_readiness_gate_write_guard.py tests\test_boot_preflight_governance.py -q`.

## 2026-05-26 Round Entry (Boot Preflight Commands Must Be Argv-Bounded)
- Date: 2026-05-26
- Mistake or miss: BOOT-0A initially ran `current_context.first_command` through `shell=True` and relied on entry-state Git checks for `--require-github`.
- Root cause: The preflight treated the context packet command as trusted operator text and treated GitHub alignment as a precondition rather than an after-gates proof.
- Fix applied: Parsed focused commands with `shlex`, allowed only Python `-m pytest`, rejected shell metacharacters, ran without shell, added gate timeouts, path-confined status writers, and rechecked Git after all gates in `--require-github`.
- Guardrail for next time: Any boot/control-plane command sourced from an artifact must be parsed into argv, allowlisted, timeout-bounded, and followed by a post-run mutation proof before claiming read-only alignment.
- Evidence paths: `scripts/boot_preflight.py`, `core/boot_status.py`, `tests/test_boot_preflight.py`, `tests/test_boot_status_contract.py`, `.venv\Scripts\python -m pytest tests\test_boot_status_contract.py tests\test_boot_preflight.py tests\test_data_readiness_gate.py tests\test_data_readiness_gate_write_guard.py tests\test_boot_preflight_governance.py -q`.

## 2026-05-26 Round Entry (Boot-Status Contract Contention Must Stop Work)
- Date: 2026-05-26
- Mistake or miss: I continued reconciling Data Readiness Gate v0 after boot-status files repeatedly flipped between the user-locked `docs/context/boot_status_current.json` contract and a competing `runtime/boot_status_current.json` contract.
- Root cause: Multiple active boot/status streams were operating in the same dirty workspace, so focused tests could pass once and then fail after a concurrent or reapplied patch restored older semantics.
- Fix applied: Stopped the implementation loop, preserved the deterministic residue/import evidence, and published a SAW BLOCK instead of claiming boot readiness.
- Guardrail for next time: If a canonical boot/status path or write guard changes during verification, stop coding immediately, freeze competing streams, choose the contract explicitly, and only then rerun tests.
- Evidence paths: `core/boot_status.py`, `scripts/boot_preflight.py`, `tests/test_boot_preflight.py`, `tests/test_boot_status_contract.py`, `tests/test_data_readiness_gate_write_guard.py`, `docs/saw_reports/saw_data_readiness_gate_v0_20260526.md`.

## 2026-05-26 Round Entry (Strict Boot Must Stay Fast And Governance-Exact)
- Date: 2026-05-26
- Mistake or miss: Strict boot preflight semantics drifted between packet-era assumptions and root truth: governance WARN was sometimes treated as blocking, while focused-contract execution was described as printed-only in places.
- Root cause: Boot readiness, safe-boot evidence, governance copy policy, and final GitHub proof were conflated while multiple BOOT-0A streams were active.
- Fix applied: Made governance WARN advisory/degraded, kept governance FAIL blocked, made default strict run boot-control tests, Portfolio smoke, and the focused current-context command, and kept `--require-github` as final read-only alignment proof rather than the `safe_boot` flag owner.
- Guardrail for next time: Keep verdict semantics in `core.boot_status` and producer mapping tests first; distinguish `safe_boot` from GitHub alignment proof, and test exact allowed labels separately from blocked action-shaped copy including whitespace variants.
- Evidence paths: `scripts/boot_preflight.py`, `scripts/governance_preflight.py`, `tests/test_boot_preflight.py`, `tests/test_boot_preflight_governance.py`, `docs/architecture/data_readiness_gate_v0.md`, `.venv\Scripts\python -m pytest tests\test_boot_preflight.py tests\test_boot_preflight_governance.py tests\test_boot_status_contract.py tests\test_data_readiness_gate_write_guard.py -q`, `.venv\Scripts\python launch.py --preflight --strict`.

## 2026-05-26 Round Entry (Root Evidence Beats Packet Artifacts)
- Date: 2026-05-26
- Mistake or miss: Governance Gate v0 packet artifacts and patch files were initially treated too much like implementation evidence, while live root files were still flipping under concurrent boot-control writers.
- Root cause: Multiple streams were editing `scripts/boot_preflight.py` and `tests/test_boot_preflight.py`, so a passing targeted run could become stale before strict root proof completed.
- Fix applied: Re-verified the live root after each flip, stopped background boot-preflight runners, mapped governance WARN to degraded and FAIL to blocked, made default strict execute the focused current-context contract, and separated `safe_boot` from the final `--require-github` GitHub-alignment proof.
- Guardrail for next time: If boot-control semantics change during verification, stop broad work, freeze to a single writer, rerun the root-supported commands, and label packet/zip/patch outputs as porting inputs until root preflight and tests prove them.
- Evidence paths: `scripts/boot_preflight.py`, `tests/test_boot_preflight.py`, `scripts/governance_preflight.py`, `docs/architecture/boot_preflight_contract.md`, `.venv\Scripts\python -m pytest tests\test_boot_preflight.py tests\test_boot_preflight_governance.py -q`, `.venv\Scripts\python scripts\governance_preflight.py --repo-root . --json`, `.venv\Scripts\python scripts\boot_preflight.py --repo-root . --strict --json`.

## 2026-05-26 Round Entry (Post-Test Sentinels Must Prove BOOT File Stability)
- Date: 2026-05-26
- Mistake or miss: BOOT-0A could have been closed from a passing targeted test even though earlier evidence showed untracked boot files sometimes snapped back to stale semantics after verification.
- Root cause: The key files were untracked and competing BOOT streams had previously run background preflight/test processes, so a single passing test was not enough proof of live-root stability.
- Fix applied: Added before/after root sentinels for governance WARN mapping, `safe_boot`/GitHub separation, final-verdict blocking, and stale test names; reran the full BOOT-0A suite and only closed after the post-suite sentinel still matched.
- Guardrail for next time: For untracked control-plane files, treat post-test source sentinels as acceptance evidence, not optional debugging.
- Evidence paths: `scripts/boot_preflight.py`, `tests/test_boot_preflight.py`, `docs/saw_reports/saw_boot_0a_shared_boot_status_contract_20260526.md`, `.venv\Scripts\python -m pytest tests\test_boot_status_contract.py tests\test_boot_preflight.py tests\test_data_readiness_gate.py tests\test_data_readiness_gate_write_guard.py tests\test_boot_preflight_governance.py -q`.

## 2026-05-26 Round Entry (Boot Gate Copy And Writes Need Their Own Guards)
- Date: 2026-05-26
- Mistake or miss: The first boot-preflight data-readiness integration carried data-gate `next_actions` into boot-status details and allowed failed preflight to refresh runtime boot-status evidence when `--write-status` was supplied.
- Root cause: The integration reused the gate payload too directly and treated explicit write intent as enough authority even after the assembled preflight verdict was blocked.
- Fix applied: Added a boot-facing sanitizer that keeps only data-readiness blockers/warnings, explicitly deferred research-validity in boot metadata/docs, blocked status writes until preflight PASS, and added focused regressions.
- Guardrail for next time: Any boot/control-plane integration must separately test copy sanitization and failed-run write blocking; explicit write flags should authorize a path, not override a blocked verdict.
- Evidence paths: `scripts/boot_preflight.py`, `tests/test_boot_preflight.py`, `docs/architecture/boot_preflight_contract.md`, `docs/saw_reports/saw_boot_preflight_data_readiness_integration_20260526.md`, `E:\Code\Quant\.venv\Scripts\python.exe -m pytest tests/test_boot_preflight.py tests/test_boot_status_contract.py -q`.

## 2026-05-27 Round Entry (Dirty-Worktree Classification Must Follow Live Root State)
- Date: 2026-05-27
- Mistake or miss: The first pass at BOOT-0A/BOOT-0B classification relied too much on stale manifest/context text and not enough on the live `git status` / `git diff` split.
- Root cause: The repository already carried mixed BOOT, governance, UI, and evidence residue, so archived truth surfaces no longer matched the current dirty worktree exactly.
- Fix applied: Reclassified from live root diffs, kept `core/boot_status.py` and `tests/test_boot_status_contract.py` in BOOT-0A, kept `scripts/governance_preflight.py` and `tests/test_boot_preflight_governance.py` in BOOT-0B, and kept `dashboard.py` and broad docs/evidence/runtime residue out of the boot-control closure.
- Guardrail for next time: Never promote a dirty-worktree manifest over live `git status` when deciding boot buckets; split mixed boot/governance files before any strict `--require-github` claim.
- Evidence paths: `git status --short`, `git diff --name-status`, `scripts/governance_preflight.py`, `tests/test_boot_preflight_governance.py`, `scripts/boot_preflight.py`, `tests/test_boot_preflight.py`, `scripts\boot_preflight.py --repo-root . --mode strict --no-tests`, `scripts\boot_preflight.py --repo-root . --mode strict --require-github --no-tests`.

## 2026-06-02 Round Entry (Matrix Bookkeeping Must Not Become Provider Approval)
- Date: 2026-06-02
- Mistake or miss: Resolving `TODO-MATRIX-001` could be mistaken for entitlement approval, WRDS access, or probe readiness if the docs only say the matrix gap is closed.
- Root cause: The new permission-truth artifact is close to provider permission language, but it is an offline metadata contract with no entitlement evidence or approval text.
- Fix applied: Refreshed current truth, product/spec, phase brief, notes, decision log, and SAW bookkeeping to mark only the metadata/builder gap as resolved while preserving entitlement, approval, clean-room, legacy cleanup, validity/C3, and public/main gaps.
- Guardrail for next time: Whenever a permission artifact moves from TODO to resolved, state the allowed-use limit, approval_ref requirement, test evidence, and forbidden provider/probe/snapshot/runtime boundaries in the same docs round.
- Evidence paths: `v2_discovery/data_lab/permission_truth.py`, `tests/test_v2_wrds_permission_truth_scope.py`, `docs/context/planner_packet_current.md`, `docs/context/bridge_contract_current.md`, `docs/context/done_checklist_current.md`, `docs/context/impact_packet_current.md`, `docs/context/multi_stream_contract_current.md`, `docs/context/post_phase_alignment_current.md`, `docs/context/observability_pack_current.md`, `docs/notes.md`, `docs/decision log.md`, `docs/saw_reports/saw_v2_d0_1_todo_matrix_bookkeeping_20260602.md`.

## 2026-05-28 Round Entry (Local Ignored Data Is Not BootReady Truth)
- Date: 2026-05-28
- Mistake or miss: Local ignored data and dirty-worktree artifacts can be mistaken for clean GitHub truth or BootReady evidence during strict data-readiness recovery.
- Root cause: The repository can contain useful local artifacts that are intentionally not tracked, but strict BootReady requires governed provenance, manifest/hash proof, and an approved intake or regeneration path before the artifacts count.
- Fix applied: Refreshed current truth surfaces for `ROUND-20260528-GOVERNED-DATA-ARTIFACT-AUTHORIZATION`, kept DataReadyStrict blocked, and recorded that authorization packets must precede regeneration or external-bundle intake.
- Guardrail for next time: Before regenerating or accepting strict-readiness artifacts, publish/approve the bounded authorization packet and keep local ignored artifacts out of GitHub truth and BootReady claims.
- Evidence paths: `docs/architecture/governed_data_artifact_authorization_20260528.md`, `docs/context/bridge_contract_current.md`, `docs/context/impact_packet_current.md`, `docs/context/done_checklist_current.md`, `docs/context/planner_packet_current.md`, `docs/context/observability_pack_current.md`, `docs/notes.md`, `docs/decision log.md`.

## 2026-05-28 Round Entry (Boot Preflight Is Not Artifact Authorization Evidence)
- Date: 2026-05-28
- Mistake or miss: The governed artifact-authorization packet listed `.venv\Scripts\python launch.py --preflight --strict` as a read-only validation command, which could be misread as DataReadyStrict or BootReady proof.
- Root cause: Boot-control preflight evidence was conflated with docs-only artifact authorization while inherited boot-control diffs and data-readiness deferral remained unresolved.
- Fix applied: Removed launch preflight from the packet validation commands, added a warning, and refreshed current truth surfaces so inherited boot-control diffs are open risk, out-of-scope, and not evidence for or against this packet.
- Guardrail for next time: Do not list boot preflight commands as artifact-authorization validation when data readiness is blocked; keep BootReady BLOCKED until a separate boot-control round proves readiness.
- Evidence paths: `docs/architecture/governed_data_artifact_authorization_20260528.md`, `docs/context/impact_packet_current.md`, `docs/context/planner_packet_current.md`, `docs/context/observability_pack_current.md`, `docs/notes.md`, `docs/lessonss.md`.

## 2026-05-30 Round Entry (Harness Flow Must Be Recorded Without Overlapping Owners)
- Date: 2026-05-30
- Mistake or miss: New harness workflow names can drift into overlapping template/skill implementation work if the docs worker records too much.
- Root cause: The workflow spans scope selection, expert context, worker done state, reconciliation, stream coordination, and feedback, but another worker owns the actual skills/templates and packet script.
- Fix applied: Added only light-touch governance records for `scope-selector`, `expert-context-packer`, `worker_done_contract`, `expert_reconciliation_matrix`, `stream_contract`, and `harness-feedback` in the owned docs files.
- Guardrail for next time: When parallel workers own skills/templates, docs workers should record the workflow contract and boundaries only; do not edit templates, skills, packet scripts, code, or truth packets.
- Evidence paths: `AGENTS.md`, `docs/decision log.md`, `docs/notes.md`, `docs/lessonss.md`.

## 2026-06-01 Round Entry (Expert Packets Must Label Dirty Harness Evidence)
- Date: 2026-06-01
- Mistake or miss: A meta-harness expert packet could be misread as permission to continue from the dirty root if copied harness skills, truth surfaces, and git evidence are not labeled by authority.
- Root cause: The local root contains useful meta-harness evidence and many dirty/untracked artifacts, but the clean implementation authority must come from an approved branch/worktree decision.
- Fix applied: Created the expert direction packet with explicit `Not Authorized` and non-authoritative dirty/local artifact sections, plus branch-state evidence and bounded expert output requirements.
- Guardrail for next time: Every expert packet built from a dirty root must include an authority model, forbidden claims, and a clean-worktree precondition before it is zipped or shared.
- Evidence paths: `docs/context/expert_packets/quant_meta_harness_direction_packet_20260601/EXPERT_DIRECTION_PACKET.md`, `docs/context/expert_packets/quant_meta_harness_direction_packet_20260601/AUTHORITY_AND_BOUNDARIES.md`, `docs/context/expert_packets/quant_meta_harness_direction_packet_20260601.zip`, `docs/saw_reports/saw_meta_harness_expert_packet_20260601.md`.

## 2026-06-01 Round Entry (Directive Intake Must Not Become Approval)
- Date: 2026-06-01
- Mistake or miss: A strong product directive for WRDS/PIT alpha-factory work could be mistaken for approval to run WRDS probes, generate snapshots, add SQLite, or begin candidate ranking/scoring.
- Root cause: The directive included concrete paths, CLI examples, and output artifacts, but current repo truth still blocks provider access, data generation, BootReady claims, and SQLite without explicit approval.
- Fix applied: Recorded the directive across product/spec/current-truth docs as idea/directive intake only, with WRDS/PIT/provenance first and explicit approval gates for provider access, snapshots, SQLite, scoring/ranking, and promotion.
- Guardrail for next time: When a pasted roadmap includes executable-looking commands, split "todo order" from "authorization" in every current truth surface before any implementation plan.
- Evidence paths: `docs/architecture/v2_alpha_factory_immediate_todo_directive_20260601.md`, `docs/context/planner_packet_current.md`, `docs/context/bridge_contract_current.md`, `docs/context/impact_packet_current.md`, `docs/context/done_checklist_current.md`, `PRD.md`, `PRODUCT_SPEC.md`, `docs/saw_reports/saw_v2_alpha_factory_directive_20260601.md`.

## 2026-06-01 Round Entry (Contract Substrate Must Stay Non-Executable)
- Date: 2026-06-01
- Mistake or miss: A V2-D0 permission/snapshot substrate can be overread as permission to connect to WRDS or generate planned snapshots if the contract code looks too close to an executable data pipeline.
- Root cause: The approved next stream names WRDS probes and PIT snapshots, but the approval covers offline contracts and provenance design only.
- Fix applied: Built dataclass and JSON Schema contracts with root provider/output/write flags forced literal false, blocked V1/boot/non-sandbox storage targets including Windows absolute/UNC paths, expanded denied-action vocabulary, aligned schema/dataclass payload validation, declared `jsonschema`, and added source-inspection/no-write tests.
- Guardrail for next time: Any future transition from contract to read-only probe or snapshot generation must require a new explicit approval, separate tests, fresh context addenda, and reviewer proof before code can import provider clients or write outputs.
- Evidence paths: `v2_discovery/data_lab/permission_matrix.py`, `v2_discovery/data_lab/snapshot_manifest.py`, `v2_discovery/data_lab/schema_registry.py`, `contracts/data_snapshot/wrds_permission_matrix.schema.json`, `contracts/data_snapshot/wrds_snapshot_manifest.schema.json`, `pyproject.toml`, `requirements.txt`, `tests/test_v2_wrds_permission_matrix.py`, `tests/test_v2_snapshot_manifest_contract.py`, `tests/test_v2_data_lab_no_v1_writes.py`.

## 2026-06-02 Round Entry (Low Confidence Routes To Expert Gate, Not Implementation)
- Date: 2026-06-02
- Mistake or miss: The V2-D0 expert packet could have been overread as permission to run a WRDS probe after the packet itself passed.
- Root cause: Low-confidence items were framed close to next-step implementation language, while actual WRDS entitlement truth was still absent.
- Fix applied: Ran Expert A/B/C reconciliation, patched Backend contract drift findings, published `MULTI_EXPERT_RECONCILED_VERDICT_20260602.md`, and kept the next stream at permission-truth authorization only.
- Guardrail for next time: Treat low-confidence WRDS/provider/snapshot/dashboard items as expert questions or approval gates until the reconciled verdict supplies explicit authorization and tests prove no-write boundaries.
- Evidence paths: `docs/handover/MULTI_EXPERT_RECONCILED_VERDICT_20260602.md`, `docs/saw_reports/saw_v2_d0_multi_expert_reconciliation_20260602.md`, `v2_discovery/data_lab/wrds_probe.py`, `v2_discovery/data_lab/snapshot_manifest.py`, `tests/test_v2_wrds_permission_matrix.py`, `tests/test_v2_snapshot_manifest_contract.py`, `.venv\Scripts\python -m pytest tests\test_v2_wrds_permission_matrix.py tests\test_v2_snapshot_manifest_contract.py tests\test_v2_data_lab_no_v1_writes.py -q`.

## 2026-06-02 Round Entry (Parallel Scope Status Needs Separate Fields)
- Date: 2026-06-02
- Mistake or miss: A single permission-status field can blur V2-D0.1 entitlement truth with PEAD_V2_001 starter dependency status, especially for `ibes.det_epsus`.
- Root cause: The same row can be pending for entitlement truth while deliberately not requested for the starter research packet.
- Fix applied: Added the V2-D0.1 scope/runtime decision artifact, resolved the PEAD starter decision, recorded the I/B/E/S dual-status rule, and originally kept `TODO-MATRIX-001` open for separate entitlement-status and PEAD-starter-scope metadata. Superseded on 2026-06-02 by the permission-truth bookkeeping round that resolved `TODO-MATRIX-001`.
- Guardrail for next time: When one artifact spans multiple scopes, require separate status fields per scope before marking a row unknown, pending, approved, or not_requested.
- Evidence paths: `docs/handover/V2_D0_1_SCOPE_AND_CLEANROOM_RUNTIME_DECISION_20260602.md`, `docs/context/planner_packet_current.md`, `docs/context/bridge_contract_current.md`, `docs/context/done_checklist_current.md`, `docs/context/impact_packet_current.md`, `docs/context/multi_stream_contract_current.md`, `docs/context/post_phase_alignment_current.md`, `docs/context/observability_pack_current.md`, `docs/architecture/v2_wrds_data_lab_policy.md`, `docs/phase_brief/phase65-brief.md`, `docs/notes.md`, `docs/decision log.md`, `PRD.md`, `PRODUCT_SPEC.md`, `docs/prd.md`, `docs/spec.md`.

## 2026-06-02 Round Entry (Expert Follow-Ups Need Conflict Labels, Not Flattened Agreement)
- Date: 2026-06-02
- Mistake or miss: Expert follow-ups with high agreement can still contain a real cross-expert conflict, especially when one expert permits a Compustat-rdq PEAD starter and another prefers I/B/E/S analyst-surprise as the first primary signal.
- Root cause: Agreement level summarizes direction, but it does not prove every expert made the same scope choice.
- Fix applied: Added the V2-D0.1 follow-up reconciliation artifact, marked Quant Research as `PARTIAL_AGREE_HIGH`, recorded the PEAD starter conflict, and converted unresolved gaps into stable TODO IDs.
- Guardrail for next time: When recording expert agreement, always separate agreement level from decision conflicts; promote only the concrete shared gates and leave conflicting choices as explicit TODOs or real follow-up questions.
- Evidence paths: `docs/handover/V2_D0_1_EXPERT_1_6_FOLLOWUP_RECONCILIATION_20260602.md`, `docs/context/planner_packet_current.md`, `docs/context/bridge_contract_current.md`, `docs/context/done_checklist_current.md`, `docs/context/impact_packet_current.md`, `docs/context/multi_stream_contract_current.md`, `docs/context/post_phase_alignment_current.md`, `docs/context/observability_pack_current.md`, `docs/phase_brief/phase65-brief.md`, `docs/notes.md`, `docs/decision log.md`, `PRD.md`, `PRODUCT_SPEC.md`, `docs/prd.md`, `docs/spec.md`.

## 2026-06-02 Round Entry (Agreement Ratings Must Not Become Authorization)
- Date: 2026-06-02
- Mistake or miss: Expert 1-6 high agreement could be misread as approval for WRDS probes, PEAD work, or V2 alpha validity claims.
- Root cause: Agreement ratings and high-confidence TODOs summarize direction, but current authority still lacks entitlement evidence, approval text, WRDS/PIT approval, and V2 alpha validity packet structure.
- Fix applied: Refreshed current truth surfaces and product/spec logs with entitlement-only V2-D0.1 gates, `PATCH_RESOLVED` row-validator status, Security approval-text/quarantine risk, conditional `PEAD_V2_001_BOUNDARY_PACKET`, and `V2_ALPHA_VALIDITY_PACKET` requirement.
- Guardrail for next time: Record agreement ratings as decision-support metadata only; never treat them as provider, probe, snapshot, data-write, dashboard, scoring, or research-validity authorization.
- Evidence paths: `docs/context/planner_packet_current.md`, `docs/context/bridge_contract_current.md`, `docs/context/done_checklist_current.md`, `docs/context/impact_packet_current.md`, `docs/context/multi_stream_contract_current.md`, `docs/context/post_phase_alignment_current.md`, `docs/context/observability_pack_current.md`, `docs/phase_brief/phase65-brief.md`, `docs/notes.md`, `docs/decision log.md`, `PRD.md`, `PRODUCT_SPEC.md`, `docs/prd.md`, `docs/spec.md`.

## 2026-06-02 Round Entry (Parent SAW Must Reconcile Worker Evidence)
- Date: 2026-06-02
- Mistake or miss: Worker B recorded the initial 28-test bookkeeping evidence, but parent reconciliation later added root-constant drift coverage and expanded the final focused suite to 51 tests.
- Root cause: The docs worker completed before reviewer-driven parent hardening, so evidence lines could have stayed stale without a final parent grep and context rebuild.
- Fix applied: Added V2-D0.1 `permission_truth.py`, closed `TODO-MATRIX-001`, patched stale PEAD/TODO wording, added root-constant regression tests, refreshed docs/current truth to the 51-test evidence, and validated the parent SAW report.
- Guardrail for next time: After subagent implementation and review, parent must rerun evidence, grep stale test-count/TODO markers, rebuild context, and update the terminal SAW report before final response.
- Evidence paths: `v2_discovery/data_lab/permission_truth.py`, `tests/test_v2_wrds_permission_truth_scope.py`, `docs/saw_reports/saw_v2_d0_1_todo_matrix_bookkeeping_20260602.md`, `docs/context/planner_packet_current.md`, `.venv\Scripts\python -m pytest tests\test_v2_wrds_permission_truth_scope.py tests\test_v2_wrds_permission_matrix.py tests\test_v2_snapshot_manifest_contract.py tests\test_v2_data_lab_no_v1_writes.py -q`, `.venv\Scripts\python scripts\build_context_packet.py --validate`.

## 2026-06-03 Round Entry (Secret Material Is Not Entitlement Evidence)
- Date: 2026-06-03
- Mistake or miss: Approval intent plus local secret material could be mistaken for non-secret entitlement evidence or final row approval.
- Root cause: The user approved aligned intent and identified local secret material, but boundary/evidence subagents found no qualifying non-secret entitlement evidence for the five WRDS rows.
- Fix applied: Created an authorization-intent packet, kept all five rows evidence_missing/pending with approval_ref null, and recorded that `secret.txt` is local secret material and is not non-secret entitlement evidence.
- Guardrail for next time: Never treat local secret-bearing files as entitlement evidence; require non-secret account/library/table evidence before approval_ref or row approval can be recorded.
- Evidence paths: `docs/authorization/V2_D0_1_WRDS_PERMISSION_TRUTH_AUTHORIZATION.md`, `docs/authorization/V2_D0_1_WRDS_PERMISSION_TRUTH_AUTHORIZATION.json`, `docs/saw_reports/saw_v2_d0_1_authorization_intent_20260603.md`.

## 2026-06-03 Round Entry (Evidence Requests Must Stay Non-Executable)
- Date: 2026-06-03
- Mistake or miss: A WRDS entitlement evidence request could drift into credential handling, provider probing, schema/table discovery, row counts, or premature approval if the request text is not explicit.
- Root cause: The next safe step asks external institutional contacts for permission truth, but the same domain vocabulary can sound like access validation unless forbidden actions are repeated in the artifact.
- Fix applied: Created V2-D0.2 request artifacts with copyable non-secret evidence-request language, all five rows still evidence_missing/pending with approval_ref null, and SAW BLOCK recorded as the correct protective status.
- Guardrail for next time: Evidence-request artifacts must ask only for dated attributable non-secret entitlement confirmation and must explicitly forbid credentials, provider access, probes, discovery, data output, and row approval.
- Evidence paths: `docs/authorization/V2_D0_2_WRDS_ENTITLEMENT_EVIDENCE_REQUEST.md`, `docs/authorization/V2_D0_2_WRDS_ENTITLEMENT_EVIDENCE_REQUEST.json`.

## 2026-06-17 Round Entry (Current Context Must Track Latest Complete Packet)
- Date: 2026-06-17
- Mistake or miss: `scripts/build_context_packet.py` validated successfully while selecting the older V2-D0.1 bookkeeping New Context Packet instead of the latest V2-D0.4C progress state.
- Root cause: The latest D0.4C addendum in `docs/context/planner_packet_current.md` did not include a complete `## New Context Packet`, so the builder fell through to the next complete packet.
- Fix applied: Added a complete D0.4C New Context Packet under the latest addendum, rebuilt `docs/context/current_context.md` and `docs/context/current_context.json`, and revalidated the context-packet contract.
- Guardrail for next time: Every current-truth addendum that should drive session bootstrap must include a complete New Context Packet before running or trusting `scripts/build_context_packet.py --validate`.
- Evidence paths: `docs/context/planner_packet_current.md`, `docs/context/current_context.md`, `docs/context/current_context.json`, `.venv\Scripts\python scripts\build_context_packet.py --validate`, `.venv\Scripts\python -m pytest tests\test_build_context_packet.py -q`.

## 2026-06-19 Round Entry (Superseded Data Evidence Must Be Archived Before Promotion)
- Date: 2026-06-19
- Mistake or miss: The corrected D2A sample was promoted to the legacy sample path before the invalid prior sample was archived under an explicit superseded-evidence name.
- Root cause: Atomic output replacement protected the active Parquet/manifest pair but did not distinguish active-output rollback from historical-evidence retention.
- Fix applied: Reproduced the legacy Parquet byte-for-byte at its original SHA256, published it under a `legacy_formula_superseded` filename with a manifest that forbids validation/strategy use, and retained the corrected sample at the active path.
- Guardrail for next time: Before replacing a known-invalid but evidence-bearing artifact, archive and hash-verify it under an explicit superseded name; atomic promotion alone is not evidence retention.
- Evidence paths: `data/processed/pead_d2_daily_returns_sample_legacy_formula_superseded_20260618.parquet`, `data/processed/pead_d2_daily_returns_sample_legacy_formula_superseded_20260618.parquet.manifest.json`, `data/processed/pead_d2_daily_returns_sample.parquet`, `scripts/pead_d2_return_contract.py`.

## 2026-06-19 Round Entry (Single-Event Smokes Miss Overlap and TOCTOU)
- Date: 2026-06-19
- Mistake or miss: A single-event strategy smoke missed duplicate canonical return keys created by overlapping event windows, and the input contract could validate a path hash before reopening a concurrently replaced file.
- Root cause: The fixture covered only a happy-path event, while input loading used a path-based two-step validate-then-read sequence.
- Fix applied: Added a full-sample canonical adapter smoke with overlapping events and unique return-key assertions, and bound manifest validation, hashing, schema checks, and pandas reads to stable captured byte snapshots.
- Guardrail for next time: Every future artifact contract must include a multi-event overlapping-window regression and a concurrent path-replacement regression before handoff or promotion.
- Evidence paths: `scripts/pead_d2b_event_window_contract.py`, `tests/test_pead_d2b_event_window_contract.py`, `data/processed/pead_d2b_event_windows_sample.parquet.manifest.json`, `docs/phase_brief/v2-pead-d2b-event-iid-window-brief.md`.

## 2026-06-19 Round Entry (Benchmark Excess Return Must Not Become Total Return)
- Date: 2026-06-19
- Mistake or miss: The existing local `ff_factors.parquet` could be overread as the D3 benchmark input even though it lacks the full D2B date spine, and `mktrf` could be mistaken for total market return.
- Root cause: Prior factor ingestion stored factor fields without a PEAD-specific benchmark manifest, source-release contract, or explicit `mktrf + rf` total-return formula.
- Fix applied: Added the D3 benchmark-input contract, recorded the formula in notes and decision log, and refreshed current truth to keep implementation/provider/CAR interpretation blocked.
- Guardrail for next time: Before benchmark implementation or CAR/BHAR interpretation, require an immutable manifest that proves full D2B session coverage, decimal units, `benchmark_return = mktrf + rf`, source citation, hashes, and no missing-date fill.
- Evidence paths: `docs/phase_brief/v2-pead-d3-benchmark-input-contract.md`, `docs/notes.md`, `docs/decision log.md`, `data/processed/ff_factors.parquet`.

## 2026-06-19 Round Entry (D2B Session Spine Can Contain Non-Benchmark Trading Dates)
- Date: 2026-06-19
- Mistake or miss: The D3 implementation assumption treated the D2B 2,862-session spine as benchmark-compatible market sessions, but the spine contains 52 dates absent from official Ken French daily factors.
- Root cause: D2B inherited its global session spine from D2A source dates; those dates include U.S. market holidays/special closures such as 2015-01-19, 2018-12-05, 2022-06-20, and 2025-01-09.
- Fix applied: Added `scripts/pead_d3_benchmark_artifact.py` with strict D2B/D2A session coverage validation, official source release/hash capture, and fail-closed missing-date handling; no benchmark artifact was published.
- Guardrail for next time: Before rerunning D3 artifact publication, audit and repair the D2B/D2A market-session spine so required benchmark dates represent actual tradable sessions; never coerce benchmark coverage by filling or dropping dates inside D3.
- Evidence paths: `scripts/pead_d3_benchmark_artifact.py`, `tests/test_pead_d3_benchmark_artifact.py`, `docs/phase_brief/v2-pead-d3-benchmark-artifact-implementation.md`, `.venv\Scripts\python -m pytest tests\test_pead_d3_benchmark_artifact.py -q`, `.venv\Scripts\python scripts\pead_d3_benchmark_artifact.py --build`.
## 2026-06-19 Round Entry (Benchmark Missingness Must Not Erase Raw Asset Returns)
- Date: 2026-06-19
- Mistake or miss: The first D3 regression expected raw `cumulative_total_return` to become null when only benchmark observations were incomplete.
- Root cause: The test conflated benchmark-adjusted completeness with asset-return completeness even though the D3 contract blocks CAR/BHAR, not raw asset return, on missing benchmark dates.
- Fix applied: Repaired `strategies/pead_event_study.py` so complete asset windows preserve raw cumulative return while benchmark return, CAR, BHAR, `window_complete`, and `eligible_for_analysis` remain benchmark-gated; updated the D3 regression accordingly.
- Guardrail for next time: Separate asset-window completeness from benchmark-window completeness in tests and reports; missing benchmark coverage blocks abnormal-return claims, not raw-return arithmetic.
- Evidence paths: `strategies/pead_event_study.py`, `tests/test_pead_d3_benchmark_artifact.py`, `docs/phase_brief/v2-pead-d3-benchmark-artifact-implementation.md`, `.venv\Scripts\python -m pytest tests\test_pead_d3_benchmark_artifact.py tests\test_pead_event_study.py -q`.

## 2026-06-20 Round Entry (Benchmark Publication Needs Source-Bound Session Proof)
- Date: 2026-06-20
- Mistake or miss: A D3 benchmark publication gate could overread "builder exists" or "in-memory coverage passed" as enough proof to publish the artifact.
- Root cause: The publication step depends on three independent locks: exact Ken French source bytes, repaired D2B session-spine hash, and immutable Parquet/manifest integrity.
- Fix applied: Ran the focused D3/D2B gate first, published only through `scripts/pead_d3_benchmark_artifact.py --build`, and independently verified manifest hash, row count, zero missing sessions, zero duplicate dates, finite numeric fields, and formula error `0.0`.
- Guardrail for next time: Before any downstream CAR/BHAR or strategy handoff, validate the benchmark manifest first and treat benchmark-input availability as separate from alpha interpretation authority.
- Evidence paths: `data/processed/pead_d3_ken_french_daily_benchmark.parquet.manifest.json`, `data/processed/pead_d3_ken_french_daily_benchmark.f7dede990475b4ecf499fbf1dee3c4a81298073f018cc3a1ba1559f3e702c589.parquet`, `scripts/pead_d3_benchmark_artifact.py`, `tests/test_pead_d3_benchmark_artifact.py`, `.venv\Scripts\python -m pytest tests\test_pead_d3_benchmark_artifact.py tests\test_pead_d2b_event_window_contract.py -q`, `.venv\Scripts\python scripts\pead_d3_benchmark_artifact.py --build`.

## 2026-06-20 Round Entry (Published Inputs Still Need an Artifact-to-Consumer Gate)
- Date: 2026-06-20
- Mistake or miss: D2B and D3 artifacts and isolated strategy tests were individually valid, but no single regression proved their full join cardinality, coverage, and formula handoff.
- Root cause: Publication tests and synthetic strategy tests stopped at their own component boundaries.
- Fix applied: Added `tests/test_pead_d3_strategy_handoff.py` to validate both manifest pointers, the full many-to-one join, 60-observation completeness, real-event CAR/BHAR formulas, and missing-benchmark behavior.
- Guardrail for next time: Before declaring an artifact handoff complete, add one consumer-level test that reads the published manifest pointers and proves cardinality, coverage, formulas, and fail-closed missingness together.
- Evidence paths: `tests/test_pead_d3_strategy_handoff.py`, `data/processed/pead_d2b_event_windows_sample.parquet.manifest.json`, `data/processed/pead_d3_ken_french_daily_benchmark.parquet.manifest.json`, `strategies/pead_event_study.py`, `docs/saw_reports/saw_v2_d3_strategy_benchmark_handoff_20260620.md`, `.venv\Scripts\python -m pytest tests\test_pead_d3_strategy_handoff.py -q`.

## 2026-06-20 Round Entry (A Handoff Test Does Not Replace Numerical Evidence)
- Date: 2026-06-20
- Mistake or miss: The completed D3 artifact-to-strategy handoff was initially
  translated directly into a dashboard-scoping recommendation even though no
  reproducible real-data CAR/BHAR/quintile artifact existed.
- Root cause: Mechanical handoff proof and numerical research evidence were
  treated as the same gate, and the proposed fallback was an ad hoc console dump
  rather than a reviewable artifact.
- Fix applied: Added a bounded validation CLI and focused tests, published one
  strict atomic JSON with D1/D2B/D3 lineage, locked daily and descriptive
  quarterly outputs, explicit limitations, and no interpretation, then ran the
  full PEAD regression and independent SAW review.
- Guardrail for next time: After an artifact-to-consumer handoff passes, require
  one deterministic, lineage-bound evidence artifact before recommending product
  or dashboard scoping; preserve fail-closed statistical gaps instead of tuning
  cohort frequency or HAC lags.
- Evidence paths: `scripts/pead_real_data_validation.py`,
  `tests/test_pead_real_data_validation.py`,
  `docs/context/e2e_evidence/pead_real_data_validation_20260620.json`,
  `docs/phase_brief/v2-pead-real-data-validation-brief.md`,
  `.venv\Scripts\python -m pytest tests\test_pead_real_data_validation.py -q`.

## 2026-06-21 Round Entry (Inference Repair Must Change the Estimator, Not the Label)
- Date: 2026-06-21
- Mistake or miss: The proposed fast path treated quarterly aggregation and removal of `ex_post_descriptive_only` as an inference repair even though both actions would change statistical policy without an approved estimator contract.
- Root cause: A non-null quarterly t-stat was mistaken for evidence that the irregular, overlapping event-cohort dependence problem had been solved.
- Fix applied: Approved a separate calendar-time portfolio methodology with outcome-independent signal formation, deterministic overlap handling, minimum leg counts, fixed HAC(59), and robustness-only stationary bootstrap; retained quarterly as descriptive-only.
- Guardrail for next time: Never promote a descriptive aggregation because it yields a non-null statistic; predeclare the estimand, dependence model, overlap rule, missingness rule, and claim boundary before implementation.
- Evidence paths: `docs/phase_brief/v2-pead-alpha-inference-methodology-gate.md`, `strategies/pead_event_study.py`, `scripts/pead_real_data_validation.py`, `docs/context/e2e_evidence/pead_real_data_validation_20260620.json`.

## 2026-06-21 Round Entry (No-Security Extreme Rows Can Vanish in Overlap Grouping)
- Date: 2026-06-21
- Mistake or miss: A naive parent-side implementation prep grouped overlap candidates by `(security_id, return_date)` and dropped null-`security_id` no-eligible-security rows, undercounting expected extreme rows by 240.
- Root cause: The latest-event overlap rule is security-keyed, but no-eligible-security extreme rows are still expected-missing diagnostics and cannot pass through a default pandas groupby on null keys.
- Fix applied: M1B separates non-null-security overlap resolution from no-security extreme diagnostics; no-security Q1/Q5 rows remain expected missing and never contribute finite returns.
- Guardrail for next time: Any security-keyed portfolio formation must explicitly define the null-security lane before grouping; reviewer count contracts should include no-security expected/missing rows.
- Evidence paths: `strategies/pead_event_study.py`, `tests/test_pead_event_study.py`, `scripts/pead_real_data_validation.py`, `docs/context/e2e_evidence/pead_calendar_time_inference_m1b.json`.

## 2026-06-21 Round Entry (Dashboard Contract Drift Must Be Fixed at the Source)
- Date: 2026-06-21
- Mistake or miss: The full repository suite stayed red because event-ledger trace labels drifted from the production/test contract names `ENTER` and `EXIT` even though the filters still used the correct actions.
- Root cause: A presentation wording improvement crossed the legend-label contract boundary and was not isolated to hover text.
- Fix applied: Restored the Plotly trace names in `dashboard.py` to `ENTER` and `EXIT`, preserved the newer lifecycle hover wording, reran the focused lifecycle regression and full pytest, and completed Reviewer A/B/C closure.
- Guardrail for next time: When UI wording changes are intentional, keep machine-checked identifiers and legend/action contracts stable unless the test and product contract are explicitly approved for migration.
- Evidence paths: `dashboard.py`, `tests/test_position_lifecycle.py`, `docs/saw_reports/saw_v2_pead_calendar_time_inference_m1b_20260621.md`, `.venv\Scripts\python -m pytest tests\test_position_lifecycle.py::test_event_ledger_chart_unchanged_enter_exit_markers -q`, `.venv\Scripts\python -m pytest -q`.

## 2026-06-25 Round Entry (Sparse Engines Need Explicit Exit Parity, Not Just a Loop Removal)
- Date: 2026-06-25
- Mistake or miss: The first M6a framework engine was accepted as synthetic-only without an active-scale architecture check; it used event-row iteration and a dense return-date-by-security pivot for turnover.
- Root cause: Small synthetic tests hid the `events x horizon x securities` materialization shape and did not force trade-to-zero parity at the final exit.
- Fix applied: Replaced the loop/pivot path with a DuckDB ASOF start lookup, bounded return-ordinal interval join, direct sparse daily aggregation, sparse previous/current turnover union, and explicit final exit. Added full-scale smoke plus entry/exit/overlap fixture coverage.
- Guardrail for next time: For every portfolio engine, test the exact turnover semantics for entry, overlap, exit, and final liquidation; add a full-scale bounded-memory smoke and a source guard against wide-matrix construction before allowing real-data wiring.
- Evidence paths: `scripts/pead_m6_pit_walk_forward_equity_curve.py`, `tests/test_pead_m6_pit_walk_forward_equity_curve.py`, `docs/context/e2e_evidence/pead_m6_pit_walk_forward_equity_curve.json`.

## 2026-06-25 Round Entry (Sparse Scale Fix Must Include Calendar, Dtypes, and Determinism)
- Date: 2026-06-25
- Mistake or miss: The first sparse repair removed the loop and pivot but still used per-security return ordinals, passed object-valued identifiers into the relational boundary, and lacked a repeatable output-hash proof.
- Root cause: Memory scale was treated as the only Reviewer C concern; calendar boundary semantics and floating aggregation reproducibility were left implicit.
- Fix applied: Added a global `return_idx:int32` calendar with explicit `entry_idx/exit_idx` interval bounds, numeric-only DuckDB relations with object-dtype rejection, one-worker compensated aggregation, canonical daily SHA-256 hashing, and shuffled-input parity coverage.
- Guardrail for next time: A sparse portfolio engine is not complete until calendar membership, relational dtypes, entry/overlap/exit liquidation turnover, and reproducible final output are each independently tested under the full-universe smoke bound.
- Evidence paths: `scripts/pead_m6_pit_walk_forward_equity_curve.py`, `tests/test_pead_m6_pit_walk_forward_equity_curve.py`, `docs/phase_brief/v2-pead-m6-pit-walk-forward-equity-curve.md`.

## 2026-07-01 Round Entry (Session Mapping Needs Immutable Calendar and Linkage Evidence)
- Date: 2026-07-01
- Mistake or miss: Earlier strict Gate A request preparation treated timezone normalization and generic session wording as sufficient, without binding immutable calendar provenance, eligible early-close sessions, conditional timing linkage, and mechanically replayable close classification.
- Root cause: Event-time semantics were described as an implementation detail rather than as first-class evidence dependencies that a reviewer must reproduce from locked bytes.
- Fix applied: Created versioned successor Gate A contract and request artifacts that bind an authorized calendar source of record, define eligible trading sessions, require an executable no-same-session mapping rule, make a timing artifact conditional on selected-source capability, and require one-to-one linkage when separate timing is used.
- Guardrail for next time: Any strict timing-PIT claim must preserve predecessor hashes, bind the source/timing/calendar artifacts by SHA-256, define session mapping mechanically, and fail closed for ambiguous timestamps, non-one-to-one timing joins, or calendar gaps.
- Evidence paths: `docs/authorization/V2_PEAD_M6B_GATE_A_EPS_DEFINITION_CONTRACT_REQUEST_20260701.json`, `docs/authorization/V2_PEAD_M6B_STRICT_DATA_SOURCE_ACCESS_REQUESTS_20260701.json`, `docs/saw_reports/saw_v2_pead_m6b_strict_data_authorization_request_20260701.md`.

## 2026-07-11 Round Entry (Terminal Evidence Must Be Reconciled Into Current Truth)
- Date: 2026-07-11
- Mistake or miss: Terminal reviewer-independence PASS was committed, but planner, bridge, done, and related current-truth surfaces still reported the superseded ownership BLOCK.
- Root cause: The review-only reconciliation intentionally committed only reviewer reports and terminal SAW evidence, while semantic drift detection was outside governance and planning preflight coverage.
- Fix applied: Ran a bounded docs-only truth reconciliation across all mandatory current-truth surfaces, preserved the payload and envelope bytes, regenerated/validated current context, reran governance and planning preflight, and published Thin SAW evidence.
- Guardrail for next time: After any terminal evidence-only commit changes a milestone verdict, immediately compare every active current-truth surface against the new verdict before declaring closure; preflight PASS does not substitute for semantic truth reconciliation.
- Evidence paths: `docs/saw_reports/saw_request_artifact_identity_terminal_review_v1_20260711.md`, `docs/context/planner_packet_current.md`, `docs/context/bridge_contract_current.md`, `docs/context/done_checklist_current.md`, `docs/saw_reports/saw_request_artifact_identity_truth_reconciliation_v1_20260711.md`.

## 2026-07-12 Round Entry (C0X→M7F0-v4)
- Date: 2026-07-12
- Mistake or miss: C0A closure claimed PASS with wrong envelope hashes; porcelain and ls-files parsers silently skipped malformed records; nested gitlinks poisoned dirt completeness.
- Root cause: Closure theater over object-store truth; parsers optimized for lenience; proof used branch checkout that cannot attach twice.
- Fix applied: Fork `aee7f4c`, fail-close both parsers, deindex+ignore 41 gitlinks, detached proof worktree planning PASS; M7F0-v4 mechanical vertical with v4 clock/overlap/live-name/cost locks.
- Guardrail for next time: Prove exact commits detached; never source-wide nonnumeric gates on CRSP; formation after map/window filters; bind ignored parquet via tracked manifest.
- Evidence paths: commits `17cb830`, `d4fcfcb`; `docs/context/e2e_evidence/pead_m7f0_v4_2019_crsp_vertical.json`; `docs/saw_reports/saw_c0x_m7f0_v4_20260712.md`.

## 2026-07-12 Round Entry (M7F1-v5.2-final)
- Date: 2026-07-12
- Mistake or miss: Uncommitted M7F1-v5 claimed implementation identity on M7F0 tip, reused map, lacked prior-20 history for January, treated identity max_date as if selection, and left BLOCK without separate evidence vs review commits.
- Root cause: Velocity over package discipline; prior-20 misframed as map repair; 2019-only panel load; Commit B conflated with terminal review.
- Fix applied: Commit A code/tests only (`138c8b7`); source-wide spine + pre-2019 load; pre-Q5 prior-20 tradability roadmap deviation (finite RET, abs(PRC)>0, VOL>0); force map rebuild; invalidate stale curve; first/last mismatch diagnostic-only; Commit B evidence/truth; Commit C A/B/C+SAW pinned to B.
- Guardrail for next time: Never bank evidence before code commit; never reuse map; never close evidence and terminal SAW in one commit; record formation tradability gates as explicit roadmap deviations.
- Evidence paths: `138c8b7`; `docs/context/e2e_evidence/pead_m7f1_v5_2019_crsp_vertical.json`; residual BLOCK 7/2448.

## 2026-07-12 M7F2-v6-final Outcome Envelope

- Mistake or miss: M7F1-v5.2 claimed map unused for selection and closed with ADVISORY_PASS (validator-invalid); residual 7 invalids mixed pre-entry delist, bridgeable blanks, and genuine ambiguities.
- Root cause: metadata honesty lag; residual policy deferred; SAW verdict enum not PASS/BLOCK.
- Fix applied: M7F2-v6-final hard replace — pre-entry exclude before Q5, blank one-day bridge, strict BLOCK + neutral carry + write-down envelope, map used_for_selection=true; SAW may PASS diagnostic with strict_curve BLOCKED.
- Guardrail for next time: never claim identity maps unused for selection; residual dispositions are structural rules not event-id lists; SAW verdict only PASS or BLOCK; neutral carry is not a finite upper bound.
- Evidence: scripts/pead_m7f2_v6_2019_crsp_vertical.py; docs/context/e2e_evidence/pead_m7f2_v6_2019_crsp_vertical.json; tests 19/19.

## 2026-07-13 Round Entry (Residual Evidence Branch Must Be Executed Before Full Scan)
- Date: 2026-07-13
- Mistake or miss: The A2 focused suite passed 44/44, but the first full Slice 2 run failed after the expensive CRSP scans because the residual-evidence branch referenced undefined `selected_event_ids` instead of the verified selection contract.
- Root cause: Tests covered the selection-lock helper and pre-write ordering, but no tiny end-to-end test executed the real `bad` residual branch through evidence and manifest publication.
- Fix applied: Replaced the stale count reference with `selection_contract["n_selected_events"]`, added a deterministic real residual-evidence regression, removed all failed-run partial outputs, committed A2.1 at `b4d35e1`, reran from a fresh clean worktree, independently audited the published parquets and identities, and banked Commit B at `9f37745`.
- Guardrail for next time: Every expensive data runner must have a small end-to-end regression for each terminal publication branch, including residual/BLOCK evidence, before a full-file scan is authorized; helper-only tests do not prove branch publication safety.
- Evidence paths: `scripts/pead_m7f4_v8_2019_crsp_vertical.py`, `tests/test_pead_m7f4_v8_2019_crsp_vertical.py`, `docs/context/e2e_evidence/pead_m7f4_v8_2019_crsp_vertical.json`, `docs/context/e2e_evidence/pead_m7f4_v8_2019_daily_returns.parquet.manifest.json`, `docs/context/e2e_evidence/pead_m7f4_v8_2019_event_ledger.parquet.manifest.json`.

## 2026-07-17 Round Entry (Protocol Byte Proof Must Avoid Ambient Package and Git Assumptions)
- Date: 2026-07-17
- Mistake or miss: The first cross-platform proof imported the independent encoder through the repository `validation` package, which pulled in pandas, and assumed Linux Git could resolve a Windows-managed worktree pointer.
- Root cause: Protocol tools were logically stdlib-only but their import path and local worktree identity still depended on ambient repository packaging and platform-specific Git metadata.
- Fix applied: Loaded the independent encoder directly from its validation directory, kept the verifier and reference implementation free of repository package imports, added an explicit `GV_FS0_GIT_OBJECT_FORMAT` override only for filesystem-copy parity checks, and retained normal CI derivation from `git rev-parse --show-object-format`.
- Guardrail for next time: A byte-parity tool must be runnable from a minimal Python installation without importing application packages; distinguish canonical-byte parity from local worktree Git discoverability and make any non-Git object-format input explicit and validated.
- Evidence paths: `validation/gv_fs0_ci_reference_encoder.py`, `scripts/verify_gv_fs0_protocol_freeze.py`, `.github/workflows/gv-fs0-protocol-freeze.yml`, `tests/test_gv_fs0_freeze_immutability_v1.py`.

## 2026-07-17 Round Entry (Hosted CI Semantics Need Native Regression Coverage)
- Date: 2026-07-17
- Mistake or miss: The first repaired candidate passed local protocol checks but still had hosted-CI risks: Windows shell glob expansion and feature-branch push base selection were not modeled closely enough.
- Root cause: Local parity focused on protocol bytes while workflow semantics were reviewed as YAML intent instead of executable branch/event behavior.
- Fix applied: Expanded protocol pytest globs inside Python, changed feature-branch push guard selection to the default branch, limited previous-SHA enforcement to default-branch pushes, and added static regression coverage for those workflow contracts.
- Guardrail for next time: Any cross-platform freeze workflow must test Windows command expansion and each GitHub event/base-selection branch before terminal audit.
- Evidence paths: `.github/workflows/gv-fs0-protocol-freeze.yml`, `tests/test_gv_fs0_freeze_immutability_v1.py`, `docs/saw_reports/saw_gv_fs0_protocol_freeze_v1_20260717.md`.

## 2026-07-18 Round Entry (Ship the First Economic Path Before Publication Machinery)
- Date: 2026-07-18
- Mistake or miss: Earlier planning grouped book, certification, UI, and publication horizontally, which would have delayed executable economic feedback and made verifier disagreement harder to localize.
- Root cause: File-layer sequencing was treated as delivery sequencing instead of following one decision through every authority boundary.
- Fix applied: Implemented OPEN vertically from source fixture and `DecisionEnvelope` through canonical events, exact snapshots, two isolated verifier attempts, ten-check certification, certification-reference event, certified result, and injection into the final read-only adapter. Permanent bundle publication remains unopened.
- Guardrail for next time: For each portfolio gate, execute one complete decision path first and require exact canonical bytes plus a deliberate disagreement test before adding a second decision or any permanent publication mechanism.
- Evidence paths: `core/gv_fs0_book.py`, `core/gv_fs0_certify.py`, `views/gv_fs0_portfolio_adapter.py`, `tests/gv_fs0_product/test_open_vertical.py`, `docs/phase_brief/gv-fs0-f1-product-slice-brief.md`.


## 2026-07-22 — C1 candidate banking lessons

- Mistake risk: treating donor committed base as if it descended from b7. Guardrail: always state explicit b7→donor-byte transformation; donor committed base is e9e9a9a.
- Mistake risk: counting only git status clean. Guardrail: also prove no skip-worktree/assume-unchanged flags and working-file blob equality to index.
- Mistake risk: operator-authored rubric replacement. Guardrail: real reviewer path requires external GitHub receipt and exact imported bytes before seal; mapping reveal only after receipt-bound seal.
- Mistake risk: self-referential manifest hash. Guardrail: staged envelope or annotated-tag binding of final manifest blob without claiming impossible self-hash.

## 2026-07-28 Round Entry (A Release Must Separate Installed Seed From User State)
- Date: 2026-07-28
- Mistake or miss: The operable Case Workspace wrote confirmation and certified output into repository-banked product data, and the first package draft omitted runtime-only contract/verifier dependencies and assumed script-path imports would resolve the repository root.
- Root cause: Branch-level dogfood was treated as equivalent to installation behavior; dependency closure and script entry semantics were not tested from a clean extracted archive.
- Fix applied: Added a fail-closed user-workspace bootstrap with exact immutable-seed verification, preserved mutable state outside the package, built an explicit deterministic release allowlist, and repeatedly executed the package from a clean extraction until the full workflow passed.
- Guardrail for next time: No product slice is shipment-ready until a clean extracted artifact can initialize, complete, persist, and reopen its primary workflow using only packaged files; run the builder and smoke by file path on both operating-system families, not only as imported test modules.
- Evidence paths: `core/gv_alpha0_ship_runtime.py`, `scripts/build_gv_alpha0_release.py`, `scripts/smoke_gv_alpha0_release.py`, `tests/gv_fs0_product/test_gv_alpha0_ship_runtime.py`, `tests/gv_fs0_product/test_gv_alpha0_release_package.py`, `.github/workflows/gv-fs0-product.yml`.

## 2026-07-28 Round Entry (Lexical Confinement and Self-Hashed Seeds Are Not Release Integrity)
- Date: 2026-07-28
- Mistake or miss: The first shipment candidate compared an absolute-but-noncanonical runtime path against the package and recomputed the seed digest from whatever bytes were present, allowing Windows-junction routing into the bundle and accepting freshly modified package seeds.
- Root cause: Symlink checks were applied only to final path objects, while Windows junctions and linked parents require canonical containment; the workspace seed manifest proved runtime-copy consistency but did not prove installed-package integrity.
- Fix applied: Canonicalized existing path ancestors before any write, confined every package/runtime/seed file after link resolution, rejected routes entering the bundle or escaping runtime, and validated the exact packaged file set and hashes against `RELEASE_MANIFEST.json` before seed initialization.
- Guardrail for next time: A release bootstrap must establish package integrity before deriving any runtime manifest, and path confinement must be tested with real platform link primitives—especially Windows junctions—not only `Path.is_symlink()`.
- Evidence paths: `core/gv_alpha0_ship_runtime.py`, `tests/gv_fs0_product/test_gv_alpha0_ship_runtime.py`, `tests/gv_fs0_product/test_gv_alpha0_release_package.py`, `release/gv-alpha0/README.md`.

## 2026-07-28 Round Entry (Hosted Evidence Must Not Dirty a Clean-Commit Build)
- Date: 2026-07-28
- Mistake or miss: The first hosted shipment run generated environment-custody evidence inside the checkout before invoking the release builder, so both Windows and Linux correctly failed the clean-tree package guard even though their full product suites passed.
- Root cause: Workflow evidence placement was treated as operationally neutral, but any checkout-local output changes the source state seen by a commit-bound builder.
- Fix applied: Routed custody JSON through GitHub `RUNNER_TEMP`, uploaded it from `${{ runner.temp }}`, and added a regression forbidding checkout-local custody output.
- Guardrail for next time: All pre-package CI evidence and logs must live under runner-temporary or artifact staging paths; the repository checkout must remain byte-identical to the candidate commit until package construction completes.
- Evidence paths: `.github/workflows/gv-fs0-product.yml`, `tests/gv_fs0_product/test_gv_alpha0_release_package.py`, hosted run `30343141406`, local focused suite `39/39`.

## 2026-07-28 Round Entry (Hosted Parity Must Be Bound to the Same Clean Artifact)
- Date: 2026-07-28
- Mistake or miss: Local clean-build evidence alone could have been reported as closure without proving that hosted Windows, hosted Linux, and an independent rebuild all emitted the same commit-bound archive.
- Root cause: Build success, fresh-machine smoke, and cross-platform byte identity are separate shipment claims even when they use the same package script.
- Fix applied: Required hosted Windows/Linux clean builds and extracted-venv smokes, exact hosted archive parity, then independently rebuilt `a88ed05` and matched SHA-256 `67f5b154182be5d9cecf050934a81b107a8d38e9ea072f0df565dd6b24fe2d57` before advancing to pilot.
- Guardrail for next time: Do not advance a packaged product to pilot until commit identity, clean tree state, artifact hash, extracted workflow smoke, and cross-platform parity all reconcile to one artifact record.
- Evidence paths: hosted run `30346381138`, `scripts/build_gv_alpha0_release.py`, `scripts/smoke_gv_alpha0_release.py`, `docs/phase_brief/gv-alpha0-ship-brief.md`.

## 2026-07-28 Round Entry (A Pilot Must Exercise the Real Packaged UI and Restart Boundary)
- Date: 2026-07-28
- Mistake or miss: An in-process AppTest or workflow helper could be overread as a pilot even though neither proves the packaged Streamlit server, browser controls, and persisted restart experience together.
- Root cause: Functional automation and operator experience share the same workflow but cross different runtime boundaries; a wrong confirmation phrase in the first browser attempt also showed that driver mistakes must be separated from product defects before assigning P0/P1.
- Fix applied: Served the exact clean `a88ed05` package, operated it through Chromium as `PILOT_BROWSER_OPERATOR_001`, confirmed the visible `CONFIRM_NO_POSITION` phrase, verified persisted `CASE_WORKSPACE_UI` certification, restarted the server against the same user-data root, and reopened certified-only in 4.435 seconds. No P0/P1 was found.
- Guardrail for next time: A release pilot must use the exact clean artifact through a real browser and include a process restart; classify a failure only after confirming the operator input matched the visible product contract.
- Evidence paths: clean artifact SHA-256 `67f5b154182be5d9cecf050934a81b107a8d38e9ea072f0df565dd6b24fe2d57`, `alpha_app.py`, `views/gv_alpha0_case_workspace.py`, temporary Chromium pilot record under the host temp directory, `docs/phase_brief/gv-alpha0-ship-brief.md`.

## 2026-07-29 Round Entry (Freeze the Stack, Not Every Implementation Detail)
- Date: 2026-07-29
- Mistake or miss: Repeated architecture-discovery rounds kept adding academically plausible edge cases and gates while legacy roadmaps exposed competing active sequences; implementation velocity risked falling behind conceptual completeness. The root checkout also appeared almost entirely deleted and reintroduced as untracked content, making it unsafe as authority.
- Root cause: Endgame completeness was conflated with immediate delivery authority, and horizontal data/strategy/risk topics were treated as serial product phases instead of parallel Build × Learn lanes behind one vertical portfolio path.
- Fix applied: Froze Slices 0–7 at contract and gate level, authorized implementation of Slices 0–2 only, moved deterministic replay immediately after the prospective micro-portfolio, separated portfolio scale from universe scale, defined B0–B6 parallel build lanes with shadow-only learning lanes, synchronized active docs, and performed the work only in the isolated Alpha release worktree.
- Guardrail for next time: Reopen a frozen boundary only when a completed slice exposes contradictory evidence, a P0/P1 custody/accounting/mandate/replay defect appears, the owner changes the mandate, or a legal/operational requirement changes. Model sophistication and hypothetical edge cases remain challengers and may not block the operating vertical.
- Evidence paths: `docs/architecture/godview_v2_frozen_build_learn_roadmap.md`, `docs/architecture/top_level_roadmap.md`, `PHASE_QUEUE.md`, `docs/phase_brief/gv-v2-frozen-build-learn-roadmap-brief.md`, `docs/context/planner_packet_current.md`, `docs/context/multi_stream_contract_current.md`, `docs/decision log.md`.

## 2026-07-29 Round Entry (Bank the Canon Before Branching the Implementation)
- Date: 2026-07-29
- Mistake or miss: The first handoff language told the next orchestrator to create Slice 0 directly from release-proof tip `93e7a55` even though the new roadmap canon existed only as an uncommitted docs diff.
- Root cause: Released ancestry and current planning authority were conflated. A clean historical base was treated as sufficient even when it did not contain the newly frozen contracts and gates.
- Fix applied: Published a next-orchestrator handover and corrected every active next-step surface to require a committed/pushed `ROADMAP_FREEZE_COMMIT` before creating the Slice 0 worktree.
- Guardrail for next time: Never branch implementation from an ancestry anchor until the governing spec, decision log, phase brief, and current context are banked in the selected base commit. Checkoutability of canon is a prerequisite for parallel execution.
- Evidence paths: `docs/handover/gv_v2_frozen_build_learn_roadmap_handover_20260729.md`, `docs/context/planner_packet_current.md`, `docs/context/bridge_contract_current.md`, `docs/archive/superseded-phase66-gv-canon-reset-0-brief.md`, `docs/decision log.md`.

## 2026-07-29 Round Entry (Authority Selection Must Be Explicit and Product Work Must Start at the User Loop)
- Date: 2026-07-29
- Mistake or miss: A structurally valid roadmap was called frozen before it was committed, a stale SAW retained a direct raw-base instruction, and a numeric Phase 66 workaround silently controlled current context. The first product gate was another contract catalogue even though the missing capability was a multi-security operating loop.
- Root cause: Documentation completeness, repository custody, context-selection mechanics, and product shipment were treated as one state. Named parallel lanes were also mistaken for a reason to create many branches before shared identity/event seams existed.
- Fix applied: Added fail-closed `docs/context/ACTIVE_BRIEF` selection; archived Phase 66; explicitly superseded contradictory evidence; recut canon reset into internal R0; made the micro-portfolio operator loop the first product slice; preserved released FS0; and grouped execution into three mergeable packages with minimum seams frozen first.
- Guardrail for next time: A roadmap is authority only when checkoutable from the implementation base. Active context must be explicitly pointed, not inferred from filenames. Governance work is not a product slice unless it changes a user-visible operating capability. Maximize independent executable work, not worker or branch count.
- Evidence paths: `scripts/build_context_packet.py`, `tests/test_build_context_packet.py`, `docs/context/ACTIVE_BRIEF`, `docs/phase_brief/phase0-gv-micro-portfolio-vertical-0-brief.md`, `docs/architecture/godview_v2_frozen_build_learn_roadmap.md`, `docs/saw_reports/saw_gv_v2_roadmap_custody_repair_20260729.md`.

## 2026-07-29 Round Entry (Integrate Through One Executable Seam, Not Compatibility Duplication)
- Date: 2026-07-29
- Mistake or miss: The three repair streams were individually green, but the shared vertical still duplicated strategy shape, order/fill construction, and book reduction. The persisted schema also retained a v1 label after incompatible fields changed.
- Root cause: Stream-local correctness was mistaken for product integration. Compatibility preservation at the shared seam would have left multiple authorities able to describe the same decision, execution, or accounting state.
- Fix applied: Banked S2/S3/S4 separately, made Strategy/Execution/Accounting the sole authorities, removed duplicate shared implementations, added the non-economic transition event to Accounting tolerance, bound certification to the reconciled V2 book and execution lineage, and bumped persisted bytes to workspace v2.
- Guardrail for next time: A parallel stream is complete only when the integrator can delete the superseded shared authority. Any incompatible persisted-shape change must change its schema identifier. A full-suite claim requires a declared, reproducible environment; borrowing an incomplete venv is evidence only for the subset it can execute.
- Evidence paths: `gv_portfolio_v0/vertical.py`, `gv_portfolio_v0/book.py`, `tests/gv_portfolio_v0/`, `docs/context/done_checklist_current.md`, `docs/saw_reports/saw_gv_micro_portfolio_v0_integration_20260729.md`.

## 2026-07-30 — Hash-bound fixtures and certification lineage

- A dependency lock can be complete while a full suite is still environmentally unclosed; distinguish package closure from tracked-data and generated-artifact custody.
- Any manifest that hashes repository text requires explicit cross-platform line-ending authority. `core.autocrlf=true` can make a clean checkout byte-invalid without making Git status dirty.
- Persisting a prior certification is insufficient. Reopen validation must verify its identity, recompute it from the exact pre-observation event prefix, bind the current certification to it, and bind both to immutable certification-record events.
- Product captions, symbols, benchmark labels, and status explanations are operator truth. If persisted, they must be derived or validated against canonical records rather than treated as harmless display fields.
- A valid event payload is not sufficient authority. Reopen validation must bind the event envelope source and instrument identities to the payload evidence and principal review; otherwise rehashing and recertification can legitimize a mislabeled event.
- A repository-relative manifest is only relocatable when the validator resolves the declared path against the same repository root used for the runtime artifact. Replacing an absolute string without changing comparison semantics preserves the defect.
- A live package path cannot be both G8 hash-green and V2-B0 intentional non-binding. If V2-B0 banks `SOURCE_PACKAGE_MANIFEST_BINDING_INVALID` on the MU candidate-card package, custody must restore the historical declared hash and **explicitly retire** the same-path G8 hash-match PASS from the custody gate (with a replacement truth test), not silently drop the node or "fix" the hash.

## 2026-07-30 Round Entry (Semantic Acceptance Must Dominate Phase Labels)

- Date: 2026-07-30
- Mistake or miss: Bounded, Portfolio Scale, Universe Scale, and Challenger were treated as completed product phases because their active briefs, tests, tags, and A/B/C packets passed. In reality the implementations repeated the same four-security economics through sessions and cells, prohibited genuine transitions, and exposed no later operator flow.
- Root cause: lower-level briefs silently weakened higher-level quantities and outcomes; reviewers proved the narrowed briefs with strong custody rigor but did not re-establish the verbatim frozen roadmap. Candidate-only regression success became psychologically close to product acceptance.
- Fix applied: preserved immutable terminals, corrected their classifications, created one canonical authority record, restored non-weakenable roadmap quantities, closed Limited Live, and opened one real ten-instrument transition slice. The candidate adds heterogeneous identities/evidence/theses, multi-position funding, SELL/REDUCE, explicit no-change, changed-why UI, persistence/reopen, replay, and correction lineage.
- Guardrail for next time: reviewer A must answer what new operator behavior exists, what materially distinct economic state is exercised, which exact original acceptance sentence is proven, and whether any quantity was weakened. Sessions, cells, runs, and slots never count as distinct instruments. Focused verification runs during implementation; full failset and independent A/B/C run once at the frozen terminal candidate.
- Evidence paths: `docs/context/gv_endgame_authority_current.md`, `docs/phase_brief/gv-operated-portfolio-10-transition-1r-brief.md`, `PHASE_QUEUE.md`, `gv_portfolio_v0/operated.py`, `gv_portfolio_v0/book.py`, `gv_portfolio_v0/execution.py`, `operated_portfolio_app.py`, `tests/gv_portfolio_v0/test_operated.py`.

## 2026-07-31 Round Entry (Projections and Stability Flags Are Not Authority)

- Date: 2026-07-31
- Mistake or miss: the operated candidate recorded deterministic selection, event-ledger trades, changed-why, and certification lineage, but execution independently read review targets; UI projections were only count/side checked; historical certification objects and a self-asserted stability boolean were trusted; persistence checked only the final parent link.
- Root cause: derived records were treated as parallel authoritative state instead of exact projections from decisions and immutable events, while lexical path locality was mistaken for canonical custody through every ancestor.
- Fix applied: selected funded IDs now drive execution; evidence ownership is instrument-specific; orders, fills, authority chains, observations, transition deltas, changed-why, books, and correction links are reconstructed or byte-validated from canonical state; every certification is replayed at its original event prefix; linked ancestors and Windows junctions are rejected before creation, replacement, and load; AppTest completes correction and fresh-process corrected reopen.
- Guardrail for next time: every persisted display or history object must name one upstream authority and be exactly reproducible from it; booleans cannot prove byte stability; path confinement must inspect and canonically resolve every existing ancestor; dependency custody must be scoped to the product acceptance surface rather than inherited from an unrelated monorepo environment.
- Evidence paths: `gv_portfolio_v0/operated.py`, `gv_portfolio_v0/operated_storage.py`, `views/gv_operated_portfolio_workspace.py`, `tests/gv_portfolio_v0/test_operated.py`, `tests/gv_portfolio_v0/test_operated_app.py`.

## 2026-07-31 Round Entry (Product CI Must Follow the Product Surface)

- Date: 2026-07-31
- Mistake or miss: after repairing the operated acceptance kernel, the next gate was incorrectly widened to regenerating hashes for a stale 119-package monorepo lock that includes unrelated broker and data stacks. Meanwhile the actual CI did not trigger on operated files and did not run operated tests.
- Root cause: repository-wide dependency governance was substituted for the original product acceptance, while hosted proof coverage was not checked against the new file surface.
- Fix applied: made `requirements-alpha.txt` the narrow operated-product dependency authority; proved Python 3.12.10, pytest 9.0.2, Streamlit 1.54.0 and `178/178` locally; added Windows/Linux operated-product CI with exact path triggers; ignored `.worktree-lifecycle/`.
- Guardrail for next time: derive environment and CI gates from the smallest executable product slice. Before naming an environment blocker, verify that the dependency file is actually required by the acceptance contract and that CI triggers on every new authoritative file.
- Evidence paths: `requirements-alpha.txt`, `.github/workflows/gv-operated-portfolio.yml`, `.gitignore`, `docs/context/planner_packet_current.md`, `tests/gv_portfolio_v0/test_operated_app.py`.

## 2026-07-31 Round Entry (Authority Tests Must Separate Ancestry from Active State)

- Date: 2026-07-31
- Mistake or miss: the complete full-suite comparison exposed two candidate-only FS0 failures because legacy tests treated accepted Slice 0 seam names, the old active slice, Replay 0 next gate, `39/100`, and obsolete root wording as one indivisible current roadmap contract. The operated workflow omitted the package entirely.
- Root cause: historical interface ancestry and active product authority were encoded in the same assertions, while CI ownership followed implementation paths rather than every authority surface consumed by the tests.
- Fix applied: added a clearly historical accepted-foundation roadmap section for the seam names; recut both FS0 tests around the operated phase, accepted Slice 0/Replay 0, `52/100`, unsafe root, and closed Limited Live; added the FS0 package and roadmap to operated workflow triggers and execution with its full tracked dependency set.
- Guardrail for next time: every authority test must label each assertion as historical ancestry, accepted foundation, or active state. Any workflow that changes an authority surface must trigger and execute every package that reads it, including the dependencies required by AppTests.
- Reviewer follow-up: `actions/checkout` on a pull-request event defaults to the synthetic merge ref, so printing `HEAD` is not exact-head proof. Pin the event head SHA, assert it before setup, and assert a clean tree. Also, under Bash/WSL, `2>nul` creates a real file named `nul`; use `/dev/null` rather than Windows device syntax.
- Evidence paths: `docs/architecture/top_level_roadmap.md`, `tests/gv_fs0_product/test_authority_chain.py`, `tests/gv_fs0_product/test_canonical_integrity_gate.py`, `.github/workflows/gv-operated-portfolio.yml`.

## 2026-08-01 Round Entry (A Background Test Process Must Prove Its Environment Before Producing Evidence)

- Date: 2026-08-01
- Mistake or miss: the first one-command full-suite rerun was launched through a detached process that did not preserve Windows `PATH`, `COMSPEC`, or `SystemRoot`. The first subprocess-using tests therefore failed to find Git or `cmd.exe`, creating 13 artificial FS0 failures even though the candidate bytes were unchanged.
- Root cause: process detachment was treated as operationally transparent. The evidence runner verified candidate SHA and cleanliness but did not verify the inherited shell/tool environment before pytest started.
- Fix applied: discarded the invalid XML; added a preflight receipt for exact SHA, tree, clean status, `PATH`, `COMSPEC`, `SystemRoot`, temp directory, Git executable, Python executable, and Python version; then reran the complete suite once. The corrected result was `2718` tests, `19` inherited failures, `0` errors, `16` skips, and `0` candidate-only failures.
- Guardrail for next time: every detached or background evidence process must fail before test execution unless repository identity, cleanliness, interpreter identity, temp path, shell, PATH, and required external tools are all proven in a retained receipt. Never classify failures from an environment-invalid run as candidate defects.
- Evidence paths: `.worktree-lifecycle/gv-operated-0d15e9c-terminal-evidence/full-suite-launch-receipt.txt`, `.worktree-lifecycle/gv-operated-0d15e9c-terminal-evidence/full-suite.xml`, `.worktree-lifecycle/gv-operated-0d15e9c-terminal-evidence/failset-comparison.json`, `docs/context/e2e_evidence/gv_operated_portfolio_terminal_20260801.md`.

## 2026-08-01 Round Entry (Terminal Closure Must Preserve the Tested Executable Tree)

- Date: 2026-08-01
- Mistake or miss: current-truth reconciliation after terminal review can silently create a second untested executable candidate if closure edits include tests, workflows, runtime, dependencies, or configuration.
- Root cause: phase closure documentation and executable certification were previously treated as one mutable commit surface.
- Fix applied: certified executable candidate `0d15e9c` first, required the closure commit to touch `docs/` only, compared every non-doc tree entry to the certified candidate, and allowed only fast-forward publication followed by a new immutable terminal tag.
- Guardrail for next time: terminal evidence binds to one executable commit. Closure may append documentation, but it must prove byte identity for every executable/non-doc path and must never amend, squash, merge-ref substitute, or rewrite the certified candidate.
- Evidence paths: `docs/context/e2e_evidence/gv_operated_portfolio_terminal_20260801.md`, `docs/saw_reports/saw_gv_operated_portfolio_terminal_20260801.md`, `docs/handover/gv_operated_portfolio_10_transition_1r_handover_20260801.md`.

## 2026-08-01 Round Entry (Genericization Earns Authority Only Through the Larger Product)

- Date: 2026-08-01
- Mistake or miss: the first Portfolio Scale proposal protected accepted source bytes by creating a parallel 25-security engine and storage path; during execution, authority and FS0 tests also initially encoded the accepted ten-security phase as permanently active. Test receipts were first directed through WSL-style paths that Windows Python did not externalize as intended, and chained large pytest responses repeatedly hit DevSpace HTTP 502.
- Root cause: historical custody, current architecture, active authority, and transport constraints were conflated. Permanent file identity was treated as safer than semantic regression, and test-output location was assumed portable across WSL and Windows Python.
- Fix applied: retained immutable candidate/closure/tag custody while evolving one shared engine, persistence implementation, app, and view; moved fixture state into declarative 10/25 scenarios; recut authority tests to distinguish accepted foundation from active phase; used Windows-native `%TEMP%` JUnit paths; split one logical gate into externally retained bounded runs.
- Guardrail for next time: genericization cannot be accepted before the new product runs through it; authority tests must separately assert historical custody, accepted foundations, and active state; evidence paths must be native to the executing interpreter; connector 502 runs are transport-invalid and never count as test results.
- Evidence paths: `gv_portfolio_v0/operated_scenarios.py`, `gv_portfolio_v0/operated.py`, `tests/gv_portfolio_v0/test_operated_25.py`, `tests/gv_fs0_product/test_authority_chain.py`, `tests/gv_fs0_product/test_canonical_integrity_gate.py`, `docs/context/e2e_evidence/gv_operated_portfolio_25_prefreeze_20260801.md`.

## 2026-08-01 Round Entry (Terminal Evidence Should Not Be Repeated When Closure Cannot Affect It)

- Date: 2026-08-01
- Mistake or miss: a terminal documentation pass can default to rerunning implementation, complete tests, hosted CI, failset comparison, and independent reviewers even when every product gate already binds to one immutable executable SHA.
- Root cause: evidence production was treated as a generic closure ritual rather than a response to a specific decision risk. This adds time and can create conflicting receipts without improving the terminal decision.
- Fix applied: froze `7ce85c4` as the sole executable candidate, reconciled its existing exact-head Windows/Linux, byte-parity, zero-candidate-only, fresh-process, and Reviewer A/B/C evidence, and limited closure to documentation/generated context plus custody publication.
- Guardrail for next time: rerun a terminal gate only when the proposed closure or successor changes bytes that the gate can observe—production, tests, workflows, dependencies, or executable configuration. Otherwise prove byte identity, publish once by fast-forward, tag, and stop.
- Evidence paths: `docs/context/e2e_evidence/gv_operated_portfolio_25_1_terminal_20260801.md`, `docs/saw_reports/saw_gv_operated_portfolio_25_1_terminal_20260801.md`, `docs/handover/phase_gv_operated_portfolio_25_1_handover.md`.
