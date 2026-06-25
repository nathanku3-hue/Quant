### 分支 · WRDS Account Access Inquiry

AI助手:


AI助手:


用户:
Data / WRDS Provenance Expert, see https://github.com/nathanku3-hue/Quant 

question: “What exact WRDS account/library/table/date/license evidence is required before a read-only probe is allowed?”
用户:

AI助手:
##Verdict

Aread-onlyWRDSprobeis**notallowedyet**undertheuploadedV2-D0packet.Theonlyclearednextactionis**V2-D0.1_WRDS_PERMISSION_TRUTH_AUTHORIZATION**:collectnon-secretentitlementevidenceandexplicitapprovaltext.Thelinkedrepo’sREADMEalsotreatsliveWRDSaccessasunresolved,notingaWRDSauthentication/PAMfailureandindirectvendorprovenancerisk.

WRDS’sowntermsmakethisahardgate:accessisonlyforauthorizedusersofsubscribinginstitutions,useisgovernedbythesubscriber’sWRDSagreement,non-subscribeddataaccessisprohibited,andlocalinstitutionsmayimposeadditionalrestrictions.WRDSalsosayscredentialsmustnotbeshared.

##Exactevidencerequiredbeforeanyread-onlyprobe

###1.Accountauthorityevidence

Providea**non-secretaccountauthorizationrecord**showing:

|Requiredfield|Exactrequirement|
|---|---|
|`account_owner`|NamedWRDS-authorizeduserorapprovedrole.Do**not**providepassword,MFAcode,`.pgpass`,credentialfile,orrawloginlog.|
|`subscriber_institution`|Institution/entitywhoseWRDSsubscriptioncoverstheaccount.|
|`account_type/status`|Activeaccounttypeandcurrentaffiliation/validitywindow.|
|`approved_access_method`|Themethodallowedfortheprobe,e.g.WRDSCloud,SSH,orremotePython/PostgreSQL.Noautomatedwebsitescraping/login.WRDSpermitsremoteSAS/R/Python-styleaccessbutprohibitsscriptedweblogin/queryautomation.|
|`account_scope`|Statementthatthisaccountisallowedtotesttheexactvendorproducts/libraries/tableslistedbelow.|
|`source_of_authority`|WRDSRep,institutionaldatalibrarian/admin,PI/licenseowner,orequivalentwrittenauthorization.|
|`account_evidence_ref`|Stableapprovalreference,ticket,emailID,memoID,ordatedsignedstatement.|

Asuccessfulloginbyitselfis**notenough**.Abroadstatementlike“wehaveWRDS”is**notenough**.

###2.License/vendorentitlementevidence

Providea**licenseentitlementrecord**foreachvendor/productfamily.WRDSdistinguishesbasesubscriptiondatafromadditionalvendordataandsaysinstitutionsareresponsibleforseparatelicensesforadditionaldata,includingCRSP,LSEG/Refinitiv,S&P/CapitalIQ/Compustat-relatedproducts,andothers.

Forthispacket’sdefaultWRDSrows,theminimumvendor/licenseevidenceis:

|Packetdataset|`library.table`|Vendor/productevidencerequired|
|---|---:|---|
|`crsp_daily_stock_file`|`crsp.dsf`|CRSP/CRSPstockdataentitlementforthesubscriber/account.WRDSidentifiesCRSPasadatavendor/productfamily.|
|`crsp_stocknames`|`crsp.stocknames`|SameCRSPentitlement,explicitlycoveringidentifier/namehistorytables.|
|`crsp_ccm_linktable`|`crsp.ccmxpf_linktable`|CRSP/CompustatMergedorequivalentCCM/linkingentitlement,explicitlycoveringthelinktable.|
|`compustat_fundamentals_quarterly`|`comp.fundq`|S&PGlobalMarketIntelligence/CompustatNorthAmericaentitlement.WRDSlistsCompustatNorthAmericaunderS&PGlobalMarketIntelligencedata.|
|`ibes_detail_eps_us`|`ibes.det_epsus`|LSEG/I/B/E/Sentitlement.WRDSlistsI/B/E/SunderLSEGdata.|

Thelicenserecordmustinclude:

`license_owner`,`subscriber_institution`,`vendor_product`,`permitted_use`,`commercial_or_academic_limit`,`redistribution/export_constraints`,`off-WRDSstorage_constraints`,`access_method_constraints`,`covered_account_or_group`,`effective_start`,`effective_end_or_renewal_status`,and`license_evidence_ref`.

###3.Exacttablepermissionevidence

Foreachapprovedrow,recordthetablepermissionasarow-levelfact.Library-levelapprovalisinsufficientunlessitexplicitlynamesthetable.

Requiredrowfields:

```json
{
"dataset_id":"crsp_daily_stock_file",
"dataset_name":"CRSPDailyStockFile",
"wrds_library":"crsp",
"wrds_table":"dsf",
"permission_status":"approved",
"allowed_uses":["read_only_permission_probe","provenance_contract"],
"license_scope":"CRSPentitlementheldby<subscriber>;probe-only;nodataoutput",
"approval_ref":"WRDS-PROBE-APPROVAL-YYYYMMDD-001",
"notes":[
"Non-secretentitlementevidenceonly.",
"Nosnapshotgeneration,rowexport,orV1canonicalwrite."
]
}
```

Rules:

-`permission_status=approved`requiresanon-empty`approval_ref`.
-Rowswithout`approval_ref`stay`unknown`,`pending`,`denied`,or`not_requested`.
-Aread-onlyprobemayinclude**only**approvedrows.
-Ifanyapprovedrowlacksexact`library.table`,stop.
-Ifevidenceapproves`crsp`generallybutnot`crsp.dsf`,`crsp.stocknames`,or`crsp.ccmxpf_linktable`specifically,stop.

###4.Date/as-of/PITevidence

Foreachapprovedtable,providedatecoverageevidence.Thismustbeexplicit,notinferred.

Requiredfields:

```json
{
"probe_as_of_utc":"2026-06-02T00:00:00Z",
"approved_research_start_date":"YYYY-MM-DD",
"approved_research_end_date":"YYYY-MM-DD",
"vendor_coverage_start_date":"YYYY-MM-DDordocumentedunknown",
"vendor_coverage_end_date":"YYYY-MM-DDorcurrent/asdocumented",
"coverage_evidence_ref":"WRDS-DATA-DICTIONARY-or-LICENSE-MEMO-ID",
"pit_required":true,
"release_date_required":true,
"no_future_leakage":true
}
```

MinimumPIT/datefieldstobindbeforeprobingtheserows:

