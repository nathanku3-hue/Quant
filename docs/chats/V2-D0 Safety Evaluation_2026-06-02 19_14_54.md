### V2-D0 Safety Evaluation

AI助手:


AI助手:


用户:
Backend / Data Contract Expert,see https://github.com/nathanku3-hue/Quant: 

Does V2-D0 safely prevent provider access, credentials, writes, V1 mutation, and snapshot output, and what minimal code change would be safe after approval?”
用户:

AI助手:
##Verdict

**Notunconditionally.**Asan**offlineV2-D0contractpacket**,itmostlypreventsprovideraccess,credentials,writes,V1mutation,andsnapshotoutput.Asa**repo-levelsafetyclaim**,Iwouldnotcallitsafeyet.

Twocaveatsmatter:

1.ThepublicGitHub`main`treeIcouldaccessdoes**not**appeartocontaintheuploadedV2-D0`v2_discovery/`package;itstillpresentsanolderPhase61-styletree/status.
2.Public`main`containslegacyWRDSscripts:oneimports`wrds`andcalls`wrds.Connection(...)`,andanothermonkeypatches`getpass.getpass`withahardcodedvaluebeforecalling`wrds.Connection(...)`.Iamnotrepeatingtheliteralvaluehere;ifreal,itshouldbetreatedasexposedandrotated.

##V2-D0packetsafetyassessment

**Provideraccess:**mostlysafeinside`v2_discovery/data_lab/`.Thepacketbuildersset`provider_access_allowed=False`,`execution_mode="offline_contract_only"`,and`wrds_connection_attempted=False`.Theno-V1-writetestscanstheV2data-labpackagefor`importwrds`,`wrds.Connection`,broker,alert,Streamlit,SQLite,andcandidate-promotionprimitives.

**Credentials:**partiallysafe.`validate_wrds_permission_probe_contract(...)`correctlyrejectsunexpectedrootfieldsandcredential/connection/output-likekeys.However,Ifoundaresidualcontractgap:`validate_permission_matrix_payload(...)`acceptsextrafieldsinside`entries[]`,and`validate_snapshot_manifest_payload(...)`acceptsextrafieldsinside`datasets[]`.TheJSONSchemavalidatorsrejectthoseextras,butthePythonpayloadvalidatorsalonesilentlyignorethem.ThatmeansacallerusingonlythedirectPythonvalidatorscouldpassrow-levelfieldslike`wrds_password`or`output_path`withoutrejection.

**WritesandV1mutation:**mostlysafeinsideV2-D0.Thepackagehasnoparquet/CSV/atomic-writeprimitives,thebuildersarein-memory,andthemanifestrejects`data/processed/`,`data/registry/`,boot-statuspaths,absolutepaths,drive-letterpaths,URL-likepaths,UNCpaths,andpathtraversal.

**Snapshotoutput:**safeascontract-only.Themanifestis`manifest_status="contract_only"`andkeeps`snapshot_generation_allowed`,`committed_wrds_output_allowed`,and`data_output_allowed`false.ItplansastorageURIbutdoesnotwriteanything.

Somyexpertstatuswouldbe:

**PATCH_REQUIREDbeforeanyprobe/providerapproval.**
**ADVISORY_PASSonlyforgeneratedbuilderoutputsplusmandatoryJSONSchemavalidation.**

##Minimalsafecodechange

Theminimalsafechangeis**not**toadd`importwrds`,nottoaddaprobe,andnottowritesnapshots.ThesafepatchistohardenthetwodirectPythonvalidatorssotheyrejectrow-leveldriftthesamewaytheschemasdo.

Addexactrow-keyvalidationhere:

```text
v2_discovery/data_lab/permission_matrix.py
validate_permission_matrix_payload(...)
rejectextra/missingkeysinsidepayload["entries"]

v2_discovery/data_lab/snapshot_manifest.py
validate_snapshot_manifest_payload(...)
rejectextra/missingkeysinsidepayload["datasets"]
```

