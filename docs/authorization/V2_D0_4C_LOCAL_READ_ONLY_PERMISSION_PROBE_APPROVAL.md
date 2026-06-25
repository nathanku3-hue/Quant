# V2-D0.4C Local Read-Only Permission Probe Approval

Status: PASS_DOCS_ONLY_APPROVAL
Authority: docs-only approval for one future local human permission probe; not execution, not data extraction, not formal permission truth closure.
Date: 2026-06-03
RoundID: ROUND-20260603-V2-D0-4C-LOCAL-READ-ONLY-PERMISSION-PROBE-APPROVAL
ScopeID: V2_D0_4C_LOCAL_READ_ONLY_PERMISSION_PROBE_APPROVAL_DOCS_ONLY

## Decision

Approve one future local-only read-only WRDS permission probe for exactly five hard-coded rows. Do not execute WRDS in this artifact. Credentials remain local-only and must not be read, quoted, logged, committed, or shared with Codex, subagents, or repo artifacts.

## SAW Verdict Fields

- `PASS_DOCS_ONLY_APPROVAL`
- `LOCAL_READ_ONLY_PERMISSION_PROBE_APPROVED_FOR_LOCAL_HUMAN_RUN`
- `WRDS_OUTPUT_BLOCKED`
- `DISCOVERY_BLOCKED`
- `FORMAL_PERMISSION_TRUTH_NOT_CLOSED`

## Approved Future Probe Scope

| library.table | probe_status | approval_status | approval_ref |
|---|---|---|---|
| `crsp.dsf` | `probe_approved_not_executed` | `not_formally_approved` | null |
| `crsp.stocknames` | `probe_approved_not_executed` | `not_formally_approved` | null |
| `crsp.ccmxpf_linktable` | `probe_approved_not_executed` | `not_formally_approved` | null |
| `comp.fundq` | `probe_approved_not_executed` | `not_formally_approved` | null |
| `ibes.det_epsus` | `probe_approved_not_executed` | `not_formally_approved` | null |

## Probe Design Constraints

- Use only the five exact hard-coded table names above.
- Use a local human-owned WRDS account through an approved local access method.
- Use only a read-only no-output permission check.
- Record only one redacted boolean-style outcome per table.
- Redact exception messages if they contain username, host, path, account, credential, SQL internals, provider banners, or provider-specific sensitive text.
- Do not persist provider output.

## Allowed Future Output Shape Only

```json
{
  "crsp.dsf": "accessible=true/false/redacted_error",
  "crsp.stocknames": "accessible=true/false/redacted_error",
  "crsp.ccmxpf_linktable": "accessible=true/false/redacted_error",
  "comp.fundq": "accessible=true/false/redacted_error",
  "ibes.det_epsus": "accessible=true/false/redacted_error"
}
```

## Explicitly Forbidden

- reading, quoting, testing, validating, copying, or using `secret.txt`;
- reading, printing, logging, committing, or sharing credentials;
- Codex/subagent login or WRDS execution in D0.4C;
- `list_libraries`, `list_tables`, schema discovery, table discovery, row counts, sample rows, SQL result exports, raw SQL logs with provider output, snapshots, or data output;
- runtime, dashboard, scoring, broker, alert, recommendation, SafeBoot, or BootReady writes;
- changing `approval_ref` from null;
- marking any row formally approved.

## Status After This Artifact

- `five_rows = probe_approved_not_executed`
- `formal_approval_ref = null`
- `permission_truth = not_closed`
- `execution_status = awaiting_separate_local_human_run`
- `data_output_status = blocked`
- `next_packet = V2-D0.4D LOCAL HUMAN PROBE EXECUTION PACKET`

## Public Documentation Basis

WRDS public materials describe web, cloud, local programming, and Python access paths for registered users, while WRDS Terms require credential confidentiality and prohibit attempts to access non-subscribed data or features. This basis supports a narrow local human permission-probe approval only; it does not authorize data extraction or prove formal table entitlement.

Sources:

- https://wrds-www.wharton.upenn.edu/pages/about/3-ways-use-wrds/
- https://wrds-www.wharton.upenn.edu/pages/grid-items/using-python-wrds-platform/
- https://wrds-www.wharton.upenn.edu/users/tou/

## D0.4D Queue

D0.4D is queued as the next packet and is the first place a local human may run the approved probe. D0.4D may record only the allowed output shape above. D0.4C itself stays docs-only and executes nothing.

## Formal Override — 2026-06-18

**Override authority**: User explicit verbal instruction ("正式解除"), session 2026-06-18 12:22 UTC+8.
**Scope of override**: One-time Codex-assisted local execution of the D0.4D probe script is permitted.
**Credentials**: User explicitly directed Codex to read `secret.txt` for this single execution. Credentials are used in-memory only; not committed, not logged to repo artifacts.
**Duo Push**: User must approve on enrolled device during script run.
**Remaining constraints still in force**: LIMIT 0 only, no data extraction, no discovery, redacted JSON output shape only.