|`library.table`|Requireddate/PITfieldstoacknowledge|
|---|---|
|`crsp.dsf`|primarykey`date,permno`;PITfield`date`|
|`crsp.stocknames`|primarykey`permno,namedt,nameendt`;effective-datefields`namedt,nameendt`|
|`crsp.ccmxpf_linktable`|primarykey`gvkey,lpermno,linkdt,linkenddt`;effective-datefields`linkdt,linkenddt`|
|`comp.fundq`|primarykey`gvkey,datadate`;PITfields`datadate,rdq`;release-datefield`rdq`|
|`ibes.det_epsus`|primarykey`ticker,anndats,fpedats`;PITfields`anndats,fpedats,revdats`;release-datefield`anndats`|

Fortheread-onlyprobe,dateevidencedoes**not**authorizesnapshotgeneration.ItonlyprovestherequestedresearchwindowandPITsemanticsareknownbeforemetadata/accesschecks.

###5.Explicitprobeapprovaltext

Theapprovalmustcontainthissubstance,preferablyverbatim:

```text
APPROVAL_REF:<stableID>

IapproveaWRDSread-onlypermissionprobeonlyforTerminalZero/QuantV2-D0.1.

Authorizedaccount/licenseowner:<nameorrole>
Subscriberinstitution/entity:<institution>
Approvedaccessmethod:<WRDSCloud/SSH/remotePython/other>
Approvedrowsonly:
-crsp.dsf
-crsp.stocknames
-crsp.ccmxpf_linktable
-comp.fundq
-ibes.det_epsus

Approveddate/as-ofscope:
-probe_as_of_utc:<timestamp>
-approvedresearchcoverage:<start_date>through<end_date>
-PIT/release-dateconstraintsmustremainenforced.

Thisapprovalpermitsonlymetadata/access/schema-stylepermissionconfirmation.
Itdoesnotpermitsnapshotgeneration,row/sampleexport,committedWRDSoutput,
data/processedwrites,data/registrywrites,runtimewrites,dashboardreader,
candidateranking/scoring/promotion,recommendations,alerts,broker/orderpaths,
SQLitestorage,SafeBoot,orBootReadyclaims.

NoWRDSpassword,MFAcode,credentialfile,.pgpass,connectionURI,rawproviderlog,
orproprietarydataoutputmaybecommittedorshared.
```

###6.Contractguardrailsthatmustremaintrue

Beforetheprobe,thepacket’sV2-D0contractmuststillvalidatewith:

```text
provider_access_allowed=false
wrds_connection_attempted=false
snapshot_generation_allowed=false
data_output_allowed=false
v1_canonical_write_allowed=false
next_allowed_action=record_permission_decision_only
```

Thatmeanstheevidencegatemayauthorizea**futurenarrowlyscopedprobeimplementation**,butthecurrentV2-D0artifactsthemselvesmustremainoffline-contract-onlyuntiltheseparateprobephaseisexplicitlyopened.

##Fail-closedrule

Theprobeisblockedifanyofthesearemissing:

`WRDSaccount/licenseowner`,`subscriber/accountscope`,exact`library.table`,row-level`permission_status=approved`,row-level`approval_ref`,vendor/licenseconstraints,date/as-of/PITcoverage,andexplicit“read-onlypermissionprobeonly;nosnapshot/dataoutput”approval.

Nocredentials,notablereads,noqueryexecution,nosnapshots,nopersistedWRDSoutput,andnoruntime/datawritesbeforethatgateiscomplete.

用户:
What exact library.table list should be approved for V2-D0.1, and which rows should remain unknown or not_requested?
What non-secret evidence is acceptable for each entitlement: email, ticket, data-librarian note, WRDS account page screenshot, or license memo?
Should ibes.det_epsus, comp.fundq, and crsp.ccmxpf_linktable all be required for PEAD_V2_001, or can PEAD start with a smaller table set?
AI助手:


AI助手:


AI助手:
Here’s a detailed, precise answer for V2-D0.1 access management and the PEAD_V2_001 probe plan:

---

## 1. Exact `library.table` list to be approved for V2-D0.1

For **V2-D0.1_WRDS_PERMISSION_TRUTH_AUTHORIZATION**, the read-only probe should **only include rows/tables that have clear entitlement evidence**. Based on the uploaded packet and standard PEAD/CRSP/Compustat/IBES pipelines:

**Approved tables:**

| Library | Table | Notes |
|---------|-------|-------|
| `crsp` | `dsf` | Daily stock file, required for stock returns and market calculations. |
| `crsp` | `stocknames` | Security identifiers and name history; required for mapping permno → gvkey. |
| `crsp` | `ccmxpf_linktable` | CRSP-Compustat link table; required only if you will merge fundamentals with stock returns. |
| `comp` | `fundq` | Quarterly fundamentals; required if PEAD computation uses accounting variables. |
| `ibes` | `det_epsus` | Detailed US earnings forecasts; required for PEAD event-response measurement. |

**Rows/tables that can remain `unknown` or `not_requested`:**

- Any vendor/library/table not explicitly licensed for your subscriber account.
- Non-core tables within each library (e.g., CRSP indices tables not needed for your PEAD implementation).
- Any tables intended for exploratory analysis but **without license evidence**.

> **Rule:** Only tables with documented non-secret approval (see next section) can be marked `approved`. Others remain `unknown` or `not_requested`.

---

## 2. Acceptable **non-secret evidence** for each entitlement

You **cannot share credentials or secret data**. Acceptable evidence per WRDS and institutional practice:

| Evidence type | Acceptable? | Notes |
|---------------|------------|-------|
| Email from WRDS rep or institutional librarian | ✅ | Must clearly state account/license approval for specific library.table; include date/reference ID. |
| Helpdesk / IT ticket | ✅ | Same as email; shows formal institutional authorization. |
| Data-librarian note (memo, PDF, signed letter) | ✅ | Can be scanned or digital; must cite subscriber account, library.table, and allowed usage. |
| WRDS account page screenshot | ✅ | Only if it shows authorized libraries, table list, and active subscription; **do not share credentials**. |
| License memo / vendor contract excerpt | ✅ | Must explicitly state permitted use, covered tables, and effective date; redact commercial/legal confidential terms if needed. |
| Raw login/log files, passwords, MFA codes | ❌ | Never acceptable. |
| .pgpass / connection files | ❌ | Never acceptable. |

> **Guiding principle:** Evidence should prove authorization, subscription, and table-level access **without revealing secret credentials or passwords**.

---

## 3. Are `ibes.det_epsus`, `comp.fundq`, and `crsp.ccmxpf_linktable` all required for PEAD_V2_001?