Addtworegressiontests:

```text
tests/test_v2_wrds_permission_matrix.py
permissionmatrixentrywithwrds_passwordmustberejectedbydirectvalidator

tests/test_v2_snapshot_manifest_contract.py
snapshotmanifestdatasetwithoutput_pathmustberejectedbydirectvalidator
```

Itestedthispatchshapeinatempcopy:thepacket’soriginal20testspassedafterstubbingthemissing`data.provenance.utc_now_iso`,andthetwoaddedadversarialtestsalsopassed,for22total.Theuploadedpacketdoesnotrunstandaloneunchangedinthisenvironmentbecauseitimports`data.provenance`,whichisnotincludedinthepacket.

##Approvalsequencing

Afterapproval,thenextsafechangeshouldstillbe**permission-truthrecordingonly**:

```text
permission_status="approved"or"denied"
approval_ref=non-secretapprovaltext/reference
license_scope=non-secretlicense/accessnote
```

Noprovidercodeshouldbeaddeduntilaseparateapprovalexplicitlysays:

```text
read-onlypermissionprobeonly;
nocredentialsinrepo;
nosnapshotgeneration;
notable/dataoutput;
noV1/data/processed/runtimewrites.
```

Beforeanysuchapproval,Iwouldalsoquarantineordeletethelegacy`test_wrds*.py`scriptsfrompublic/mainandrotateanyexposedWRDScredential-likevalue.

用户:
After row-level exact-key validation is patched, is there any remaining validator/schema parity gap?
What is the minimal V2-D0.1 artifact shape for recording permission truth without adding provider access?
Should the direct Python validators require JSON Schema validation internally, or is exact-key parity enough?
用户:

AI助手:
Icouldnotverifythisasmergedtopublic`main`:therenderedGitHubtreestillshowsPhase61-erastatusandroot`test_wrds*.py`files,andIfoundno`v2_discovery`matchinthatrenderedpage.SothisanswerisbasedontheuploadedV2-D0packetplusthehypotheticalrow-levelexact-keypatch.

##1.Afterrow-levelexact-keyvalidation,isthereanyremainingvalidator/schemaparitygap?

**Yes,if“parity”meansdirectPythonvalidatorsacceptexactlythesamerawpayloadsastheJSONSchemas.**

Buttheremaininggapssplitintotwocategories:

###Materialpermission-truthgap

Themostimportantremainingdirect-validatorgapisinthe**snapshotmanifestdatasetrows**:

```python
payload["datasets"][0]["permission_status"]="bogus"
```

Afteronlyaddingrow-levelexact-keychecks,`validate_snapshot_manifest_payload(...)`wouldstillacceptthisbecause`_require_datasets(...)`onlyrequires`permission_status`tobenon-emptytext.TheJSONSchemarejectsitbecauseitrequiresoneof:

```text
unknown,pending,approved,denied,not_requested
```

ThatshouldbepatchedbeforeV2-D0.1ifthemanifestisallowedtoreflectpermissiontruth.

###Formalraw-payloadparitygaps

ThedirectvalidatorsstillcoerceornormalizesomevaluesthattheschemasrejectasrawJSONpayloads.Examples:

```text
permissionmatrix:
provider="WRDS"directaccepts,schemarejects
created_at_utc=123directaccepts,schemarejects
entries[0].dataset_id=123directaccepts,schemarejects
entries[0].pit_required="false"directaccepts,schemarejects
entries[0].allowed_uses=["PROVENANCE_CONTRACT"]directaccepts,schemarejects
entries[0].notes=[7]directaccepts,schemarejects

snapshotmanifest:
provider="WRDS"directaccepts,schemarejects
permission_matrix_sha256=uppercasedirectaccepts/lowercases,schemarejects
schema_registry_uriwithbackslashesdirectnormalizes,schemarejects
datasets[0].dataset_id=123directaccepts,schemarejects
datasets[0].primary_key=[123]directaccepts,schemarejects
datasets[0].release_date_field=123directaccepts,schemarejects
```

