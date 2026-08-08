# AOV-0 run_4 Dual-Role Authority + Direct SOFR — SAW Receipt

Mode: `CLOSURE_REPORT`
Date: 2026-08-07
RoundID: `ROUND-20260807-AOV0-RUN4-DUAL-ROLE-SOFR`
ScopeID: `AOV0-RUN4-DUAL-ROLE-FOUR-SOURCE-CUT-V1`
Branch: `codex/pit-source-authority-1`
Working authority: valid DevSpace worktree; broken root checkout not repaired

SAW Verdict: BLOCK

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: inherited active AOV-0 first-real-seal gate | Domains: Product, Data Provenance, Quant Research, Software Engineering, Governance

## Intent

Collapse the redundant company-screen dependency without compatibility, admit direct post-gate NY Fed SOFR, and leave the real first-seal path blocked only on genuine Capital IQ primary-security identity and completed post-close market bytes.

## Implementer pass

- Removed active `screen_source`, `ciq_screen_universe`, screen-file, and screen-retrieval-time dependencies rather than aliasing them.
- Made `run_4.xlsx` the sole frozen company-level raw object with receipt roles `COMPANY_UNIVERSE` and `QUARTERLY_FUNDAMENTALS`.
- Recut `aov0_ciq_decision_cut_v1` and first-seal validation to exactly four source receipts: quarterly fundamentals/universe, primary-security master, primary-security market data, and direct NY Fed SOFR.
- Regenerated the real `run_4` intermediate panel/state and receipt.
- Admitted real direct NY Fed SOFR after the 15:00 America/New_York gate and mechanically reverified raw/output hashes.
- Synchronized current product/spec/context/checklist/phase/decision/lesson/notes authority surfaces.
- No compatibility fallback, real CIQ market admission, real seal, commit, push, outcome opening, or live-capital action occurred.

## Acceptance checks

| Check | Result |
|---|---|
| CHK-01 scope remains the first-real-seal data gate; no provider programme, UI, optimizer, broker, or compatibility widening | PASS |
| CHK-02 `run_4.xlsx` remains exact raw SHA-256 `17f356e47c9e3ecf9600ad21db153338f4941272e0a1ffb9fd7b872c6636f056`, 215,249 bytes, 109 entities | PASS |
| CHK-03 `run_4` receipt carries both `COMPANY_UNIVERSE` and `QUARTERLY_FUNDAMENTALS`; `run_2` is historical evidence only and absent from active AOV code/test/cut blockers | PASS |
| CHK-04 active decision cut requires exactly four source receipts and retains contract/universe/input hash, chronology, asset-set, and primitive-vs-P&L return reconciliation | PASS |
| CHK-05 regenerated fundamentals remain 1,203 absolute-quarter rows and 109 current states with 56 complete / 52 partial / 1 no-absolute-history | PASS |
| CHK-06 full AOV regression | PASS — `59/59` |
| CHK-07 ZERO-COMPAT | PASS — `0/0/0/0/0/0/0` |
| CHK-08 direct NY Fed SOFR admission occurred after 15:00 ET; raw/output hashes mechanically reverify and latest effective date is 2026-08-06 | PASS |
| CHK-09 real CLI gate now reports only missing CIQ primary-security/market inputs; no `run_2` timestamp or SOFR blocker remains | PASS |
| CHK-10 context generation/validation and active docs agree on four-source authority and admitted SOFR | PASS |
| CHK-11 selected `py_compile`, `pip check`, and `git diff --check` | PASS |
| CHK-12 real first seal remains fail-closed with `prospective_clock_started=false`, `financial_alpha_evidence=0`; no commit/push/live action | PASS |
| CHK-13 independent terminal reviewer on exact recut candidate | BLOCKED — review remained pending through expiry; both allowed post-expiry status attempts returned upstream 502 and no findings were returned |

ChecksTotal: 13
ChecksPassed: 12
ChecksFailed: 1

## Reviewer capacity / ownership

A bounded independent PRODUCT review was launched against exact candidate/evidence manifest digests. The retained review remained `pending` through its expiry window; the first post-expiry status call returned upstream HTTP 502 and the one retry returned the same upstream 502. No reviewer findings or PASS result were returned.

Reviewer A/B/C independence therefore cannot be claimed for this exact recut. Local deterministic evidence is not promoted to independent review. This is a closure-evidence blocker only; it does not justify missing the already-scheduled post-16:00 prospective data cut.

## Findings

| Severity | Impact | Fix / disposition | Owner | Status |
|---|---|---|---|---|
| Blocking for terminal SAW PASS | No independent terminal review result exists for the exact recut bytes. | Re-run independent terminal review against the exact final bytes when reviewer service is available. | Reviewer lane | Open external |
| Blocking for first real seal, not local implementation | Real Capital IQ primary Security/Trading Item mapping and completed post-16:00 ET daily total-return/price/volume export are absent. | Admit only the real provider exports with actual retrieval times; then run CIQ builder → cut → seal → exact reopen. | Data / Operator | Open time/provider gate |
| Material, closed | Separate `run_2` screen authority created a redundant retrieval-time dependency after `run_4` fully owned the same frozen company universe. | Destructively removed the active screen role and made `run_4` the sole company-level raw authority. | Data/AOV | Closed |
| Material, closed | Direct SOFR had been time-gated and absent before 15:00 ET. | Direct NY Fed retrieval admitted at `2026-08-07T19:00:08.894288Z`; hashes reverified. | Data/AOV | Closed |