- **Depends on the PEAD analysis scope:**
  - If PEAD_V2_001 requires **earnings announcement returns only**, `crsp.dsf` + `crsp.stocknames` may be enough for initial testing.  
  - If you also compute **abnormal returns relative to fundamentals or forecast-based analysis**, then `comp.fundq` and `ibes.det_epsus` become necessary.
  - `crsp.ccmxpf_linktable` is only required if you are **merging stock returns with Compustat fundamentals**.

> **Best practice:** Start with the minimal table set for which you have license evidence (`crsp.dsf` + `crsp.stocknames`) and mark other tables `not_requested`. Expand approvals later once the license/memo/email evidence for `ibes.det_epsus`, `comp.fundq`, or `crsp.ccmxpf_linktable` is collected.

---

### ✅ Recommended V2-D0.1 Table Permission Plan

```text
Approved:
- crsp.dsf
- crsp.stocknames

Unknown / not_requested:
- crsp.ccmxpf_linktable
- comp.fundq
- ibes.det_epsus
```

> This allows a **safe read-only probe** for PEAD_V2_001 without violating license constraints. Later, once formal entitlement evidence exists, you can mark the other tables as approved.

---

If you want, I can draft a **ready-to-submit V2-D0.1 table/row approval matrix** with `approved` / `unknown` / `not_requested` flags that matches WRDS rules, which you can directly attach to your authorization packet. It will also include non-secret evidence references for each table. Do you want me to do that?

AI助手:


AI助手:


AI助手:
Here’s a precise breakdown for V2-D0.1 based on your uploaded packet and WRDS standards:

---

## 1. Exact `library.table` list to approve for V2-D0.1

For the **read-only permission probe**, only **fully approved tables with verified account/license evidence** may be listed. Based on the V2-D0 packet defaults:

| Library | Table | Notes / Row-level requirements |
|---------|-------|-------------------------------|
| `crsp` | `dsf` | Required for daily stock time series. Row-level approval per `permno, date`. |
| `crsp` | `stocknames` | Required for historical identifier/name mappings. Row-level approval per `permno, namedt, nameendt`. |
| `crsp` | `ccmxpf_linktable` | Required only if using CRSP/Compustat Merged link functionality. Row-level approval per `gvkey, lpermno, linkdt, linkenddt`. |
| `comp` | `fundq` | Required for quarterly fundamentals (Compustat). Row-level approval per `gvkey, datadate`. |
| `ibes` | `det_epsus` | Required for U.S. I/B/E/S EPS data. Row-level approval per `ticker, anndats, fpedats`. |

**Row-level states for V2-D0.1:**

- `approved` — only if non-secret evidence exists and maps to table/date coverage.
- `unknown` — table exists but no account/license evidence yet.
- `not_requested` — table is optional for future use or outside the initial scope.

> For initial probe (V2-D0.1), tables like `crsp.dsf` and `crsp.stocknames` are usually **mandatory**. `crsp.ccmxpf_linktable`, `comp.fundq`, `ibes.det_epsus` can remain `unknown` or `not_requested` if the immediate probe does not need merged/earnings/fundamentals yet.

---

## 2. Acceptable non-secret evidence per table

WRDS explicitly forbids sharing credentials or raw logs. Acceptable evidence types include:

| Evidence type | Acceptable? | Notes |
|---------------|-------------|-------|
| Email from WRDS/data librarian/PI confirming entitlement | ✅ | Must include account, institution, allowed library/tables, date coverage. |
| Ticket or helpdesk request/approval | ✅ | Same conditions as email. Can be internal ticket ID or institutional note. |
| Data librarian note / memo | ✅ | Must be signed/dated and clearly reference the library/table and permitted use. |
| WRDS account page screenshot (without password/MFA) | ✅ | Only metadata visible; must not reveal credentials. Shows active account, institution, and accessible libraries. |
| License memo from vendor (CRSP, Compustat, IBES) | ✅ | Confirms institutional subscription and table-level entitlement. |

**Unacceptable:** passwords, `.pgpass`, raw query logs, MFA codes, database dump, or any proprietary WRDS output.

---

## 3. Minimal table set for PEAD_V2_001

- **PEAD_V2_001** (Post-Earnings Announcement Drift experiment) **does not strictly require all tables initially**.
- Minimum required for the **initial probe**:

1. `crsp.dsf` — daily stock prices (for returns and trading dates).
2. `crsp.stocknames` — to map identifiers (`permno`) over time.

- Optional / can be `unknown` / added later:

1. `crsp.ccmxpf_linktable` — only needed if linking to Compustat fundamentals is necessary.
2. `comp.fundq` — optional for fundamental analysis.
3. `ibes.det_epsus` — optional if studying EPS revisions/analyst forecasts; may be deferred until PEAD extension.

> **Rule of thumb:** start with minimal tables needed for the probe (CRSP prices and names) to satisfy read-only provenance; expand once license/account evidence for other tables is fully collected.

---

✅ **Summary guidance**

- Approve only tables with explicit non-secret evidence.
- Use `unknown` or `not_requested` for optional/secondary tables.
- PEAD initial probe can start with just `crsp.dsf` and `crsp.stocknames`.
- Evidence types: email, ticket, librarian note, account screenshot (metadata only), or vendor license memo.

---

If you want, I can draft a **V2-D0.1 “approved table list” template** showing exactly which rows should be `approved` vs `unknown` vs `not_requested` for your PEAD probe, including placeholders for email/ticket/license references. This makes your next step plug-and-play. Do you want me to do that?

用户:
What exact library.table list should be approved for V2-D0.1, and which rows should remain unknown or not_requested?
What non-secret evidence is acceptable for each entitlement: email, ticket, data-librarian note, WRDS account page screenshot, or license memo?
Should ibes.det_epsus, comp.fundq, and crsp.ccmxpf_linktable all be required for PEAD_V2_001, or can PEAD start with a smaller table set?
AI助手:


AI助手:


AI助手:
Here’s a detailed breakdown for **V2-D0.1 WRDS permission preparation** based on your questions:  

---

## 1️⃣ Library.table list to approve for V2-D0.1

For a **read-only metadata/probe** in V2-D0.1, the **minimal approved tables** (assuming the PEAD workflow described in your packet) are:

| Library | Table | Notes / Minimum needed for PEAD_V2_001 |
|---------|-------|----------------------------------------|
| crsp    | dsf   | Daily stock file; required for CRSP returns and event windows. Must be explicitly approved. |
| crsp    | stocknames | Required if mapping permno → company identifiers for PIT or linking purposes. Can remain unknown if PEAD workflow does not need historical name coverage at first. |
| crsp    | ccmxpf_linktable | Required only if merging with Compustat identifiers. If PEAD can start purely on returns, this may remain `unknown` initially. |
| compustat | fundq | Required if the PEAD workflow requires quarterly fundamentals. Optional if PEAD is only analyzing price reactions without fundamentals; can start with `not_requested`. |
| ibes     | det_epsus | Required only if PEAD needs EPS forecast/revision data. Optional at start if PEAD is only return/event-window based; can be `not_requested`. |

**Rule of thumb:**  
- **Required tables**: CRSP daily stock (`crsp.dsf`) to start any PEAD-style analysis.  
- **Optional / delayed tables**: `comp.fundq`, `ibes.det_epsus`, and `crsp.ccmxpf_linktable` can initially be `unknown` or `not_requested` depending on the analysis scope.  

So **PEAD_V2_001 can start with a minimal table set**, but you must explicitly mark any not-yet-approved table as `unknown` or `not_requested` to avoid accidental access.

---

## 2️⃣ Non-secret evidence acceptable per entitlement

Per WRDS / V2-D0.1 guidance, **do not share passwords, MFA, or raw credentials**. Acceptable **non-secret proof** includes:

| Evidence type | Acceptable? | Notes |
|---------------|------------|------|
| Email from WRDS / institutional librarian confirming entitlement | ✅ | Must clearly name account, library.table, and purpose (“read-only probe”) |
| Ticket / ticket ID with written authorization | ✅ | Include date, authorizing party, and scope |
| Data-librarian or PI note / memo | ✅ | Must specify exact tables, approved access method, and date range |
| License memo / license excerpt | ✅ | Can be scanned PDF or official excerpt; must clearly state subscriber, product, table, and scope |
| WRDS account page screenshot | ✅ | Only metadata / entitlement info; **do not** include username/password/MFA codes |

**Forbidden:**  
- Passwords, `.pgpass` files, SAS keys, raw login logs, screenshots showing sensitive account details.  

**Best practice:** Keep a clear `approval_ref` for each table/entitlement.

---

## 3️⃣ PEAD_V2_001 table dependencies

- **ibes.det_epsus:** Only needed if PEAD workflow requires earnings forecast/revision analysis. Can start without.  
- **comp.fundq:** Only needed for fundamentals-linked PEAD. Optional at start if focusing purely on price reactions.  
- **crsp.ccmxpf_linktable:** Only needed if you merge CRSP and Compustat identifiers. Optional if you start PEAD using only CRSP returns.

**Implication:**  
You can start PEAD_V2_001 with **just `crsp.dsf`** approved. The other tables can remain `unknown` or `not_requested` until the workflow expands.  

**Recommendation for V2-D0.1 readiness:**  
- Approve `crsp.dsf` first.  
- Mark `crsp.stocknames`, `crsp.ccmxpf_linktable`, `comp.fundq`, `ibes.det_epsus` as `unknown` or `not_requested`.  
- Update approval evidence incrementally as workflow requires additional tables.  

---

If you want, I can **produce a ready-to-use V2-D0.1 table/row approval map** showing exactly which tables should be `approved` vs `unknown/not_requested` for PEAD_V2_001, including placeholders for non-secret evidence references. This can serve as a compliance-ready artifact.  

Do you want me to do that next?

用户:
What exact library.table list should be approved for V2-D0.1, and which rows should remain unknown or not_requested?
What non-secret evidence is acceptable for each entitlement: email, ticket, data-librarian note, WRDS account page screenshot, or license memo?
Should ibes.det_epsus, comp.fundq, and crsp.ccmxpf_linktable all be required for PEAD_V2_001, or can PEAD start with a smaller table set?
用户:

AI助手:
##Directanswer

For**V2-D0.1**,theapprovalrequestshouldcover**onlythefiverowsalreadypresentintheV2-D0packet’sdefaultWRDSpermissionmatrix**:

|Packetrow|Exact`library.table`|Approvaltarget|
|---|---:|---|
|`crsp_daily_stock_file`|`crsp.dsf`|ApproveifCRSPstock/securityentitlementisevidenced.|
|`crsp_stocknames`|`crsp.stocknames`|ApproveifCRSPidentifier/name-historyentitlementisevidenced.|
|`crsp_ccm_linktable`|`crsp.ccmxpf_linktable`|ApproveonlyifCCM/CRSP-CompustatMergedentitlementisevidenced.|
|`compustat_fundamentals_quarterly`|`comp.fundq`|ApproveonlyifCompustatNorthAmericaquarterlyfundamentalsentitlementisevidenced.|
|`ibes_detail_eps_us`|`ibes.det_epsus`|ApproveonlyifLSEG/I/B/E/SDetailEPSUSentitlementisevidenced.|

Everythingelseshouldbe**`not_requested`**forV2-D0.1unlessanewmatrixversionexplicitlyaddsit.Thatmeansno`crsp.msf`,no`comp.funda`,no`ibes.id`,no`ibes.idsum`,no`ibes`summarytables,noOrbis/BvD,noTAQ,nooptions,nocorporate-actionsexpansion,noFINRA,andnolink-tablesubstitutions.

Therepo’scurrentpublicREADMEstillidentifiesliveWRDSauthentication/provenanceasanopenoperationalrisk,sohistoricalWRDSoutputsorlibraryscansshouldnotbetreatedasentitlementapproval.WRDSalsomakesthepermissionboundaryexplicit:credentialscannotbeshared,usersmustaccessWRDSonlythroughapprovedmethodssuchasWRDSwebsite,WRDSCloud/SSH,orremoteSAS/R/Python-styledatabaseconnections,andattemptstoaccessnon-subscribeddataareprohibited.

##StatusruleforV2-D0.1rows

Usethisexactstatuspolicy:

|Situation|Correct`permission_status`|
|---|---|
|Evidenceexistsandnamestheaccount,subscriber,product/license,exact`library.table`,permitteduse,dates,andapprovalreference|`approved`|
|Evidencerequesthasbeensentbutnotanswered|`pending`|
|Therowisinthefive-rowmatrixbutnoentitlementtruthisknownyet|`unknown`|
|Therowisdeliberatelyexcludedfromthecurrentprobescope|`not_requested`|
|Dataowner,WRDSRep,librarian,PI,orlicenseauthoritysaysno|`denied`|