Therearealsoreversegapswherethe**directvalidatorisstricterthanschema**,forexampleduplicatedatasetIDsandpathtraversalunder`data/runtime_cache/v2_data_lab/`.Thatisgoodforsafety,butitisstillnotexactparityifsomeonecallsraw`validate_payload(...)`insteadofthewrapperthatrunsbothschemaandPythonvalidation.

Mystatuswouldbe:

```text
row-levelexact-keypatch:
fixesthecredential/output-fielddriftgap

remaining:
snapshotdatasetpermission_statusenumgap
string/bool/typecoerciongaps
direct-onlyuniqueness/pathrulesnotrepresentedinschema
```

So:**noobviousremainingcredential/output/provider/writerwideninggapfromrowextras**,but**formalvalidator/schemaparityisstillnotclosed**.

##2.MinimalV2-D0.1artifactshapeforrecordingpermissiontruthwithoutprovideraccess

Thesafestminimalshapeis**notanewprobeartifact**and**notasnapshotmanifest**.Itshouldbeoneupdatedpermission-matrixpayloadusingtheexistingmatrixcontractshape,withonlyrow-levelpermissiontruthchanged.

Thatmeans:

```json
{
"schema_version":"1.0.0",
"matrix_id":"V2_D0_WRDS_PERMISSION_MATRIX",
"scope_id":"V2-D0_WRDS_PERMISSION_AND_SNAPSHOT_PROVENANCE_CONTRACT",
"authority":"offline_contract_only",
"provider":"wrds",
"provider_access_allowed":false,
"snapshot_generation_allowed":false,
"data_output_allowed":false,
"v1_canonical_write_allowed":false,
"entries":[
{
"dataset_id":"crsp_daily_stock_file",
"wrds_library":"crsp",
"wrds_table":"dsf",
"dataset_name":"CRSPDailyStockFile",
"permission_status":"approved",
"allowed_uses":[
"provenance_contract"
],
"license_scope":"NON_SECRET_LICENSE_SCOPE_OR_ENTITLEMENT_REF",
"pit_required":true,
"provider_access_allowed":false,
"snapshot_generation_allowed":false,
"data_output_allowed":false,
"v1_canonical_write_allowed":false,
"approval_ref":"NON_SECRET_APPROVAL_REF",
"notes":[
"V2-D0.1permissiontruthonly;noWRDSconnection,query,snapshotgeneration,dataoutput,V1write,dashboardruntimeintegration,ranking,scoring,alert,brokerpath,SQLite,SafeBoot,orBootReadyauthorization."
]
}
],
"denied_actions":[
"wrds_provider_connection",
"pit_snapshot_generation",
"committed_wrds_output",
"v1_canonical_data_write",
"data_processed_write",
"candidate_ranking",
"candidate_scoring",
"candidate_promotion",
"recommendations",
"dashboard_runtime_integration",
"alert_or_broker_path",
"sqlite_storage",
"safe_boot_claim",
"boot_ready_claim"
],
"created_at_utc":"2026-06-02T00:00:00Z",
"code_ref":"v2_discovery/data_lab/permission_matrix.py@v2-d0"
}
```

Keyconstraints:

```text
approvedrow:
permission_status="approved"
approval_ref=non-secretapproval/ticket/referencetext
license_scope=non-secretentitlementscope
provider/output/V1flagsremainfalse

deniedrow:
permission_status="denied"
approval_refmayremainnull,butanon-secretevidencerefinnotesissafer

pending/unknownrow:
noimpliedapproval
provider/output/V1flagsremainfalse

allowed_uses:
forV2-D0.1,safestminimumis["provenance_contract"]
add"read_only_permission_probe"onlyifaseparateapprovalexplicitlyauthorizesaread-onlyprobeprotocol
```

