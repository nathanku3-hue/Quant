### 分支 · WRDS Credential Control

AI助手:


AI助手:


用户:
Security / Ops / Compliance Expert, ,see https://github.com/nathanku3-hue/Quant: 

Can use current zip plus a small credential/access addendum.
Real question: “How should WRDS credential use, permission probing, local logs, and license boundaries be controlled without leaking secrets or creating unauthorized data outputs?”
AI助手:


AI助手:


AI助手:
I’ll review the GitHub repo and the uploaded packet, then turn the core security/compliance controls into a concise addendum you can drop into the project.

用户:
The output of this plugin was redacted.
用户:
The output of this plugin was redacted.
用户:
The output of this plugin was redacted.
用户:
The output of this plugin was redacted.
用户:
The output of this plugin was redacted.
用户:
The output of this plugin was redacted.
用户:
The output of this plugin was redacted.
用户:
The output of this plugin was redacted.
用户:
The output of this plugin was redacted.
用户:
The output of this plugin was redacted.
用户:
The output of this plugin was redacted.
用户:
The output of this plugin was redacted.
用户:
The output of this plugin was redacted.
AI助手:
I found the repo’s public README still flags WRDS auth as an open operational risk, while the packet is stricter: it treats all provider access, credential handling, snapshots, and data writes as not authorized yet.

用户:
The output of this plugin was redacted.
AI助手:
## 1. Verdict: ADVISORY_PASS

Offline control design passes. **Provider-facing WRDS work remains BLOCKED** until explicit approval and non-secret entitlement evidence exist. Repo status also flags live WRDS auth as unresolved. 

## 2. Required Approval Text For Provider-Facing Work

“Approve **V2-D0.1 WRDS read-only permission probe only** for these `library.table` targets: `[list]`. No credentials in repo/logs/prompts. No data rows, schema dumps, row counts, snapshots, `data/processed` writes, dashboard use, rankings, alerts, broker paths, SQLite, SafeBoot, or BootReady claims. Output limited to a redacted permission matrix: approved/denied/unknown, approval ref, timestamp, operator.”

## 3. Credential / Secret Handling Requirements

Use only the licensed user’s own WRDS account. WRDS requires users to protect usernames/passwords and forbids sharing credentials.  Treat `.pgpass`, env vars, connection URIs, usernames, passwords, raw exceptions, and screenshots as secret-bearing surfaces; PyWRDS can use `.pgpass` and PostgreSQL env vars. 

## 4. Egress and Audit-Log Controls

Deny-by-default egress; allow only `wrds-pgdata.wharton.upenn.edu:9737` over TLS for the approved probe. Audit log must contain only: run id, operator, approval ref, target ids, boolean permission result, sanitized error class, timestamp, tool/version hash. No SQL text, credentials, raw provider logs, rows, schemas, counts, samples, or file paths with secrets.

## 5. Forbidden Files / Commands / Outputs

Forbid `get_table`, `raw_sql` data extraction, exports to CSV/XLSX/pickle/parquet, snapshots, `data/processed`, runtime cache writes unless separately approved. WRDS docs show these APIs can list libraries/tables, query data, and save outputs, so they must stay outside the permission probe. 

## 6. Dirty-Root Authority Model

Dirty/untracked local files are **non-authoritative**. They may inform risk review only. Authority must come from committed contracts, approved evidence, and sanitized matrix artifacts.

## 7. Stop Rules

Stop immediately on missing approval, credential prompt in logs, non-allowlisted egress, unexpected table/library, row/schema/count output, provider throttling/account warning, subscription ambiguity, `.pgpass` exposure, or any attempt to convert probe output into dashboard/runtime/BootReady evidence. WRDS also prohibits actions to access non-subscribed data/features. 

## 8. Confidence: 8/10

## 9. Next action:

Add the approval text above as the credential/access addendum, then collect **non-secret WRDS entitlement evidence** or hold.

用户:
What exact approval text should be required before any provider-facing WRDS probe?
What audit log fields are allowed, and which fields must be forbidden because they may leak credentials, schemas, rows, or license-sensitive info?
What should happen to legacy WRDS scripts before any clean-room probe: quarantine, delete, move, or document as forbidden historical code?
AI助手:


AI助手:
Here’s a precise framework based on WRDS licensing, credential security, and clean-room policy from your repo and packet:

---

## 1. Required Approval Text Before Any Provider-Facing WRDS Probe

Before running **any probe against WRDS**, approval must be documented in writing. The approval should **explicitly include**:

```
Approval granted for V2-D0.1 WRDS read-only permission probe only.
Targets: <approved library.table list>
Operator: <authorized operator>
Approval reference ID: <ticket/approval code>
Constraints:
  - No credentials in repo, logs, prompts, or screenshots.
  - No data rows, schemas, row counts, snapshots, processed outputs, or exports.
  - Only redacted permission matrix allowed (approved/denied/unknown, timestamp, operator, approval ref).
  - Output may not feed dashboards, alerts, rankings, or any runtime code.
Expiration: <date or event triggering re-approval>
```

This ensures legal compliance, prevents secret leakage, and confines results to non-sensitive permission metadata.

---

## 2. Audit Log Fields: Allowed vs Forbidden

**Allowed fields** (safe, non-sensitive):

- `run_id` – unique probe run identifier  
- `operator` – authorized person or service running the probe  
- `approval_ref` – internal approval ticket/code  
- `target_ids` – library/table identifiers (redacted, no row counts)  
- `permission_result` – enum: `approved`, `denied`, `unknown`  
- `sanitized_error_class` – error categories, not full exception text  
- `timestamp` – UTC time of execution  
- `tool_version_hash` – for traceability

**Forbidden fields** (must never appear in logs):

- Raw SQL queries or any text revealing table structure  
- Row-level data, schemas, counts, or sample values  
- Connection strings, usernames, passwords, `.pgpass` contents  
- Screenshots of provider UIs  
- Local file paths containing secrets, snapshots, or caches  
- Any provider throttling/warning messages containing account info  

This ensures **no license-sensitive, row-level, or secret information is leaked**.

---