Forthe**fullV2-D0.1entitlement-probescope**,allfiverowsmayberequested,butnoneshouldbemarked`approved`untilevidenceexists.Fora**smallerPEADstarterscope**,marktheunusedrows`not_requested`,not`unknown`,sotheycannotaccidentallyentertheread-onlyprobe.

##Acceptablenon-secretevidence

Allofthesecanbeacceptable,butonlyiftheyare**redacted,dated,attributable,stable,andspecific**.

|Evidencetype|Acceptable?|Useitfor|Caveat|
|---|---:|---|---|
|EmailfromWRDSRep,institutionaldatalibrarian,licensedPI,dataadmin,orequivalent|Yes|Accountauthority,productentitlement,tableapproval,read-onlyprobeapproval|Mustcontainastableapprovalreferenceorbeconvertedintoone.|
|Institutional/WRDS/libraryticket|Yes|Bestoperationalevidence|Mustshowresolvedapproval,notmerelyaquestion.|
|Data-librariannoteormemo|Yes|Verygoodentitlementevidence|Mustnamesubscriber,account/role,vendorproduct,tables,useconstraints,anddates.|
|WRDSaccountpagescreenshot|Partial|Accountstatus,affiliation,accounttype,sometimesproductvisibility|Notenoughbyitselfforvendor/tablelicenseunlessitclearlyshowsproduct/tableentitlements.RedactsessionIDs,cookies,MFAprompts,credentials,unnecessaryusernamedetails.|
|Redactedlicensememo/subscriptionmemo|Yes|Strongestlicenseevidence|Mayproveinstitutionentitlementbutstillneedsaccount/scopeapprovalforthisspecificprobe.|
|Datadictionaryscreenshot|Partial|Datecoverage,schema/PITfields|Doesnotprovelicenseentitlement.|
|Successfullogin,librarylist,rowcount,oldqueryoutput,repoartifact,rawSQLlog|No|Notpermissionevidence|Theseproveactivityoravailability,notauthorization.|

Theevidencerecordshouldlooklikethis,withnosecrets:

```json
{
"evidence_ref":"WRDS-V2D01-20260602-001",
"evidence_type":"data_librarian_note",
"issuer_role":"institutionalWRDS/datalibrarian",
"subscriber_institution":"<institution>",
"authorized_account_or_role":"<nameduserorapprovedrole>",
"approved_access_method":"WRDSCloudorremotePython/PostgreSQL",
"permitted_use":"read_only_permission_probe_only_no_data_output",
"covered_rows":[
"crsp.dsf",
"crsp.stocknames",
"crsp.ccmxpf_linktable",
"comp.fundq"
],
"research_date_window":"YYYY-MM-DDthroughYYYY-MM-DD",
"probe_as_of_utc":"2026-06-02T00:00:00Z",
"constraints":[
"nocredentialsharing",
"norow/sampleexport",
"nosnapshotgeneration",
"noV1canonicalwrite",
"nodata/processedwrite"
]
}
```

##Entitlement-by-entitlementevidence

|Entitlement|Rowsitcanapprove|Acceptableevidence|
|---|---:|---|
|**WRDSaccountauthority**|Nonebyitself;itunlocksaccount-leveleligibilityonly|WRDSaccountpagescreenshotpluslibrarian/WRDSRepnoteorticketconfirmingactivesubscriberaffiliation,accounttype,approvedaccessmethod,andthattheaccount/rolemayperformtheV2-D0.1read-onlyprobe.WRDSaccounttypesandaccessvarybyaffiliation/role.|
|**CRSPstock/securitydata**|`crsp.dsf`,`crsp.stocknames`|Email,ticket,librariannote,accountsubscriptionscreenshot,orlicensememoconfirmingCRSPstock/securitydataaccessforthesubscriber/account.|
|**CCM/CRSP-CompustatMerged**|`crsp.ccmxpf_linktable`|MustexplicitlymentionCCM,CRSP/CompustatMerged,ortheexacttable.CRSP+CompustatseparatelyisnotenoughunlesstheauthorityconfirmsCCMaccess,becauseWRDSdescribesCCMasanadditionalCRSPproductsubscription.|
|**S&P/CompustatNorthAmerica**|`comp.fundq`|Email,ticket,librariannote,accountsubscriptionscreenshot,orlicensememoconfirmingCompustatNorthAmericaquarterlyfundamentals.WRDSlistsCompustatNorthAmericaunderS&PGlobalMarketIntelligencedata.|
|**LSEG/I/B/E/S**|`ibes.det_epsus`|Email,ticket,librariannote,accountsubscriptionscreenshot,orlicensememoconfirmingI/B/E/SdetailEPS/earningsestimates.WRDSlistsI/B/E/SunderLSEGdata.|

ForI/B/E/S-linkedPEADwork,alsorecordhowI/B/E/SidentifierswillbelinkedtoCRSP.WRDSnotesI/B/E/Shasidentifiertablessuchas`ibes.id`and`ibes.idsum`,andWRDS’sLinkingSuiteseparatelydescribesanIBES-CRSPlinkthatrequiresbothIBESandCRSPsubscriptions.Thosetablesare**not**inthecurrentV2-D0.1five-rowmatrix,sodonotsilentlyaddthem.

##PEAD_V2_001:allthreerequired,orsmallerstart?

PEAD**canstartwithasmallertableset**.Do**not**make`ibes.det_epsus`,`comp.fundq`,and`crsp.ccmxpf_linktable`allmandatoryunless`PEAD_V2_001`isexplicitlydefinedasacombinedCompustat+I/B/E/Sanalyst-surprisevariant.

###Recommendedstarter:Compustat-basedPEAD

ForthefirstWRDS-provenancePEADstart,Iwouldusethissmaller,defensiblescope:

|Status|`library.table`|Reason|
|---|---:|---|
|`approved`|`crsp.dsf`|Dailypost-announcementreturns.|
|`approved`|`crsp.stocknames`|Historicalidentifier/name/tickerauditsupport.|
|`approved`|`crsp.ccmxpf_linktable`|PIT-ishCompustat`gvkey`toCRSP`permno`linking.|
|`approved`|`comp.fundq`|Quarterlyearningsevent/release-date/fundamentalsource,including`datadate`and`rdq`semantics.|
|`not_requested`|`ibes.det_epsus`|NotneededforthefirstCompustat-rdqPEADvariant.|

Thatisthecleanest**PEAD_V2_001starterset**ifthefirstvariantis“earningsannouncement/quarterlyfundamentals/CRSPdrift”ratherthananalyst-estimatesurprise.

###I/B/E/Sanalyst-surprisePEAD