Theartifactshould**not**contain:

```text
wrds_username
wrds_password
tokens
credentialrefs
connectionstrings
SQL/querytext
output_path
snapshot_path
rowcounts
sampledata
providerlogs
data/runtimepathsasgeneratedoutputs
```

IwouldnotregenerateorcommitasnapshotmanifestastheminimalD0.1artifact.Ifacontract-onlymanifestisregeneratedlatertoupdate`permission_matrix_sha256`,thatshouldremainaseparatenon-provider,non-outputstep.

##3.ShoulddirectPythonvalidatorsrequireJSONSchemavalidationinternally?

**No,notinternallyascurrentlystructured.**Exact-keyparityaloneisalso**notenough**.

Thebetterruleis:

```text
DirectPythonvalidatorsshouldbestrictenoughtomatchschemasemanticsfortheirpublicinputs:
exactkeys
exactlowercaseenums
exactstring/null/booltypes
exactfalseflags
nocoercionofrawpayloadvalues
cross-rowuniqueness
pathconfinement
```

Thentheschema-registrywrappershouldremainthecombinedcompliancegate:

```text
validate_permission_matrix_schema(payload):
JSONSchemavalidation
thendirectPythonvalidation

validate_snapshot_manifest_schema(payload):
JSONSchemavalidation
thendirectPythonvalidation
```

Iwouldavoidmaking`validate_permission_matrix_payload(...)`call`validate_permission_matrix_schema(...)`directlybecausethecurrentregistryalreadyimportsthedirectvalidatorafterschemavalidation.Makingthedirectvalidatorcallbackintotheregistryriskscircularimports,recursion,andrepo-root/schema-filecoupling.

Theminimalsafedesignis:

```text
1.Keepdirectvalidatorsstandalone.
2.Hardendirectvalidatorstoreject,notcoerce,rawexternalpayloaddrift.
3.Keepschema-registryvalidationasthemandatoryCI/releasegate.
4.Addteststhatprovedirectandschemavalidatorsbothrejectthesameadversarialpayloads.
```

Concretely,aftertherow-keypatch,IwouldstilladdthesesmallparitytestsbeforeapprovingD0.1:

```text
permissionmatrixdirectvalidatorrejects:
provider="WRDS"
created_at_utc=123
entries[0].dataset_id=123
entries[0].pit_required="false"
entries[0].allowed_uses=["PROVENANCE_CONTRACT"]
entries[0].notes=[7]

snapshotmanifestdirectvalidatorrejects:
datasets[0].permission_status="bogus"
datasets[0].dataset_id=123
datasets[0].primary_key=[123]
release_date_field=123
uppercasepermission_matrix_sha256
backslashschema_registry_uri
```

Finalrecommendation:

```text
ForV2-D0.1:
exact-keyparityisnecessarybutnotsufficient.
donotwireJSONSchemavalidationinternallyintothedirectvalidators.
insteadpatchdirectvalidatorstoenforceschema-equivalentraw-payloadsemantics,andrequiretheexistingschema-registrywrappersinCI/review.
```

用户:
After row-level exact-key and raw-payload strictness patches, are there any remaining direct-validator/schema parity gaps?
Should allowed_uses for V2-D0.1 approved rows be only provenance_contract, with read_only_permission_probe added only after separate approval?
Should snapshot manifest regeneration stay forbidden until a separate “contract-only hash refresh” approval?
用户:

AI助手:
IstillcannotverifyapatchedV2-D0.1onpublic`main`;therenderedrepopagestillshowsPhase61-erastatus,root`test_wrds*.py`files,andnovisible`v2_discovery`match.SothisisconditionalontheuploadedV2-D0packetplusthestatedpatches.

##1.Afterrow-levelexact-keyandraw-payloadstrictnesspatches,areanyparitygapsleft?

