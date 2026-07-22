# Done Checklist - Current

## Active Addendum — V2-B0A Local Source Abstention Repair (2026-07-23)

- [x] Audit accepted: REPAIR_CURRENT_SLICE (semantic blockers; CI already green).
- [x] Relabel slice/UI to local research-card preflight / certified source-authority abstention.
- [x] Validate package manifest URI/hash; emit `SOURCE_PACKAGE_MANIFEST_BINDING_INVALID` (historical package preserved).
- [x] Authorization: `retrieval_or_receipt_time=null`; explicit `authorization_recorded_at` + out-of-band provenance.
- [x] Delete positive ADMITTED publication, DataAdmissionCertificate, automatic ADVANCE_TO_FULL_RESEARCH.
- [x] Reject positive admission with `V2B0_POSITIVE_ADMISSION_NOT_AUTHORIZED`.
- [x] Narrow regressions for binding mismatch, positive rejection, forbidden-use failure, no auto-advancement.
- [x] Regenerate block/result/current decision; pin CI hashes.
- [ ] Hosted product + protocol + Ubuntu/Windows parity green on repair tip.
- [ ] Narrow independent review; merge PR #6.

Next action: push repair tip → hosted green → independent review → merge. Do not open B0B until merge.