If`PEAD_V2_001`isinsteaddefinedas“analystestimatesurprise/forecastrevision/I/B/E/S-basedsurprise,”then`ibes.det_epsus`becomesrequired.But`ibes.det_epsus`aloneisnotenoughforarobustlinkedPEADpathunlesstheidentifier-linkrouteisalsoapprovedanddocumented.Underthecurrentfive-rowmatrix,thatmeanseither:

1.approveallfivedefaultrowsandtreatI/B/E/Slinkageasunresolveduntilalatermatrixamendment;or
2.amendthematrixtoaddtheexactI/B/E/Sidentifier/linktablesbeforeanyI/B/E/S-linkedPEADprobe.

###CombinedPEADvariant

Useallfiveonlyforacombinedvariant:

```text
crsp.dsf
crsp.stocknames
crsp.ccmxpf_linktable
comp.fundq
ibes.det_epsus
```

ThatcombinedscopeisvalidforV2-D0.1onlyifeveryrowhasan`approval_ref`.ItshouldnotbetheminimumPEADgate.

##Recommendeddecision

Set**V2-D0.1defaultfullrequest**tothefive-rowmatrixabove,butforthefirstPEADimplementationpathchoosethesmallerCompustat-basedstarter:

```text
ApproveforPEAD_V2_001starter:
-crsp.dsf
-crsp.stocknames
-crsp.ccmxpf_linktable
-comp.fundq

Leavenot_requestedforPEAD_V2_001starter:
-ibes.det_epsus
```

Keep`ibes.det_epsus`as`unknown`onlyiftheteamintendstorequestI/B/E/Sentitlementnowbuthasnotyetreceivedtheanswer.Use`not_requested`ifthefirstPEADcutdeliberatelyexcludesI/B/E/S.

用户:
Should V2-D0.1 request all five default rows, or should PEAD_V2_001 start with the smaller Compustat PEAD set?
Is ibes.det_epsus not_requested for PEAD_V2_001 starter, or unknown because entitlement will be requested now?
What evidence format is acceptable as approval_ref: librarian ticket, WRDS email, license memo, or signed internal note?
用户:

AI助手:
##Decision

**Doboth,butkeepthescopesseparate.**

**V2-D0.1shouldrequestentitlementtruthforallfivedefaultrows**becausetheuploadedpacket’sdefaultWRDSmatrixalreadynamesthosefivedatasetsastheintendedprovenanceuniverse.

**PEAD_V2_001shouldstartwiththesmallerCompustatPEADset**andshould**not**beblockedbyI/B/E/Sentitlement.

Thecleanstructureis:

```text
V2-D0.1entitlement-truthrequest:
-askaboutallfivedefaultrows
-noprovideraccess
-notableread
-nosnapshot
-nodataoutput

PEAD_V2_001starterdependencyset:
-requireonlytheCompustat-basedPEADrows
-leaveI/B/E/Soutofthestarter
```

Thismatchesthepacketboundary:V2-D0.1isauthorization/evidencecollection,notPEADimplementationandnotaWRDSprobe.ThepublicrepoalsostillshowsWRDSprovenanceasunresolved,notingliveWRDSauthenticationfailureandboundedfallbackprovenance,sothefail-closedgateremainsappropriate.WRDSaccessitselfmuststaywithinauthorized-user,subscribed-data,credential-confidentiality,andapproved-access-methodboundaries.

##Exactrowmatrix

|Row|`library.table`|V2-D0.1entitlementrequest|PEAD_V2_001starter|Statusguidance|
|---|---:|---:|---:|---|
|`crsp_daily_stock_file`|`crsp.dsf`|Requestnow|Required|`pending`afterrequest,`approved`onlywith`approval_ref`.|
|`crsp_stocknames`|`crsp.stocknames`|Requestnow|Required|`pending`afterrequest,`approved`onlywith`approval_ref`.|
|`crsp_ccm_linktable`|`crsp.ccmxpf_linktable`|Requestnow|Required|`pending`afterrequest,`approved`onlywithexplicitCCM/link-tableevidence.|
|`compustat_fundamentals_quarterly`|`comp.fundq`|Requestnow|Required|`pending`afterrequest,`approved`onlywithCompustatNorthAmericaevidence.|
|`ibes_detail_eps_us`|`ibes.det_epsus`|Requestnowasoptional/futurePEAD-surpriseentitlementtruth|**Notrequired**|`pending`inV2-D0.1ifrequestednow;`not_requested`inPEAD_V2_001starterscope.|

Rowsoutsidethosefiveshouldremain:

```text
not_requested
```

Thatincludes`crsp.msf`,`comp.funda`,`ibes.id`,`ibes.idsum`,I/B/E/Ssummarytables,TAQ,OptionMetrics,Zacks,FactSet,Orbis/BvD,CompustatGlobal,andanysubstitutelinktablesunlessalatermatrixversionexplicitlyaddsthem.

##Howtohandle`ibes.det_epsus`

Usetwostatusesconceptually:

```text
Entitlement-truthstatusforV2-D0.1:pending,ifyourequestI/B/E/Snow.
PEAD_V2_001starter-usestatus:not_requested.
```

Sotheansweris:

**`ibes.det_epsus`is`not_requested`forthePEAD_V2_001starter.**

Itis**not`unknown`inthestarterscope**justbecauseentitlementisbeingrequestedinparallel.`unknown`meansentitlementtruthisnotknown.`not_requested`meanstherowisdeliberatelyoutsidethecurrentstarterdependencyset.

IntheV2-D0.1permission-truthartifact,usethisrule:

|Situation|`ibes.det_epsus`status|
|---|---|
|NoonehasaskedforI/B/E/Sentitlementyet|`unknown`|
|Ticket/email/requesthasbeensent|`pending`|
|Authorityapprovesexact`ibes.det_epsus`scope|`approved`with`approval_ref`|
|AuthoritydeniesI/B/E/Sortable-levelaccess|`denied`|
|TeamdecidesnottoaskforI/B/E/Sinthisauthorizationround|`not_requested`|

Forthe**PEAD_V2_001starter**,itremains:

```json
{
"dataset_id":"ibes_detail_eps_us",
"wrds_library":"ibes",
"wrds_table":"det_epsus",
"pead_v2_001_starter_scope":"not_requested",
"reason":"StarterisCompustat-rdqPEAD,notanalyst-estimate-surprisePEAD."
}
```

I/B/E/Sshouldbecomerequiredonlyforananalyst-estimateoranalyst-surprisePEADvariant.WRDSdescribesI/B/E/Sasanalystforecast,earningsestimate,andrecommendationdata,whichisadifferentevidencepathfromaCompustatquarterly-fundamentalsPEADstarter.

