# GV-V2-B0A Decision Packet — MU G_supply Local Source Abstention

- slice_classification: `GV-V2-B0A-LOCAL-SOURCE-ABSTENTION`
- case_id: `V2_B0_MU_G_SUPPLY_BLOCK_ONLY_1`
- subject/module: `MU` / `G_supply`
- access_authorization_hash: `e352042a4d8ffe67551e9dd3932194093b6e9a2ed3d010a88bb6cb6715c7e484`
- authorization_provenance: `OUT_OF_BAND_OWNER_APPROVAL_FOR_LOCAL_EVALUATION_ONLY`
- retrieval_or_receipt_time: `None`
- source_manifest_hash: `feb9e71b520fcad67282891d9da36d3998760991dcf58c50140186b6ebad2cd1`
- admission_hash: `d1b891152477504b29e041baba304396fa2a7be2d01fcc701f960a15d7f49f2f`
- admission_status: `BLOCKED`
- primary_block_reason: `MISSING_POINT_IN_TIME_AUTHORITY`
- research_action: `HOLD_FOR_EVIDENCE`
- portfolio_action: `NO_POSITION`
- decision_id: `DECISION_V2_B0_MU_G_SUPPLY_1`
- rationale_ref: `V2B0:ADM:d1b891152477504b29e041baba304396fa2a7be2d01fcc701f960a15d7f49f2f`
- certification_status: `CERTIFIED`
- shipped_product_score: `39` (frozen; no uplift)
- functional_stage: `CERTIFIED_SINGLE_DECISION_OPERABLE`
- observed_comparison_count: `0` (B0A is local abstention, not G08 observation)

## Source package
- path: `data/candidate_cards/MU_supercycle_candidate_card_v0.json`
- sha256: `f87e7908854791c327b3a04eb46b873fb995283a4b8015c1bca7bd7066f53f2d`
- class: local research candidate card (not official filing / not physical supply)
- note: package manifest may declare a non-binding historical artifact_sha256; admission surfaces SOURCE_PACKAGE_MANIFEST_BINDING_INVALID when so.

## Admission checks (fail-closed; block-only)
- `completeness`: `FAIL` — missing_declared=6; real_supply=False; filing=False
- `contradictions`: `PASS` — No admitted indispensable real facts to contradict; contradiction check vacuous.
- `forbidden_use_enforcement`: `PASS` — Research card not promoted to real evidence; forbidden synthetic-as-real held.
- `immutable_byte_identity`: `PASS` — exact hashes verified
- `licence_and_permitted_use`: `PASS` — Access auth is local evaluation-only; investable/real-provider uses forbidden.
- `package_manifest_binding`: `FAIL` — sha_mismatch:declared=368c4fb3f7afc4673f2bbffd3a39a977159a779e8929e0a327db461d1ee05abd:actual=f87e7908854791c327b3a04eb46b873fb995283a4b8015c1bca7bd7066f53f2d
- `point_in_time_availability`: `FAIL` — No known_at/publication_time/effective_period for physical supply facts.
- `positive_admission_gate`: `PASS` — No ADMITTED path taken; block-only local abstention retained.
- `purpose_compatibility`: `PASS` — Gate purpose is local research-card admission preflight / certified source-authority abstention; not real external admission.
- `semantic_and_schema_validity`: `FAIL` — Research candidate card is schema-valid as research_only identity, but is not a G_supply real-admission evidence schema.

## Research rationale
Admission blocked (MISSING_POINT_IN_TIME_AUTHORITY). Local research-card package lacks real point-in-time physical-supply or official filing authority for MU G_supply. HOLD_FOR_EVIDENCE is the correct research-triage abstention; REJECT_THESIS would overclaim thesis death from data absence. Positive ADMITTED / ADVANCE_TO_FULL_RESEARCH is not authorized in B0A.

## Claim boundary
V2-B0A local research-card admission preflight / certified source-authority abstention for one MU G_supply package. Not a real external source admission. No established mispricing, alpha, investability, tradability, trade recommendation, score uplift, or general decision improvement claim. A certified local-source abstention is a valid functional result. Research HOLD_FOR_EVIDENCE maps only to paper NO_POSITION. Positive ADMITTED / ADVANCE_TO_FULL_RESEARCH is not authorized in B0A.
