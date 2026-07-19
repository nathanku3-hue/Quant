# Reviewer A — GV-E0A-OPERABLE Candidate C2 Strategy and Regression

Mode: `ADVISORY_REVIEW`  
RoundID: `ROUND-20260719-GV-E0A-OPERABLE-CANDIDATE-C2-REVIEW-A`  
ScopeID: `GV_E0A_OPERABLE_CANDIDATE_C2_REVIEWER_A_STRATEGY_REGRESSION`  
Hierarchy Confirmation: Approved | Session: current-thread | Trigger: inherited SAW reviewer pass (SMALL CHANGE) | Domains: Strategy correctness and regression risks | FallbackSource: owner E0A operable candidate C2 pin + `docs/phase_brief/gv-e0a-operable-brief.md`

Reviewer role: strategy correctness and regression risks only.  
Reviewer posture: independent, read-only. No edits outside this report path, no commit, no push, no providers.

Worktree: `C:/Users/Lenovo/.devspace/worktrees/Quant-e0a-operable-fix`  
ReviewedCommit (immutable pin): `446ac6d8162d62c794aaa5a93530a4ab6cf48231`  
Transport lineage: `490a234` (F1C substrate) → `45f9f96` (Transport C operable vertical) → `446ac6d` (C2 filelock AppTest dep)  
Branch: `codex/gv-e0a-operable`

Hosted evidence (banked, not re-run here): GitHub Actions GV-FS0 Product run `29655802878` PASS; Ubuntu product-proof PASS; Windows product-proof PASS; Windows/Linux byte parity PASS.

## Verdict

**PASS.** No Critical or High strategy/regression findings on exact candidate C2 (`446ac6d`).

## Must-verify checklist

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Research decision hash includes subject MU, module G_supply, custody hashes, claim boundary | **PASS** | `core/gv_e0a_operable.py` `_research_decision_preimage` hashes via `domain_hash("GV-E0A:RESEARCH_DECISION:V1", …)`: `subject="MU"`, `module="G_supply"`, `research_action="HOLD_FOR_EVIDENCE"`, `portfolio_action="NO_POSITION"`, four exact `custody_hashes` from `E0_CUSTODY_SHA256`, `alpha_claim=False`, and full `CLAIM_BOUNDARY` text. Callers cannot inject custody hashes; publication always re-verifies disk bytes. Tests pin hash `b4694a69bd1bc35a0d97a839ad47b66b517da1bd0f4abccd56bacca22d9e8e38` (`tests/gv_fs0_product/test_e0a_operable.py`). |
| 2 | Certified decision rationale binds research hash (not free-text only) | **PASS** | `DecisionEnvelope.rationale_ref` is exactly `E0A:RD:<research_decision_hash>` (`RATIONALE_REF_PREFIX` + hash). `build_e0a_decision` rejects non-prefix refs. `_assert_certified_binds_research` enforces decision_id, NO_POSITION action, rationale_ref equality, and prefix↔hash consistency before cert/publish return. Presentation row `Rationale` is that same bound ref. Expected: `E0A:RD:b4694a69bd1bc35a0d97a839ad47b66b517da1bd0f4abccd56bacca22d9e8e38`. HOLD_FOR_EVIDENCE maps only to paper NO_POSITION (zero shares, NAV 1000). |
| 3 | Default UI is single current decision; F1C dual bundle not default authority | **PASS** | `dashboard.py::_render_portfolio_allocation_page` sole authority call is `render_gv_fs0_current_decision(st)`; caption states one active certified decision and F1C dual-role as evidence-only; fail-closed error path never falls back to dual bundle. Adapter `render_gv_fs0_current_decision` loads one current file; `render_gv_fs0_certified_bundle` remains evidence-only (not imported by dashboard). AST test `test_dashboard_default_path_is_single_current_not_dual_bundle` forbids dual-bundle import/call. AppTest expects one subheader `… — NO_POSITION` and `len(app.table)==1`. |
| 4 | Forbidden: alpha/FS1/provider/broker paths not introduced | **PASS** | E0A vertical modules (`core/gv_e0a_operable.py`, `scripts/publish_gv_e0a_current.py`, `views/gv_fs0_portfolio_adapter.py` current path) contain no yfinance/provider/broker/FS1/order paths. Research payload forces `alpha_claim=False` and claim boundary forbids alpha/investability/tradability. Active docs list FORBIDDEN = providers, real prices, FS1 batch, PEAD, alpha, broker, dual-authority UI. Frozen F1C dual-fixture substrate retained as non-authority evidence only. |
| 5 | Score remains 39 ceiling language if present in active docs | **PASS** | Active canon keeps `SHIPPED_PRODUCT_SCORE = 39/100` (owner ceiling; no alpha) with stage-only `FUNCTIONAL_STAGE = CERTIFIED_SINGLE_DECISION_OPERABLE` and explicit no-uplift rule in `PRD.md`, `PRODUCT_SPEC.md`, `README.md`, `docs/architecture/top_level_roadmap.md`, `docs/phase_brief/gv-e0a-operable-brief.md`, bridge/planner/observability packets. No active claim of 40+ score. |