## 3. Handling Legacy WRDS Scripts Before Clean-Room Probe

Legacy scripts may contain unsafe SQL or credentials. Recommended policy:

- **Quarantine**: Move scripts to a secure, non-executable archive (`/quarantine/legacy_wrds`)  
- **Document**: Maintain a manifest listing:
  - Script name
  - Original purpose
  - Any observed sensitive operations (SQL, export, raw logs)  
- **Do not delete immediately**: Retain for auditing or historical reference  
- **Do not run** in any new probe environment until cleaned and re-approved  
- Optionally, flag in version control as `FORBIDDEN_HISTORICAL_CODE`  

This preserves auditability while preventing accidental exposure.

---

Following this framework ensures:

- WRDS credentials never leave authorized accounts  
- All outputs remain non-sensitive  
- Legacy code is isolated to prevent accidental data leakage  

---

If you want, I can **draft a ready-to-insert YAML-style “credential/access addendum”** that enforces these rules for your repo and pipeline. It would include explicit fields, allowed/forbidden logs, and quarantine guidance. Do you want me to create that?

用户:

AI助手:
##Requiredapprovaltextbeforeanyprovider-facingWRDSprobe

Usethisexactapprovalblock.NoWRDSconnectionshouldoccurunlesseverybracketedvalueisfilledandsigned/recorded.

```text
WRDSPROVIDER-FACINGREAD-ONLYPERMISSIONPROBEAPPROVAL

ApprovalID:
Approver:
Approverrole:
ApprovaltimestampUTC:
Operator:
WRDSlicensedaccountowner:
Subscriber/institution:
ConfirmedaccountownerhasacceptedcurrentWRDSTermsofUse:yes/no
ConfirmedaccountownerisauthorizedfortherequestedWRDSservicesundertheSubscriberagreement:yes/no
Confirmednoshared,transferred,embedded,pasted,orrepository-storedWRDScredentialswillbeused:yes/no
Confirmedcredentialsource:interactivelocalpromptorapprovedlocalsecretstoreonly;nosecretsinrepo,logs,prompts,tickets,screenshots,notebooks,orartifacts:yes/no

Approvedscope:
Provider:WRDSonly
Networkdestination:wrds-pgdata.wharton.upenn.edu:9737only,TLSrequired
Executionmode:read-onlypermissionprobeonly
Approvedlibrary.tabletargets:
-[library].[table]
-[library].[table]

Allowedoperation:
Foreachapprovedtarget,attemptonlytheminimumoperationneededtoclassifypermissionasapproved/denied/unknown.
Theprobemustnotextract,print,persist,cache,summarize,ortransformWRDSdata.

Allowedoutput:
Aredactedpermissionmatrixcontainingonly:
approval_id
run_id
timestamp_utc
operator_id
provider=wrds
library
table
dataset_id
permission_status=approved|denied|unknown|error
sanitized_error_class
policy_version
code_ref
tool_version
no_data_output_confirmed=true

Explicitlyforbidden:
Nousername,password,token,.pgpasscontent,connectionURI,DSN,SQLtext,rawexceptiontext,providerbanner,providerlog,tablelist,schema,columnname,rowcount,samplerow,dataframeshape,dataframehead/tail,queryresult,downloadedfile,cachefile,snapshot,CSV,parquet,pickle,SQLitedatabase,data/processedwrite,dashboardintegration,ranking/scoring,recommendation,alert,broker/orderpath,SafeBootclaim,BootReadyclaim,orpromotionclaim.

Stoprule:
Theoperatormuststopimmediatelyandmarktherunblockedifcredentialsappearinanysurface,anunapprovedWRDStargetistouched,anydata/schema/count/sampleisreturned,networkegressisnotallowlisted,theproviderreturnsanaccount/securitywarning,ortheprobeattemptstoproduceanythingbeyondtheredactedpermissionmatrix.

Thisapprovaldoesnotauthorizeingestion,schemadiscovery,snapshotgeneration,deriveddataoutputs,researchclaims,commercialuse,redistribution,oraccesstonon-subscribedWRDSdata/features.
```

ThiswordingisintentionallynarrowbecauseWRDSaccessisforauthorizedusersundersubscriberrestrictions,credentialsmustbekeptconfidentialandnotshared,andactionstoaccessnon-subscribeddata/featuresareprohibited.

##Auditlogfieldsallowed

TheauditlogshouldbeanallowlistedJSONLrecord,notfree-formtext.Allowedfields:

```json
{
"event_type":"wrds_permission_probe",
"run_id":"uuid-or-content-hash",
"approval_id":"non-secretapprovalreference",
"timestamp_utc":"ISO-8601UTC",
"operator_id":"internalnon-secrethandle",
"provider":"wrds",
"network_allowlist_id":"policyreference",
"credential_mode":"interactive_local_prompt|approved_local_secret_store",
"credential_presence_confirmed":true,
"credential_value_logged":false,
"library":"approved_wrds_library_id",
"table":"approved_wrds_table_id",
"dataset_id":"internaldatasetid",
"permission_status":"approved|denied|unknown|error",
"sanitized_error_class":"auth_failed|permission_denied|network_error|provider_error|policy_block|unknown",
"no_rows_returned":true,
"no_schema_returned":true,
"no_counts_returned":true,
"no_output_file_written":true,
"no_cache_written":true,
"policy_version":"credential-access-addendumversion",
"code_ref":"clean-roomprobecoderef",
"tool_version":"wrds/python/driverversiononly",
"commit_sha":"clean-roomprobecommit",
"decision":"record_permission_decision_only|blocked",
"blocked_reason_code":"optionalenum,norawtext"
}
```

Thelogmaycontaintherequested`library.table`identifiersonlywhenthoseidentifierswerealreadyintheapprovedscope.Itmaynotexpandscopebyloggingdiscoveredlibraries,tablelists,schemas,orprovider-returnedalternatives.WRDSPythonexamplesshowthat`list_libraries`,`list_tables`,`describe_table`,`get_table`,and`raw_sql`canexposelibraries,tables,schemas,rowcounts,androws,sotheclean-roomprobemustnotlogthoseoutputs.

