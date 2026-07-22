# GV-V2-B0 Decision Packet — MU G_supply Real Block-Only Admission

- case_id: `V2_B0_MU_G_SUPPLY_BLOCK_ONLY_1`
- subject/module: `MU` / `G_supply`
- access_authorization_hash: `96e5c2557b2edc52192bb4dee4860a3b8cda0f81b982ccf85ee7ce8c541746d3`
- source_manifest_hash: `9a2c793c83f54324a3ea43372163c15fb9a761407a70868310ecd71eac9894e0`
- admission_hash: `5bbc438597cc31d0d34c6c6bd984e345e1ffb1c1743d40d51daa920bf9ac1f5a`
- admission_status: `BLOCKED`
- primary_block_reason: `MISSING_POINT_IN_TIME_AUTHORITY`
- research_action: `HOLD_FOR_EVIDENCE`
- portfolio_action: `NO_POSITION`
- decision_id: `DECISION_V2_B0_MU_G_SUPPLY_1`
- rationale_ref: `V2B0:ADM:5bbc438597cc31d0d34c6c6bd984e345e1ffb1c1743d40d51daa920bf9ac1f5a`
- certification_status: `CERTIFIED`
- shipped_product_score: `39` (frozen; no uplift)
- functional_stage: `CERTIFIED_SINGLE_DECISION_OPERABLE`
- observed_comparison_count: `0` (V2-B0 is admission, not G08 observation)

## Source package
- path: `data/candidate_cards/MU_supercycle_candidate_card_v0.json`
- sha256: `368c4fb3f7afc4673f2bbffd3a39a977159a779e8929e0a327db461d1ee05abd`
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