## Strategy correctness notes

1. **Authority chain (E0A)**  
   frozen MU `G_supply` custody (4 exact SHA-256 files) → hash-addressed research decision (`HOLD_FOR_EVIDENCE`) → paper `DecisionEnvelope` (`NO_POSITION`, `DECISION_E0A_HOLD_FOR_EVIDENCE_1`) → book/cert → atomic current publication → single default Streamlit decision. Adapter remains presentation-only (no accounting/verifier/publish).

2. **Research hash preimage integrity**  
   Preimage excludes circular self-reference to `research_decision_hash`. Custody set and per-file digests are re-checked against the frozen map before hashing. Deep-frozen return prevents mutation of authority fields.

3. **HOLD_FOR_EVIDENCE → NO_POSITION**  
   Research action and portfolio action are distinct and explicit; mapping is enforced in constants, book builder (`build_no_position_source_fixture` + E0A decision builder), certification assertion, and UI caption. No OPEN economics introduced on the E0A current path.

4. **Rationale binding vs free text**  
   Prior F1A/F1B style free-text refs (`RATIONALE:NO_POSITION_1`) are not used for E0A. Certified/current product authority uses the hash-bound `E0A:RD:…` form only; production publish rejects caller-injected certified results and custody hashes.

5. **Default vs substrate**  
   F1C permanent two-role bundle at `data/gv_fs0/gv_fs0_certified_bundle.json` remains banked evidence substrate. Default product authority is `data/gv_fs0/gv_fs0_current_decision.json` (tracked identity pinned by product tests). Dual-authority compatibility UI is not the default path.

6. **Regression posture**  
   Candidate C2 (`446ac6d`) is Transport C (`45f9f96`) plus filelock dep for hosted AppTests; strategy semantics of the operable vertical are unchanged by the dep-only C2 commit. Hosted product-proof + byte parity banked on this lineage.

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| None | No in-scope strategy or claim-boundary defect on candidate C2 | None | Reviewer A | Closed |
| Low | Live focused pytest not re-executed inside this Reviewer A session | Hosted GV-FS0 Product `29655802878` already banked PASS; optional local reconfirm by Reviewer B/C: `.venv\Scripts\python -m pytest tests/gv_fs0_product/test_e0a_operable.py tests/gv_fs0_product/test_e0a_streamlit_apptest.py -q` on exact pin | Reviewer B/C or SAW reconcile | Residual evidence gap, not strategy defect |

## Ownership statement

Reviewer A is independent of implementer ownership for candidate C2, used the pinned worktree with branch `codex/gv-e0a-operable` at exact `446ac6d8162d62c794aaa5a93530a4ab6cf48231` (verified via `E:/Code/Quant/.git/refs/heads/codex/gv-e0a-operable` and worktree `logs/HEAD`), and performed read-only strategy/regression verification only. No provider, PEAD, FS1, alpha promotion, broker, dual-authority UI, score uplift, commit, or push.

## NextAction

Reconcile with Reviewer B and Reviewer C on exact pin `446ac6d8162d62c794aaa5a93530a4ab6cf48231`. Preserve sole active gate **GV-E0A-OPERABLE**, score **39/100**, and do not open FS1 / providers / dual-authority default UI.

## ClosurePacket

```
ClosurePacket: RoundID=ROUND-20260719-GV-E0A-OPERABLE-CANDIDATE-C2-REVIEW-A; ScopeID=GV_E0A_OPERABLE_CANDIDATE_C2_REVIEWER_A_STRATEGY_REGRESSION; ChecksTotal=5; ChecksPassed=5; ChecksFailed=0; Verdict=PASS; OpenRisks=live_pytest_not_rerun_in_A_session; NextAction=reconcile_with_reviewers_B_C_on_446ac6d_preserve_score_39_no_fs1
```

SAW Verdict: **PASS**