## Scope split summary

In-scope actions are closed locally except independent review availability: run_4 authority collapse, four-source cut, real SOFR admission, regression/static/context validation. The provider/time-gated CIQ mapping and completed market export are the explicit next operational dependency, not an engineering defect.

Inherited out-of-scope items remain unchanged: Episode-2 hosted/publication custody, matured prospective evidence, model mutation, broker/live capital, and Limited Live.

## Validation / evidence

- Focused recut matrix: `42/42 PASS`.
- Full AOV: `59/59 PASS`.
- ZERO-COMPAT: seven counters all zero.
- `scripts/build_context_packet.py` and `--validate`: PASS.
- selected `py_compile`: PASS.
- `pip check`: `No broken requirements found`.
- `git diff --check`: PASS.
- Real `run_4` raw SHA-256: `17f356e47c9e3ecf9600ad21db153338f4941272e0a1ffb9fd7b872c6636f056`.
- Real SOFR retrieval: `2026-08-07T19:00:08.894288Z`; raw SHA-256 `445ca1ae93a7ae904681716d8e37088fab905ae4f74f32fc2619a459918d54cc`; Parquet SHA-256 `ed75219416a524f17cb3e29b9e4fadff2dcfa1d12a8368d752007aac779c4e5e`; raw/output re-hash match PASS.
- Real CLI state: market builder `BLOCKED_MISSING_CIQ_RAW_INPUTS_OR_RETRIEVAL_TIMES`; decision cut missing only risky Parquets + security/market receipts; first seal lists SOFR as present and remains `BLOCKED_MISSING_ADMITTED_INPUTS` with financial-alpha evidence `0`.

## Document Changes Showing

| Path group | Change summary | Reviewer status |
|---|---|---|
| `research/aov0/contracts.py`, `research/aov0/ciq_fundamentals.py` | remove active screen source; make run_4 sole company authority | local PASS; independent review unavailable |
| `scripts/aov0_build_ciq_fundamentals.py`, `scripts/aov0_build_decision_cut.py`, `scripts/aov0_first_seal.py` | dual-role receipt + exact four-source cut/seal validation | local PASS; independent review unavailable |
| `tests/aov0/*` touched in recut | no-screen/four-source regressions and end-to-end synthetic seal path | 59/59 PASS |
| `data/aov0/source_receipts/ciq_quarterly_fundamentals_run_4_20260807.json` | dual-role real run_4 receipt | raw hash/counts verified |
| `data/aov0/current/official_sofr.parquet`, `data/aov0/source_receipts/nyfed_sofr_current.json` | real direct post-15:00 NY Fed SOFR admission | raw/output hashes verified |
| PRD / PRODUCT_SPEC / README / phase / checklist / current context / spec / decision / notes / lessons | current authority synchronized to run_4-only company source + admitted SOFR | context/static PASS |

## Document Sorting

Canonical active truth remains `docs/context/gv_endgame_authority_current.md` → `docs/context/planner_packet_current.md` / `bridge_contract_current.md` / `done_checklist_current.md` → active phase brief/checklist/spec → PRD/PRODUCT_SPEC/README → decision/notes/lessons → this terminal SAW receipt.

## Open Risks

Open Risks: independent reviewer service unavailable for the exact recut; real CIQ primary Security/Trading mapping and completed post-16:00 ET market export remain external; prospective clock is still false and financial-alpha evidence remains zero; Episode-2 external custody remains separate.

## Next action

Next action: after 16:00 America/New_York, admit only real CIQ Security/Trading mapping and completed daily total-return/price/volume bytes with actual retrieval times; run `aov0_build_ciq_market.py`, build the four-source decision cut with first execution `2026-08-10T13:30:00Z`, run the first real seal, and exact-reopen immediately. If either real provider export is absent or fails identity/timing/return reconciliation, stop without substitution.

ClosurePacket: RoundID=ROUND-20260807-AOV0-RUN4-DUAL-ROLE-SOFR; ScopeID=AOV0-RUN4-DUAL-ROLE-FOUR-SOURCE-CUT-V1; ChecksTotal=13; ChecksPassed=12; ChecksFailed=1; Verdict=BLOCK; OpenRisks=independent reviewer unavailable on exact recut bytes | real CIQ security and post-close market exports remain external; NextAction=after 16:00 ET admit only real CIQ security mapping and completed market bytes then build cut seal exact reopen and rerun independent review when available
ClosureValidation: PASS
SAWBlockValidation: PASS