##Auditlogfieldsforbidden

Forbidthesefieldnamesandanysynonyms/camelCasevariants.Thevalidatorshouldrejectthewholerecord,notredactafterthefact.

```text
username
wrds_username
user
password
pass
pwd
token
secret
credential
credential_value
pgpass
.pgpass
pgpass_path
env
environment
connection_uri
connection_string
dsn
host_user_combo
mfa_code
duo_code

sql
query
raw_sql
where_clause
columns
column_names
schema
schema_json
describe_table
describe_output
table_list
library_list
discovered_libraries
discovered_tables
row_count
rows
obs
limit
shape
head
tail
sample
preview
dataframe
records
result
query_result
provider_response
raw_exception
traceback
stdout
stderr
notebook_output
screenshot

output_path
snapshot_path
cache_path
csv_path
parquet_path
pickle_path
sqlite_path
data_processed_path
artifact_uri
download_uri
manifest_uri
hash_of_data
data_hash
schema_hash
file_hash
```

Alsoforbid“helpful”aggregatesubstitutessuchas`libraries_found_count`,`tables_found_count`,`schema_column_count`,`first_error_message`,or`available_dataset_count`.Thosecanleaklicense-sensitiveentitlement,schema,andprovider-discoveryinformationevenwithoutrows.

##WhattodowithlegacyWRDSscriptsbeforeaclean-roomprobe

Do**not**merelydocumentthem.Thecorrectsequenceis:

1.**Immediatesecretincidenthandling:**rotate/revokeanyWRDScredentialthatmayhaveappearedincode,logs,`.pgpass`,shellhistory,notebooks,screenshots,CIoutput,orpublicGithistory.Isawcredential-likehard-codinginalivelegacyWRDSfile;Iamnotrepeatingit.WRDSexplicitlyrequiresusername/passwordconfidentialityandsayssharingcredentialscanterminatetheaccount.

2.**Deletesecret-bearingworking-treefiles:**anyfilecontainingaliteralusername/password/tokenmustberemovedfromtheexecutablerepo,notmovedintoa“quarantine”folderwiththesecretintact.

3.**Historycleanup:**becausetherepoispublic,treatexposedcredentialsascompromisedevenafterdeletion.Rotatefirst,thenuseahistory-rewrite/removalprocessforsecret-bearingcommitswherefeasible,andinvalidateanyforks/clones/CIcachesthatmayretainthevalue.

4.**Quarantinenon-secretlegacyWRDScodeasforbiddenhistoricalcode:**provider-facingscriptswithoutembeddedsecretsshouldbemovedoutofrunnablepaths,renamedwithanon-executablesuffixsuchas`.disabled`,anddocumentedina`docs/security/wrds_legacy_quarantine.md`inventory.Theyshouldnotremainas`test_wrds*.py`orrunnablescripts.Theliverepocurrentlylistsseveraltop-levelWRDStest/outputartifacts,including`test_wrds*.py`,`test_wrds_tables.py`,`all_wrds_libs.txt`,schema/outputfiles,andWRDStargetoutputs.

5.**Blockimports/execution:**addCIchecksthatfailon`importwrds`,`wrds.Connection`,`raw_sql`,`get_table`,`describe_table`,`list_tables`,`list_libraries`,`.pgpass`,`wrds_username`,`password`,`bvd_orbis_trial`,andany`data/processed`writeunlessthefileistheapprovedclean-roomprobemoduleandtheapprovalfixtureispresent.

Theclean-roomprobeshouldstartfromanewminimalmodulewithexact-keycontracts.Legacycodemaybepreservedonlyas**redacted,non-executablehistoricalevidence**;secret-bearingversionsshouldnotbepreservedintherepoatall.

用户:
Is the approval text final enough to become the credential/access addendum?
Which audit fields are allowed vs forbidden in machine-checkable form?
Should legacy WRDS scripts be deleted, disabled, quarantined, or history-scrubbed before probe approval?
AI助手:


AI助手:


AI助手:


AI助手:
### 1. Is the approval text final enough to become the credential/access addendum?

**Yes, with one small change.**

The approval text from the prior answer is sufficiently specific to serve as the project's **Credential & Provider Access Addendum v1.0** because it:

- Defines a single authorized activity (read-only permission probe).
- Defines the approval authority.
- Defines approved targets.
- Defines allowed outputs.
- Defines forbidden outputs.
- Defines stop conditions.
- Defines credential handling requirements.
- Defines license-boundary restrictions.
- Defines audit requirements.

The only addition I would make before calling it final is an explicit precedence clause:

```text
Precedence

This Credential & Provider Access Addendum supersedes any conflicting behavior,
examples, scripts, notebooks, tests, historical utilities, READMEs, comments,
or implementation details elsewhere in the repository.

Where a conflict exists, this Addendum controls.
```

And a clean-room clause:

```text
Clean-Room Requirement

Provider-facing execution must occur only through an approved clean-room probe
implementation explicitly referenced by code_ref in the approval record.

Legacy WRDS scripts, notebooks, utilities, and experiments are not approved
execution paths.
```

With those two additions, I would consider it production-ready as a formal access-control addendum.

---

### 2. Machine-checkable audit policy

A machine-enforceable allowlist is preferable to a denylist.

