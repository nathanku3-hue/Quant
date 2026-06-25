### ZIP file extraction query

AI助手:


AI助手:


用户:
Architecture / Governance Expert, see https://github.com/nathanku3-hue/Quant:
 “Should the project proceed to read-only WRDS probe from a clean isolated surface, or must dirty-root classification happen first?”

AI助手:


AI助手:
I can help analyze the governance and architecture implications for your WRDS probe question. To give a precise recommendation, I need to review the contents of the uploaded expert packet first. I’ll start by inspecting what’s inside your ZIP file.

AI助手:
It looks like my current environment has too many active sessions to open the ZIP file directly. Let’s work around this by first identifying the file type inside the ZIP and then selectively extracting it.  

Can you confirm if you want me to extract **all files** from the ZIP for analysis, or just the **main report or instructions**?

用户:

AI助手:
##Governanceverdict

**Donotruntheread-onlyWRDSprobeyet.**Thenextauthorizedstepis**V2-D0.1WRDSpermission-truthauthorization**:collectnon-secretentitlementevidenceandexplicitapprovaltext.

Betweenthetwooptionsyougave,myansweris:

**Acleanisolatedprobesurfaceistherighteventualpath;dirty-rootclassificationdoesnothavetobecompletedfirstonlyiftheprobesurfaceisgenuinelyclean,separatelyreviewed,andnotderivedfromorexecutedinsidethedirtyroot.**

Buttheprojectis**notclearedtoprobetoday**,becausetheuploadedpacketexplicitlysaystheprobeisdeferreduntilexactWRDSentitlementevidenceexists.

##Why

Theuploaded`README_DECISION_CARD.md`andreconciledverdictsaythepacketis**ADVISORY_PASS/PATCH_RESOLVED**,but**doesnotauthorizeWRDS/provideraccessorread-onlyprobeexecution**.Theapprovednextstreamisonly:collectnon-secretWRDSentitlementevidenceandapprovaltextbeforeanyread-onlypermissionprobecanevenbeproposed.

Thepacket’sowndirty-rootlanguageisalsoimportant:dirty-rootevidenceis**non-authoritative**andshouldbebypassedbyusing**cleanreviewedfilesonly**.Thatmakesdirty-rootclassificationablockerforroot-basedclaims,merge-back,BootReady/SafeBoot,runtimeintegration,snapshots,dashboardreader,orpromotion,butnotnecessarilyablockerforasealedclean-roompermissionprobe.

ThereisanadditionalgovernanceredflaginthepublicGitHubrepo:public`main`stillexposesWRDS-orientedscriptsatthetoplevel,includingexecutableWRDSconnectioncode,andonerawfilecontainsahard-codedcredential-likevaluethatIwillnotrestate.Thatmeans**donottreatthecurrentpublicreporootasacleanprobesurface**.TherepoalsodescribesthecurrentpublicstateasPhase61,withliveWRDSauthenticationstillfailingandprovenancerelyingonaboundedbedrockfallback,whichisolder/differentfromtheJune2V2-D0packet.

##Requiredorder

1.**Immediatesecurityhygiene:**rotate/revokeanyexposedWRDScredentialifreal,removeorquarantinecommittedcredential-bearing/probescriptsfromanyfutureauthoritysurface,andensureno`.env`,`.pgpass`,WRDSconfig,rawproviderlogs,orhard-codedcredentialvaluesarepresent.

2.**V2-D0.1permission-truthauthorization:**collectthenon-secretevidencenamedinthepacket:WRDSaccount/licenseowner,approvedaccountscope,exact`library.table`permissions,license/accessconstraints,date/as-ofcoverage,`approval_ref`perapprovedrow,andexplicittextlimitingtheactionto**“read-onlypermissionprobeonly;nosnapshot/dataoutput.”**

3.**Cleanisolatedprobesurface:**createaminimalworktree/container/packagefromreviewedV2-D0/V2-D0.1filesonly.Itmustexcludethedirty/publicrootWRDSscripts,outputfiles,runtimepaths,`data/**`,`data/processed/**`,`data/registry/**`,SQLite,dashboardcode,brokerpaths,andcredentials.

4.**Separateprobeapproval:**onlyaftersteps1–3shouldaread-onlyprobeprotocolbeapproved.Theprobeshoulduseout-of-reposecretinjection,producenorawproviderdata,nosnapshots,nocommittedoutput,nodashboard/runtimewrites,andnoBootReady/SafeBootclaims.

5.**Dirty-rootclassificationlater:**classifythedirtyrootbeforeanymerge-back,useofrootartifactsasevidence,snapshotgeneration,dashboardreader,datawrite,runtimeintegration,scoring/ranking,promotion,orreadinessclaim.

##Decisionrule

**Iftheprobewillrunfromthecurrentreporootorfromanythingcopiedbroadlyoutofit,dirty-rootclassificationmusthappenfirst.**

**Iftheprobewillrunfromanewlycreated,attestedcleansurfacecontainingonlyreviewedV2-D0.1probefiles,thendirty-rootclassificationcanbedeferred.**Inthatcase,thedirtyrootremainsquarantinedandnon-authoritative.

Myrecommendeddecisiontext:

>**HOLDWRDSprobeexecution.ProceednextwithV2-D0.1WRDSpermission-truthauthorizationandcredentialhygiene.Afterentitlementevidenceandexplicitapprovalarerecorded,aread-onlyWRDSpermissionprobemaybeproposedfromacleanisolatedreviewedsurface.Dirty-rootclassificationisnotthefirstgateforthatclean-roomprobe,butismandatorybeforeanyroot-basedevidence,merge-back,runtimeintegration,dataoutput,snapshot,dashboard,promotion,SafeBoot,orBootReadyclaim.**

用户:
What is the minimum definition of a “clean isolated probe surface”?
Which files are allowed into that surface, and which legacy WRDS/root files must be explicitly excluded?
Before merge-back, what proof is required that dirty-root artifacts did not influence the probe design or output?
用户:

AI助手:
## Minimum definition

A **clean isolated probe surface** is a newly created, attestable micro-worktree/container whose only design inputs are the reviewed V2-D0/V2-D0.1 authorization artifacts and whose only runtime purpose is a **read-only WRDS permission check** against explicitly approved `library.table` rows.

It must meet all of these minimum conditions:

1. **Created from empty state**
   - New directory, new container, or new ephemeral worktree.
   - Not the current Quant repo root.
   - No inherited `.git`, `.venv`, caches, outputs, local ignored files, or untracked files.

2. **Built by allowlist, not copy-all**
   - Files enter only through an explicit path allowlist with SHA256 hashes.
   - The uploaded packet zip can be treated as an advisory source anchor; for this uploaded copy I computed SHA256:
     `fd604c71733ea7965964b4cc643eb7f571a812a5ff22aab3beea587b9e089fca`.
   - No broad repo clone, no `rsync .`, no “copy package folder and clean later.”

3. **No dependency on the dirty root**
   - `PYTHONPATH`, `sys.path`, editable installs, local package paths, and imports must not resolve to the Quant root.
   - The current packet code imports `data.provenance.utc_now_iso`; a clean surface must **not** satisfy that by importing the root `data/` package. Use a reviewed one-function local clock shim or patch the imports under review.

4. **Secrets outside the filesystem**
   - No `.env`, `.pgpass`, WRDS config, hard-coded username/password, raw connection log, or provider credential file.
   - Runtime credentials, once separately approved, must be injected by a secret manager or one-shot environment injection and redacted from logs.

5. **Minimal runtime authority**
   - Read-only provider action only.
   - Only the approved `library.table` rows from V2-D0.1 entitlement evidence.
   - No snapshot, no schema dump, no row counts, no sample rows, no table discovery sweep, no dashboard/runtime write, no SQLite, no ranking/scoring/recommendation/promotion path.

