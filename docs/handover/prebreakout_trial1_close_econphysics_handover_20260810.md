# PREBREAKOUT Trial-1 Close → Econphysics × Winner Selection Handover — 2026-08-10

## Executive status

Branch: `codex/pit-source-authority-1`

Git head during close: `ea044007c3ffbffefaae727f92806b647b4a6f89`

Current PREBREAKOUT state:

```text
W2 Trial-1 contract             = FROZEN / historical Trial-1 authority
W3 real authority              = COMPLETE
Trial #1                       = CLOSED / FAILED / permanently charged 1/8
Trial #1 failure class         = MARKET_BEHAVIOR_DISCOVERY_BRANCH_FAIL
W4 real Atlas                  = COMPLETE / SEALED / FRESH-PROCESS VERIFIED
W5 development                 = COMPLETE / economic FAIL
W6 untouched lockbox           = NOT CONSUMED
Trial #2                       = NOT AUTHORIZED
Successor mechanism            = ECONPHYSICS_PREBREAKOUT_v1 / CONTRACT NOT YET FROZEN
financial_alpha_evidence       = 0
capital_authority              = NONE
```

The next correct action is **not Trial #2**. Freeze the causal contract for `ECONPHYSICS_PREBREAKOUT_v1` first.

Canonical integration lock:

`docs/architecture/econphysics_winner_selection_integration_lock_20260810.md`

Close evidence:

`docs/context/e2e_evidence/prebreakout_trial1_close_20260810.json`

---

## 1. Trial #1 closed exactly once

Original open remains unchanged:

```text
open chain hash = 67999418489331536960f042de0dd96da12f1572fa6c6ab01e600914d1ef71a9
open recorded_at = 2026-08-10T20:00:50.847608Z
```

Final close:

```text
ledger result_status = FAILED
scientific status    = FAIL
close recorded_at    = 2026-08-10T21:55:46.709318Z
close chain hash     = a3d9322eb05442f9fcdcd12f80a6a22d51b00d9edbc0635cc00841461871f9ee
ledger file sha256   = 797afa36dc133e65e6baebf69c80849e0af3a35618a2a389bd7d6cca62502183
ledger lines         = 2
material trials      = 1 / 8
```

No second `TRIAL_OPEN` was appended. The close costs zero additional trials and does not refund Trial #1.

Final result artifact:

`data/prebreakout/compiled/trial1_real_20260810/trial1_development_result.json`

```text
result_sha256      = 8d92db73509da82e692b48e0fe67aa303a68b7ff79aa80aab74491764ca62e1a
result file sha256 = 43e2e41bb230f80965c5c5a017005830945cae2129375a582169aa2221056b3b
```

---

## 2. Final W4 Atlas is complete and verified

Canonical final W4 artifact:

`data/prebreakout/compiled/trial1_real_20260810/w4_discovery_atlas.json.gz`

Hashes:

```text
Atlas internal sha256 = c471bf11fbca068edbd3e5084cc7121cd6339a3f6fd0852055f015be411b6e68
Atlas file sha256     = 942bbaf89264ac87d96f88dae00653f756aa29c356caaa75d0f58e4f350f70a6
Atlas code sha256     = 1d4b6241cccf03c92a109916ccb421479ad9c50916992af67f470af06fd3ed74
fresh-process verify  = PASS
```

The scientific Atlas module remained byte-identical throughout completion.

The direct monolithic run exceeded the DevSpace hard 300-second command cap because the frozen matched-control implementation repeatedly rescans the ordinary pool. Completion therefore used a staged mechanical executor under `tmp/prebreakout_w4_staged_executor.py` without changing `atlas.py` semantics.

The pre-indexed matched-control executor was first compared against the frozen `_build_matched_control_census(...)` on real Trial-1 winner/false/control rows. Equality passed for matched groups, unmatched cases, winner matched counts, and false-winner matched counts:

```text
MATCH_OPT_EQUIVALENCE_PASS
```

Final staged-executor SHA-256 bound into the close artifact:

```text
7c60e4bb89a17916ecd0faa3c10f69f7a778553230fcb10d8442985b5d65130c
```

This helper is execution plumbing only. It is not successor scientific authority and must not be treated as a mechanism change.

---

## 3. W4 result

The sealed and verified Atlas reports:

```text
input development rows                    = 1,238,254
statistical winner episodes               = 2,381
true/detected winner episodes              = 909
missed winner episodes                     = 1,472
median effective TTFLD (miss=0)            = 0
median TTFLD among detected winners        = 11 sessions
statistical false-winner decision rows     = 90,954
statistical ordinary-control rows          = 911,228
cases without exact matched control        = 0
incomplete-horizon rows                    = 61,532
smoke traces                               = 23
```

There is no W4 PIT/custody invalidation. Full W3/PIT binding was reverified date-by-date before Atlas sealing; fresh-process Atlas hash verification passed.

The W4 result confirms the retained diagnosis: when Trial #1 fires it can be early, but it misses most winner episodes. The median effective lead is zero because misses dominate.

---

## 4. W5 economic failure remains decisive

Frozen W5 development run:

```text
run sha256 = 768d873113187662687172bc5437f23a6fef90a8cf9e9b2b8a5b051b7071488d
```

Four informative fold recall lifts:

```text
0.75860330040991253
0.81331048901190295
0.5293137480804978
0.67281576903825957
```

Median:

```text
0.71570953472408605
```

The frozen development survival sign requires recall lift `>1`. It fails.