#### Allowed audit schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "event_type",
    "run_id",
    "approval_id",
    "timestamp_utc",
    "operator_id",
    "provider",
    "library",
    "table",
    "permission_status",
    "policy_version",
    "code_ref"
  ],
  "properties": {
    "event_type": {
      "enum": ["wrds_permission_probe"]
    },
    "run_id": {
      "type": "string"
    },
    "approval_id": {
      "type": "string"
    },
    "timestamp_utc": {
      "type": "string"
    },
    "operator_id": {
      "type": "string"
    },
    "provider": {
      "enum": ["wrds"]
    },
    "library": {
      "type": "string"
    },
    "table": {
      "type": "string"
    },
    "permission_status": {
      "enum": [
        "approved",
        "denied",
        "unknown",
        "error"
      ]
    },
    "sanitized_error_class": {
      "enum": [
        "auth_failed",
        "permission_denied",
        "network_error",
        "provider_error",
        "policy_block",
        "unknown"
      ]
    },
    "policy_version": {
      "type": "string"
    },
    "code_ref": {
      "type": "string"
    },
    "tool_version": {
      "type": "string"
    },
    "commit_sha": {
      "type": "string"
    },
    "decision": {
      "enum": [
        "record_permission_decision_only",
        "blocked"
      ]
    },
    "blocked_reason_code": {
      "type": "string"
    },
    "no_rows_returned": {
      "const": true
    },
    "no_schema_returned": {
      "const": true
    },
    "no_counts_returned": {
      "const": true
    },
    "no_output_file_written": {
      "const": true
    },
    "no_cache_written": {
      "const": true
    }
  }
}
```

---

#### Forbidden fields

Machine-checkable forbidden field list:

```json
[
  "username",
  "wrds_username",
  "password",
  "token",
  "secret",
  "credential",
  "credential_value",
  "pgpass",
  "connection_uri",
  "connection_string",
  "dsn",

  "sql",
  "query",
  "raw_sql",

  "schema",
  "schema_json",
  "columns",
  "column_names",

  "row_count",
  "rows",
  "sample",
  "preview",
  "records",
  "result",
  "query_result",

  "table_list",
  "library_list",
  "discovered_tables",
  "discovered_libraries",

  "raw_exception",
  "traceback",
  "stdout",
  "stderr",

  "output_path",
  "snapshot_path",
  "cache_path",

  "csv_path",
  "parquet_path",
  "pickle_path",
  "sqlite_path",

  "download_uri",
  "artifact_uri",

  "provider_response"
]
```

Implementation recommendation:

```python
if set(record.keys()) - ALLOWED_FIELDS:
    reject_log_record()
```

Use an allowlist validator rather than attempting to sanitize a larger log.

---

### 3. What should happen to legacy WRDS scripts?

The answer is **all four actions, applied by category**.

| Script Category | Action |
|----------------|---------|
| Contains credentials/secrets | Delete immediately and rotate credentials |
| Secret-bearing Git history | History-scrub after credential rotation |
| Provider-facing WRDS code without secrets | Quarantine and disable |
| Historical reference material | Preserve only as non-executable documentation |

Recommended policy:

#### A. Secret-bearing files

```text
DELETE
ROTATE
HISTORY-SCRUB
```

Do not quarantine files that still contain credentials.

---

#### B. Executable WRDS utilities

```text
QUARANTINE
DISABLE
```

Move to:

```text
archive/wrds_legacy/
```

Rename:

```text
*.disabled
```

Examples:

```text
test_wrds.py.disabled
wrds_probe_old.py.disabled
wrds_download.py.disabled
```

No executable entrypoints remain.

---

#### C. Historical artifacts

Convert to documentation:

```text
docs/security/wrds_legacy_inventory.md
```

Document:

- filename
- purpose
- date found
- risk classification
- disposition

but not executable code.

---

#### D. Before probe approval

The repository should satisfy:

```text
0 credential-bearing WRDS files
0 runnable WRDS scripts
0 approved provider-facing paths except clean-room probe
0 active exports/snapshots
1 approved clean-room implementation
1 machine-validated audit schema
1 signed approval record
```

### Final recommendation

**Credential/access addendum:** Ready for adoption after adding the precedence clause and clean-room clause.

**Audit policy:** Use a strict allowlist schema with `additionalProperties=false`; reject any record containing fields outside the approved set.

**Legacy WRDS code:**  
- Secret-bearing code → **delete + rotate + history-scrub**.  
- Non-secret WRDS executables → **quarantine and disable**.  
- Historical reference value → **retain only as non-executable documentation**.  

That is the safest and most defensible control posture before any WRDS probe approval is granted.

用户:
Is the approval text final enough to become the credential/access addendum?
Which audit fields are allowed vs forbidden in machine-checkable form?
Should legacy WRDS scripts be deleted, disabled, quarantined, or history-scrubbed before probe approval?
AI助手:


AI助手:


AI助手:


AI助手:
## 1. Is the approval text final enough to become the credential/access addendum?

**Yes.** I would classify it as **READY_TO_ADOPT** with only two minor hardening edits:

### Addendum Status
```text
Status: APPROVED FOR ADOPTION
Version: 1.0
Applies to: All WRDS-related code, probes, credentials, logs, artifacts, CI jobs, notebooks, scripts, and operators.
Authority: This addendum overrides any less restrictive WRDS handling guidance elsewhere in the repository.
```

### Additional Clause A — Approval Expiration
```text
Probe approval expires after 30 calendar days unless renewed.

Any change to:
- approved datasets
- approved tables
- approved libraries
- operator
- institution
- WRDS account owner
- probe implementation

requires a new approval.
```

### Additional Clause B — Evidence Classification
```text
Permission-matrix evidence is operational evidence only.

Permission results shall not be interpreted as:
- entitlement confirmation
- subscription confirmation
- data availability confirmation
- production readiness
- SafeBoot readiness
- BootReady readiness
- research readiness
- deployment readiness

