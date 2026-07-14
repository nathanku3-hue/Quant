# SAW Report — M7F3-v7 SELF_FINANCING_PORTFOLIO_TRUTH

RoundID: `ROUND-20260712-M7F3-V7-SELF-FINANCING`  
ScopeID: `M7F3_V7_SELF_FINANCING_PORTFOLIO_TRUTH`  
Mode: `CLOSURE_REPORT`  
Branch: `c0x/m7f0-v4`

## SAW Verdict: PASS

Mechanically correct self-financing diagnostic package complete. `strict_curve_status=BLOCKED` by residual envelope design. Score path ~70–73 diagnostic; research validity ceiling remains ~30. Does not flip readiness or promote primary curve.

## Hierarchy Confirmation:

Approved | Session | Trigger: M7F3-v7 owner GO with deltas | Domains: Data, Research (flagged), Docs/Ops

## Ownership Check

- Implementer: parent execution agent (Commit A code + Commit B evidence)
- Reviewer A: strategy correctness — **PASS** (agent `019f561a-e587-76e2-834c-62214472c5a1`)
- Reviewer B: runtime/ops — **PASS** (agent `019f561a-e58c-7da2-841b-f3d9d08c97bd`)
- Reviewer C: data integrity — **PASS** (agent `019f561a-e590-7b81-81c8-f31e1df0e051`)
- Implementer ≠ reviewers: confirmed (three distinct subagent IDs)

## Commit pins

| Commit | Role | SHA |
|--------|------|-----|
| A | code + tests + brief; v6 CLI retired | `bae1f65609b723cc6462d9bbd1967340a0cb3310` |
| B | evidence JSON + manifests only (no seven-surface reconcile) | `b5c66bc740926fc51294107a8951c2993400203a` |
| C | this SAW + seven truth surfaces | (this commit) |

Evidence `implementation_identity.commit` = **A**.

## Findings

| Severity | Impact | Fix | Owner | Status |
|----------|--------|-----|-------|--------|
| High (accepted residual) | 4/2448 windows outcome-ambiguous | Envelope legs + Shapley only | Research | Open (by design) |
| Medium | Snapshot non-PIT ceiling ~30 | Separate as-of link | Data | Accepted ceiling |
| Low | stderr still prints `M7F2_BLOCKED:` on v7 path | Rename to `M7F3_BLOCKED:` | Implementer | Open non-blocking |
| Info | Neutral carry not finite upper bound | Named in evidence | Research | Done |

## Reviewer A — Strategy: PASS

Daily sequence, bridge≠selection, dead write-down, equity-only turnover, Shapley sum-to-gap, first-bad residual metric, claim ceiling, no event-id policy, v6 retired.

## Reviewer B — Runtime: PASS

Atomic writes, map rebuild, detached proof gate, identity→A, no readiness flip, v6 exit 2, legs+manifests, no CCM/WRDS/UI.

## Reviewer C — Data integrity: PASS

2448/2444/4/2; first-bad sum 0.007208; Shapley 16 states err≈0 both legs; turnovers differ; commit A pin; pre_entry_excluded=12; no CCM.

## Document Changes Showing

| Path | Change | Reviewer |
|------|--------|----------|
| `scripts/pead_m7f3_v7_2019_crsp_vertical.py` | self-financing engine | A/B/C PASS |
| `scripts/pead_m7f2_v6_2019_crsp_vertical.py` | CLI retired exit 2 | B PASS |
| `tests/test_pead_m7f3_v7_2019_crsp_vertical.py` | 24 unit tests | A/C PASS |
| Evidence + manifests | DIAGNOSTIC_COMPLETE | B/C PASS |
| Seven truth surfaces | Commit C reconcile | Ops |
| This SAW | terminal reconciliation | — |

## Evidence

- Unit tests: 24/24 PASS (parent)
- Full run: DIAGNOSTIC_COMPLETE; strict_curve_status=BLOCKED
- Selected 2448; ok 2444; invalid 4; bridged 2; pre_entry_excluded 12
- selected_event_set_sha256 `caeccc642e5d052b211cc5ecfc335bf4f63d0fd7d63018a6b40c5d6965ad2e6d`
- summed_first_bad_date_target_weight **0.00720823** (~0.721%); debug count share 0.001634 non-authoritative
- Legs: neutral net 0.19419 turn 27.0219; write_down net 0.18548 turn 27.0297
- Shapley 16-state both legs; sum_equals_gap abs err ~0
- Evidence SHA-256 `49c594c8ac6e71d50dcc6f021e9e3ee5af29a4ca68717b72a90cbab11c00b488` bound to A
- Curve promoted: false

Open Risks: residual_outcome_ambiguities_envelope_only; snapshot_non_PIT_link_ceiling; low_stderr_label

Next action: hold readiness/UI/strategy/historical-link/CCM; use envelope diagnostics only; optional rename M7F2_BLOCKED label.

## Closure Packet

ClosurePacket: RoundID=ROUND-20260712-M7F3-V7-SELF-FINANCING; ScopeID=M7F3_V7_SELF_FINANCING_PORTFOLIO_TRUTH; ChecksTotal=30; ChecksPassed=30; ChecksFailed=0; Verdict=PASS; OpenRisks=residual_envelope_and_snapshot_ceiling; NextAction=hold_readiness_use_self_financing_envelope_diagnostics_only

## ClosureValidation:

ClosureValidation: PASS

## SAWBlockValidation

SAWBlockValidation: PASS (Verdict PASS|BLOCK, Findings, Hierarchy, Document Changes, Evidence, Next action present)
