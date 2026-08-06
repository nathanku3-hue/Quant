# PAIR-DECISION-SERIES-1 — Episode 2 Brief

> Supersession: this brief remains the immutable Episode-2 implementation/custody record. It no longer selects Episode 3 as the next product milestone. After Episode-2 closeout, `docs/phase_brief/alpha-organism-vertical-0-brief.md` controls the next product gate.

Date: 2026-08-06
Branch: `codex/pit-source-authority-1`
Base: `ab258c3b0f1e734a1d0c9d4d8c7f529dfb2e0cbb` (episode 1 release-ready tip)
Status: `EPISODE 2 LOCALLY IMMUTABLE AT 39f7be3; EXACT LOCAL 115/115 PASS; EXTERNAL AUDIT/PUBLICATION PENDING; LIVE CLOSED`
Canonical product maturity: `70/100` (operability, custody, and replay only)
Portfolio-alpha evidence: `0`
Limited Live: `CLOSED; NOT AUTHORIZED`

## Product result

Temporal pair series under one profile:

```text
episode 1 sealed cash/abstention at common cut T1
→ later common Cboe BZX MU/NVDA cut T2
→ same banked MU + NVDA subject packages
→ same comparator / cost / policy / horizon / source contract
→ source-derived packets at T2
→ real MU / real NVDA / cash episode 2
→ calculation-only preview
→ explicit cash/abstention confirmation or reject-all
→ atomic persistence
→ certification lineage
→ exact fresh-process reopen of the two-episode ledger
```

Episode-1 hardcoding is removed from the source adapter, prospective operation, scenario profile, and Command Center. The next open registered episode is selected by sealed count.

Both subject packages remain `ABSTAIN / NO_POSITION`. Episode 2 confirmation retains certified cash, creates no orders or fills, charges no cost, and preserves unexplained residual `0`.

## Source contract (unchanged family)

- Episode 1 capture: `data/gv_pair_decision_series/mu_nvda_episode_1/common_market_source_capture.json`.
- Episode 2 capture: `data/gv_pair_decision_series/mu_nvda_episode_2/common_market_source_capture.json`.
- Parser: `GV_CBOE_BZX_SYMBOL_XML_ROW` version `1.0.0`.
- Source contract: `CBOE_BZX_TWO_ROW_CAPTURE_V1`.
- Episode 2 source timestamp: `2026-08-06T11:52:08.000000Z`.
- Episode 2 retrieval/knowledge time: banked capture `retrieval_knowledge_at`.
- Episode 2 decision timestamp: first whole minute strictly after knowledge (`2026-08-06T12:00:00.000000Z`).
- Every episode binds `decision_cut_knowledge_at == capture.retrieval_knowledge_at`; source time cannot follow retrieval time.
- Every `n > 1` cut must be later than episode `n-1` and carry a distinct `decision_cut_id`.
- `outcome_open_not_before` is mechanically equal to knowledge time plus the sealed minimum calendar-day horizon.
- Command Center still cannot author price, source, permission, parser, row, receipt, or market timestamps.

## Series invariants preserved from episode 1

- `decision_series_id = PAIR_DECISION_SERIES_1`
- `comparator_spec`
- `cost_model_id = GV_PAPER_FIXED_FEE_USD_2_PER_ORDER_V1`
- `decision_policy_version = PAIR_BANKED_EVIDENCE_ABSTAIN_OR_CASH_V1`
- `source_contract_version = CBOE_BZX_TWO_ROW_CAPTURE_V1`
- `outcome_horizon_spec` (30-calendar-day common-source-cut rule)
- banked-only MU and NVDA subject evidence paths/hashes
- `outcome_data_loaded = false` and `outcome_status = SEALED_NOT_OPENED`

## Acceptance

- [x] Episode 1 remains sealable, certified, and exactly reopenable.
- [x] Episode 2 uses a later distinct common market cut.
- [x] Series invariants fail closed on drift.
- [x] Adjacent-cut chronology, strict decision-after-knowledge, capture/contract knowledge equality, and outcome-open derivation fail closed.
- [x] Manual market-authority controls remain deleted without compatibility.
- [x] Synthetic `MERID` remains absent from the acceptance path.
- [x] Preview is mutation-free for each open episode.
- [x] Confirmation and reject-all preserve cash, costs, residual, persistence, and certification.
- [x] Two-episode ledger reconstructs byte-exactly in a fresh process.
- [ ] One independent cross-domain audit against an immutable candidate SHA.
- [ ] Candidate branch push and hosted exact-head checks.
- [ ] Owner-authorized fast-forward/protected-branch publication when sought.

## Forbidden scope

No new portfolio engine, provider framework, compatibility path, synthetic acceptance security, optimizer, broker, advice, live capital, score uplift, outcome opening, alpha claim, or 5/25-security expansion.

## What Was Done

- Sealed episode 1 for real MU / real NVDA / cash with forward contracts and exact reopen.
- Removed episode-1 hardcoding from `market_source_adapter.py`, `prospective.py`, `operated_scenarios.py`, and `command_center.py`.
- Banked a later distinct common Cboe BZX market cut and source-derived packets for episode 2 under unchanged series contracts.
- Proved two-episode mutation-free preview, cash/abstention confirmation, residual `0`, and exact multi-episode reconstruction.
- Closed three Episode-3-facing temporal gaps: immediate-prior ordering, exact-minute decision timing, and horizon-derived outcome opening.
- Exact candidate `39f7be3894623c095994066b8f0ea2895b968643` reconstructs through `git archive` and passes the exact selected `115/115` matrix; the earlier `142/142` count is superseded. The inherited `websockets.legacy` warning remains non-blocking.

## What Is Locked

- Active product gate is `PAIR-DECISION-SERIES-1 — EPISODE 2`.
- Episode 1 remains release-ready at `ab258c3` with hosted Windows/Ubuntu exact-head proof and local `110/110`.
- Episode 2 local immutable candidate is `39f7be3894623c095994066b8f0ea2895b968643`; exact local archived-byte matrix passes `115/115`. Push, hosted proof, and independent audit remain pending external custody.
- Published main `9af5259` and `pit-alpha-authority-cut-1-terminal` remain immutable prior receipts.
- `dashboard.py` / Command Center remains the sole operator product.
- Series uses real MU, real NVDA, and cash only; no synthetic companion is accepted.
- Subject evidence is banked-only; outcomes remain sealed and unopened until preregistered rules permit.
- Canonical product maturity remains `70/100`; portfolio-alpha evidence remains `0`.
- Limited Live remains closed.

## What Is Next

- Local freeze and exact matrix are complete at `39f7be3`; run push/hosted matrix plus independent audit only under separate external authority.
- Publish only through owner-authorized fast-forward and tag equality.
- Preserve the episode registry as prospective-custody substrate; do not open outcomes before eligibility.
- Transfer the active product gate to `ALPHA-ORGANISM-VERTICAL-0`; Episode 3 is removed from the critical path.

## First Command

`E:\code\quant\tmp\gv25env\Scripts\python.exe -m pytest -q tests/test_gv_immutable_market_packet.py tests/test_gv_pit_transaction.py tests/test_gv_pit_operated_capital.py tests/test_gv_pit_operated_rotation.py tests/test_dash_1_page_registry_shell.py tests/gv_portfolio_v0/test_operated.py tests/gv_portfolio_v0/test_operated_25.py tests/gv_portfolio_v0/test_prospective.py tests/gv_portfolio_v0/test_real_evidence_mu.py tests/gv_portfolio_v0/test_same_evidence_shadow.py`