Additional approvals remain required.
```

With those additions, the approval text is sufficiently precise to serve as the repository's credential/access addendum.

---

# 2. Machine-checkable audit policy

Instead of prose, define explicit allowlists and denylists.

## Allowed Fields

```json
{
  "allowed_fields": [
    "event_type",
    "run_id",
    "approval_id",
    "timestamp_utc",
    "operator_id",
    "provider",
    "network_allowlist_id",
    "credential_mode",
    "credential_presence_confirmed",
    "credential_value_logged",
    "library",
    "table",
    "dataset_id",
    "permission_status",
    "sanitized_error_class",
    "no_rows_returned",
    "no_schema_returned",
    "no_counts_returned",
    "no_output_file_written",
    "no_cache_written",
    "policy_version",
    "code_ref",
    "tool_version",
    "commit_sha",
    "decision",
    "blocked_reason_code"
  ]
}
```

### Required Fields

```json
{
  "required_fields": [
    "event_type",
    "run_id",
    "approval_id",
    "timestamp_utc",
    "operator_id",
    "provider",
    "permission_status",
    "policy_version",
    "code_ref"
  ]
}
```

### Enumerations

```json
{
  "permission_status": [
    "approved",
    "denied",
    "unknown",
    "error"
  ],
  "sanitized_error_class": [
    "auth_failed",
    "permission_denied",
    "network_error",
    "provider_error",
    "policy_block",
    "unknown"
  ]
}
```

---

## Forbidden Fields

Any occurrence of these keys should fail validation.

```json
{
  "forbidden_fields": [
    "username",
    "wrds_username",
    "password",
    "pwd",
    "token",
    "secret",
    "credential",
    "credential_value",
    "pgpass",
    "connection_uri",
    "connection_string",
    "dsn",

    "sql",
    "query",
    "raw_sql",
    "where_clause",

    "rows",
    "row_count",
    "records",
    "result",
    "query_result",

    "columns",
    "column_names",
    "schema",
    "schema_json",
    "describe_table",

    "table_list",
    "library_list",
    "discovered_tables",
    "discovered_libraries",

    "dataframe",
    "head",
    "tail",
    "sample",
    "preview",
    "shape",

    "stdout",
    "stderr",
    "traceback",
    "raw_exception",

    "output_path",
    "snapshot_path",
    "cache_path",

    "csv_path",
    "parquet_path",
    "pickle_path",
    "sqlite_path",

    "artifact_uri",
    "download_uri",

    "data_hash",
    "schema_hash",
    "file_hash"
  ]
}
```

### Validation Rule

```text
Policy:
additionalProperties = false
```

Meaning:

```text
If a field is not explicitly allowlisted,
the log record is invalid.
```

That is significantly safer than trying to maintain an ever-growing denylist.

---

# 3. What should happen to legacy WRDS scripts?

The answer is **all four actions, in sequence**, depending on script contents.

## Category A — Contains credentials or secrets

Examples:

```python
username="..."
password="..."
```

Action:

```text
1. Revoke/rotate credential.
2. Delete working-tree copy.
3. History-scrub repository.
4. Remove from CI caches.
5. Remove from release artifacts.
```

Disposition:

```text
DELETE + HISTORY-SCRUB
```

Not quarantine.

Not disable.

Not archive.

Secrets should not remain preserved.

---

## Category B — No secrets, but provider-facing

Examples:

```python
wrds.Connection()
db.raw_sql(...)
db.get_table(...)
db.describe_table(...)
```

Action:

```text
1. Move out of runnable paths.
2. Rename *.disabled.
3. Mark as historical.
4. Exclude from CI.
5. Record in quarantine inventory.
```

Disposition:

```text
DISABLE + QUARANTINE
```

Not delete.

These files may have audit value.

---

## Category C — Generated WRDS outputs

Examples:

```text
all_wrds_libs.txt
wrds_tables.txt
schema dumps
permission dumps
snapshot manifests
exports
```

Action:

```text
1. Review for license-sensitive content.
2. Remove from active repo.
3. Preserve only if approved.
4. Otherwise delete.
```

Disposition:

```text
QUARANTINE PENDING REVIEW
```

---

## Category D — Clean-room replacement

Action:

```text
Create entirely new probe code.

No code copied from legacy scripts.

New code starts from:
- approval contract
- permission matrix contract
- audit contract
- stop rules
```

Disposition:

```text
NEW IMPLEMENTATION ONLY
```

---

# Final recommendation

For governance purposes:

```text
Credential/Addendum Status:
READY_TO_ADOPT

Audit Policy:
Allowlist-only
(additionalProperties = false)

Legacy WRDS Scripts:
A) Secret-bearing → DELETE + HISTORY-SCRUB
B) Provider-facing but non-secret → DISABLE + QUARANTINE
C) Existing WRDS outputs/artifacts → QUARANTINE FOR REVIEW
D) Future probe → CLEAN-ROOM REIMPLEMENTATION
```

That is the most defensible security, operations, and compliance posture before granting any WRDS probe approval.

用户:
Is the approval text final enough to become the credential/access addendum?
Which audit fields are allowed vs forbidden in machine-checkable form?
Should legacy WRDS scripts be deleted, disabled, quarantined, or history-scrubbed before probe approval?
用户:

AI助手:
Yes—theapprovaltextis**finalenoughtobecomethecredential/accessaddendum**onceitismadeversioned,signed,target-specific,andexpiry-limited.Itshouldbetreatedasa**hardprecondition**,notguidance.

Provider-facingWRDSworkshouldremain**blocked**unlesstheaddendumhasafilledapprovalID,namedapprover,namedoperator,approved`library.table`allowlist,confirmationofWRDSauthorization,confirmationthatcredentialsarenotshared/stored/logged,andashortexpiry.WRDSaccessisrestrictedtoauthorizedusersunderthesubscriberagreement,usersmustprotectWRDSusernames/passwords,andactionstoaccessnon-subscribeddataorfeaturesareprohibited.

##1.Finaladdendumstatus

Usethisstatus:

```text
STATUS:FINALFORCONTROLUSE

Thiscredential/accessaddendumissufficienttogateWRDSprovider-facingpermissionprobes.

NoWRDSnetworkconnection,login,library/tableprobe,SQLexecution,permissioncheck,
orproviderinteractionmayoccurunlessthisaddendumiscompleted,approved,inforce,
target-specific,andrecordedbeforeexecution.