6. **Output is permission evidence only**
   - Allowed output is a sanitized permission result/attestation: approved row, approval reference, attempted permission check class, allow/deny/error status, timestamp, runner hash, environment hash.
   - Forbidden output: provider data rows, row counts, table schemas, library listings, raw SQL result sets, snapshot manifests representing generated data, parquet/csv/json data dumps, or dashboard/runtime artifacts.

The current public repo is not a clean probe surface. It currently exposes top-level WRDS probe scripts and WRDS/BvD output artifacts; the repo listing shows files such as `test_wrds.py`, `test_wrds2.py`, `test_wrds3.py`, `test_wrds4.py`, `test_wrds_tables.py`, `wrds_target_output.txt`, and related output/schema text files. Raw examples contain WRDS connection/listing behavior, and one output file contains provider-derived table/row-count style results. 

## Files allowed into the minimum surface

Use this as the minimum allowlist.

### Authority and approval docs

Allowed:

```text
README_DECISION_CARD.md
EVIDENCE_AND_CHECKS.md
LOW_CONFIDENCE_AND_OUT_OF_BOUNDARY.md
PACKET_MANIFEST.md
docs/handover/MULTI_EXPERT_RECONCILED_VERDICT_20260602.md
docs/architecture/v2_wrds_data_lab_policy.md
docs/authorization/V2_D0_1_WRDS_PERMISSION_TRUTH_AUTHORIZATION.md      # new
docs/authorization/V2_D0_1_WRDS_PERMISSION_TRUTH_AUTHORIZATION.json    # new, machine-readable
```

The new V2-D0.1 authorization file must contain the non-secret entitlement evidence: WRDS account/license owner, approved account scope, exact `library.table` rows, license/access constraints, date/as-of coverage, `approval_ref` per approved row, and the explicit phrase:

```text
read-only permission probe only; no snapshot/data output
```

### Contract code

Allowed, after hash verification or reviewed patching:

```text
v2_discovery/data_lab/permission_matrix.py
v2_discovery/data_lab/wrds_probe.py
v2_discovery/data_lab/schema_registry.py
contracts/data_snapshot/wrds_permission_matrix.schema.json
```

Important: do **not** import the repo-root `data.provenance`. Add a reviewed clean shim instead, for example:

```text
probe_support/clock.py
```

or patch the imported modules so `utc_now_iso()` is local to the probe surface.

### Probe runner

Allowed only after V2-D0.1 approval:

```text
probe/v2_d0_1_readonly_permission_probe.py
probe/v2_d0_1_permission_probe_result.schema.json
tests/test_probe_surface_isolation.py
tests/test_probe_result_schema_no_data.py
tests/test_v2_wrds_permission_matrix.py
requirements-probe.lock
pyproject-probe.toml
```

The probe runner must be newly written or clean-room reviewed. It must not be copied from `test_wrds*.py`, `test_wrds_tables.py`, or any legacy WRDS script.

The only file in the clean surface allowed to contain provider connection code after approval is the new reviewed V2-D0.1 runner. Before that approval, even `import wrds` and `wrds.Connection` remain forbidden.

### Optional guardrail-only files

These can be included only if the surface needs to prove “no snapshot path” behavior, and the live probe runner must not use them:

```text
v2_discovery/data_lab/snapshot_manifest.py
contracts/data_snapshot/wrds_snapshot_manifest.schema.json
tests/test_v2_snapshot_manifest_contract.py
tests/test_v2_data_lab_no_v1_writes.py
```

For the minimum read-only permission probe, I would exclude snapshot files by default. Including them widens the surface and creates more proof burden.

## Files that must be explicitly excluded

These exclusions should be written into `EXCLUDED_DIRTY_ROOT_ARTIFACTS.md` and enforced by a scan.

### Legacy WRDS scripts and outputs

Explicitly exclude:

```text
test_wrds.py
test_wrds2.py
test_wrds3.py
test_wrds4.py
test_wrds_tables.py
all_wrds_libs.txt
wrds_schema_hunter_output.txt
wrds_target_output.txt
bvd_orbis_schema.txt
orbis_schema.txt
orbis_all_tables.txt
test_orbis_industry.py
test_orbis_print.py
```

Also exclude any file matching:

```text
*wrds*
*orbis*
*bvd*
*out*.txt
final_*.txt
*_output.txt
*_schema.txt
```

unless it is one of the clean allowlisted V2-D0/V2-D0.1 files above.

The reason is not only execution risk. These files can contaminate **design** by telling the probe what libraries/tables to check based on prior dirty-root discovery rather than current entitlement evidence.

### Root runtime/data/app surfaces

Explicitly exclude:

```text
data/**
data/processed/**
data/registry/**
runtime/**
reports/**
promotion_packets/**
research_data/**
backtests/**
core/**
execution/**
models/**
strategies/**
views/**
scripts/**
dashboard.py
launch.py
main_console.py
main_bot_orchestrator.py
```

The public repo root currently contains broad app/runtime folders and files such as `data/`, `core/`, `execution/`, `models/`, `strategies/`, `views/`, `scripts/`, `dashboard.py`, and orchestration entrypoints; those are outside a permission-probe surface. 

### Secrets, environments, caches, and repo machinery

Explicitly exclude:

```text
.git/**
.venv/**
__pycache__/**
.pytest_cache/**
.mypy_cache/**
.pytest_tmp_scheduler*
.claude/**
.codex/**
.env
.env.*
.pgpass
*.pgpass
wrds_config*
credentials/**
secrets/**
provider_logs/**
raw_provider_logs/**
```

The root `pyproject.toml`, `requirements.txt`, and `requirements.lock` should also be excluded from the minimum probe surface. Use a new minimal `requirements-probe.lock` instead. The root dependency set belongs to the full application and includes unrelated dashboard, broker, market-data, and analytics dependencies; that is too wide for a permission probe.

### Broad governance/history docs

For the minimum surface, exclude broad root-history documents unless separately justified:

```text
docs/decision log.md
docs/notes.md
docs/lessonss.md
docs/context/*
PRD.md
PRODUCT_SPEC.md
docs/prd.md
docs/spec.md
docs/phase_brief/*
```

The exception is the small set of named authority files in the allowlist. The design must come from the specific V2-D0/V2-D0.1 gate, not from broad historical context.

## Required proof before merge-back

A statement like “we did not use dirty-root files” is not enough. Before merge-back, require a **non-influence evidence packet** containing these artifacts.

### 1. Surface manifest

File:

```text
PROBE_SURFACE_MANIFEST.json
```

Required fields:

```text
surface_id
created_at_utc
container_image_digest or venv_hash
source_file_paths
sha256_per_file
origin_per_file: packet | v2_d0_1_new | reviewed_patch | clean_shim
review_ref_per_file
explicit_exclusion_policy_hash
```

Every included file must trace to either the uploaded V2-D0 packet, the new V2-D0.1 authorization, or a reviewed clean-room patch. No file may have origin `dirty_root`.

### 2. Creation transcript

File:

```text
SURFACE_CREATION_TRANSCRIPT.txt
```

It must show that the surface was created from empty state using an allowlist. It should include equivalent evidence for:

```text
pwd
tree -a
sha256sum -c allowlist.sha256
git status --porcelain=v1 -uall       # if git is initialized
```

It must not show a broad clone/copy of the Quant root.

### 3. Import provenance proof

File:

```text
IMPORT_PROVENANCE.json
```

It must record, at runtime:

```text
cwd
sys.path
PYTHONPATH
module.__file__ for every imported local module
pip freeze or lockfile hash
```

Hard fail if any local module resolves under the dirty Quant root, especially:

```text
data.provenance
core.*
scripts.*
views.*
dashboard
execution.*
strategies.*
models.*
```

This is the key proof that the packet’s `data.provenance` dependency was not accidentally satisfied by the dirty root.

### 4. Forbidden artifact scan

File:

```text
FORBIDDEN_SCAN_RESULTS.txt
```

Minimum checks:

```text
find . -type f
grep/rg for excluded filenames: test_wrds, wrds_target_output, all_wrds_libs, orbis, bvd
grep/rg for credential-like tokens
grep/rg for provider-output tokens: row count, describe_table, list_libraries, list_tables
grep/rg for forbidden write/runtime tokens: to_parquet, to_csv, os.replace, sqlite3, streamlit, BrokerPort, submit_order, emit_alert, promote_candidate
secret scan result
```

Expected result: no matches, except the newly reviewed probe runner may contain the approved provider connection primitive after V2-D0.1 approval.

### 5. Design provenance memo

File:

```text
PROBE_DESIGN_PROVENANCE.md
```

It must list the only design inputs used:

```text
README_DECISION_CARD.md
MULTI_EXPERT_RECONCILED_VERDICT_20260602.md
v2_wrds_data_lab_policy.md
V2_D0_1_WRDS_PERMISSION_TRUTH_AUTHORIZATION.{md,json}
permission_matrix.py / wrds_probe.py / schema
```

It must explicitly say that these were **not** consulted or used:

```text
test_wrds*.py
test_wrds_tables.py
wrds_target_output.txt
all_wrds_libs.txt
wrds_schema_hunter_output.txt
bvd/orbis schema dumps
root docs/decision log.md
root notes/lessonss
data/**
runtime/**
dashboard/core/execution/scripts/**
```

For every probed `library.table`, the memo must map:

```text
library.table -> approval_ref -> entitlement evidence source
```

No row may have source “found in old WRDS output,” “from root script,” or “from prior probe log.”

### 6. Probe execution ledger

File:

```text
PROBE_EXECUTION_LEDGER.json
```

Required fields:

```text
surface_id
runner_sha256
command
started_at_utc
ended_at_utc
credential_injection_method: redacted_external_secret
approved_rows_attempted
result_schema_hash
output_sha256
no_snapshot_generation: true
no_data_output: true
no_schema_dump: true
no_row_count_output: true
no_dashboard_runtime_write: true
no_sqlite_write: true
```

The result file must be exact-schema and sanitized. Suggested allowed result columns:

```text
dataset_id
wrds_library
wrds_table
approval_ref
permission_check_status
error_class
checked_at_utc
```

Forbidden result fields:

```text
rows
row_count
columns
schema
sample
query_result
output_path
snapshot_path
raw_sql
connection_uri
username
password
token
```

### 7. Post-run filesystem proof

File:

```text
POST_RUN_DIFF_AND_OUTPUT_PROOF.txt
```

It must show:

```text
tree -a before
tree -a after
hashes before/after
```

The only new files should be sanitized attestation files. No `data/`, `runtime/`, `reports/`, `promotion_packets/`, parquet, csv, sqlite, provider logs, or dashboard artifacts.

### 8. Merge diff proof

Before merge-back, the proposed diff must contain only reviewed clean files. It must not include:

```text
probe outputs
credentials
raw logs
provider table data
legacy WRDS scripts
data/runtime/report artifacts
root broad dependency changes
dashboard/runtime/broker/candidate code
```

If the probe runner is merged at all, it should be disabled by default and require a future explicit approval flag. The safer merge-back is docs/tests/protocol plus sanitized permission summary, not executable credentialed probe code.

## Merge-back decision rule

Merge-back is allowed only if all three statements are proven by artifacts, not just asserted:

1. **No dirty-root import:** runtime import provenance shows no module loaded from the dirty Quant root.
2. **No dirty-root design input:** every probed `library.table` traces to V2-D0.1 entitlement evidence, not legacy WRDS outputs or scripts.
3. **No dirty-root output influence:** result schema contains only permission status fields and no provider data, schemas, row counts, snapshots, dashboard/runtime writes, or copied legacy logs.

If any legacy WRDS/root artifact was read, copied, imported, mounted on `PYTHONPATH`, used to choose tables, or used to interpret output, the surface is not clean and merge-back must be blocked pending dirty-root classification.

用户:
What exact file allowlist defines the clean isolated probe surface?
Is dirty-root classification deferred only for a clean-room probe, but mandatory before merge-back?
What proof artifacts are mandatory: surface manifest, import provenance, forbidden scan, execution ledger?
AI助手:
Here’s the distilled governance guidance based on the uploaded packet and best-practice clean-room principles:

---

## 1️⃣ Exact allowlist defining the clean isolated probe surface

Only these files may enter the clean isolated surface:

### Authority / approval documents
```
README_DECISION_CARD.md
EVIDENCE_AND_CHECKS.md
LOW_CONFIDENCE_AND_OUT_OF_BOUNDARY.md
PACKET_MANIFEST.md
docs/handover/MULTI_EXPERT_RECONCILED_VERDICT_20260602.md
docs/architecture/v2_wrds_data_lab_policy.md
docs/authorization/V2_D0_1_WRDS_PERMISSION_TRUTH_AUTHORIZATION.md
docs/authorization/V2_D0_1_WRDS_PERMISSION_TRUTH_AUTHORIZATION.json
```

### Contract/probe code
```
v2_discovery/data_lab/permission_matrix.py
v2_discovery/data_lab/wrds_probe.py
v2_discovery/data_lab/schema_registry.py
contracts/data_snapshot/wrds_permission_matrix.schema.json
probe_support/clock.py    # reviewed local shim, replaces data.provenance
```

### Probe runner / tests
```
probe/v2_d0_1_readonly_permission_probe.py
probe/v2_d0_1_permission_probe_result.schema.json
tests/test_probe_surface_isolation.py
tests/test_probe_result_schema_no_data.py
tests/test_v2_wrds_permission_matrix.py
requirements-probe.lock
pyproject-probe.toml
```

> ✅ **Note:** No legacy WRDS scripts, root runtime folders, or data snapshots are allowed. Only reviewed and vetted V2-D0/V2-D0.1 artifacts enter.

---

## 2️⃣ Dirty-root classification

- **Deferred for clean-room probe:** Yes. If the probe runs **entirely from the clean allowlist surface**, dirty-root classification is **not required before the probe**.  
- **Mandatory before merge-back:** Absolutely. Any merge-back that touches repo root, dashboard/runtime integration, snapshots, scoring, or promotion **must first classify dirty-root artifacts** to ensure no contamination influenced design or output.

---

## 3️⃣ Mandatory proof artifacts

Before merge-back or any trusted result:

1. **Surface manifest (`PROBE_SURFACE_MANIFEST.json`)**
   - Tracks included files, SHA256, origin (packet / reviewed patch / clean shim).
2. **Import provenance (`IMPORT_PROVENANCE.json`)**
   - Runtime `sys.path`, module paths, verification that no imports resolved under dirty root.
3. **Forbidden scan results (`FORBIDDEN_SCAN_RESULTS.txt`)**
   - Scan confirms no legacy WRDS scripts, output files, credentials, snapshots, or dashboard/runtime artifacts are present.
4. **Execution ledger (`PROBE_EXECUTION_LEDGER.json`)**
   - Captures runner SHA, command, start/end times, redacted secret injection, and output hash. Ensures no snapshot or raw provider data generated.

> Optional supporting artifacts: creation transcript, design provenance memo, post-run filesystem proof, merge diff proof — recommended for audits but the four above are mandatory.

---

In short:

- ✅ Only allowlisted files make up the clean probe surface.  
- ✅ Dirty-root classification is deferred **only** for clean-room probes.  
- ✅ Mandatory proof artifacts before any merge-back: **surface manifest, import provenance, forbidden scan, execution ledger**.

---

If you want, I can produce a **ready-to-use JSON/YAML template** for the clean isolated probe surface, with SHA256 placeholders and origin fields, so it can be directly applied in CI and governance validation. This ensures nothing outside the allowlist ever enters.  

Do you want me to generate that template?

