# V2-D0.4B WRDS Local Auth Method Confirmed

Status: WRDS_LOCAL_AUTH_USER_ATTESTED_AVAILABLE; FORMAL_PERMISSION_TRUTH_NOT_CLOSED
Authority: correction artifact only; this is not execution approval, row approval, provider access approval, or data-output approval.
Date: 2026-06-03
RoundID: ROUND-20260603-V2-D0-4B-WRDS-LOCAL-AUTH-METHOD-CONFIRMED
ScopeID: V2_D0_4B_WRDS_LOCAL_AUTH_METHOD_CONFIRMED_NO_EXECUTION

## Correction

Replace the overbroad stance `WRDS/provider access blocked` with:

`WRDS local authentication method is user-attested available through user-owned local credentials, but actual login has not been verified by Codex/subagents, credentials were not read, and formal table-level permission truth is not closed.`

## Required State

- `local_auth_method = user_attested_local_auth_available`
- `actual_login_verified_by_agent = false`
- `credentials = local_only_do_not_read_do_not_quote_do_not_commit`
- `secret_txt = do_not_read_do_not_quote_do_not_use`
- `formal_approval_ref = null`
- `permission_truth = not_closed`
- `wrds_execution = governance_blocked_until_probe_approval`
- `s_and_p_capital_iq_pro = deferred_fallback`

## SAW / Governance Status Fields

- `WRDS_LOCAL_AUTH_USER_ATTESTED_AVAILABLE`
- `FORMAL_PERMISSION_TRUTH_NOT_CLOSED`
- `ALLOW_LOCAL_READ_ONLY_PERMISSION_PROBE_PLAN_ONLY`
- `BLOCK_PROBE_EXECUTION_UNTIL_SEPARATE_APPROVAL`
- `BLOCK_DATA_OUTPUT_RUNTIME_SNAPSHOTS`

## Row State

| library.table | probe_plan_status | approval_status | approval_ref |
|---|---|---|---|
| `crsp.dsf` | `probe_plan_pending` | `not_approved` | null |
| `crsp.stocknames` | `probe_plan_pending` | `not_approved` | null |
| `crsp.ccmxpf_linktable` | `probe_plan_pending` | `not_approved` | null |
| `comp.fundq` | `probe_plan_pending` | `not_approved` | null |
| `ibes.det_epsus` | `probe_plan_pending` | `not_approved` | null |

## Allowed In This Artifact

- Status correction from overbroad provider-access blocked language to user-attested local auth availability.
- Hard-coded read-only permission probe plan outline.
- Validation rules for a future permission probe plan.
- No-execution guardrails.

## Hard-Coded Probe Plan Outline

This outline is plan-only and cannot be executed until separate explicit approval is recorded.

1. Confirm the future probe is local read-only permission truth only.
2. Use user-owned local credentials without Codex reading, quoting, printing, storing, or committing them.
3. Check only the five listed library.table permission targets.
4. Record only permission truth states allowed by a future approval packet.
5. Emit no provider data, row counts, sample rows, SQL logs with provider output, snapshots, runtime dashboard output, scoring output, broker/order output, or data artifacts.

## Validation Rules

- `actual_login_verified_by_agent` must remain `false` in this artifact.
- `formal_approval_ref` must remain `null`.
- Every row must remain `not_approved`.
- Every row must remain `probe_plan_pending`.
- A future probe cannot execute from this artifact alone.
- A future probe must not expose row counts, sample rows, schema discovery, SQL logs with provider output, snapshots, or dashboard/runtime output.
- `secret.txt` must not be read, quoted, used, tested, validated, or treated as entitlement evidence.

## Forbidden

- Reading, quoting, testing, validating, using, printing, or committing credentials or `secret.txt`.
- WRDS login, SSH, Python WRDS, SAS, SQL, API, or provider execution.
- `list_libraries`, `list_tables`, `describe`, schema discovery, or table discovery.
- Row counts, sample rows, snapshots, SQL logs with provider output, or data output.
- Runtime/dashboard/scoring/broker writes.
- Approval reference fabrication.
- Changing any row to approved.

## Public Documentation Basis

WRDS public documentation describes web, cloud, and local PC/programming access paths, including local language installations and ODBC/JDBC interfaces. WRDS account guidance also states passwords are confidential and not to be shared. This public basis supports only the existence of local/authenticated access methods and credential confidentiality; it does not prove this user's login, table entitlement, or row-level permission truth.

Sources:

- https://wrds-www.wharton.upenn.edu/pages/about/3-ways-use-wrds/
- https://wrds-www.wharton.upenn.edu/pages/about/wrds-account-types/

## Bottom Line

V2-D0.4B confirms a user-attested local authentication method is available, but Codex/subagents did not verify login, did not read credentials, did not use `secret.txt`, did not access WRDS/provider, and did not close formal table-level permission truth.