Thisaddendumauthorizesonlyaread-only,minimalWRDSpermissionclassificationprobe.
Itdoesnotauthorizedataextraction,schemadiscovery,entitlementdiscovery,rowcounts,
samples,snapshots,cachewrites,dashboardintegration,model/runtimeuse,commercialuse,
redistribution,oraccesstonon-subscribedWRDSdata/features.
```

Iwouldaddtheserequiredmetadatafieldstomakeitoperationallyfinal:

```yaml
addendum_id:"wrds-credential-access-addendum-v1"
approval_id:"required"
approval_status:"approved"
approver_name_or_ref:"required"
approver_role:"PI|DataOwner|Compliance|InstitutionalWRDSAdmin"
operator_ref:"required_non_secret_internal_ref"
wrds_account_owner_ref:"required_non_secret_internal_ref"
subscriber_or_institution_ref:"required"
approval_timestamp_utc:"required"
expires_at_utc:"required_max_14_days_after_approval"
approved_provider:"wrds"
approved_host:"wrds-pgdata.wharton.upenn.edu"
approved_port:9737
tls_required:true
approved_targets:
-"library.table"
annual_wrds_terms_confirmed:true
subscriber_authorization_confirmed:true
no_shared_credentials_confirmed:true
no_repo_credentials_confirmed:true
no_log_credentials_confirmed:true
no_data_output_authorized:true
no_schema_output_authorized:true
no_snapshot_authorized:true
```

##2.Machine-checkableallowedauditschema

Useanallowlistschemawith`additionalProperties:false`.Thatmattersmorethanredaction.

```json
{
"$schema":"https://json-schema.org/draft/2020-12/schema",
"$id":"wrds-permission-probe-audit-v1.schema.json",
"title":"WRDSclean-roompermissionprobeauditrecord",
"type":"object",
"additionalProperties":false,
"required":[
"schema_version",
"event_type",
"run_id",
"approval_id",
"approval_scope_hash",
"timestamp_utc",
"operator_ref",
"provider",
"egress_policy_id",
"egress_host",
"egress_port",
"tls_required",
"auth_mode",
"auth_value_persisted",
"target_library",
"target_table",
"target_id",
"operation",
"permission_status",
"sanitized_error_class",
"blocked_reason_code",
"rows_returned",
"schema_returned",
"row_count_returned",
"output_file_written",
"cache_written",
"raw_provider_payload_logged",
"freeform_text_logged",
"policy_version",
"code_ref",
"commit_sha",
"tool_version"
],
"properties":{
"schema_version":{
"const":"wrds_permission_probe_audit_v1"
},
"event_type":{
"const":"wrds_permission_probe"
},
"run_id":{
"type":"string",
"pattern":"^[0-9a-fA-F-]{32,36}$"
},
"approval_id":{
"type":"string",
"pattern":"^[A-Za-z0-9_.:-]{6,128}$"
},
"approval_scope_hash":{
"type":"string",
"pattern":"^sha256:[a-f0-9]{64}$"
},
"timestamp_utc":{
"type":"string",
"format":"date-time"
},
"operator_ref":{
"type":"string",
"pattern":"^(op|operator)_[A-Za-z0-9_.:-]{6,128}$"
},
"provider":{
"const":"wrds"
},
"egress_policy_id":{
"type":"string",
"pattern":"^[A-Za-z0-9_.:-]{3,128}$"
},
"egress_host":{
"const":"wrds-pgdata.wharton.upenn.edu"
},
"egress_port":{
"const":9737
},
"tls_required":{
"const":true
},
"auth_mode":{
"enum":[
"interactive_local_prompt",
"approved_local_secret_store"
]
},
"auth_value_persisted":{
"const":false
},
"target_library":{
"type":"string",
"pattern":"^[a-z][a-z0-9_]{0,63}$"
},
"target_table":{
"type":"string",
"pattern":"^[a-z][a-z0-9_]{0,63}$"
},
"target_id":{
"type":"string",
"pattern":"^[a-z][a-z0-9_]{0,63}\\.[a-z][a-z0-9_]{0,63}$"
},
"operation":{
"const":"minimal_permission_classification"
},
"permission_status":{
"enum":[
"approved",
"denied",
"unknown",
"blocked",
"error"
]
},
"sanitized_error_class":{
"enum":[
"none",
"auth_failed",
"permission_denied",
"network_error",
"provider_error",
"provider_warning",
"policy_block",
"unknown"
]
},
"blocked_reason_code":{
"enum":[
"none",
"missing_approval",
"expired_approval",
"unapproved_target",
"egress_violation",
"auth_value_exposure_detected",
"data_or_schema_returned",
"row_count_returned",
"output_write_attempted",
"cache_write_attempted",
"license_ambiguity",
"provider_warning",
"legacy_code_detected",
"dirty_root",
"unknown"
]
},
"rows_returned":{
"const":false
},
"schema_returned":{
"const":false
},
"row_count_returned":{
"const":false
},
"output_file_written":{
"const":false
},
"cache_written":{
"const":false
},
"raw_provider_payload_logged":{
"const":false
},
"freeform_text_logged":{
"const":false
},
"policy_version":{
"type":"string",
"pattern":"^[A-Za-z0-9_.:-]{3,128}$"
},
"code_ref":{
"type":"string",
"pattern":"^[A-Za-z0-9_./:-]{3,200}$"
},
"commit_sha":{
"type":"string",
"pattern":"^[a-f0-9]{7,40}$"
},
"tool_version":{
"type":"string",
"pattern":"^[A-Za-z0-9_.:+-]{1,80}$"
}
}
}
```

Thisschemaallowsonlyanarrowpermissionmatrixauditrecord.Itdoes**not**allowrawSQL,tablediscoveryoutput,schemametadata,rows,samples,resultshapes,filepaths,rawprovidererrors,stdout/stderr,orcredentials.ThatisnecessarybecauseWRDSPythonusagesupportslogin,librarylisting,tablelisting,dataqueries,rawSQL,row-limitedextraction,andlocalexportformats,allofwhichareoutsidetheclean-roompermissionprobe.

##3.Machine-checkableforbiddenfields

Usethisasthescannercontractforauditlogs,artifacts,notebooks,CIlogs,locallogs,andpermissionoutputs.Theallowedauditschemaaboveshouldbeappliedfirst;thisforbiddenlistshouldthenbeusedacrossallotherfilesandruntimesurfaces.

```yaml
wrds_forbidden_audit_and_artifact_fields_v1:
reject_freeform_fields:
-message
-detail
-details
-reason
-description
-comment
-note
-notes
-stdout
-stderr
-traceback
-exception
-raw_exception
-provider_response
-provider_payload
-response_body

