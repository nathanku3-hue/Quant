# Request Artifact Identity Repair V1 — Quarantine Manifest

Status: `INVALID_NOT_DISPATCHED`
Mode: `EXECUTION_PACKET`
RoundID: `ROUND-20260711-REQUEST-ARTIFACT-IDENTITY-REPAIR-V1`
ScopeID: `REQUEST_ARTIFACT_IDENTITY_REPAIR_V1`

These files are preserved only as audit evidence of a denied dispatch attempt. They are not active authorization, request, review, dispatch, validation, or readiness artifacts. No message represented by these files was proven sent.

| Original path | Quarantined path | SHA-256 | Reason |
|---|---|---|---|
| `docs/authorization/V2_PEAD_M6B_GATE_ABC_SOURCE_ACCESS_DISPATCH_20260711.md` | `docs/quarantine/request_artifact_identity_repair_v1/V2_PEAD_M6B_GATE_ABC_SOURCE_ACCESS_DISPATCH_20260711.md.invalid` | `ed2db3015413bc71edea919d5c15800514e74b5918253af3d86788614baf872d` | Unbound dispatch claim; Markdown hash was mislabeled as the JSON hash. |
| `docs/authorization/V2_PEAD_M6B_GATE_ABC_SOURCE_ACCESS_DISPATCH_20260711.json` | `docs/quarantine/request_artifact_identity_repair_v1/V2_PEAD_M6B_GATE_ABC_SOURCE_ACCESS_DISPATCH_20260711.json.invalid` | `5975304aee17b6b46a481f690b3be7ac76ee37d5000e9e1e58fcbed1b88b8a30` | Unbound dispatch claim; exact request artifacts were absent from the declared commit. |
| `docs/saw_reports/saw_v2_pead_m6b_gate_abc_request_dispatch_20260711.md` | `docs/quarantine/request_artifact_identity_repair_v1/saw_v2_pead_m6b_gate_abc_request_dispatch_20260711.md.invalid` | `153a70d94691050c5c1c415c9ecb6440ad67799b13825eb5ff5f2abd8956d329` | Reviewer PASS depended on invalid artifact identity and cannot support dispatch. |

Quarantine rules:

- Preserve bytes; do not normalize, repair, reuse, dispatch, or cite these files as current truth.
- The Markdown and JSON dispatch hashes are separate values and must never be represented by one ambiguous packet hash.
- Any legacy, divergent, reconstructed, or unbound request/dispatch artifact remains rejected.
- No remote, dispatch, source/provider access, factual validation, readiness change, Gate D work, publication, or data output is authorized by this manifest.
