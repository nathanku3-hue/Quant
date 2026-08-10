# PREBREAKOUT Trial-1 → W4 Handover — 2026-08-10

## Executive status

Owner stream: `PREBREAKOUT_DISCOVERY_v1`

Branch: `codex/pit-source-authority-1`

Base Git head before this documentation handover: `685f82a10678af2de86393714a9979c64a73bc4c`

Critical chain now:

`W4 real census completion -> close charged Trial #1 -> stop; DO NOT consume W6`

Current scientific/custody state:

```text
W2 contract                     = frozen / unchanged
W3 real source authority        = COMPLETE
Trial #1                        = OPEN / permanently charged 1 of 8
Trial #1 flags                  = FROZEN BEFORE LABEL MATERIALIZATION
Development labels              = OPENED only after exact Trial #1 charge + flag freeze
W5 development                  = COMPLETE / 4 informative folds
W5 median recall lift           = 0.71570953472408605
W4 real census                  = INCOMPLETE / no final Atlas artifact yet
W6 untouched lockbox            = NOT CONSUMED / DO NOT OPEN
financial_alpha_evidence        = 0
capital_authority               = NONE
broker orders                   = NONE
```

The immediate next worker task is **only to finish the real W4 census against the already-frozen Trial-1 flag and label custody, then close Trial #1.** Do not rerun search, retune Trial-1, inspect W6, restart W7/W8/W9/ML work on this critical path, or create broker orders.

---

## 1. W2 remains immutable

Frozen W2 contract:

```text
PREBREAKOUT_W2_CONTRACT_v1
SHA-256 = 94c8756e11d4e31cbf4d6ca4953b63c83306f4b357a42f0b70c94ae3fd261e71
```

Key frozen laws remain:

```text
B                         = close_t > prior 20 observed exact-listing session high
accepted B cooldown       = >20 exact-listing observed sessions
B-1                       = immediately prior observed exact-listing session
TTFLD window              = B-20 ... B-1 on the exact listing clock
primary label             = 20-session date-local top-5% right tail
hard Trial/Search budget  = 8 material trials
```

Do not change these semantics in place.

---

## 2. W3 real source authority is complete

Canonical W3 compiled directory:

`data/prebreakout/compiled/w3_real_authority_20250324_20260807/`

Verified source custody remains:

```text
sessions                 = 346
first_session            = 2025-03-24
last_session             = 2026-08-07
market/listing rows      = 1,894,207
union companies          = 5,919
union exact listings     = 6,018
missing close            = 0
missing volume           = 0
missing total return     = 177,820
lifecycle parts          = 12/12
lifecycle entity union   = exact same 5,919 companies
```

Canonical W3 hashes:

```text
source custody manifest      = 7c892dca7461cc71560996b0f0d701818776dd2f67b7766900e0c89cdd17a72e
session partition            = 8c210715d52bbc56aa68f093a6e733b0cb9bfb334260d762c197240c97336463
authority manifest           = 49dc4fb471f9c0ef82aa8bdc3a81d55e6ddf682ba9df7e5e317f695088dd0ba5
authority bundle             = e13df0033020abe34de96311412edce1360b9504bda049eb8857a76ca54873f6
MU/SNDK proof bundle         = 7bf933603d8705f9588e765fed4cd74774516c37862b5b1dadcbe65d33970971
```

All 346 date-local W3 packets were compiled and independently hash-checked against their landed files.

### MU / SNDK

Exact provider identities remain:

```text
MU   = CIQSEC:IQ289030 / Trading Item 2630498 / SPT2630498
SNDK = CIQSEC:IQ1860586153 / Trading Item 1929119896 / SPT1929119896
```

Frozen W2 accepted episodes:

```text
MU   = 11
SNDK = 12
```

All 23 W3 B-1 proofs now resolve:

```text
PIT_ELIGIBLE_B_MINUS_1 = 23 / 23
DETERMINISTIC_UNAVAILABLE = 0
```

They remain statistical/promotion weight zero and must never become acceptance-weighted named cases.

---

## 3. Exact single-corpus partition is frozen

The 346 provider sessions are partitioned exactly as:

```text
60   feature warmup
226  W5 development decisions
20   post-development label embargo / maturity support
20   W6 untouched lockbox decisions
20   W6 lockbox label-maturity tail
----
346 total
```

Exact boundaries:

```text
warmup                    2025-03-24 .. 2025-06-17
W5 development            2025-06-18 .. 2026-05-12
post-development embargo  2026-05-13 .. 2026-06-10
W6 decisions              2026-06-11 .. 2026-07-10
W6 label tail             2026-07-13 .. 2026-08-07
```