reject_auth_secret_fields:
-username
-user_name
-wrds_username
-userid
-user_id
-password
-passwd
-pwd
-pass
-token
-api_key
-secret
-credential
-credentials
-credential_value
-auth_value
-pgpass
-.pgpass
-pgpass_path
-connection_uri
-connection_url
-connection_string
-dsn
-database_url
-env
-environment
-mfa_code
-duo_code

reject_query_fields:
-sql
-raw_sql
-query
-query_text
-statement
-where
-where_clause
-select
-from
-join
-columns
-column
-column_names
-date_cols
-obs
-limit

reject_discovery_fields:
-library_list
-libraries
-discovered_libraries
-table_list
-tables
-discovered_tables
-describe_table
-schema
-schema_json
-schema_hash
-column_count
-table_count
-library_count
-available_dataset_count

reject_data_fields:
-rows
-row
-row_count
-count
-counts
-records
-result
-results
-query_result
-dataframe
-df
-shape
-dtypes
-head
-tail
-sample
-preview
-values
-data
-data_hash
-hash_of_data

reject_output_location_fields:
-output
-output_path
-output_file
-artifact
-artifact_uri
-download_uri
-manifest_uri
-snapshot
-snapshot_path
-cache
-cache_path
-csv_path
-parquet_path
-pickle_path
-xlsx_path
-excel_path
-sqlite_path
-database_path
-data_processed_path

reject_value_patterns:
-"(?i)postgresql://"
-"(?i)postgres://"
-"(?i)wrds-pgdata\\.wharton\\.upenn\\.edu.*:"
-"(?i)password\\s*="
-"(?i)passwd\\s*="
-"(?i)PGPASSWORD"
-"(?i)PGUSER"
-"(?i)PGPASSFILE"
-"(?i)\\.pgpass"
-"(?i)select\\s+.+\\s+from\\s+"
-"(?i)conn\\.raw_sql"
-"(?i)conn\\.get_table"
-"(?i)conn\\.list_tables"
-"(?i)conn\\.list_libraries"
-"(?i)to_csv\\("
-"(?i)to_pickle\\("
-"(?i)to_parquet\\("
-"(?i)to_excel\\("
-"(?i)to_sql\\("
```

Theauditwritershouldfailclosed:ifafieldisnotintheallowlist,rejecttherecord.Ifaforbiddenkeyorvaluepatternappearsanywhereinlogsorartifacts,marktherun`blocked`anddonotpublishthepermissionmatrix.

##4.LegacyWRDSscripts:delete,disable,quarantine,orscrub?

Useallfour,dependingonrisk.Thecorrectansweris**notoneaction**.

|Legacyitemtype|Requiredactionbeforeprobeapproval|
|---|---|
|Anyscript,notebook,log,config,shellhistory,CIoutput,orartifactcontainingWRDSusername/password/token/connectionstring/`.pgpass`content|**Rotatecredentialsimmediately,deletefromworkingtree,andhistory-scrubifcommittedorpushed.**Treatascompromised.|
|Anycommittedsecret-bearingfileinapublicorsharedrepo|**History-scrubpluscredentialrotation.**DeletingonlythelatestfileisinsufficientbecauseGithistory,forks,caches,andclonesmayretainit.|
|Non-secretbutrunnableWRDSscriptsusing`wrds.Connection`,`raw_sql`,`get_table`,`list_tables`,`list_libraries`,exports,orbroaddiscovery|**Disableandquarantineoutsiderunnable/importablepaths.**Renamewith`.disabled`ormoveunderaclearlynon-executablequarantinedirectory.|
|Non-secrethistoricalcodeneededforauditcontext|**Documentasforbiddenhistoricalcode**,withpurpose,risk,last-seenpath,andreplacementclean-roommodule.Donotkeepitrunnable.|
|WRDSoutputartifacts:tablelists,librarylists,schemadumps,counts,CSV/parquet/pickle/xlsx/sqliteoutputs,manifests,snapshots|**Deletefromexecutable/releaseartifacts;quarantineonlyiflegal/compliancerequiresretention.**Donotuseasevidenceforapproval.|
|Unknownordirty-rootWRDS-relatedfiles|**Blockprobeapprovaluntiltriaged.**Unknownfilesarenotauthoritative.|

Finalpolicy:

```text
Beforeclean-roomWRDSprobeapproval:

1.Secret-bearinglegacyWRDSmaterial:rotate,delete,andhistory-scrub.
2.Non-secretrunnableWRDSmaterial:disableandquarantine.
3.Non-secrethistoricalmaterialneededforaudit:documentasforbiddenhistoricalcode.
4.WRDS-derivedoutputs,schemas,tablelists,samples,counts,andsnapshots:deleteorcompliance-quarantine;neveruseasprobeinput.
5.Dirty/untrackedWRDSfiles:blockapprovaluntilreviewed.
6.Onlythenewclean-roomprobemodulemaybeexecutable,andonlywithavalidcredential/accessaddendum.
```

Sotheapprovalsequenceshouldbe:

```text
BLOCKprovider-facingprobe
→triagelegacyWRDSfiles
→rotate/scrubanyexposedcredentials
→deleteorcompliance-quarantineWRDS-derivedoutputs
→disable/quarantinenon-secretlegacyscripts
→documentforbiddenhistoricalcode
→verifycleantreeandCIscannerpass
→approvetarget-specificcredential/accessaddendum
→runclean-roomminimalpermissionprobeonly
→emitschema-validatedredactedauditrecordonly
```

Myfinalrecommendation:**approvetheaddendumtextasfinalforpolicyuse,butdonotapproveanyactualWRDSprobeuntillegacyWRDSmaterialisremovedfromrunnablepaths,anyexposedsecretsarerotatedandhistory-scrubbed,andtheauditschemaaboveisenforcedfail-closed.**

用户:
Exact approval text before WRDS probe?
Allowed vs forbidden audit-log fields?
What to do with legacy WRDS scripts?
AI助手:


AI助手:


AI助手:
Here’s a clear, final summary for all three questions:

---

## 1. Exact approval text before any WRDS probe

```text
WRDS PROVIDER-FACING READ-ONLY PERMISSION PROBE APPROVAL