用户:
What exact file allowlist defines the clean isolated probe surface?
Is dirty-root classification deferred only for a clean-room probe, but mandatory before merge-back?
What proof artifacts are mandatory: surface manifest, import provenance, forbidden scan, execution ledger?
用户:

AI助手:
##Directanswer

**Yes:**dirty-rootclassificationmaybedeferred**only**foraclean-room,cleanisolatedread-onlypermissionprobe.Itis**mandatorybeforemerge-back**ofanyprobecode,proberesult,designconclusion,entitlementmapping,orruntime-facingchangeintotheQuantroot.

**Yes:**themandatoryproofartifactsincludeatleast:

```text
PROBE_SURFACE_MANIFEST.json
IMPORT_PROVENANCE.json
FORBIDDEN_SCAN_RESULTS.txt
PROBE_EXECUTION_LEDGER.json
```

Formerge-back,Iwouldalsorequire:

```text
SURFACE_CREATION_TRANSCRIPT.txt
POST_RUN_DIFF_AND_OUTPUT_PROOF.txt
PROBE_DESIGN_PROVENANCE.md
MERGE_BACK_REVIEW.md
```

Thefouryounamedaremandatory;theextrafourclosethegapbetween“cleanatruntime”and“safetomergeback.”

---

#Exactcleanisolatedprobesurfaceallowlist

The**credentialedruntimesurface**shouldcontain**only**thefollowingfiles.Nootherpacketfiles,repofiles,ignoredfiles,rootdocs,outputs,caches,orlegacyWRDSfilesareallowed.

```text
ALLOWLIST.sha256
PROBE_SURFACE_POLICY.md
PROBE_SURFACE_MANIFEST.json

docs/authorization/V2_D0_1_WRDS_PERMISSION_TRUTH_AUTHORIZATION.md
docs/authorization/V2_D0_1_WRDS_PERMISSION_TRUTH_AUTHORIZATION.json
docs/handover/MULTI_EXPERT_RECONCILED_VERDICT_20260602.md
docs/architecture/v2_wrds_data_lab_policy.md

v2_discovery/__init__.py
v2_discovery/data_lab/__init__.py
v2_discovery/data_lab/permission_matrix.py
v2_discovery/data_lab/wrds_probe.py
v2_discovery/data_lab/schema_registry.py

contracts/data_snapshot/wrds_permission_matrix.schema.json

probe_support/__init__.py
probe_support/clock.py

probe/v2_d0_1_readonly_permission_probe.py
probe/v2_d0_1_permission_probe_result.schema.json

requirements-probe.lock
```

Thatistheminimumallowedruntimesurfaceforacredentialedprobe.

##Importantpatchrule

Thepacketversionsofthesefilesareallowedonlyafterclean-importpatching:

```text
v2_discovery/data_lab/__init__.py
v2_discovery/data_lab/permission_matrix.py
v2_discovery/data_lab/wrds_probe.py
```

Reason:theuploadedpacket’sV2-D0codeimports`data.provenance`.InadirtyQuantroot,thatimportcouldresolveintoroot`data/**`,whichisexplicitlyforbidden.Sotheclean-roomsurfacemustdooneofthefollowing:

```text
fromprobe_support.clockimportutc_now_iso
```

oruseanotherreviewedlocalshimwiththesameminimalfunction.

Itmust**not**satisfythatdependencyusing:

```text
data/provenance.py
data/**
PYTHONPATH=<Quantroot>
editableinstallofQuant
```

Forthecredentialedruntimesurface,`v2_discovery/data_lab/__init__.py`shouldbeareviewedminimalstuborimportonlytheallowlistedmodules.Itshould**not**import`snapshot_manifest.py`.

---

#Filesfromtheuploadedpacketthatmaybesourceanchors

TheuploadedpacketzipIinspectedhasSHA256:

```text
fd604c71733ea7965964b4cc643eb7f571a812a5ff22aab3beea587b9e089fca
```

Onlythesepacketfilesshouldbecopiedorusedassourceanchorsfortheclean-roomsurface:

```text
README_DECISION_CARD.md
EVIDENCE_AND_CHECKS.md
LOW_CONFIDENCE_AND_OUT_OF_BOUNDARY.md
PACKET_MANIFEST.md
docs/handover/MULTI_EXPERT_RECONCILED_VERDICT_20260602.md
docs/architecture/v2_wrds_data_lab_policy.md
v2_discovery/data_lab/permission_matrix.py
v2_discovery/data_lab/wrds_probe.py
v2_discovery/data_lab/schema_registry.py
contracts/data_snapshot/wrds_permission_matrix.schema.json
```

Butnotallofthosebelonginthecredentialedruntimeimage.Theruntimeimageshouldincludeonlytheexactallowlistabove.

Thesepacketfilesshould**not**becopiedintothecredentialedruntimesurface:

```text
MULTI_STREAM_PLAN.md
CURRENT_TRUTH_V2_D0_EXCERPTS.md
EXPECTED_MULTI_EXPERT_OUTPUT.md
decision_log_tail.md
notes_tail.md
lessonss_tail.md
docs/context/*
PRD.md
PRODUCT_SPEC.md
docs/prd.md
docs/spec.md
docs/phase_brief/*
docs/decisionlog.md
docs/notes.md
docs/lessonss.md
pyproject.toml
requirements.txt
v2_discovery/data_lab/snapshot_manifest.py
contracts/data_snapshot/wrds_snapshot_manifest.schema.json
tests/*
```

Testscanbeusedina**non-credentialedreviewharness**,butnotinthecredentialedprovider-accesssurface.

---

#LegacyWRDS/rootfilesthatmustbeexplicitlyexcluded

ThecurrentpublicreporootlistslegacyWRDS/BvD/Orbisscriptsandoutputsincluding`all_wrds_libs.txt`,`bvd_orbis_schema.txt`,`orbis_all_tables.txt`,`orbis_schema.txt`,`test_orbis_industry.py`,`test_orbis_print.py`,`test_wrds.py`,`test_wrds2.py`,`test_wrds3.py`,`test_wrds4.py`,`test_wrds_tables.py`,`wrds_schema_hunter_output.txt`,and`wrds_target_output.txt`;thosemustbeexplicitlyexcludedfromthecleanprobesurface.

Usethisexclusionblock:

```text
all_wrds_libs.txt
wrds_schema_hunter_output.txt
wrds_target_output.txt
bvd_orbis_schema.txt
orbis_schema.txt
orbis_all_tables.txt

test_wrds.py
test_wrds2.py
test_wrds3.py
test_wrds4.py
test_wrds_tables.py
test_orbis_industry.py
test_orbis_print.py

*out*.txt
*_output.txt
*_schema.txt
final_*.txt
```

Thereporootalsolistsbroadruntime/applicationdirectoriessuchas`backtests/`,`core/`,`data/`,`execution/`,`models/`,`research_data/`,`scripts/`,`strategies/`,`tests/`,`utils/`,and`views/`,alongwithrootentrypointslike`dashboard.py`,`launch.py`,`main_bot_orchestrator.py`,and`main_console.py`;noneofthosebelonginthecleanisolatedWRDSprobesurface.

Exclude:

```text
.git/**
.venv/**
__pycache__/**
.pytest_cache/**
.mypy_cache/**
.pytest_tmp_scheduler*
.claude/**
.codex/**
skills/**

backtests/**
core/**
data/**
docs/context/**
execution/**
models/**
research_data/**
runtime/**
scripts/**
strategies/**
tests/**
utils/**
views/**

dashboard.py
launch.py
main_bot_orchestrator.py
main_console.py

pyproject.toml
requirements.txt
requirements.lock
Dockerfile
Dockerfile.*
AGENTS.md
GITHUB_SETUP.md
PHASE_QUEUE.md
top_level_PM.md
```

Alsoexcludeallsecretsandprovider-localstate:

```text
.env
.env.*
.pgpass
*.pgpass
wrds_config*
credentials/**
secrets/**
provider_logs/**
raw_provider_logs/**
```

---

#Dirty-rootclassificationrule

Theruleis:

```text
Dirty-rootclassificationmaybedeferredonlyfortheclean-roomprobe.
Dirty-rootclassificationismandatorybeforemerge-back.
```

Moreexactly:

##Dirty-rootclassificationmaybedeferredonlyifallaretrue

```text
Theprobesurfaceiscreatedfromemptystate.
Filesenteronlybyexplicitallowlist.
NoQuantrootclone/copyispresent.
NoQuantrootpathismounted.
NoPYTHONPATHpointsatQuantroot.
NoeditableinstallpointsatQuantroot.
NolocalmoduleresolvesunderQuantroot.
NolegacyWRDS/rootfileisread,copied,imported,grepped,orused.
Everyprobedlibrary.tablemapstoV2-D0.1entitlementevidence.
Theprobeproducespermission-statusevidenceonly.
```

##Dirty-rootclassificationismandatorybeforeanyofthese

```text
merge-backintoQuantroot
useofrootartifactsasevidence
useoflegacyWRDSoutputstochoosetables
snapshotgeneration
providerdataoutput
schemadump
rowcountoutput
dashboardreader
runtimeintegration
SQLite/candidateregistry
ranking/scoring/recommendation/alertpath
broker/orderpath
SafeBootclaim
BootReadyclaim
promotionclaim
```

Ifanydirty-rootartifactinfluencesprobedesignoroutput,thentheprobeisnolongerclean-roomandmerge-backisblocked.

---

#Mandatoryproofartifacts

##1.`PROBE_SURFACE_MANIFEST.json`

Mandatorybeforeexecutionandbeforemerge-back.

Itmustproveexactlywhatwasinthesurface:

```json
{
"surface_id":"v2-d0-1-wrds-readonly-cleanroom-<date-or-hash>",
"created_at_utc":"...",
"source_packet_sha256":"fd604c71733ea7965964b4cc643eb7f571a812a5ff22aab3beea587b9e089fca",
"allowlist_sha256":"...",
"files":[
{
"path":"v2_discovery/data_lab/wrds_probe.py",
"sha256":"...",
"origin":"packet_plus_reviewed_clean_import_patch",
"review_ref":"..."
}
],
"excluded_root_policy_sha256":"...",
"dirty_root_origin_allowed":false
}
```

Hard-failconditions:

```text
origin=dirty_root
unhashedfile
unreviewedpatch
fileoutsideallowlist
missingV2-D0.1authorization
```

##2.`IMPORT_PROVENANCE.json`

Mandatoryatruntime.

Itmustrecord:

```text
cwd
sys.path
PYTHONPATH
environmenthash
lockfilehash
module.__file__foreverylocalimportedmodule
runnersha256
```

ItmustprovethatnoimportresolvedunderthedirtyQuantroot,especiallynot:

```text
data.provenance
data/**
core/**
scripts/**
views/**
dashboard
execution/**
strategies/**
models/**
utils/**
```

Hard-failcondition:

```text
AnyimportedmodulepathstartswiththeQuantrootpath.
```

##3.`FORBIDDEN_SCAN_RESULTS.txt`

Mandatorybeforeexecutionandafterexecution.

Itmustshowscansfor:

```text
legacyWRDSfilenames
legacyOrbis/BvDfilenames
credential-liketokens
provideroutputartifacts
schema/row-count/table-listingoutput
forbiddenwriteprimitives
dashboard/runtime/broker/promotionprimitives
```

Minimumforbiddenstrings/patterns:

```text
test_wrds
test_wrds_tables
all_wrds_libs
wrds_target_output
wrds_schema_hunter_output
orbis
bvd
.pgpass
WRDS_PASSWORD
password
credential
list_libraries
list_tables
describe_table
row_count
to_parquet
to_csv
sqlite3
streamlit
BrokerPort
submit_order
emit_alert
promote_candidate
```

Theonlycontrolledexceptionisthatthereviewedproberunnermaycontaintheapprovedconnectionprimitive**after**V2-D0.1authorization.

##4.`PROBE_EXECUTION_LEDGER.json`

Mandatoryafterexecution.

Itmustrecord:

```json
{
"surface_id":"...",
"runner_sha256":"...",
"command":"...",
"started_at_utc":"...",
"ended_at_utc":"...",
"credential_injection_method":"redacted_external_secret",
"approved_rows_attempted":[
{
"wrds_library":"...",
"wrds_table":"...",
"approval_ref":"..."
}
],
"result_schema_hash":"...",
"output_sha256":"...",
"no_snapshot_generation":true,
"no_data_output":true,
"no_schema_dump":true,
"no_row_count_output":true,
"no_dashboard_runtime_write":true,
"no_sqlite_write":true,
"no_dirty_root_import":true
}
```

Allowedresultfieldsonly:

```text
dataset_id
wrds_library
wrds_table
approval_ref
permission_check_status
error_class
checked_at_utc
runner_sha256
surface_id
```

Forbiddenresultfields:

```text
rows
row_count
columns
schema
sample
query_result
raw_sql
connection_uri
username
password
token
snapshot_path
output_path
```

---

#Additionalmerge-backproofIwouldrequire

##5.`SURFACE_CREATION_TRANSCRIPT.txt`

Mustshowthesurfacewascreatedfromemptystatebyallowlist,notcopiedfromroot:

```text
pwd
tree-a
sha256sum-cALLOWLIST.sha256
gitstatus--porcelain=v1-uall#ifgitinitialized
```

##6.`PROBE_DESIGN_PROVENANCE.md`

Mustmapeveryprobedrow:

```text
library.table->approval_ref->V2-D0.1entitlementevidence
```

Itmustexplicitlystatethatthesewerenotconsulted:

```text
test_wrds*.py
test_wrds_tables.py
wrds_target_output.txt
all_wrds_libs.txt
wrds_schema_hunter_output.txt
bvd_orbis_schema.txt
orbis_schema.txt
orbis_all_tables.txt
data/**
runtime/**
dashboard/core/execution/scripts/**
rootdocs/decisionlog.md
rootnotes/lessonss
```

##7.`POST_RUN_DIFF_AND_OUTPUT_PROOF.txt`

Mustprovetheprobeproducedonlysanitizedpermissionevidence:

```text
tree-abefore
tree-aafter
hashesbefore/after
listofnewfiles
```

Allowednewfiles:

```text
probe_results/V2_D0_1_PERMISSION_PROBE_RESULT.json
PROBE_EXECUTION_LEDGER.json
IMPORT_PROVENANCE.json
FORBIDDEN_SCAN_RESULTS.txt
POST_RUN_DIFF_AND_OUTPUT_PROOF.txt
```

Forbiddennewfiles:

```text
*.parquet
*.csv
*.sqlite
*.db
providerlogs
schemadumps
row-countoutputs
librarylistings
data/**
runtime/**
reports/**
promotion_packets/**
```

##8.`MERGE_BACK_REVIEW.md`

Muststate:

```text
Nodirty-rootimportoccurred.
Nodirty-rootfileinfluencedprobedesign.
NolegacyWRDSoutputinfluencedtableselection.
Noproviderdatawasemitted.
Nosnapshot/schema/row-countoutputwasproduced.
Noruntime/dashboard/broker/promotionpathchanged.
```

---

#Merge-backgate

Merge-backisallowedonlywhenthisdecisionpredicateistrue:

```text
clean_surface_manifest_valid
ANDimport_provenance_has_no_dirty_root_paths
ANDforbidden_scan_clean_before_and_after
ANDexecution_ledger_says_no_data_no_snapshot_no_schema_no_row_count
ANDeveryprobedlibrary.tablemapstoV2-D0.1approval_ref
ANDpost_run_diff_contains_only_sanitizedproofartifacts
ANDdirty_root_classification_completedforanyroot-touchingmergetarget
```