**Materialwideninggap:likelyno.**
Ifthepatchesreallymakethedirectvalidatorsrejectexactrow-keydrift,non-JSON-nativetypes,enumcasedrift,stringcoercion,boolcoercion,hashnormalization,pathnormalization,andnull/stringconfusion,thentheriskydirectionshouldbeclosed:

```text
directPythonvalidatoracceptspayload
JSONSchemarejectspayload
```

Thatwasthedangerousdirection,becauseitcouldletcredential/output/provider/writefieldsorcoerciblevaluesslipthroughadirect-validator-onlycall.

**Stricttwo-wayparity:probablystillnotperfectunlessschemasarealsohardened.**
Therearestilllikelydirect-stricter/schema-loosergapsunlessyoupatchtheschemastoo:

```text
JSONSchemaacceptspayload
directPythonvalidatorrejectspayload
```

Thosearesaferthanthereverse,buttheyarestillparitygaps.

Thelikelyremainingonesare:

```text
permissionmatrix:
duplicateentries[].dataset_id
directvalidatorshouldreject
schemacurrentlydoesnotexpressunique-by-dataset_id

duplicateallowed_usesvalues,ifdirectrejectsthemafterrawstrictness
directvalidatormayreject
schemacurrentlylacksuniqueItems

blank/sentineltextvalues,ifdirectrejectsorrefusesnormalization
directvalidatormayreject
schemacurrentlyallowssomestringsasmerelytype=string/minLength=1,
andapproval_refmaybestring/null

snapshotmanifest:
duplicatedatasets[].dataset_id
directvalidatorshouldreject
schemacurrentlydoesnotexpressunique-by-dataset_id

planned_storage_uriwithtraversalorembeddedprotocol-ishtextaftertheallowedprefix
directvalidatorshouldreject
schemacurrentlyonlyrequiresprefixpattern:
data/runtime_cache/v2_data_lab/.*

blankrelease_date_field/effective_date_field,ifdirectrejectsblanksinsteadofnormalizingtoNone
directvalidatormayreject
schemacurrentlyallowsstring/nullwithoutminLength

duplicate/blankprimary_keyorpoint_in_time_fieldsentries,ifdirectaddsstricterPIThygiene
directvalidatormayreject
schemacurrentlyonlyrequiresnon-emptyarrayofnon-emptystrings
```

Thereisalsoa**semanticgap**,notexactlyavalidator/schemaparitygap:

```text
permission_matrix_sha256
```

Bothschemaanddirectvalidatorcancheck“isthisalowercase64-charhexstring,”butneithercanprovethehashmatchestheactualpermission-matrixartifactunlessthemanifestvalidatorreceivesthematrixpayloadtoo.ThatisacceptableforV2-D0ifmanifestrefreshisseparatelyapprovedandtested,butitshouldnotbemistakenforfullsemanticverification.

Mypracticalverdict:

```text
Ifdirectvalidatorsarepatchedonly:
noobviousremainingsafety-wideningparitygap;
butexacttwo-wayparitystillhasdirect-stricter/schema-loosercases.

Ifdirectvalidatorsandschemasarebothpatched:
paritycanbemateriallyclosedexceptforcross-rowuniquenessandhash-to-sourcetruth,
whichshouldremaindirect-validator/CIsemanticchecks.
```

Iwouldnotweakenthedirectvalidatorstomatchtheschemas.Forsafety,patchschemasupwardwhereeasy,andkeepdirect-onlysemanticcheckswhereJSONSchemaisawkward.

##2.ShouldV2-D0.1approvedrowsuseonly`provenance_contract`?

**Yes.**

ForV2-D0.1,anapprovedrowshouldmean:

```text
permissiontruthwasrecorded
```

Itshouldnotmean:

```text
provideraccessmaybegin
credentialsmayberesolved
WRDSmaybequeried
schemadiscoverymayrun
snapshotplanningmayadvance
snapshotgenerationmayrun
```