Development source custody deliberately excludes W6 decisions and the W6 label tail.

---

## 4. Pre-charge Trial-1 custody was frozen before the charge

Canonical pre-charge directory:

`data/prebreakout/compiled/trial1_precharge_20260810/`

Pre-charge receipt:

```text
receipt_sha256                   = 07c9eedbaacc4dd1e463d91ad68947f36dede4551f6c39e81a602b8247586731
source_manifest_sha256           = 3d481b36d80eca9653720b0cecb45808fa2f29fef66623fdb2aa5d2cf921d0d8
code_bundle_sha256               = f4e1c8a904c5664feb38e89f27467ae1fd40095d1157ee813e54648f86022136
prepared_variant_sha256          = 652f04cf04b4ede02f7e014e95f66eeba2662d370452eccfbb3bc07761debfd1
decision_spine_sha256            = ab7e8dfa3574da1543021ba12442225356e598ef7a0b47acf9e8037274cf3a04
development_label_custody_sha256 = 2f9fdc0270a4feb0b6b59ceb23f0a4b7008292b8c30a5fff968c7d07cf89f7b3
episode_anchor_custody_sha256    = 318acec3e9ba026eb475575571ba43ca94141207819f92c33e6b19f12304b3f7
source_receipt_bundle_sha256     = fbd42e2de3f06a304326cd20aafd09c6430cfcfb9ca50218f9a7b5f7486d2708
```

Pre-charge assertions that were true and remain audit evidence:

```text
development_label_visibility     = HASHED_NOT_INSPECTED
development_label_payload_saved  = false
episode_payload_saved            = false
result_inspection_performed      = false
trial_open_appended              = false at precharge freeze
material_trials_consumed         = 0 at precharge freeze
W6 lockbox included              = false
W6 labels opened                 = false
W6 market rows read              = false
```

The real market feature preflight successfully processed `1,672,514` rows across `5,940` exact listings; missing provider Total Return now causes local abstention/invalid-history state rather than aborting the whole frame.

---

## 5. Trial #1 is now charged exactly once

Canonical ledger:

`data/prebreakout/ledger/trial_ledger.jsonl`

It contains exactly one entry and no close entry yet.

Trial open:

```text
trial_id              = PREBREAKOUT_TRIAL_1_M0
sequence              = 0
event_type            = TRIAL_OPEN
recorded_at           = 2026-08-10T20:00:50.847608Z
chain_hash            = 67999418489331536960f042de0dd96da12f1572fa6c6ab01e600914d1ef71a9
cumulative_trials     = 1 / 8
source_manifest       = 3d481b36d80eca9653720b0cecb45808fa2f29fef66623fdb2aa5d2cf921d0d8
code_sha256           = f4e1c8a904c5664feb38e89f27467ae1fd40095d1157ee813e54648f86022136
variant_sha256        = 652f04cf04b4ede02f7e014e95f66eeba2662d370452eccfbb3bc07761debfd1
untouched access      = FORBIDDEN
prospective access    = FORBIDDEN
```

**This `1/8` charge is permanent. Do not append a second Trial-1 open.** Any continuation must reuse this exact ledger entry.

---

## 6. Trial-1 flags were frozen before label materialization

Canonical result-bearing directory:

`data/prebreakout/compiled/trial1_real_20260810/`

Flag-freeze receipt:

```text
receipt_sha256            = 4c29b0455e20ccde39734ef14b961de2cb6f6c384f26d9acf783a033472c3f8e
flag_projection_rows      = 1,561,972
flag_projection_sha256    = 2e018f086fc77da7d9b3b3c768f4bfa39d348368b329f529d35ca06a3062dd12
W3 projection_sha256      = 994e91d9394e9dbabc9049c677ebacce2d50114a6d4810602b1971220d04d03c
development labels saved  = false at flag freeze
development labels seen   = false at flag freeze
W6 market rows read       = false
```

This receipt binds the exact Trial open chain hash and proves the required order:

`TRIAL_OPEN -> immutable Trial-1 flags -> development label materialization`

Do not regenerate flags from outcome-visible data or change the candidate after this point.

---

## 7. Development labels opened only after the charge and flag freeze

Label-open receipt:

```text
receipt_sha256                    = f7770a3bba61e22157a6eecc8903c4227412491c1c9cebcbd8e2bfa8155ed076
development_label_file_sha256     = 51c9f07093038e00965b0e03c03958ba2201875f5339fdf43ea58facd47bbccf
development_label_payload_sha256  = 2f9fdc0270a4feb0b6b59ceb23f0a4b7008292b8c30a5fff968c7d07cf89f7b3
development_label_rows            = 1,238,254
episode_anchor_file_sha256        = a15d31dcb805c44976c03254abd62080f1bb9692c4a0d6eef4f7864e84f06453
episode_anchor_payload_sha256     = 318acec3e9ba026eb475575571ba43ca94141207819f92c33e6b19f12304b3f7
episode_anchor_rows               = 30,391
precharge label hash reproduced   = true
precharge episode hash reproduced = true
prediction before label           = true
W6 labels opened                  = false
W6 included                       = false
```

Incomplete 20-session outcomes are explicit `INCOMPLETE_HORIZON`; they are not imputed and do not enter matured development denominators.

---

## 8. W5 development completed and already fails the primary lift sign

W5 artifacts:

`data/prebreakout/compiled/trial1_real_20260810/w5_development_run.json.gz`

`data/prebreakout/compiled/trial1_real_20260810/w5_recall_lift_summary.json`

W5 development run hash:

```text
768d873113187662687172bc5437f23a6fef90a8cf9e9b2b8a5b051b7071488d
```

All four temporal OOS folds are informative.

Fold recall lifts:

```text
fold 0 = 0.75860330040991253
fold 1 = 0.81331048901190295
fold 2 = 0.5293137480804978
fold 3 = 0.67281576903825957
```

Median temporal-OOS recall lift:

```text
0.71570953472408605
```

Frozen right-tail survival requires recall/lift to beat the breadth-matched baseline (`> 1`). Therefore Trial #1 has already produced an **economic failure sign** on the primary development metric.

Do not retune Trial #1. Do not spend Trial #2 merely to rescue this result. Finish W4 first so the failure is characterized under the frozen census and can be closed cleanly.

---

## 9. W4 is the remaining incomplete step

The real W4 Atlas output has **not** been materialized yet. No canonical `w4_atlas...` result file exists under `data/prebreakout/compiled/trial1_real_20260810/` at this handover.

The last real W4 attempt exposed a nullable scalar bug: incomplete labels arrive through DuckDB/Pandas as `pd.NA`, but the Atlas normalizer originally only handled Python `None` / float NaN. That mechanical bug was fixed in `research/prebreakout_atlas_v1/atlas.py` and the focused W4 suite now passes.

Current W4 implementation additionally carries the real-data mechanics required by this corpus:

- exact **listing-local** session ordinals for B/B-1/TTFLD, not global-session adjacency;
- warmup/prehistory flags may extend early-development TTFLD without entering false-winner/control decision counts;
- `INCOMPLETE_HORIZON` rows remain visible but are excluded from matured winner/false-winner/control denominators;
- full ordinary-control sets are preserved by exact count + identity-set hash instead of materializing a huge Cartesian pair table;
- W3 authority can be verified lazily date-by-date from the hash-bound authority manifest instead of holding all 226 full packets in memory.

Current W4 code SHA-256:

```text
1d4b6241cccf03c92a109916ccb421479ad9c50916992af67f470af06fd3ed74
```

### Exact next action

1. Reuse the existing Trial #1 ledger open. **Do not append another open.**
2. Reuse the landed flag projection, W3 projection, development label Parquet, and episode anchor Parquet.
3. Run only the real W4 census path against those frozen artifacts.
4. Verify the final Atlas report hash and custody assertions.
5. Inspect W4 only after its artifact is sealed.
6. If W4 shows no PIT/custody invalidation, close Trial #1 as the already-observed economic failure (primary recall lift < 1).
7. If W4 instead finds an actual custody/PIT invalidation, close with the appropriate non-economic invalidation status/reason; do not reinterpret the W5 number as valid Alpha evidence.
8. Stop. **Do not consume W6.**

Do not reopen W5 search or alter the Trial-1 candidate after W4.

---

## 10. W6 remains strictly untouched

W6 lockbox decisions are the 20 sessions:

`2026-06-11 .. 2026-07-10`

W6 label-maturity tail is:

`2026-07-13 .. 2026-08-07`

At this handover:

```text
W6 real lockbox consumed     = false
W6 real label surface opened = false
W6 market rows used by Trial1 precharge = false
W6 included in source manifest = false
```

**Do not open or score W6 because Trial #1 did not survive W5 development.**

There is no “one look anyway” exception.

---

## 11. Current focused validation

The current PREBREAKOUT selected matrix passes:

```text
W3 PIT / real-source mechanics       24 tests
W2/W5 discovery + precharge          33 tests
W4 Atlas                             17 tests
W6 untouched evaluator              13 tests
---------------------------------------------
TOTAL                                87 / 87 PASS
```

Selected PREBREAKOUT modules/scripts also compile successfully under the repo Python 3.12 `.venv`.

This validation is mechanical/custody evidence. It does not make the failed W5 lift positive and does not authorize W6 or capital.

---

## 12. Current code custody / Git warning

The PREBREAKOUT executable changes for this round are still local working-tree bytes unless separately committed. Do **not** reset/revert them when taking over.

Current key file hashes:

```text
research/prebreakout_pit_v1/authority.py
  185b68016f41928bf7a19a438b0a13e144c1e483faaa9d76620846a4f4b62e27
research/prebreakout_pit_v1/real_source.py
  221fe01c66fa55e97767d5ff30e8981d6671bde6391353aea577a7375ef5f248
research/prebreakout_discovery_v1/trial1_m0.py
  811b8e7f6e5af6720fb003edcc3d1020caecafb6572923af03e8bcc1406c8bda
research/prebreakout_discovery_v1/precharge_custody.py
  7678ab572ce5abf32f69c5f7b5cb4e20de76badc0b172cf098ec6c70e2a38fdb
research/prebreakout_discovery_v1/walk_forward.py
  92a0a605bececae35682200d6330daeba9549c2dd9d23065ca27491232378814
research/prebreakout_atlas_v1/atlas.py
  1d4b6241cccf03c92a109916ccb421479ad9c50916992af67f470af06fd3ed74
research/prebreakout_untouched_evaluator_v1/contracts.py
  347b839067555a0a4d0a9b8fc2a64e9225be280a2cac91f67095617d52a52831
research/prebreakout_untouched_evaluator_v1/evaluator.py
  14700396141323afce97c742dd772ce216a32f8da5803cf174fe066672d6bf4e
scripts/prebreakout_compile_w3_real_source.py
  1a82d36b18e601fee0e3419085e8707cfe16c8bd15971f3076fa5baaf92faed5
scripts/prebreakout_freeze_trial1_precharge.py
  d63ebf981d042b33e609e5de74f23965f8f3596265128ae35ec61d21225e2192
scripts/prebreakout_run_trial1_w4_w5.py
  a5a189fe25a54cceacb63f535243c4a4d9a5936166719c94b1c6ce556581241e
```

The worktree also contains many unrelated dirty/untracked files from concurrent streams. Do not wholesale-stage, reset, clean, or revert the repository.

---

## 13. Stop rules

Do not:

- append another `TRIAL_OPEN` for Trial #1;
- retune Trial #1 after seeing W5 outcomes;
- consume or inspect W6;
- change W2 B/B-1/TTFLD/horizon/search-budget law;
- use AOV-109/current-primary/ticker/entity/PERMNO fallback;
- back-project survivor/current-primary state;
- requery A2;
- restart W7/VSB, W8 Sector Rotation, W9/CRV1, replication, ML, optimizer, or extra search on this critical path;
- create broker orders;
- claim financial Alpha or capital authority from W3/W4/W5 development evidence.

---

## 14. Takeover verification checklist

Before doing anything else, verify:

```text
git branch = codex/pit-source-authority-1
W2 hash = 94c8756e11d4e31cbf4d6ca4953b63c83306f4b357a42f0b70c94ae3fd261e71
W3 authority bundle = e13df0033020abe34de96311412edce1360b9504bda049eb8857a76ca54873f6
W3 sessions = 346
MU/SNDK proof bundle = 7bf933603d8705f9588e765fed4cd74774516c37862b5b1dadcbe65d33970971
Trial ledger line count = 1
Trial #1 cumulative material trials = 1/8
Trial #1 chain hash = 67999418489331536960f042de0dd96da12f1572fa6c6ab01e600914d1ef71a9
flag freeze receipt = 4c29b0455e20ccde39734ef14b961de2cb6f6c384f26d9acf783a033472c3f8e
label open receipt = f7770a3bba61e22157a6eecc8903c4227412491c1c9cebcbd8e2bfa8155ed076
W5 median lift = 0.71570953472408605
W4 final Atlas artifact = absent/incomplete
W6 consumed = false
```

If any of those differ, stop and reconcile custody before continuing.

---

## One-line next action

**Finish the real W4 census from the already-frozen Trial-1 artifacts, seal/verify it, close Trial #1 as FAIL unless W4 proves a custody invalidation, and stop without touching W6.**
