# ECONPHYSICS PREBREAKOUT S0 Economic Dynamics Diagnostic v2

Date: 2026-08-11
Status: `DIAGNOSTIC_ONLY / SAME_PIT_CORPUS / NO_WINNER_MARKET_W6_ACCESS / NO_PROMOTION_AUTHORITY`

## Question

The frozen S0 M0/M1 shootout establishes that the incumbent **persistence** interpretation fails its economic-transition gate. It does **not** by itself establish that structured fundamentals contain no transition information. This diagnostic isolates the missing question: for each structured node, is the lawful next-PIT operator closer to level-state persistence, first-difference persistence, first-difference mean reversion, or second-difference/acceleration, and does reversing either already-frozen M0/M1 state representation reveal stable dynamics?

This is a posterior diagnostic on a corpus whose persistence results and reversal behavior have already been inspected. It is not a new untouched/preregistered Alpha or promotion read. Any later confirmatory continuation must freeze its chosen operator/representation before a genuinely untouched or prospective evaluation.

## Fixed data/evaluation law

- Reuse the exact admitted S0 Original-filing PIT corpus, source receipt, master, transition-plan predecessor gate, four temporal folds, and deterministic CIQSEC 20% XS holdout.
- Preserve the exact existing targets: next-PIT inventory/revenue normalization, revenue direction, and operating-margin direction.
- Fold support remains `lift_vs_no_information_baseline > 1` **and** `directional_association > 0`; stable support requires `>=3/4` temporal folds with the existing minimum-N/coverage law.
- XS holdout is corroboration only and is never used to choose an operator.
- No market data, equity/winner labels, W6, K/selection breadth, threshold search, fitted parameter, bootstrap, provider call, or capital action is available to this diagnostic.

## Economic orientation and operators

For revenue and operating margin, higher is positive. For inventory, define the economic level as `e_q = -(inventory_q / revenue_q)` so an increase means inventory normalization.

Let `e0=e[FQ0]`, `e1=e[FQ-1]`, `e2=e[FQ-2]`, and `e4=e[FQ-4]`. The primitive fixed family is:

- `LEVEL_STATE_PERSISTENCE = sign(e0-e4)`.
- `DELTA_PERSISTENCE = sign(e0-e1)`.
- `DELTA_MEAN_REVERSION = -sign(e0-e1)`.
- `DELTA2_ACCELERATION = sign((e0-e1)-(e1-e2))`.

Two representation-conditioned operators are also fixed because M0 and M1 encode information beyond a single primitive delta:

- `M0_STATE_MEAN_REVERSION = -frozen_M0_prediction_direction`.
- `M1_STATE_MEAN_REVERSION = -frozen_M1_prediction_direction`.

M0/M1 implementation bytes and their original persistence failures are not mutated. The diagnostic reports every operator; it performs no winner-take-all operator selection.

## Routing law

Per node:

- If any fixed low-freedom operator supports the mechanism in `>=3/4` folds, route `DYNAMICS_SIGNAL_PRESENT` and retain that node. Do not classify that node as observable-insufficient.
- If the full fixed operator family has adequate fold coverage but none reaches `>=3/4`, route `NO_LOW_FREEDOM_DYNAMICS_SIGNAL` for that node.
- If coverage is inadequate, route `UNOBSERVED`; do not infer insufficiency.

Integrated routing is node-specific. If at least one node survives, route `NODE_SPECIFIC_DYNAMICS_SURVIVORS`; an integrated M0/M1 failure may not discard the entire structured surface. `OBSERVABLE_INSUFFICIENCY_CANDIDATE` is allowed only when all core nodes have adequate coverage and the full low-freedom family fails.

## Layer boundary

If a node eventually requires new causal observables, keep the upstream economic layer separate from the downstream expectation layer. Upstream examples are orders/backlog, pricing/mix, utilization/capacity, and channel inventory. Revisions, management guidance, and consensus belong to the downstream expectation-gap layer and must not be mixed into this dynamics diagnosis.

## Implementation / evidence

- Runtime: `research/econphysics_prebreakout_v1/dynamics_diagnostic.py`.
- Runner: `scripts/econphysics_prebreakout_s0_dynamics_diagnostic.py`.
- Real diagnostic: `data/prebreakout/analysis/econphysics_s0_economic_dynamics_diagnostic_v2.json`.
- Frozen persistence comparison retained unchanged: `data/prebreakout/analysis/econphysics_s0_m0_m1_shootout_v2.json`.