##PEAD_V2_001starterset

ForthefirstCompustat-basedPEADimplementation,approveonlythisrequiredset:

```text
crsp.dsf
crsp.stocknames
crsp.ccmxpf_linktable
comp.fundq
```

Rationale:

`crsp.dsf`givesdailyreturn/pricingobservations.

`crsp.stocknames`giveshistoricalidentifier/name/tickersupport.

`crsp.ccmxpf_linktable`linksCompustat`gvkey`toCRSP`permno`;thisneedsexplicitCCMevidencebecauseWRDSdescribesCCMasanadditionalCRSPproductsubscriptionforlinkingCRSPandCompustat.

`comp.fundq`givesquarterlyfundamentals/earningsannouncementtimingsurfaceforaCompustat-rdqPEADpath;WRDSlistsCompustatNorthAmericaunderS&PGlobalMarketIntelligenceanddescribesannualandquarterlyfundamentalscoverage.

SothePEADstarterapprovaltextshouldsay:

```text
PEAD_V2_001starterrequiredrows:
-crsp.dsf
-crsp.stocknames
-crsp.ccmxpf_linktable
-comp.fundq

PEAD_V2_001starternot_requested:
-ibes.det_epsus

I/B/E/SmayberequestedinV2-D0.1onlyasoptional/futureentitlementtruth
forlateranalyst-estimate-surprisevariants,anditisnotablockerforthe
Compustat-rdqPEADstarter.
```

##Acceptable`approval_ref`formats

Allfourformatsareacceptable**iftheyarestable,non-secret,attributable,dated,andtable-specific**.

|Format|Acceptableas`approval_ref`?|Strength|Requirement|
|---|---:|---:|---|
|Librarian/data-servicesticket|Yes|Strongestoperationalreference|Mustshowresolvedapprovalorauthoritativeentitlementconfirmation,notjustanopenquestion.|
|WRDSemail|Yes|Strong|MustbefromWRDSSupport,WRDSRep,institutionalWRDSadministrator,orequivalent;usemessageID,ticketID,archiveID,orhashedemailreference.|
|Licensememo|Yes|Strongestlicensereference|Mustidentifyvendor/productentitlementandsubscribercoverage;oftenneedsasecondaccount/scopeapprovalreference.|
|Signedinternalnote|Yes,conditionally|Goodifsignerhasauthority|SignermustbePI/licenseowner/datalibrarian/WRDSRep/delegatedauthority.Aself-attestationbytheimplementerisnotenough.|

Bestpractice:make`approval_ref`a**singleinternalevidence-bundleID**,thenattachoneormoreevidencedocumentsbehindthatID.

Example:

```json
{
"approval_ref":"WRDSAUTH-20260602-V2D01-PEAD-COMP-001",
"approval_ref_type":"evidence_bundle",
"evidence_refs":[
"LIB-TICKET-20260602-1842",
"LIC-MEMO-COMPUSTAT-CRSP-2026Q2",
"WRDS-EMAIL-MSGID-HASH-7F91C2"
],
"approved_rows":[
"crsp.dsf",
"crsp.stocknames",
"crsp.ccmxpf_linktable",
"comp.fundq"
],
"not_requested_for_pead_v2_001_starter":[
"ibes.det_epsus"
]
}
```

The`approval_ref`mustnotbeapassword,credentialfile,WRDSconnectionURI,rawlogintranscript,rawproviderlog,`.pgpass`,MFAprompt,cookie-bearingscreenshot,orunredactedlicensetext.WRDStermsrequirecredentialconfidentialityandprohibitaccesstonon-subscribeddata;theyalsospecifyallowedaccessmethodsandprohibitscriptedwebsitelogin/queryautomation.

##Minimumcontentinsidetheapprovalevidence

Whicheverformatyouuse,theevidencemuststateorcross-reference:

```text
account_or_role_authorized
subscriber_institution
approved_access_method
vendor/productentitlement
exactlibrary.tablerows
approveduse=read-onlypermission/provenanceprobeonly
norow/sampleexport
nosnapshotgeneration
nocommittedWRDSoutput
noV1canonical/data/processed/runtimewrites
researchdatewindoworas-ofscope
license/storage/redistributionconstraints
issuer/authority
date
stableapproval_ref
```

##Recommendedfinalcall

Usethisasthedecision:

```text
V2-D0.1willrequestentitlementtruthforallfivedefaultrows.

PEAD_V2_001willstartasthesmallerCompustat-rdqPEADstarterandwill
requireapprovalonlyfor:
-crsp.dsf
-crsp.stocknames
-crsp.ccmxpf_linktable
-comp.fundq

ForPEAD_V2_001starter:
-ibes.det_epsus=not_requested

ForV2-D0.1entitlementtruth:
-ibes.det_epsus=pendingoncetheI/B/E/Srequestissent
-ibes.det_epsus=unknownbeforetherequestissent
-ibes.det_epsus=approvedonlywithexacttable-levelapproval_ref
```

ThatgivesthefastestsafePEADpathwithoutlosingthebenefitofresolvingI/B/E/Sentitlementtruthforlateranalyst-surprisevariants.

用户:
What exact library.table rows are needed for V2-D0.1?
What non-secret evidence proves entitlement?
Can PEAD start with fewer than CRSP + Compustat + IBES + CCM?
用户:

AI助手:
## 1. Exact `library.table` rows needed for **V2-D0.1**

For **V2-D0.1_WRDS_PERMISSION_TRUTH_AUTHORIZATION**, request entitlement truth for the packet’s **five default WRDS rows**:

| Dataset ID | Exact `library.table` | V2-D0.1 status target | PEAD_V2_001 starter? |
|---|---:|---:|---:|
| `crsp_daily_stock_file` | `crsp.dsf` | Request entitlement truth | **Required** |
| `crsp_stocknames` | `crsp.stocknames` | Request entitlement truth | **Required** |
| `crsp_ccm_linktable` | `crsp.ccmxpf_linktable` | Request entitlement truth | **Required** for Compustat-to-CRSP linking |
| `compustat_fundamentals_quarterly` | `comp.fundq` | Request entitlement truth | **Required** for Compustat-rdq PEAD |
| `ibes_detail_eps_us` | `ibes.det_epsus` | Request entitlement truth for future analyst-surprise variants | **Not required** for the Compustat starter |

Rows outside those five should remain:

```text
not_requested
```

That means no `crsp.msf`, no `comp.funda`, no `ibes.id`, no `ibes.idsum`, no I/B/E/S summary tables, no TAQ, no OptionMetrics, no Zacks, no FactSet, no Orbis/BvD, and no substitute link tables unless a later matrix amendment explicitly adds them.

The packet itself keeps V2-D0 offline: permission matrix only, no provider access, no snapshot generation, no data output, and no V1 canonical writes. An entry may be marked `approved` only with an explicit `approval_ref`.

## 2. Status handling

Use two separate scopes so the decision does not blur:

```text
V2-D0.1 entitlement-truth scope:
- all five default rows are requested
- status becomes pending once the request is sent
- status becomes approved only with table-specific approval_ref

PEAD_V2_001 starter scope:
- only the Compustat PEAD rows are required
- ibes.det_epsus is not_requested
```

So for I/B/E/S:

```text
ibes.det_epsus in V2-D0.1 = pending, if you request entitlement now
ibes.det_epsus in PEAD_V2_001 starter = not_requested
```

Do **not** mark `ibes.det_epsus` as `unknown` inside the PEAD starter if the starter deliberately excludes I/B/E/S. `unknown` means “we do not know entitlement truth.” `not_requested` means “outside this scope by design.”

## 3. Non-secret evidence that proves entitlement

Acceptable evidence is any stable, dated, attributable record that proves **account authority + vendor/product entitlement + exact table scope + allowed use** without exposing secrets.

| Evidence format | Acceptable as entitlement evidence? | Notes |
|---|---:|---|
| Librarian / data-services ticket | **Yes** | Best operational evidence if resolved or explicitly approved. |
| WRDS Support / WRDS Rep email | **Yes** | Use ticket ID, message ID, or hashed archive reference as `approval_ref`. |
| Data-librarian note | **Yes** | Good if it names subscriber, account/role, product, tables, use constraints, and dates. |
| Redacted license memo / subscription memo | **Yes** | Strongest license evidence, but may still need account/scope approval. |
| Signed internal note | **Yes, conditionally** | Only if signed by PI, license owner, data librarian, WRDS admin, or delegated authority. Self-attestation is not enough. |
| WRDS account page screenshot | **Partial** | Can support account status or product visibility, but usually not enough alone for license/table entitlement. Redact cookies, session IDs, usernames if unnecessary, MFA prompts, and credentials. |
| Successful login, old query output, library list, row count, raw SQL log | **No** | These show access/activity, not permission. |

The evidence must not include a WRDS password, MFA code, `.pgpass`, connection URI, credential file, session cookie, unredacted license text, raw provider data, row samples, or query output. WRDS terms state that credentials must not be shared, users must use approved access methods, scripted website login/query automation is prohibited, and attempts to access non-subscribed data are prohibited. 

## 4. Required content inside the evidence

Each `approval_ref` or evidence bundle should contain, at minimum:

```json
{
  "approval_ref": "WRDSAUTH-20260602-V2D01-001",
  "issuer_role": "institutional data librarian / WRDS Rep / license owner / PI",
  "subscriber_institution": "<institution>",
  "authorized_account_or_role": "<named WRDS-authorized user or approved role>",
  "approved_access_method": "WRDS Cloud / SSH / remote Python-PostgreSQL / other approved method",
  "permitted_use": "read_only_permission_probe_only_no_data_output",
  "approved_rows": [
    "crsp.dsf",
    "crsp.stocknames",
    "crsp.ccmxpf_linktable",
    "comp.fundq",
    "ibes.det_epsus"
  ],
  "research_date_window": "YYYY-MM-DD through YYYY-MM-DD",
  "probe_as_of_utc": "2026-06-02T00:00:00Z",
  "constraints": [
    "no credential sharing",
    "no row/sample export",
    "no snapshot generation",
    "no committed WRDS output",
    "no V1 canonical/data/processed/runtime writes",
    "respect vendor redistribution and storage limits"
  ]
}
```

A license memo alone can prove institutional subscription, but it may not prove that this specific account, role, or probe is authorized. The cleanest structure is an internal evidence-bundle ID that points to a librarian ticket, WRDS email, and redacted license memo.

## 5. Entitlement proof by row

| `library.table` | Entitlement evidence needed |
|---|---|
| `crsp.dsf` | CRSP stock/security data entitlement for the subscriber/account. WRDS lists CRSP as a WRDS data-vendor product family.  |
| `crsp.stocknames` | Same CRSP entitlement, explicitly covering identifier/name-history support or the exact table. |
| `crsp.ccmxpf_linktable` | Explicit CCM / CRSP-Compustat Merged entitlement or exact-table approval. Do not infer this from generic CRSP + generic Compustat access; WRDS describes CCM as an additional CRSP product subscription for linking CRSP and Compustat.  |
| `comp.fundq` | S&P Global Market Intelligence / Compustat North America quarterly fundamentals entitlement. WRDS lists Compustat North America under S&P Global Market Intelligence data.  |
| `ibes.det_epsus` | LSEG / I/B/E/S detail EPS / earnings estimates entitlement. WRDS lists I/B/E/S under LSEG data.  |

## 6. Can PEAD start with fewer than CRSP + Compustat + I/B/E/S + CCM?

**Yes, PEAD can start without I/B/E/S.**

The recommended **PEAD_V2_001 starter** is a **Compustat-rdq PEAD** path:

```text
Required:
- crsp.dsf
- crsp.stocknames
- crsp.ccmxpf_linktable
- comp.fundq

Not requested for starter:
- ibes.det_epsus
```

That is fewer than the full CRSP + Compustat + I/B/E/S + CCM universe because it excludes I/B/E/S.

But for a real WRDS-backed Compustat PEAD with post-announcement return drift, I would **not** go smaller than:

```text
crsp.dsf
crsp.stocknames
crsp.ccmxpf_linktable
comp.fundq
```

Reason: `comp.fundq` gives the quarterly event/fundamental surface, `crsp.dsf` gives daily post-event returns, `crsp.stocknames` supports historical identifier audit, and `crsp.ccmxpf_linktable` links Compustat `gvkey` to CRSP `permno`.

So the final decision should be:

```text
V2-D0.1 requests entitlement truth for all five default rows.

PEAD_V2_001 starts with the smaller Compustat PEAD set:
- crsp.dsf
- crsp.stocknames
- crsp.ccmxpf_linktable
- comp.fundq

For PEAD_V2_001 starter:
- ibes.det_epsus = not_requested

For V2-D0.1 entitlement truth:
- ibes.det_epsus = pending once requested
- ibes.det_epsus = approved only with exact table-level approval_ref
```

用户:
Should V2-D0.1 request all five rows now, or only the four-row Compustat PEAD starter first? This affects I/B/E/S status: pending vs not_requested.