Sothefinalgovernanceansweris:

```text
ProceedwithV2-D0.1authorizationfirst.
Thenallowaread-onlyWRDSpermissionprobeonlyfromtheexactclean-roomallowlistabove.
Dirty-rootclassificationisdeferredonlyforthatisolatedclean-roomexecution.
Dirty-rootclassificationismandatorybeforemerge-backoranyroot-derivedclaim.
Themandatoryproofartifactsaresurfacemanifest,importprovenance,forbiddenscan,executionledger,pluscreationtranscript,designprovenance,post-rundiffproof,andmerge-backreview.
```

用户:
What exactly counts as a clean isolated probe surface?
Which root/legacy WRDS files must be excluded?
What proof is needed before merge-back?
AI助手:
Here’s a precise, governance-aligned summary based on the V2-D0 packet you uploaded:  

---

## 1️⃣ Definition of a clean isolated probe surface

A **clean isolated probe surface** is:

- A **newly created worktree/container/directory**: no inherited `.git`, `.venv`, caches, or outputs.  
- **Allowlist-only content**: files enter only via an explicit reviewed list (see below).  
- **No dependencies on the dirty Quant root**: `PYTHONPATH`, editable installs, or local imports must not resolve to legacy modules.  
- **No secrets or provider credentials in files**: credentials injected via secret manager/environment only.  
- **Minimal runtime authority**: can only run **read-only WRDS permission probes** on explicitly approved `library.table` rows.  
- **Sanitized output**: only permission-check attestation, no snapshots, data dumps, schema/output rows, or dashboard/runtime writes.

---

## 2️⃣ Root/legacy WRDS files that must be excluded

**Legacy WRDS scripts and outputs:**

```text
test_wrds.py
test_wrds2.py
test_wrds3.py
test_wrds4.py
test_wrds_tables.py
all_wrds_libs.txt
wrds_schema_hunter_output.txt
wrds_target_output.txt
bvd_orbis_schema.txt
orbis_schema.txt
orbis_all_tables.txt
test_orbis_industry.py
test_orbis_print.py
```

**Other forbidden legacy/root items:**

```text
data/**
runtime/**
backtests/**
core/**
execution/**
models/**
research_data/**
scripts/**
strategies/**
tests/**
views/**
dashboard.py
launch.py
main_console.py
main_bot_orchestrator.py
pyproject.toml
requirements.txt
requirements.lock
.env*
.pgpass
credentials/**
secrets/**
provider_logs/**
raw_provider_logs/**
```

> All of these must **not** be present, mounted, or imported.

---

## 3️⃣ Proof required before merge-back

Before merging probe code or results into the root repo, these artifacts are mandatory:

1. **`PROBE_SURFACE_MANIFEST.json`** – lists all files in the surface, SHA256, origin, review reference.  
2. **`IMPORT_PROVENANCE.json`** – shows runtime module paths, `sys.path`, PYTHONPATH, ensures no imports resolved under dirty root.  
3. **`FORBIDDEN_SCAN_RESULTS.txt`** – verifies absence of legacy WRDS/root files, credentials, provider outputs, forbidden primitives.  
4. **`PROBE_EXECUTION_LEDGER.json`** – runtime record, only allowed outputs (permission status), no snapshots/data/schema/row counts.  
5. **`SURFACE_CREATION_TRANSCRIPT.txt`** – shows surface built from empty state using allowlist.  
6. **`PROBE_DESIGN_PROVENANCE.md`** – documents only V2-D0/V2-D0.1 authorization inputs; confirms no legacy WRDS/root artifacts influenced design.  
7. **`POST_RUN_DIFF_AND_OUTPUT_PROOF.txt`** – confirms no unauthorized outputs created.  
8. **`MERGE_BACK_REVIEW.md`** – verifies compliance: no dirty-root influence, no provider data emitted, no runtime/dashboard modifications.

---

✅ **Governance rules:**

- Dirty-root classification **may be deferred** only for this isolated clean probe execution.  
- Dirty-root classification **is mandatory** before merge-back or using any root artifacts as evidence, snapshot, or promotion.  
- Only the allowlisted files plus reviewed shims and V2-D0.1 authorization artifacts may exist in the probe surface.  

---

If you want, I can generate a **complete ready-to-use allowlist table** that enumerates exactly which files go into the clean probe surface and which are forbidden, including SHA256 hashes from your uploaded packet. This ensures the clean-room surface is fully auditable.  

Do you want me to do that?

用户:
What exactly counts as a clean isolated probe surface?
Which root/legacy WRDS files must be excluded?
What proof is needed before merge-back?
用户:

AI助手:
##Governanceanswer

A**cleanisolatedprobesurface**isanewlycreated,allowlist-built,credential-minimalenvironmentwhoseonlypurposeistorunafuture**read-onlyWRDSpermissionprobe**againstV2-D0.1-approved`library.table`rows.

Itis**not**thecurrentQuantreporoot,notacloneoftheroot,notacopiedworkingtree,andnotanythingthatcanimportfromthedirtyroot.ThecurrentpublicreporootcontainslegacyWRDS/BvD/Orbisscriptsandoutputfiles,plusbroadruntimedirectoriessuchas`data/`,`core/`,`execution/`,`models/`,`scripts/`,`strategies/`,`views/`,androotappentrypoints;thatrootcannotbetreatedasthecleanprobesurface.

Dirty-rootclassificationistherefore:

```text
Deferredonlyforthesealedclean-roomprobe.
Mandatorybeforemerge-backoranyroot-derivedclaim.
```

---

#1.Whatexactlycountsasacleanisolatedprobesurface?

Minimumdefinition:

```text
Afreshdirectory/container/worktreecreatedfromemptystate,
populatedonlybyanexplicitSHA256allowlist,
withnoQuant-rootclone/copy/mount/importpath,
nocredentialsondisk,
nolegacyWRDS/rootfiles,
nodata/runtime/dashboard/broker/promotionsurfaces,
andnooutputexceptsanitizedpermission-statusevidence.
```

Itmustsatisfyalloftheseconditions:

```text
1.Createdfromemptystate.
2.Builtbyallowlist,notbycopyingtherepoanddeletingthings.
3.Everyincludedfilehaspath+SHA256+origin+reviewreference.
4.No.git,.venv,cache,ignoredfile,untrackedfile,localdata,orrepohistory.
5.NoPYTHONPATH,editableinstall,symlink,bindmount,orimportpathpointingtoQuantroot.
6.Noimportofrootdata.provenance,core.*,scripts.*,execution.*,dashboard,views.*,strategies.*,models.*,orutils.*.
7.No.env,.pgpass,WRDSconfig,credentialfile,rawproviderlog,orcommittedsecret.
8.NoprovideraccessuntilV2-D0.1entitlementevidenceandexplicitapprovalexist.
9.Afterapproval,provideraccessislimitedtoread-onlypermissionchecksforapprovedrowsonly.
10.Outputispermissionevidenceonly:allow/deny/errorstatus,timestamps,hashes,approvalreferences.
```

Theuploadedpacket’sownnextgateisnot“runprobe”;itis**V2-D0.1WRDSpermission-truthauthorization**.TheuploadedpacketalsosaysWRDS/provideraccessandread-onlyprobeexecutionremainunauthorizeduntilnon-secretentitlementevidenceandexplicitapprovaltextexist.

---

#2.Exactfileallowlistforthecleansurface

Thisisthe**credentialedruntimeallowlist**.Nothingelsebelongsintheprobesurface.

```text
ALLOWLIST.sha256
PROBE_SURFACE_POLICY.md
PROBE_SURFACE_MANIFEST.json
EXCLUDED_DIRTY_ROOT_ARTIFACTS.md

docs/authorization/V2_D0_1_WRDS_PERMISSION_TRUTH_AUTHORIZATION.md
docs/authorization/V2_D0_1_WRDS_PERMISSION_TRUTH_AUTHORIZATION.json
docs/handover/MULTI_EXPERT_RECONCILED_VERDICT_20260602.md
docs/architecture/v2_wrds_data_lab_policy.md

v2_discovery/__init__.py
v2_discovery/data_lab/__init__.py
v2_discovery/data_lab/permission_matrix.py
v2_discovery/data_lab/wrds_probe.py
v2_discovery/data_lab/schema_registry.py

contracts/data_snapshot/wrds_permission_matrix.schema.json

probe_support/__init__.py
probe_support/clock.py

probe/v2_d0_1_readonly_permission_probe.py
probe/v2_d0_1_permission_probe_result.schema.json

requirements-probe.lock
```

TheuploadedpacketzipIinspectedhasSHA256:

```text
fd604c71733ea7965964b4cc643eb7f571a812a5ff22aab3beea587b9e089fca
```

TheV2-D0.1authorizationfilesarenewrequiredfiles.Untiltheyexist,thecleansurfaceisincompleteandmustnotrunacredentialedWRDSprobe.

---

#3.Requiredclean-importpatch

Thepacketversionsofthesefilesareusableonlyafterclean-importpatching:

```text
v2_discovery/data_lab/__init__.py
v2_discovery/data_lab/permission_matrix.py
v2_discovery/data_lab/wrds_probe.py
```

Reason:thepacketcodeimports:

```text
data.provenance.utc_now_iso
```

Thatisunsafeinaclean-roomprobebecauseitcanresolveintoroot`data/**`.Replaceitwiththelocalshim:

```text
probe_support/clock.py
```

Approvedpattern:

```python
fromprobe_support.clockimportutc_now_iso
```

Forbiddenpattern:

```python
fromdata.provenanceimportutc_now_iso
```

Also,`v2_discovery/data_lab/__init__.py`shouldbereducedtoaminimalreviewedstuborlimitedexports.Itmustnotimport`snapshot_manifest.py`forthecredentialedprobesurface.

---

#4.Filesthatmaybesourceanchorsbutshouldnotallenterruntime

Thesepacketfilesmaybeusedduringreview/constructionassourceanchors:

```text
README_DECISION_CARD.md
EVIDENCE_AND_CHECKS.md
LOW_CONFIDENCE_AND_OUT_OF_BOUNDARY.md
PACKET_MANIFEST.md
docs/handover/MULTI_EXPERT_RECONCILED_VERDICT_20260602.md
docs/architecture/v2_wrds_data_lab_policy.md
v2_discovery/data_lab/permission_matrix.py
v2_discovery/data_lab/wrds_probe.py
v2_discovery/data_lab/schema_registry.py
contracts/data_snapshot/wrds_permission_matrix.schema.json
```

Buttheruntimecredentialedsurfaceshouldremainthesmallerallowlistabove.

Do**not**copytheseintothecredentialedruntimesurface:

```text
CURRENT_TRUTH_V2_D0_EXCERPTS.md
MULTI_STREAM_PLAN.md
EXPECTED_MULTI_EXPERT_OUTPUT.md
decision_log_tail.md
notes_tail.md
lessonss_tail.md
docs/context/**
PRD.md
PRODUCT_SPEC.md
docs/prd.md
docs/spec.md
docs/phase_brief/**
docs/decisionlog.md
docs/notes.md
docs/lessonss.md
pyproject.toml
requirements.txt
tests/**
v2_discovery/data_lab/snapshot_manifest.py
contracts/data_snapshot/wrds_snapshot_manifest.schema.json
```

Testsmayrunina**non-credentialedreviewharness**.Theyshouldnotbepresentinthecredentialedprovider-accesssurface.

---

#5.RootandlegacyWRDSfilesthatmustbeexcluded

Thesemustbeexplicitlyexcludedbypath/name:

```text
all_wrds_libs.txt
wrds_schema_hunter_output.txt
wrds_target_output.txt

test_wrds.py
test_wrds2.py
test_wrds3.py
test_wrds4.py
test_wrds_tables.py

bvd_orbis_schema.txt
orbis_schema.txt
orbis_all_tables.txt
test_orbis_industry.py
test_orbis_print.py
```

ThecurrentpublicrootliststheseWRDS/BvD/Orbisfilesdirectly,whichiswhytherootisnotacleanprobesurface.

Alsoexcludegenericlegacyoutputpatterns:

```text
*out*.txt
*_output.txt
*_schema.txt
final_*.txt
audit_output.txt
output.txt
out.txt
out2.txt
out_*.txt
```

Excluderootapplication/runtime/datasurfaces:

```text
.git/**
.venv/**
__pycache__/**
.pytest_cache/**
.mypy_cache/**
.pytest_tmp_scheduler*
.pytest_tmp_scheduler2/**
.pytest_tmp_scheduler_fulltrace/**
.pytest_tmp_scheduler_runs/**
.claude/**
.codex/**
skills/**

backtests/**
core/**
data/**
docs/context/**
execution/**
models/**
research_data/**
runtime/**
scripts/**
strategies/**
tests/**
utils/**
views/**

dashboard.py
launch.py
main_bot_orchestrator.py
main_console.py
```

Thepublicreporootcurrentlyexposesthesebroadruntimeandapplicationdirectoriesandrootentrypoints,sotheyshouldbeoutsidethepermission-probesurface.

Excluderootdependency/build/configfiles:

```text
pyproject.toml
requirements.txt
requirements.lock
Dockerfile
Dockerfile.*
.dockerignore
.gitignore
AGENTS.md
GITHUB_SETUP.md
PHASE_QUEUE.md
top_level_PM.md
README.md
```

Useanewminimalfileinstead:

```text
requirements-probe.lock
```

Excludeallsecrets/provider-localstate:

```text
.env
.env.*
.pgpass
*.pgpass
wrds_config*
credentials/**
secrets/**
provider_logs/**
raw_provider_logs/**
```

---

#6.Dirty-rootclassificationrule

Dirty-rootclassificationmaybedeferred**only**whenallofthisistrue:

```text
Theprobesurfacewascreatedfromemptystate.
Filesenteredonlythroughtheexactallowlist.
NoQuantrootpathwascopied,cloned,mounted,symlinked,imported,orsearched.
NolegacyWRDS/rootfilewasread,grepped,imported,orused.
NoPYTHONPATHpointstoQuantroot.
NoeditableinstallpointstoQuantroot.
NomoduleresolvesunderQuantroot.
Everyprobedlibrary.tablemapstoV2-D0.1entitlementevidence.
Probeoutputcontainspermissionstatusonly.
```

Dirty-rootclassificationismandatorybeforeanyofthis:

```text
merge-backintoQuantroot
useofproberesultasrootevidence
useofrootfilesasevidence
useoflegacyWRDSoutputstochoosetables
snapshotgeneration
schemadump
rowcountoutput
providerdataoutput
dashboardreader
runtimeintegration
SQLite/candidateregistry
ranking/scoring/recommendation/alertpath
broker/orderpath
promotionclaim
SafeBootclaim
BootReadyclaim
```

---

#7.Mandatoryproofbeforemerge-back

Theminimummandatoryproofpacketis:

```text
PROBE_SURFACE_MANIFEST.json
SURFACE_CREATION_TRANSCRIPT.txt
IMPORT_PROVENANCE.json
FORBIDDEN_SCAN_RESULTS.txt
PROBE_DESIGN_PROVENANCE.md
PROBE_EXECUTION_LEDGER.json
POST_RUN_DIFF_AND_OUTPUT_PROOF.txt
MERGE_BACK_REVIEW.md
```

Thefourabsolutelynon-negotiableartifactsare:

```text
PROBE_SURFACE_MANIFEST.json
IMPORT_PROVENANCE.json
FORBIDDEN_SCAN_RESULTS.txt
PROBE_EXECUTION_LEDGER.json
```

