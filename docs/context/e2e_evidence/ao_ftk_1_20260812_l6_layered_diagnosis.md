# AO-FTK-1 L6 Layered Diagnosis (Sensing-First)

**Slice:** `AO-FTK-1-20260812`  
**Mode:** `SENSING_FIRST`  
**First fail:** `None`  
**Failure route:** `NONE_IN_SCOPE_PASS`  
**financial_alpha_evidence:** `0`

## D1→D9

| Layer | Status | In-scope | Notes |
|---|---|---|---|
| `D1_CUSTODY_PIT` | `PASS` | True | Operator immutability pins match; dof=2; economic cuts BLOCKED_UNSET; no PIT rewrite. |
| `D2_DATA_OBSERVABLE` | `PASS` | True | Admitted snapshots=23047, adjacent pairs=17662; predecessor gate enforced; missingness abstains (no row deletion). |
| `D3_MEASUREMENT_POWER` | `PASS` | True | Inventory evaluable N=7129 qualifying_folds=4; margin evaluable N=12282 qualifying_folds=4. |
| `D4_REPRESENTATION_SNR` | `PASS` | True | Continuous inventory lag-1 + continuous M1 surface retained; inventory coverage=0.5031761716544325, abstention=0.47780545804552144; margin coverage=0.8668831168831169; services inventory NOT_APPLICABLE count=5720 measured. |
| `D5_MECHANISM_SELF_TRANSITION` | `PASS` | True | Inventory INV_DELTA_MEAN_REVERSION status=PASS lift=1.0838590956887488 assoc=0.1817139581541989 supporting_folds=3; margin MARGIN_M1_STATE_MEAN_REVERSION status=PASS lift=1.1528995539147822 assoc=0.22607557663994765 supporting_folds=3. |
| `D6_SELECTION_ENRICHMENT` | `NOT_IN_SCOPE_SENSING_FIRST` | False | No selection estimand preregistered this turn; sensing-only. |
| `D7_CONFIRMATION_TIMING` | `NOT_IN_SCOPE_SENSING_FIRST` | False | No confirmation/timing estimand preregistered this turn. |
| `D8_HOLD_EXIT_CONVEXITY` | `NOT_IN_SCOPE_SENSING_FIRST` | False | No hold/exit estimand preregistered this turn. |
| `D9_ECONOMICS_COST_CAPACITY` | `NOT_IN_SCOPE_SENSING_FIRST` | False | Economic cuts remain BLOCKED_UNSET; do not bind payoff/catastrophe after peeking. F6 asymmetry catastrophe NOT_IN_SCOPE_SENSING_FIRST. |

## Information gain

Relative to the prior L3/L4 representation freeze (unjoined, uncharged), this one-shot join+eval measured fold-stable next-PIT transition association on the frozen 2-DOF surface (surface_status=BOTH_NODES_MEASURABLE_SIGNAL). Inventory operator INV_DELTA_MEAN_REVERSION: PASS (lift=1.0838590956887488, assoc=0.1817139581541989). Margin operator MARGIN_M1_STATE_MEAN_REVERSION: PASS (lift=1.1528995539147822, assoc=0.22607557663994765). No economic cuts were bound; financial_alpha_evidence remains 0.

**May change next (owner only):** Owner may later authorize economic-cut freeze + second trial, bounded refinement, or STOP — not auto-dispatched.

**Forbidden to change:**

- second evaluation without new owner auth
- threshold/parameter grid
- DOF collapse or third DOF
- operator/feature rewrite under same freeze
- post-hoc economic cut binding
- W6 open
- capital / alpha claim
- AO-FTK-2 autonomous open
- Q invention / QM revival in FTK