Sothesafestapproved-rowshapeis:

```json
{
"dataset_id":"crsp_daily_stock_file",
"wrds_library":"crsp",
"wrds_table":"dsf",
"dataset_name":"CRSPDailyStockFile",
"permission_status":"approved",
"allowed_uses":[
"provenance_contract"
],
"license_scope":"NON_SECRET_LICENSE_SCOPE",
"pit_required":true,
"provider_access_allowed":false,
"snapshot_generation_allowed":false,
"data_output_allowed":false,
"v1_canonical_write_allowed":false,
"approval_ref":"NON_SECRET_APPROVAL_REF",
"notes":[
"V2-D0.1recordspermissiontruthonly.Noproviderconnection,credentialuse,query,schemadiscovery,snapshotgeneration,dataoutput,V1mutation,ranking,scoring,alert,broker,dashboardruntime,SQLite,SafeBoot,orBootReadyauthorization."
]
}
```

`read_only_permission_probe`shouldbeaddedonlyafteraseparateapprovalthatexplicitlyauthorizesaread-onlyprovider-accessstep.

IwouldalsoexcludethesefromV2-D0.1approvedrowsunlessseparatelyapproved:

```text
schema_discovery
pit_snapshot_design
read_only_permission_probe
```

Even“read-only”provideraccessisstillprovideraccess:itmayrequirecredentials,createprovider-sidelogs,revealaccountentitlementstate,oraccidentallydriftintoschema/tableprobing.KeepD0.1aspermission-truth-only.

##3.Shouldsnapshotmanifestregenerationstayforbiddenuntilaseparate“contract-onlyhashrefresh”approval?

**Yes.**

D0.1shouldnotautomaticallyregeneratethesnapshotmanifestjustbecausepermissionrowschanged.TheminimalD0.1artifactshouldbethepermission-matrixtruthupdate,notarefreshedmanifest.

Reason:

```text
permissionmatrixupdate:
recordsentitlementtruth

snapshotmanifestrefresh:
mutatesasnapshot-facingcontractsurface
updatespermission_matrix_sha256
maycopyapprovedstatusesintodatasets[]
canbemisreadasmovementtowardsnapshotgeneration
```

Aseparateapprovalcansafelyallowamanifestrefresh,butitshouldbeexplicitandnarrow:

```text
approvalscope:
contract-onlyhashrefresh

allowed:
recomputepermission_matrix_sha256fromtheapprovedpermissionmatrix
regenerate/updateonlythecontract-onlymanifestpayload
preservemanifest_status="contract_only"
preserveprovider_access_allowed=false
preservesnapshot_generation_allowed=false
preservecommitted_wrds_output_allowed=false
preservedata_output_allowed=false
preservev1_canonical_write_allowed=false
preservedenied_actions
validatethroughJSONSchema+directPythonvalidators

forbidden:
importwrds
callwrds.Connection
resolvecredentials
queryprovidermetadata
queryproviderdata
writeparquet/csv/jsondatasnapshots
writedata/processedordata/registry
mutateV1canonicaldata
addrowcounts,samples,providerlogs,extractionlogs,oroutputpaths
```

Onenuance:ifastaticsnapshot-manifestartifactalreadyexistsandCItreatsitasauthoritative,leavingitstaleafteraD0.1matrixupdatecreatesanevidence-truthmismatch.Thesafeoptionsareeither:

```text
A.donotincludeorvalidateaD0.1snapshotmanifestartifactyet;or
B.obtaintheseparatecontract-onlyhash-refreshapprovalandupdateonlythemanifestcontractfields.
```

Finalrecommendation:

```text
D0.1:
permissionmatrixonly
approvedrowsallowed_uses=["provenance_contract"]
noread_only_permission_probe
nosnapshotmanifestrefresh

D0.1+separatehash-refreshapproval:
contract-onlymanifestrefreshallowed
noprovideraccess
nocredentials
nosnapshotoutput
noV1mutation
```