ButIwouldnotapprovemerge-backwithoutalleight.

---

##`PROBE_SURFACE_MANIFEST.json`

Mustproveexactlywhatenteredthesurface.

Requiredfields:

```json
{
"surface_id":"v2-d0-1-wrds-readonly-cleanroom-...",
"created_at_utc":"...",
"source_packet_sha256":"fd604c71733ea7965964b4cc643eb7f571a812a5ff22aab3beea587b9e089fca",
"allowlist_sha256":"...",
"files":[
{
"path":"v2_discovery/data_lab/wrds_probe.py",
"sha256":"...",
"origin":"packet_plus_reviewed_clean_import_patch",
"review_ref":"..."
}
],
"excluded_dirty_root_policy_sha256":"...",
"dirty_root_origin_allowed":false
}
```

Hardfailifanyfilehas:

```text
origin=dirty_root
missinghash
missingreview_ref
pathoutsideallowlist
unreviewedpatch
```

---

##`SURFACE_CREATION_TRANSCRIPT.txt`

Mustprovethesurfacewascreatedfromemptystate.

Requiredevidence:

```text
pwd
tree-a
sha256sum-cALLOWLIST.sha256
gitstatus--porcelain=v1-uall#ifgitinitialized
```

Itmustnotshow:

```text
gitclonenathanku3-hue/Quant
rsyncQuant/clean_probe/
cp-rQuantclean_probe
unzipfullrepo
copypackagethendeletefiles
```

---

##`IMPORT_PROVENANCE.json`

Mustprovethedirtyrootwasnotimported.

Requiredfields:

```json
{
"cwd":"...",
"python_executable":"...",
"python_version":"...",
"PYTHONPATH":"...",
"sys_path":["..."],
"local_modules":[
{
"module":"v2_discovery.data_lab.wrds_probe",
"file":".../clean_surface/v2_discovery/data_lab/wrds_probe.py",
"sha256":"..."
}
],
"lockfile_sha256":"...",
"runner_sha256":"...",
"dirty_root_path":"...",
"dirty_root_import_detected":false
}
```

HardfailifanymoduleresolvesunderQuantroot,especially:

```text
data.provenance
data/**
core/**
scripts/**
views/**
dashboard
execution/**
strategies/**
models/**
utils/**
```

---

##`FORBIDDEN_SCAN_RESULTS.txt`

Mustbeproducedbeforeandafterexecution.

Minimumscantargets:

```text
legacyWRDSfilenames
legacyOrbis/BvDfilenames
credential-liketokens
providerdataoutput
schemadumpoutput
rowcountoutput
table/listingdiscoveryoutput
forbiddenwriteprimitives
dashboard/runtime/broker/promotionprimitives
```

Minimumforbiddenpatterns:

```text
test_wrds
test_wrds_tables
all_wrds_libs
wrds_target_output
wrds_schema_hunter_output
orbis
bvd

.pgpass
WRDS_PASSWORD
password
credential
secret
token

list_libraries
list_tables
describe_table
row_count
fetchall
to_parquet
to_csv
sqlite3
streamlit
BrokerPort
submit_order
emit_alert
promote_candidate
```

Controlledexception:

```text
TheapprovedproberunnermaycontaintheminimumWRDSconnectionprimitiveonlyafterV2-D0.1authorization.
```

Nolegacyprobescriptmaybereused.

---

##`PROBE_DESIGN_PROVENANCE.md`

Mustprovetableselectioncamefromentitlementevidence,notlegacyoutputs.

Requiredmapping:

```text
library.table->approval_ref->entitlementevidencesource
```

Itmustexplicitlystatethatthesewerenotconsulted:

```text
test_wrds*.py
test_wrds_tables.py
wrds_target_output.txt
all_wrds_libs.txt
wrds_schema_hunter_output.txt
bvd_orbis_schema.txt
orbis_schema.txt
orbis_all_tables.txt
data/**
runtime/**
dashboard.py
core/**
execution/**
scripts/**
views/**
rootdocs/decisionlog.md
rootnotes/lessonss
```

Hardfailifanyprobedtablesourceis:

```text
oldWRDSoutput
legacyscript
rootdiscoverylog
schemahunteroutput
priordirty-rootresult
```

---

##`PROBE_EXECUTION_LEDGER.json`

Mustprovewhatranandwhatdidnotrun.

Requiredfields:

```json
{
"surface_id":"...",
"runner_sha256":"...",
"command":"...",
"started_at_utc":"...",
"ended_at_utc":"...",
"credential_injection_method":"redacted_external_secret",
"approved_rows_attempted":[
{
"wrds_library":"...",
"wrds_table":"...",
"approval_ref":"..."
}
],
"result_schema_hash":"...",
"output_sha256":"...",
"no_snapshot_generation":true,
"no_data_output":true,
"no_schema_dump":true,
"no_row_count_output":true,
"no_dashboard_runtime_write":true,
"no_sqlite_write":true,
"no_dirty_root_import":true
}
```

Allowedresultfieldsonly:

```text
dataset_id
wrds_library
wrds_table
approval_ref
permission_check_status
error_class
checked_at_utc
runner_sha256
surface_id
```

Forbiddenresultfields:

```text
rows
row_count
columns
schema
sample
query_result
raw_sql
connection_uri
username
password
token
snapshot_path
output_path
```

---

##`POST_RUN_DIFF_AND_OUTPUT_PROOF.txt`

Mustprovetheruncreatedonlysanitizedattestationfiles.

Requiredevidence:

```text
tree-abefore
tree-aafter
hashesbefore
hashesafter
listofnewfiles
```

Allowednewfiles:

```text
probe_results/V2_D0_1_PERMISSION_PROBE_RESULT.json
PROBE_EXECUTION_LEDGER.json
IMPORT_PROVENANCE.json
FORBIDDEN_SCAN_RESULTS.txt
POST_RUN_DIFF_AND_OUTPUT_PROOF.txt
```

Forbiddennewfiles:

```text
*.parquet
*.csv
*.sqlite
*.db
providerlogs
schemadumps
row-countoutputs
librarylistings
data/**
runtime/**
reports/**
promotion_packets/**
```

---

##`MERGE_BACK_REVIEW.md`

Muststatethemerge-backdecisionexplicitly:

```text
Nodirty-rootimportoccurred.
Nodirty-rootfileinfluencedprobedesign.
NolegacyWRDSoutputinfluencedtableselection.
Noproviderdatawasemitted.
Noschemadumpwasemitted.
Norowcountwasemitted.
Nosnapshotwasgenerated.
Nodashboard/runtime/broker/promotionpathchanged.
Dirty-rootclassificationcompletedforanyroot-touchingmergetarget.
```

---

#Finalgate

Merge-backisblockedunlessthispredicateistrue:

```text
V2_D0_1_authorization_exists
ANDclean_surface_manifest_valid
ANDallowlist_hash_verified
ANDno_dirty_root_file_origin
ANDimport_provenance_has_no_dirty_root_paths
ANDforbidden_scan_clean_before_and_after
ANDevery_probed_library_table_maps_to_approval_ref
ANDexecution_ledger_says_no_data_no_snapshot_no_schema_no_row_count
ANDpost_run_diff_contains_only_sanitized_attestation_files
ANDdirty_root_classification_completed_for_merge_target
```

Sotheoperationalansweris:

```text
Useonlytheexactclean-roomallowlist.
ExcludealllegacyWRDS/root/runtime/datafiles.
RunonlyafterV2-D0.1authorization.
Deferdirty-rootclassificationonlyfortheisolatedclean-roomprobe.
Requiredirty-rootclassificationbeforemerge-back.
Approvemerge-backonlywithmanifest,importprovenance,forbiddenscan,designprovenance,executionledger,post-rundiffproof,andmerge-backreview.
```