Approval ID:
Approver:
Approver role:
Approval timestamp UTC:
Operator:
WRDS licensed account owner:
Subscriber / institution:
Confirmed account owner has accepted current WRDS Terms of Use: yes/no
Confirmed account owner is authorized for the requested WRDS services under the Subscriber agreement: yes/no
Confirmed no shared, transferred, embedded, pasted, or repository-stored WRDS credentials will be used: yes/no
Confirmed credential source: interactive local prompt or approved local secret store only; no secrets in repo, logs, prompts, tickets, screenshots, notebooks, or artifacts: yes/no

Approved scope:
Provider: WRDS only
Network destination: wrds-pgdata.wharton.upenn.edu:9737 only, TLS required
Execution mode: read-only permission probe only
Approved library.table targets:
  - [library].[table]
  - [library].[table]

Allowed operation:
For each approved target, attempt only the minimal operation needed to classify permission as approved / denied / unknown.
The probe must not extract, print, persist, cache, summarize, or transform WRDS data.

Allowed output:
A redacted permission matrix containing only:
  approval_id
  run_id
  timestamp_utc
  operator_id
  provider = wrds
  library
  table
  dataset_id
  permission_status = approved | denied | unknown | error
  sanitized_error_class
  policy_version
  code_ref
  tool_version
  no_data_output_confirmed = true

Explicitly forbidden:
No username, password, token, .pgpass content, connection URI, DSN, SQL text, raw exception text, provider banner, provider log, table list, schema, column name, row count, sample row, dataframe shape, dataframe head/tail, query result, downloaded file, cache file, snapshot, CSV, parquet, pickle, SQLite database, data/processed write, dashboard integration, ranking/scoring, recommendation, alert, broker/order path, SafeBoot claim, BootReady claim, or promotion claim.

Stop rule:
The operator must stop immediately and mark the run blocked if credentials appear in any surface, an unapproved WRDS target is touched, any data/schema/count/sample is returned, network egress is not allowlisted, the provider returns an account/security warning, or the probe attempts to produce anything beyond the redacted permission matrix.

This approval does not authorize ingestion, schema discovery, snapshot generation, derived data outputs, research claims, commercial use, redistribution, or access to non-subscribed WRDS data/features.
```

---

## 2. Allowed vs forbidden audit-log fields

**Allowed fields** (for machine-checkable audit records):

- `run_id`, `approval_id`, `timestamp_utc`, `operator_ref`
- `provider = wrds`, `egress_host = wrds-pgdata.wharton.upenn.edu`, `egress_port = 9737`, `tls_required = true`
- `auth_mode = interactive_local_prompt | approved_local_secret_store`
- `target_library`, `target_table`, `target_id`
- `operation = minimal_permission_classification`
- `permission_status = approved | denied | unknown | blocked | error`
- `sanitized_error_class = none | auth_failed | permission_denied | network_error | provider_error | provider_warning | policy_block | unknown`
- `blocked_reason_code` (enumerated: missing_approval, expired_approval, unapproved_target, egress_violation, auth_value_exposure_detected, data_or_schema_returned, row_count_returned, output_write_attempted, cache_write_attempted, license_ambiguity, provider_warning, legacy_code_detected, dirty_root, unknown)
- `rows_returned = false`, `schema_returned = false`, `row_count_returned = false`
- `output_file_written = false`, `cache_written = false`
- `raw_provider_payload_logged = false`, `freeform_text_logged = false`
- `policy_version`, `code_ref`, `commit_sha`, `tool_version`

**Forbidden fields** (must never appear; block the record if present):

- Any credentials: `username`, `wrds_username`, `password`, `pwd`, `token`, `.pgpass`, `connection_uri`, `dsn`, `env`, `mfa_code`, `duo_code`, etc.
- Any SQL or query: `sql`, `raw_sql`, `query`, `statement`, `columns`, `where_clause`, etc.
- Discovery / schema / table lists: `library_list`, `table_list`, `discovered_libraries`, `discovered_tables`, `describe_table`, `schema`, `column_count`, etc.
- Data content / outputs: `rows`, `row_count`, `records`, `result`, `dataframe`, `df`, `head`, `tail`, `sample`, `shape`, `values`
- Output locations: `output_path`, `snapshot_path`, `cache_path`, `csv_path`, `parquet_path`, `pickle_path`, `sqlite_path`, `data_processed_path`
- Any freeform or raw provider responses, stdout/stderr, tracebacks, or notes that could leak secrets or schema info

*Validator should fail-closed: any forbidden key or value pattern appearing anywhere in logs or artifacts blocks the probe.*

---

## 3. What to do with legacy WRDS scripts

| Type | Required action before probe approval |
|------|--------------------------------------|
| Secret-bearing legacy scripts, notebooks, logs, configs, shell history, CI output | **Rotate credentials, delete from working tree, history-scrub** |
| Non-secret but runnable WRDS scripts (using `wrds.Connection`, `raw_sql`, `get_table`, `list_tables`, `list_libraries`, exports) | **Disable & quarantine** (`.disabled` suffix or quarantine folder) |
| Non-secret historical code needed for audit context | **Document as forbidden historical code**; do not keep runnable |
| WRDS output artifacts (tables, schemas, snapshots, CSV/parquet/pickle outputs) | **Delete from executable/release artifacts**; quarantine only for legal/compliance retention |
| Unknown or dirty-root WRDS-related files | **Block approval until reviewed** |

**Sequence before running clean-room probe:**

1. Block probe until legacy materials are triaged.
2. Rotate/revoke any exposed credentials.
3. Delete or history-scrub secret-bearing files.
4. Disable/quarantine non-secret runnable WRDS scripts.
5. Document non-secret historical code.
6. Delete or compliance-quarantine any WRDS outputs.
7. Verify clean working tree and CI scan passes.
8. Approve addendum with target-specific metadata.
9. Run clean-room minimal permission probe only.
10. Emit schema-validated, redacted audit record.  

---

This forms a complete **credential/access addendum, audit log schema, and legacy code policy** suitable for compliance and operational enforcement.

用户:
Exact approval text before WRDS probe?
Allowed vs forbidden audit-log fields?
What to do with legacy WRDS scripts?
用户:

