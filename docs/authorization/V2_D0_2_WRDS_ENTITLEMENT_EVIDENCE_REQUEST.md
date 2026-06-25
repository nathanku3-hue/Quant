# V2-D0.2 WRDS Entitlement Evidence Request - No Credential Use

Status: REQUEST_PREPARED_EVIDENCE_MISSING
RoundID: ROUND-20260603-V2-D0-2-ENTITLEMENT-EVIDENCE-REQUEST
ScopeID: V2_D0_2_WRDS_ENTITLEMENT_EVIDENCE_REQUEST_NO_CREDENTIAL_USE
Authority: PM/subagent task and evidence-request artifact only; not approval, not provider access, and not runtime authority.
SAW Status: BLOCK correct block because non-secret dated attributable entitlement evidence is still missing.

## Mission

Convert V2-D0.1 from authorization-intent-only to table-specific permission truth by obtaining non-secret, dated, attributable entitlement evidence for the exact five WRDS rows. This artifact prepares the evidence request; it does not read, quote, test, validate, or use local secret material and does not access WRDS or any provider.

## Current State

V2-D0.1 authorization intent exists, but evidence is missing. The current V2-D0.1 artifacts record all five rows as pending with `approval_ref` null:

- `docs/authorization/V2_D0_1_WRDS_PERMISSION_TRUTH_AUTHORIZATION.md`
- `docs/authorization/V2_D0_1_WRDS_PERMISSION_TRUTH_AUTHORIZATION.json`

## Five-Row Evidence Request State

| library.table | evidence_status | permission_status | approval_ref |
| --- | --- | --- | --- |
| crsp.dsf | evidence_missing | pending | null |
| crsp.stocknames | evidence_missing | pending | null |
| crsp.ccmxpf_linktable | evidence_missing | pending | null |
| comp.fundq | evidence_missing | pending | null |
| ibes.det_epsus | evidence_missing | pending | null |

## Required Evidence

The evidence must be non-secret, dated, and attributable to an institutional data librarian, WRDS representative, PI, license owner, or data administrator. It should confirm:

- account or license owner;
- account or institutional scope;
- exact library.table permissions for `crsp.dsf`, `crsp.stocknames`, `crsp.ccmxpf_linktable`, `comp.fundq`, and `ibes.det_epsus`;
- license/access constraints and allowed internal research/provenance use;
- date or as-of coverage for the permission statement;
- attributable sender or signer name, role, institution, and contact channel;
- whether the evidence can be stored in repo documentation as non-secret entitlement evidence.

## Copyable Evidence-Request Message

```text
Subject: Non-secret WRDS entitlement confirmation request for five table-level permissions

Hello,

I am preparing an internal permission-truth record for a local quantitative research project. Please do not send credentials, passwords, tokens, SSH details, WRDS connection strings, data extracts, snapshots, schema listings, table listings, row counts, or query output.

Could you provide a dated, attributable, non-secret entitlement confirmation for whether our account/institution/license has permission to access the following exact WRDS library.table rows for internal research/provenance documentation use?

- crsp.dsf
- crsp.stocknames
- crsp.ccmxpf_linktable
- comp.fundq
- ibes.det_epsus

Please include, if available:

1. account or license owner;
2. account or institutional scope;
3. exact table-level permission status for each listed library.table;
4. license/access constraints and allowed use notes;
5. date or as-of coverage for the permission statement;
6. your name, role, institution or WRDS/licensing relationship, and contact channel;
7. whether this confirmation may be stored as non-secret entitlement evidence in internal project documentation.

This request is only for entitlement evidence. It does not request credentials, provider access, probes, snapshots, schema discovery, table discovery, row counts, data output, or runtime validation.

Thank you.
```

## Forbidden Scope

This artifact does not authorize and must not trigger:

- credentials, passwords, tokens, SSH details, or connection strings;
- provider or WRDS access;
- login, SSH, Python WRDS, SAS, SQL, schema discovery, table listings, row counts, snapshots, data output, or runtime checks;
- reading, quoting, testing, validating, or using `secret.txt`;
- row approval, approval_ref assignment, final permission truth, clean-room proof, legacy cleanup, secret remediation, SafeBoot, or BootReady.

## PM / Subagent Task

Task: send the copyable evidence-request message to the institutional data librarian, WRDS representative, PI, license owner, or data administrator.

Acceptance condition: obtain non-secret, dated, attributable evidence that explicitly covers each of the five rows, or record that evidence was declined/unavailable. Until then, all rows remain `evidence_missing`, `pending`, and `approval_ref=null`.

## SAW-Block Rationale

SAW Verdict expected for this docs-only request round: BLOCK.

Reason: the request artifact is prepared, but the blocking evidence has not been obtained. Blocking is correct and protective because the repo still lacks qualifying non-secret entitlement evidence and must not approve any row or run any provider/probe/runtime path.

Next action: send the request, collect or decline non-secret entitlement evidence, then prepare a separate approval_ref artifact only if qualifying evidence exists.