W4 also gives median effective TTFLD `0`, triggering the separate `NO_POSITIVE_PREBREAKOUT_LEAD` falsifier.

Final triggered economic falsifiers:

```text
NO_RIGHT_TAIL_ENRICHMENT
NO_POSITIVE_PREBREAKOUT_LEAD
```

These are economic failures, not infrastructure or custody failures.

---

## 5. MU / SNDK governance correction is now explicit

MU and SNDK remain useful integration traces, but they are not family pass/fail targets.

Final close artifact records:

```text
smoke_role           = ZERO_WEIGHT_INTEGRATION_TRACE
smoke_used_for_close = false
```

The old `_development_survival()` implementation contains a governance defect in which `not smoke["all_checked_pass"]` can force overall `FAIL`. That defect did **not** determine this Trial #1 close: Trial #1 independently fails W5 lift and W4 median-effective-TTFLD.

Do not use Trial #1, W4/W5 decompositions, or MU/SNDK outcomes to invent the successor economic mechanism.

---

## 6. ECONPHYSICS × WINNER_SELECTION integration lock

The successor PREBREAKOUT system is not “state machine instead of winner selection.” Winner selection remains the bridge from causal research to Alpha.

Frozen role chain:

```text
ECON_STATE_v1
→ EXPECTATION_GAP_v1
→ WINNER_SELECTION_v1
→ MARKET_CONFIRMATION_v1
→ CONTINUATION_EXIT_v1
→ right-tail falsification / realized capture
```

Governing rule:

> **Forecast winners through causal economic state, not by fitting winner outcomes directly.**

More precisely:

> **Economic physics generates the state representation; winner selection converts that state into cross-sectional capital priority; market outcomes falsify and calibrate confidence boundaries, but do not invent the causal mechanism.**

Roles:

- `ECON_STATE_v1`: cause model — supply/demand, capacity, inventory, pricing, utilization, cost, margin, orders/backlog, revisions/guidance, capital-cycle response.
- `EXPECTATION_GAP_v1`: mispricing model — economic-state-implied trajectory versus priced/consensus trajectory.
- `WINNER_SELECTION_v1`: full-PIT cross-sectional ranking into `alpha_priority_score`.
- `MARKET_CONFIRMATION_v1`: market recognition, capturability and entry timing; price/volume/volatility/breadth live here rather than replacing the economic cause model.
- `CONTINUATION_EXIT_v1`: hold/exit based on persistence, expectation-gap closure and preregistered economic falsifiers.

Top-5% winners, Precision/Recall/Lift@K, TTFLD, false/missed winners, right-tail wealth capture and `I vs I+X` remain external evaluation/falsification measures.

They may answer whether the integrated system works. They may not choose causal variables, graph edges, signs, lags, windows or thresholds.

---

## 7. Trial #1 interpretation under the new lock

Correct interpretation:

> `PREBREAKOUT_TRIAL1_M0_MARKET_EARLY_WARNING_V1` proves that a market-only proxy representation is insufficient for PREBREAKOUT winner selection on this development corpus.

Incorrect interpretations:

```text
winner selection itself is invalid
near-high should simply be removed because the historical winner decomposition says so
compression+volume should become Trial #2 because it looked better post hoc
MU/SNDK should be explicitly optimized
```

Trial #1 is retained as historical failed evidence. It is not a feature-selection oracle for the successor causal graph.

---

## 8. W6 remains untouched

Final close fields:

```text
w6_lockbox_opened = false
w6_labels_opened  = false
```

Trial #1 did not survive development, so no W6 look is authorized.

Do not consume W6 while designing or freezing `ECONPHYSICS_PREBREAKOUT_v1`.

---

## 9. Focused validation

Final selected PREBREAKOUT matrix rerun:

```text
W3 + W2/W5 + W4 + W6 mechanics = 87 / 87 PASS
```

This is mechanical/custody validation only. It does not create financial Alpha evidence.

---

## 10. Next action

**Do not open Trial #2.**

First freeze `ECONPHYSICS_PREBREAKOUT_v1` with, at minimum:

1. causal graph with ex-ante economic rationale for every edge;
2. PIT observable manifest — source, field, unit, release/availability clock, vintage/revision law, missingness and exact identity binding;
3. state definitions and transition laws;
4. expectation-gap definition and consensus/market-expectation observables;
5. cross-sectional winner-selection mapping to `alpha_priority_score`;
6. invariance assumptions across time/industry/regime;
7. economic falsifiers and custody invalidators;
8. market-confirmation boundary and forbidden outcome→mechanism feedback;
9. continuation/exit boundary;
10. explicit Trial/Search custody preserving the already-consumed `1/8` charge.

Only after that contract is frozen may another material trial/search action be considered.

---

## 11. Stop rules

Do not:

- reopen or retune Trial #1;
- append another Trial-1 open;
- open Trial #2 before the successor causal contract freeze;
- reset/refund the existing `1/8` charge;
- use W4/W5 winner decomposition to invent causal mechanism variables or thresholds;
- tune to MU/SNDK;
- consume W6;
- retune VSB into PREBREAKOUT discovery;
- requery A2;
- change W2 Trial-1 B/B-1/TTFLD custody retrospectively;
- claim financial Alpha or capital authority;
- create broker orders on this path.

---

## Git warning

No commit or push was performed by this close round.

The worktree still contains unrelated concurrent dirty streams. Do not wholesale-stage, reset, clean or revert them.

The original documentation handover commit remains:

```text
ea044007c3ffbffefaae727f92806b647b4a6f89
```

Current closure docs/data are working-tree state until separately committed.
