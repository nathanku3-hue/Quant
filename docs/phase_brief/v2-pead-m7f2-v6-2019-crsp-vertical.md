# M7F2-v6-final 2019 CRSP Outcome-Envelope Vertical

Mode: `EXECUTION_PACKET`  
RoundID: `ROUND-20260712-M7F2-V6-FINAL`  
ScopeID: `M7F2_V6_FINAL_2019_OUTCOME_ENVELOPE`  
Branch: `c0x/m7f0-v4`  
Implementation: `m7f2-v6-final`  
Supersedes: `m7f1-v5.2-final` (no compatibility path)

## Purpose

Hard-replace the v5.2 residual BLOCK with a commit-bound diagnostic package:

1. Exclude pre-entry delists **before** breadth/Q5 and rerank.
2. Bridge only blank, post-entry, one-session RET gaps when adjacent abs(PRC)>0 and next RET prove continuity.
3. Emit **strict_curve_status=BLOCKED** plus neutral carry-to-cash and −100% write-down sensitivity curves with per-event attribution for residual ambiguities.
4. Correct map-selection metadata (`used_for_selection=true` for identity).

## Semantic locks

| Lock | Rule |
|------|------|
| Pre-entry delist | `DLSTCD>=200` on any panel session **strictly before entry** → exclude before breadth/Q5; Q5 reranks on survivors. Structural only — **no event-id policy in production code** (ids only in tests). |
| Bridge | Blank RET only (not B/C/S/…); post-entry; one session; adjacent abs(PRC)>0 on prev+next; next RET finite numeric; gap day **r=0** (no invented return). |
| Envelope | Residual ambiguities → diagnostic package: `strict_block` + `neutral_carry_to_cash` + `write_down_100pct`. Neutral carry is **not** a justified finite upper bound. |
| Map | Future-informed identity map is selection input; `used_for_selection=true`; not a return-window gate. |

## Filter order

1. unique_permno_map  
2. assign_formation_entry_source_wide_spine_only_no_return_filter  
3. dedup_one_event_per_formation_date_permno  
4. pre_q5_prior20_observability_tradability_gate  
5. **exclude_pre_entry_delist_before_breadth_q5**  
6. formation_breadth_distinct_permno_ge_50  
7. deterministic_q5_rerank  
8. suppress_later_event_on_entry_overlap  
9. resolve_selected_windows_bridge_blank_one_day  
10. outcome_envelope_if_residual_ambiguous  
11. equal_weight_active_slots_incl_cash  

## Claim ceiling

- Flagged research only; not alpha; not tradable; `m6b_data_contract_ready=false`
- Link: non-PIT snapshot CUSIP8; research validity ceiling ~30
- Score: diagnostic package target **70–74**; research validity stays ~30; current baseline until close **60**
- SAW may **PASS** for completed diagnostic scope while `strict_curve_status=BLOCKED`

## Forbidden

- Strict readiness flip; alpha/tradable; multi-year expansion; as-of/historical-link claim  
- UI/strategy promotion; WRDS login  
- Event-id allowlists in production policy  
- Dual-run / compatibility path with v5.2 selection  
- Claiming neutral carry as a justified upper bound  
- Promoting sensitivity curves as primary PASS  

## Commit protocol

| Commit | Contents |
|--------|----------|
| A | code + tests + this brief only; clean worktree |
| B | evidence JSON, manifests, **all seven** truth surfaces (after rerun from A) |
| C | full independent Reviewer A/B/C + SAW (`PASS`/`BLOCK` only), pinned to B |

## Artifacts

- Script: `scripts/pead_m7f2_v6_2019_crsp_vertical.py`
- Tests: `tests/test_pead_m7f2_v6_2019_crsp_vertical.py`
- Evidence: `docs/context/e2e_evidence/pead_m7f2_v6_2019_crsp_vertical.json`
- Sensitivity: `data/processed/pead_m7f2_v6_2019_daily_returns_{neutral_carry_to_cash,write_down_100pct}.parquet`