用户:
After row-level exact-key patch, any remaining schema/validator gap?
What is the minimal permission-truth artifact with no provider access?
Should Python validators call JSON Schema internally?
AI助手:


AI助手:


AI助手:
Based on the uploaded V2-D0 packet and assuming the **row-level exact-key patch** has been applied:

---

## 1. Remaining schema/validator gap

After exact-key enforcement, the main **remaining gaps** are:

- **Enum/semantic values**: Direct Python validators may accept strings that are type-correct but not in the allowed enum (e.g., `"permission_status": "bogus"`). JSON Schema can enforce enums more strictly.
- **Cross-row uniqueness**: e.g., `entries[].dataset_id` duplicates. Schemas may not express uniqueness, while direct validators can reject duplicates.
- **Hashes and references**: `permission_matrix_sha256` or other derived fields may still be unchecked by the direct validators.
- **Schema-stricter vs validator-stricter differences**: Direct validators may reject some paths or types the schema allows; these are safe but not strictly “parity”.

✅ **Risky widening gaps (credential/output/provider access)** should now be closed after exact-key patch.

---

## 2. Minimal permission-truth artifact (no provider access)

The safest minimal V2-D0.1 artifact should:

- Only record **permission truth**, no provider access, no credentials, no data output, no snapshot, no V1 mutation.
- Use `allowed_uses = ["provenance_contract"]`.
- Keep all provider/output flags false.

Example shape:

```json
{
  "schema_version": "1.0.0",
  "matrix_id": "V2_D0_WRDS_PERMISSION_MATRIX",
  "authority": "offline_contract_only",
  "provider": "wrds",
  "provider_access_allowed": false,
  "snapshot_generation_allowed": false,
  "data_output_allowed": false,
  "v1_canonical_write_allowed": false,
  "entries": [
    {
      "dataset_id": "crsp_daily_stock_file",
      "dataset_name": "CRSP Daily Stock File",
      "permission_status": "approved",
      "allowed_uses": ["provenance_contract"],
      "pit_required": true,
      "approval_ref": "NON_SECRET_APPROVAL_REF",
      "license_scope": "NON_SECRET_LICENSE_SCOPE",
      "provider_access_allowed": false,
      "snapshot_generation_allowed": false,
      "data_output_allowed": false,
      "v1_canonical_write_allowed": false,
      "notes": [
        "V2-D0.1 permission truth only; no provider access, credentials, snapshot, or V1 write."
      ]
    }
  ],
  "created_at_utc": "2026-06-02T00:00:00Z"
}
```

---

## 3. Should Python validators call JSON Schema internally?

**No.** The recommended design:

- **Keep Python validators standalone** for speed, testability, and circular-import avoidance.
- **Direct validators should enforce exact-key and type/enum strictness**, matching schema semantics.
- **JSON Schema validation should remain a separate CI/release gate**, not internal to the direct validators.
- Regression tests can verify that **direct validators + schema validation** reject the same adversarial payloads.

✅ Summary:

- Exact-key + raw-payload strictness → closes the credential/output gaps.  
- Minimal artifact = permission-truth-only rows, no provider, output, snapshot, or V1 write.  
- Direct Python validators should **not call JSON Schema internally**, but should enforce parity with schema semantics.  

---

If you want, I can draft a **concrete V2-D0.1 artifact template** ready for commit that follows these rules. This would be a fully safe “permission-truth-only” JSON payload. Do you want me to do that?

用户:
After row-level exact-key patch, any remaining schema/validator gap?
What is the minimal permission-truth artifact with no provider access?
Should Python validators call JSON Schema internally?
AI助手:


AI助手:


AI助手:


用户:
After row-level exact-key patch, any remaining schema/validator gap?
What is the minimal permission-truth artifact with no provider access?
Should Python validators call JSON Schema internally?
用户:

