# GV-V2-B0 Decision Packet — MU G_supply Real Block-Only Admission

- case_id: `V2_B0_MU_G_SUPPLY_BLOCK_ONLY_1`
- subject/module: `MU` / `G_supply`
- access_authorization_hash: `430b1a2b195dc92b4ee42f0e39f42be7b8d2f969bd4c77a3d0789187fb1cdf74`
- source_manifest_hash: `8d43b05ab37dc5bc0dd4f5657244672328695843ea9b958f2bfdda13363ffb00`
- admission_hash: `03a4f427843b8a7e2e0726c0bc86d1338d2e42d185bb5ad90adc47fbffc57176`
- admission_status: `BLOCKED`
- primary_block_reason: `MISSING_POINT_IN_TIME_AUTHORITY`
- research_action: `HOLD_FOR_EVIDENCE`
- portfolio_action: `NO_POSITION`
- decision_id: `DECISION_V2_B0_MU_G_SUPPLY_1`
- rationale_ref: `V2B0:ADM:03a4f427843b8a7e2e0726c0bc86d1338d2e42d185bb5ad90adc47fbffc57176`
- certification_status: `CERTIFIED`
- shipped_product_score: `39` (frozen; no uplift)
- functional_stage: `CERTIFIED_SINGLE_DECISION_OPERABLE`
- observed_comparison_count: `0` (V2-B0 is admission, not G08 observation)

## Source package
- path: `data/candidate_cards/MU_supercycle_candidate_card_v0.json`
- sha256: `f87e7908854791c327b3a04eb46b873fb995283a4b8015c1bca7bd7066f53f2d`
- class: local research candidate card (not official filing / not physical supply)

## Admission checks (fail-closed)
- `completeness`: `FAIL` — missing_declared=6; real_supply=False; filing=False
- `contradictions`: `PASS` — No admitted indispensable real facts to contradict; contradiction check vacuous.
- `forbidden_use_enforcement`: `PASS` — Research card not promoted to real evidence; forbidden synthetic-as-real held.
- `immutable_byte_identity`: `PASS` — exact hashes verified
- `licence_and_permitted_use`: `PASS` — Access auth is evaluation-only; investable/real-provider uses forbidden.
- `point_in_time_availability`: `FAIL` — No known_at/publication_time/effective_period for physical supply facts.
- `purpose_compatibility`: `FAIL` — Gate purpose requires real G_supply admission evidence; local package is research_only identity.
- `semantic_and_schema_validity`: `FAIL` — Research candidate card is schema-valid as research_only identity, but is not a G_supply real-admission evidence schema.

## Research rationale
Admission blocked (MISSING_POINT_IN_TIME_AUTHORITY). No real point-in-time physical-supply or official filing authority is admitted for MU G_supply. HOLD_FOR_EVIDENCE is the correct research-triage abstention; REJECT_THESIS would overclaim thesis death from data absence.

## Claim boundary
V2-B0 block-only real admission attempt for one MU G_supply package. No established mispricing, alpha, investability, tradability, trade recommendation, score uplift, or general decision improvement claim. A certified admission block / data abstention is a valid functional result. Research HOLD_FOR_EVIDENCE maps only to paper NO_POSITION.
