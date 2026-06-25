### Research Lane Evidence Value

AI助手:


AI助手:


用户:
Quant Research Expert

Needs a separate research packet, not this zip alone.
Real question: “After WRDS/PIT/provenance is authorized, which research lane has the highest evidence value first: PEAD variants, corporate actions/capital return, meta-labeling, or Orbis/BvD network edge?”
用户:

AI助手:


AI助手:


AI助手:


AI助手:
It looks like my environment currently has too many active sessions to process the ZIP extraction. We can still address your main question without opening the file: you asked which research lane has the **highest evidence value first** after WRDS/PIT/provenance is authorized. Let’s break it down carefully.  

The options you listed are:

1. **PEAD variants** – Post-Earnings Announcement Drift research is strong in empirical finance, with clear, replicable alpha signals, especially in large-cap markets. Evidence value is high, especially for short-horizon earnings strategies.  
2. **Corporate actions / capital return** – Studying buybacks, dividends, spin-offs has high signal-to-noise ratios historically; evidence is well documented, especially for event-driven returns.  
3. **Meta-labeling** – This is a newer machine learning layer (labeling events for predictive models). The evidence is promising but often less robust than fundamental or well-documented financial event studies, because it depends on model quality and overfitting control.  
4. **Orbis/BvD network edge** – Using corporate ownership networks from Orbis/BvD for predictive signals is cutting-edge. Evidence is emerging but less standardized; it’s valuable but not as “first-line” as PEAD or traditional corporate actions.  

**Ordering by practical evidence value (after WRDS/PIT provenance is authorized):**

**1. PEAD variants** – historically most replicable, high alpha evidence  
**2. Corporate actions / capital return** – strong event-study-based evidence  
**3. Meta-labeling** – promising, but model-dependent  
**4. Orbis/BvD network edge** – innovative but still exploratory  

If you want, I can also prepare a **separate research packet outline** showing how each lane’s evidence can be documented, citing WRDS/PIT sources, which seems aligned with your request for a separate packet beyond the ZIP you uploaded.  

Do you want me to do that next?

用户:

用户:
What is the smallest PEAD_V2_001 hypothesis worth testing first?
Which PEAD features are allowed in the first packet, and which are too broad for first-lane work?
What kill rule would make PEAD lose first-lane priority to corporate actions or meta-labeling?
AI助手:


AI助手:


AI助手:
Let’s break this down carefully. You’re asking about **PEAD (Post-Earnings Announcement Drift) research prioritization** in a multi-lane quant research workflow, relative to other research lanes like corporate actions, meta-labeling, and Orbis/BvD network edges. Here's a structured answer:

---

### 1. **Smallest PEAD_V2_001 hypothesis worth testing first**

The “smallest” hypothesis in PEAD_V2_001 should be **narrow, concrete, and directly measurable**, ideally with:

- **Single-event focus:** One earnings surprise metric (e.g., earnings per share beat/fail for one quarter).
- **Simple cross-section:** Limit to a single market (e.g., US equities only) and avoid multi-factor overlays initially.
- **Clear dependent variable:** Daily or intraday return 1–5 days post-announcement.
- **Minimal confounders:** Ignore size, industry, or other controls in first pass.

**Example first hypothesis:**
> “Stocks in the S&P 500 that beat earnings expectations by >5% show a positive cumulative return over the 3 trading days after the announcement.”

This is testable quickly with WRDS/PIT data and fits the “first-lane” idea: **high signal, low operational overhead**.

---

### 2. **PEAD features allowed in the first packet vs too broad**

**Allowed in first-lane (high evidence, low complexity):**

- Standardized **EPS surprise** or **earnings-to-price ratio change**.
- **Basic post-announcement returns** (1–5 days).
- Simple **volatility or volume adjustments** for noise.
- Single-region, single-market, single-quarter slices.

**Too broad / for later lanes:**

- Multi-factor adjustments (size, momentum, value, liquidity simultaneously).
- Aggregated meta-signals (e.g., combination of multiple PEAD variants across quarters or sectors).
- Network or cross-market spillovers.
- Non-standardized event types (e.g., multi-event corporate events mixed with earnings).
- Any feature requiring **Orbis/BvD network edges** integration.

> **Rule of thumb:** First-lane PEAD features are atomic, measurable, and low-dimensional.

---

### 3. **Kill rule that deprioritizes PEAD in favor of corporate actions or meta-labeling**

PEAD should lose first-lane priority if **its expected information gain or evidence value is low relative operational cost**. A concrete “kill rule”:

1. **Data availability trigger:**
   - If WRDS/PIT earnings data is **incomplete**, missing >20% of the target universe in the quarter, drop PEAD first-lane.
2. **Signal-to-noise threshold:**
   - If preliminary intraday/backtest shows **Sharpe < 0.5** or **t-stat < 1.5**, PEAD is deprioritized.
3. **Comparative evidence value:**
   - If corporate actions or meta-labeling offer:
     - Stronger causal identification (e.g., forced share repurchases, dividends with clear timing).
     - Fewer missing observations.
   - Then move those to first-lane.

> Operationally: a simple **priority score** can be computed:

\[
\text{Priority} = \frac{\text{Expected t-stat or IC}}{\text{Data latency × complexity}}
\]

Whichever lane scores highest takes first-lane execution.

---

**Summary Table:**

| PEAD Aspect                  | First-lane Allowed? | Notes |
|-------------------------------|------------------|-------|
| Single EPS surprise measure    | ✅ Yes           | Minimal hypothesis |
| Multi-factor signal            | ❌ No            | Too broad |
| Cross-market/network features  | ❌ No            | Later lanes |
| 1–3 day post-announcement return| ✅ Yes           | Directly measurable |
| Aggregated meta-signals        | ❌ No            | Too high-dim |

**Kill rule triggers:**
- Incomplete WRDS/PIT data
- Low preliminary t-stat / IC
- Comparative advantage of corporate actions/meta-labeling

---

If you want, I can **draft a full “first-lane PEAD packet”** listing exactly which columns/features from your uploaded zip are safe to use, which to exclude, and provide the **exact first-lane hypothesis ready for testing**.  

Do you want me to do that next?

用户:

AI助手:
##Verdict:ADVISORY_PASS

**Recommendedfirstresearchlane:PEADvariants.**

**One-linereason:**PEADhasthehighestfirstevidencevaluebecauseitisthecleanestfalsifiableeventlane,alreadyhasboundedlocalPhase56/G7readinessintheuploadedpacket,andmapsmostdirectlytoWRDS/PITcontrols:CRSP/Compustatlinking,earningsreport-datehandling,andI/B/E/S-stylesurpriseconstruction.WRDSdescribesCCMaslinkingCRSPmarket/corporate-actiondatawithCompustatfundamentals;WRDSI/B/E/Scoversanalystforecasts/earningsestimates;andtheCRSP/Compustatguidelists**RDQ**as“ReportDateofQuarterlyEarnings,”whichmakesPEADthebestfirsttestofPITeventtiming.

**RankorderafterWRDS/PIT/provenanceauthority:**

1.**PEADvariants**—first.
2.**Corporateactions/capitalreturn**—second.
3.**Meta-labeling/edgesurvival**—third.
4.**Orbis/BvDnetworkedge**—fourth/later.

Corporateactionshasrealevidencepotential,especiallybecauseCRSPexplicitlycoverscorporateactionsandpermanentidentifiers,andthepayout/repurchaseliteratureisstrong;buttheuploadedpacket’sPhase57contextsaysthelocalfirstpacketwasevidence-only/no-promotionandbelowC3,soitshouldfollowPEADunlessPEADpermissionsareunavailable.

Meta-labelingshouldnotbefirstbecauseitisafilteronabasesignal,notabaseevidencelane.Thelabeling/meta-labelingstackdependsoneventlabels,sidepredictions,andforwardoutcomes,soitshouldonlystartafterPEADorcorporate-actionslabelssurviveOOSandleakagechecks.

Orbis/BvDmaybethemostdifferentiatedlong-runedge,butitistheworstfirstlanebecausethefirstresearchpacketwouldmostlytestlicensescope,entityresolution,ownership-historydrift,andpublic-privatelinkagequality.Moody’sdescribesOrbisascovering625M+entities,blending170+sources,andprovidingextensiveownershiplinks/hierarchies,whichisvaluablebuthigh-burdenforfirstevidence.

Icreatedthestandaloneresearchpackethere:

[DownloadtheDOCXresearchpacket](sandbox:/mnt/data/quant_research_lane_decision_packet_20260602.docx)
[DownloadtheMarkdownresearchpacket](sandbox:/mnt/data/quant_research_lane_decision_packet_20260602.md)

AI助手:
##1.Verdict:**ADVISORY_PASS**

**PEADshouldkeepfirst-lanepriority,butonlyas`PEAD_V2_001`,notasthebroadPEADVariantFactory.**Thefirstpacketshouldbeanarrow,preregistered,research-onlytestofearnings-surprisedriftusingthealready-defined`PEAD_DAILY_V0`boundaryfromthepacket.

Separatepacketfile:[PEAD_V2_001_first_lane_research_packet_20260602.md](sandbox:/mnt/data/PEAD_V2_001_first_lane_research_packet_20260602.md)

---

##2.RecommendedFirstResearchLane:**PEAD**

###Smallest`PEAD_V2_001`hypothesisworthtestingfirst

>IntheauthorizedTier-0canonicalWRDSU.S.equitiesuniverse,aPIT-safeanalystearnings-surprisebucketformedstrictlybeforethetradableentrytimepredictssame-directionpost-announcementdriftoverashortfixedpost-eventwindow,afterliquidityandcostcontrols.

**Primarycell:**

|Field|`PEAD_V2_001`setting|
|---|---|
|Universe|U.S.commonequitieswithvalidPITCRSP/Compustat/I/B/E/Slinkage|
|Event|EarningsannouncementflagfromapprovedPITrelease-datepolicy|
|Surprise|I/B/E/SactualEPSminuslatesteligibleanalystconsensusforecast,convertedtopredeclaredsurprisebuckets|
|Construction|Top-surprisebucketvsbottom-surprisebucket;equal-weight;research-onlyspreadplusleg-levelreporting|
|Entry|`event_window_lag=+1`tradingday|
|Hold|`holding_days=5`tradingdays|
|Liquidity|Primaryfloor:`ADVUSD20m`|
|Cost|Preapprovedfamily/defaultcostmodel;nottuned|
|Evidence|Eventstudy+same-engineportfolioevidence+OOS/walk-forward+bootstrap/permutation+monotonicity|

ThisisthesmallestusefultestbecausePEADisalreadyawell-documentedphenomenon,butfirst-laneevidenceshouldtestonlywhetherthedriftsurvivesyourPIT,cost,liquidity,andprovenancegates.BernardandThomasdocumentpredictablefutureearnings-announcementreactionsfromcurrentearningsinformation,andLivnat/MendenhallfindstrongerdriftwhensurpriseismeasuredusinganalystforecastsandI/B/E/Sactualsratherthanonlytime-seriesCompustatearnings.

---

##3.One-LineReason

**PEADhasthebestfirstevidencevaluebecausetherepoalreadyhasaboundedPhase56PEADhistoryandadefined`PEAD_DAILY_V0`familywithafinite24-cellbudget;corporateactionshaspriorevidencebutunderperformed,meta-labelingneedsbaselabels,andOrbis/BvDhastoomuchaccess/entity/PIT-linkingrisk.**

---

##4.EvidenceRequiredBeforeStart

BeforeanyPEADexecution,require:

1.**WRDSpermissionproof**fortheexactrowsneeded:CRSPdailystockfile,CRSPstocknames,CRSP/Compustatlinktable,Compustatquarterlyfundamentals,andI/B/E/SdetailEPSUS,oranexplicitlyapprovednarrowersubstitute.

2.**PITsnapshotmanifest**withrowcounts,hashes,schemaIDs,extractiontimestamp,approvalrefs,source-qualitymetadata,androllback/removalpolicy.

3.**Announcement-timepolicy**thatmapsearningseventstotradabledateswithoutsame-dayleakage.Conservativefirstpacket:use`+1`trading-dayentry.

4.**Identifier-linkpolicy**forPERMNO/GVKEY/I/B/E/Slinkage,link-datevalidity,ticker/CUSIPdrift,delistings,andsurvivorship-safeuniverseconstruction.

5.**Onepredeclaredprimarycell**plusonlytheexistingfiniterobustnessgrid:
-`holding_days={1,3,5,10}`
-`liquidity_floor={adv_usd_5m,adv_usd_20m,adv_usd_50m}`
-`event_window_lag={1,2}`
-Maxplannedcells:`24`

###AllowedPEADfeaturesinPacket1

Theseareallowedbecausetheymatchthepacket’s`PEAD_DAILY_V0`familydefinition:

|Allowedfeature|Useinfirstpacket|
|---|---|
|`earnings_event_flag`|Defineseventeligibilityonly|
|`earnings_surprise_bucket`|Definestop/bottomorbucketmonotonicity|
|`liquidity_filter`|Controlstradability/costsensitivity|
|`price_return_window`|Definesevent-windowevidenceandholding-windowreturn|

Alloweddiagnostics,**notsignalfeatures**:eventcounts,bucketcounts,row-count/hashchecks,sector/sizeexposurereport,cost/turnoverattribution,event-datelagaudit,andleg-levelCARtables.

###Toobroadforfirst-lanePEAD

Do**not**includethesein`PEAD_V2_001`:

-analystrevisionsasaseparatefeature
-announcementgapreturn
-volumeshock
-pre-eventrunup
-short-interestpressure
-accrualquality
-capital-cyclescore
-revenuesurprise
-estimatedispersion
-options,borrow,skew,crowding
-sector/industry-neutralconstruction
-broaduniverse-choiceknobs
-dynamicrebalancecadence
-stop-loss/take-profitoverlays
-MLormeta-labeling
-Orbis/BvD/private-networkedges
-anypost-resultbest-cellselection,ranking,scoring,dashboardsurfacing,orpromotionlanguage

Thefirstpacketshouldansweronequestion:**doesaclean,liquid,PIT-safeearnings-surprisebucketdriftatall?**

---

##5.KillCriteria

PEADlosesfirst-lanepriorityif**any**ofthesehardgatesfail.

###A.Datakill

KillPEADfirstifthereisnoauditablePITevent/surprisesnapshot,novalidCRSP/Compustat/I/B/E/Slinkage,unresolvedannouncement-timeleakage,missingdelistinghandling,ornoapprovedpermissionrowfortherequireddata.

**Priorityhandoff:**movetoCorporateActionsifofficialcapital-return/corporate-actiondataisauthorizedandcleanerthanPEADsurprisedata.

###B.Primary-effectkill

KillPEADifthepredeclaredprimarycell:

`+1lag/5-dayhold/ADVUSD20m/top-vs-bottomsurprisebucket`

hasnon-positivenettop-minus-bottomdrift,non-monotonebucketreturns,orunstablesigninOOS/walk-forwardsplits.

**Priorityhandoff:**movetoCorporateActionsifthePEADgrosseffectisabsent;movetoMeta-labelingonlyifPEADhasagrossedgebutsurvivaldependsonobservablecost/regime/liquiditystates.

###C.Liquidity/costkill

KillPEADiftheeffectappearsonlyinilliquidnamesbelowtheADVUSD20mprimaryfloor,flipsnegativeundertheapprovedcostmodel,ordependsmateriallyonnamesthatcannotsurviverealisticslippage/impactassumptions.ThisgateshouldbestrictbecauseChordiaetal.findPEADconcentratedinhighlyilliquidstocksandestimatethattransactioncostscanaccountformostpaperlong-shortprofits.

###D.Robustnesskill

KillPEADifbootstrap/permutation/regimetestsdonotsupporttheprimary-celldirection,orifmultiple-testingcorrectionleavesonlypost-hoc/best-cellevidence.

###E.Scopekill

KillPEADiftheonlywaytomakeitworkistoaddnon-allowlistedfeatures,useambiguoussame-dayeventtiming,expandbeyondthe24-cellbudget,orconvertoutputsintoranking/scoring/promotion.

---

##6.DeferredLanesWithReason

**CorporateActions/CapitalReturnEdgeLab—second.**IthaspriorPhase57evidence,butthatpacketunderperformedthelockedC3baselineandusedaproxy-stylecorporate-actionyield.ItbecomesfirstonlyifPEADiskilledbydata,primaryeffect,orliquidity/costgates.

**Meta-labeling/EdgeSurvivalModel—third.**Itshouldnotleadbecauseitrequiresgovernedbase-sleevelabels.ItbecomesvaluableonlyafterPEADorCorporateActionsproducesenoughlabeledsuccesses/failurestomodelsurvivalundercost,regime,liquidity,orcrowdingpressure.

**Orbis/BvDNetworkEdge—hold.**Potentiallydifferentiated,buttoomuchlicense/access,entity-resolution,PITdrift,andpublic/privateidentifier-linkingriskforfirst-lanework.

---

##7.Out-of-BoundaryConfirmed

Noimplementation.NoWRDS/providercalls.Nosnapshotgeneration.No`data/processed`writes.Nocandidateranking/scoring.Nodashboardsurfacing.Nopromotionpacket.NoSafeBoot/BootReadyclaim.Noalerts,broker/orderpaths,orlive-tradingsemantics.

---

##8.Confidence:**7.5/10**

Thesequencingisstrongbecause`PEAD_DAILY_V0`isalreadyboundedandPEADhasexternalempiricalgrounding.ConfidenceiscappedbecauseactualWRDSpermissions,PITeventcoverage,andI/B/E/Slinkagequalityarestillunknown.

---

##9.NextAction

Publishaone-page`PEAD_V2_001`approvalpacketwiththeprimarycell,four-featureallowlist,24-cellmaximumrobustnessgrid,snapshot-manifestrequirements,andthekillrulesabove.Do**not**approvethebroaderPEADVariantFactoryuntilthisminimalPEADpacketsurvivesfirst-laneevidencegates.

用户:
Is first lane officially PEAD_V2_001, not “PEAD Variant Factory”?
Is the first PEAD hypothesis Compustat-rdq PEAD or I/B/E/S analyst-surprise PEAD?
What kill rule would move priority from PEAD to corporate actions?
用户:

AI助手:
## 1. Is first lane officially `PEAD_V2_001`, not “PEAD Variant Factory”?

**Yes.**

The first lane should be recorded as:

> **`PEAD_V2_001` — Minimal PIT-safe analyst-surprise PEAD test**

Not:

> **PEAD Variant Factory**

“PEAD Variant Factory” is the broader roadmap container. It includes many axes: announcement gap, revisions, volume shock, pre-event runup, accruals, short interest, neutralization, universe knobs, rebalance choices, and so on. That is **too broad for first-lane evidence**.

So the correct governance framing is:

| Item | Status |
|---|---|
| `PEAD_V2_001` | **First-lane research packet** |
| `PEAD_DAILY_V0` | Existing bounded family / feature-budget shell |
| PEAD Variant Factory | **Deferred until `PEAD_V2_001` survives** |

This is still **advisory priority**, not execution approval. WRDS/PIT/provenance authorization must come first.

---

## 2. Is the first PEAD hypothesis Compustat-RDQ PEAD or I/B/E/S analyst-surprise PEAD?

**Primary answer: I/B/E/S analyst-surprise PEAD.**

The first hypothesis should **not** be framed as “Compustat-RDQ PEAD.” It should be:

> **I/B/E/S analyst-surprise PEAD, using a PIT-safe earnings event-date policy.**

The first-packet surprise definition should be:

> **I/B/E/S EPS actual − latest eligible analyst consensus forecast**, bucketed into predeclared surprise buckets before the tradable entry time.

Compustat `rdq` is still important, but its role is mainly:

1. **PIT release-date / announcement-date validation**
2. **Compustat quarterly fundamentals linkage**
3. **Cross-checking event timing**
4. **Supporting CRSP/Compustat/I/B/E/S issuer joins**

So the clean distinction is:

| Component | First packet choice |
|---|---|
| Event timing | PIT-safe earnings release policy; Compustat `rdq` may be part of validation |
| Surprise signal | **I/B/E/S analyst surprise** |
| First tradable entry | `+1` trading day after event eligibility |
| First hypothesis name | `PEAD_V2_001_ANALYST_SURPRISE` or equivalent |

A pure **Compustat-RDQ PEAD** test would be a fallback or separate packet, not the highest-value first hypothesis. It usually tests earnings drift using Compustat-based earnings data and report dates, but it does not capture the clean analyst-expectations surprise that makes the first PEAD test sharper.

So the packet should say:

> **Primary PEAD_V2_001 hypothesis: I/B/E/S analyst-surprise PEAD. Compustat `rdq` is event-timing/provenance support, not the primary surprise definition.**

If I/B/E/S detail EPS / estimate data is not authorized, then PEAD should not quietly mutate into Compustat-RDQ PEAD. That would require a new narrowed packet, likely `PEAD_V2_001B_COMPSTAT_RDQ_FALLBACK`.

---

## 3. What kill rule would move priority from PEAD to corporate actions?

Use this as the hard handoff rule:

> **Move priority from PEAD to Corporate Actions if `PEAD_V2_001` cannot produce a PIT-safe, cost-surviving, liquid, OOS-stable analyst-surprise drift in the predeclared primary cell, while corporate-action/capital-return data is authorized with a cleaner PIT event taxonomy.**

The specific kill rule should be:

### `PEAD_TO_CORP_ACTIONS_KILL_RULE`

PEAD loses first-lane priority to Corporate Actions if **any one** of these is true:

| Kill gate | Condition |
|---|---|
| **Data kill** | I/B/E/S analyst-surprise data, CRSP/Compustat/I/B/E/S linkage, Compustat `rdq`/announcement timing, delisting handling, or PIT snapshot provenance cannot be authorized/audited. |
| **Primary-effect kill** | The predeclared primary cell has **non-positive net top-minus-bottom drift** after costs. |
| **Monotonicity kill** | Surprise buckets are not directionally monotone: large positive surprises do not outperform neutral/negative surprises in the expected order. |
| **OOS stability kill** | The effect has unstable sign across OOS/walk-forward splits. |
| **Liquidity/cost kill** | The effect exists only below the `ADV USD 20m` primary liquidity floor or flips negative under the approved cost/slippage model. |
| **Scope kill** | PEAD only looks viable after adding disallowed first-packet features such as revisions, gap return, volume shock, short interest, accruals, quality score, ML/meta-labeling, neutralization, or post-hoc best-cell selection. |

The first primary cell should be:

```text
signal: I/B/E/S analyst-surprise bucket
entry_lag: +1 trading day
hold: 5 trading days
liquidity_floor: ADV USD 20m
construction: top-surprise bucket vs bottom-surprise bucket
cost_model: preapproved default, not tuned
```

Corporate Actions becomes first only if its own data state is cleaner:

```text
corporate_actions_priority = true
iff
  PEAD hard gate fails
  AND official PIT corporate-action / capital-return taxonomy is authorized
  AND event dates, payout/issuance fields, share-count changes, and CRSP adjustment logic are auditable
```

Important distinction:

- If PEAD has **no clean gross edge**, move to **Corporate Actions**.
- If PEAD has a **gross edge but only survives in certain cost/liquidity/regime states**, then move toward **Meta-labeling**, not Corporate Actions.
- If PEAD data is blocked and Corporate Actions data is also blocked, hold rather than widen.

## Final decision language

Use this wording:

> **First lane is `PEAD_V2_001`, not PEAD Variant Factory. The first PEAD hypothesis is I/B/E/S analyst-surprise PEAD, with Compustat `rdq` used for PIT event-date/provenance support. Kill PEAD and move priority to Corporate Actions if the predeclared `+1` lag / 5-day hold / ADV USD 20m analyst-surprise spread fails data authorization, net effect, monotonicity, OOS stability, or liquidity/cost gates, provided corporate-action event data is authorized and cleaner.**

用户:
What is the smallest PEAD_V2_001 hypothesis?
Which PEAD features are allowed first?
What kill rule would demote PEAD?
AI助手:


AI助手:


AI助手:
Here’s a concise summary for first-lane PEAD research based on `PEAD_V2_001`:

---

## 1. Smallest `PEAD_V2_001` Hypothesis

**Definition:**  

> In the authorized WRDS PIT-safe universe of U.S. equities, the top-vs-bottom I/B/E/S analyst-surprise bucket predicts post-announcement price drift over a fixed short post-event window, conditional on liquidity and cost controls.

**Primary cell details:**

| Field | Setting |
|---|---|
| Universe | PIT-safe CRSP/Compustat/I/B/E/S U.S. equities |
| Event | Earnings announcement (PIT-safe) |
| Signal | I/B/E/S EPS actual − eligible consensus |
| Entry | `+1` trading day after announcement |
| Hold | 5 trading days |
| Liquidity | ADV ≥ USD 20m |
| Cost | Preapproved default model |
| Evidence | Event-study CAR + OOS stability + monotone bucket returns |

This is the minimal first-lane hypothesis: it tests **whether a clean analyst-surprise drift exists** without extra features or ML/meta-labeling.

---

## 2. Allowed PEAD Features in First Packet

| Feature | Usage |
|---|---|
| `earnings_event_flag` | Defines eligible event rows |
| `earnings_surprise_bucket` | Top vs bottom or bucket monotonicity |
| `liquidity_filter` | ADV floor / tradability control |
| `price_return_window` | Defines post-event drift / CAR calculation |

**Allowed diagnostics** (report only):

- Event counts and bucket counts
- Row-count and PIT hash checks
- Sector/size exposure report
- Leg-level CAR tables
- Predeclared robustness grid (24 cells max)

**Not allowed in first-lane packet:**

- Analyst revisions or volume shock
- Pre-event runup or accrual metrics
- Short interest, options, skew, crowding features
- Sector/industry neutralization or universe expansion
- Dynamic rebalance or stop-loss/take-profit overlays
- ML/meta-labeling, Orbis/BvD network features
- Post-hoc best-cell selection or dashboard promotion

---

## 3. Kill Rule to Demote PEAD

PEAD loses first-lane priority to **Corporate Actions / Capital Return** if **any of the following hard gates fail**:

| Kill Gate | Condition |
|---|---|
| **Data Kill** | PIT-safe analyst-surprise, CRSP/Compustat/I/B/E/S linkage, or announcement timing not auditable/authorized |
| **Primary-effect Kill** | Predeclared primary cell has **non-positive net top-minus-bottom drift** |
| **Monotonicity Kill** | Surprise buckets do not show expected directional ordering |
| **OOS Stability Kill** | Effect is not stable in walk-forward/out-of-sample tests |
| **Liquidity/Cost Kill** | Drift exists only below ADV USD 20m or flips under cost/slippage model |
| **Scope Kill** | Effect requires disallowed features (gap, revisions, ML/meta-labeling, etc.) |

**Priority handoff:** Corporate Actions becomes first only if the data and event definitions for payouts, repurchases, or share changes are auditable and PIT-safe.

---

This framework ensures **PEAD_V2_001** is minimal, fully auditable, and clearly scoped, while giving a defined path to demotion if it fails core evidence or data gates.  

I can also draft a **one-page visual “first-lane PEAD packet”** showing primary cell, allowed features, and kill rules for rapid review. Do you want me to create that?

用户:
What is the smallest PEAD_V2_001 hypothesis?
Which PEAD features are allowed first?
What kill rule would demote PEAD?
AI助手:


AI助手:


AI助手:
Here’s the distilled first-lane guidance for **PEAD_V2_001** based on the packets and governance rules:  

---

## 1. Smallest PEAD_V2_001 Hypothesis

The minimal first-lane test is:

> **I/B/E/S analyst-surprise PEAD** in a PIT-safe U.S. equities universe.

**Primary cell details:**

| Field | Setting |
|---|---|
| Universe | U.S. common equities with CRSP/Compustat/I/B/E/S linkage approved |
| Event | Earnings announcement from PIT snapshot (`rdq` validation optional) |
| Surprise | I/B/E/S EPS actual − latest eligible analyst consensus, bucketed |
| Entry | `+1` trading day after event |
| Hold | 5 trading days |
| Liquidity | ADV ≥ USD 20m |
| Cost | Default preapproved cost model |
| Evidence | Event-study CAR / post-event return, OOS split, bootstrap/permutation monotonicity |

This is the **smallest meaningful hypothesis**: it tests **clean, liquid, PIT-safe analyst-surprise drift** without adding extra features or universe expansions.

---

## 2. PEAD Features Allowed in First Packet

| Feature | Allowed? | Notes |
|---|---|---|
| `earnings_event_flag` | ✅ | Defines event eligibility |
| `earnings_surprise_bucket` | ✅ | Top vs bottom or monotone bucket |
| `liquidity_filter` | ✅ | Controls tradable universe |
| `price_return_window` | ✅ | Defines event-window evidence |
| Event counts / hash / row-count diagnostics | ✅ | Allowed for QC |
| Sector/size exposure, CAR table | ✅ | Allowed for reporting/diagnostics |

**Not allowed (too broad for first-lane):**

- Analyst revisions, announcement gap return, volume shock  
- Pre-event runup, short-interest, accruals  
- Revenue surprise, estimate dispersion  
- Meta-labeling, ML signals, neutralization  
- Post-hoc selection, dashboard surfacing, promotion language  
- Orbis/BvD network features  

> Only features that **support a clean PIT-safe analyst-surprise drift test** are allowed.

---

## 3. Kill Rule to Demote PEAD

PEAD loses first-lane priority if **any of these conditions occur**:

| Kill Gate | Condition |
|---|---|
| **Data kill** | I/B/E/S or linkage data unavailable or PIT snapshot unauthorized |
| **Primary-effect kill** | Primary cell top-minus-bottom spread is ≤ 0 after costs |
| **Monotonicity kill** | Surprise buckets are not directionally monotone |
| **OOS stability kill** | Effect is inconsistent across walk-forward splits |
| **Liquidity/cost kill** | Effect exists only in illiquid stocks or flips under cost model |
| **Scope kill** | PEAD requires non-allowlisted features or post-hoc tuning to survive |

**Action if killed:** Move first-lane priority to **Corporate Actions / Capital Return**, assuming those data are authorized and PIT-safe.  

---

✅ **Summary:**  

- **Smallest hypothesis:** PIT-safe I/B/E/S analyst-surprise PEAD, 5-day hold, +1 lag, ADV ≥ 20m.  
- **Allowed features:** event flag, surprise bucket, liquidity filter, price-return window, and QC diagnostics only.  
- **Kill rule:** Data unavailability, null/negative effect, monotonicity or OOS failure, liquidity/cost dependence, or feature-scope expansion → shift priority to Corporate Actions.  

---

I can also **draw a concise visual “first-lane PEAD decision tree”** showing allowed features, primary cell, and kill-rule gates if you want a one-page reference. Do you want me to do that?

用户:
What is the smallest PEAD_V2_001 hypothesis?
Which PEAD features are allowed first?
What kill rule would demote PEAD?
用户:

AI助手:
## Official first lane

**Yes: first lane is `PEAD_V2_001`, not “PEAD Variant Factory.”**

Use this label:

> **`PEAD_V2_001 — Minimal PIT-safe I/B/E/S analyst-surprise PEAD test`**

“PEAD Variant Factory” is deferred. It should not be used as the first-lane name because it invites too many knobs, features, and post-hoc variants.

---

## 1. Smallest `PEAD_V2_001` hypothesis

The smallest hypothesis worth testing is:

> **In the authorized PIT WRDS U.S. equities universe, a pre-event-safe I/B/E/S analyst EPS surprise bucket predicts same-direction post-earnings drift over a short fixed window, after liquidity and cost controls.**

Primary test cell:

| Field | First setting |
|---|---|
| Signal | **I/B/E/S analyst EPS surprise** |
| Surprise definition | Actual EPS − latest eligible consensus forecast |
| Event timing | PIT-safe earnings event policy; Compustat `rdq` allowed for validation/provenance |
| Entry | `+1` trading day after event |
| Hold | `5` trading days |
| Universe | U.S. common equities with valid CRSP / Compustat / I/B/E/S linkage |
| Liquidity floor | `ADV USD 20m` |
| Construction | Top surprise bucket vs bottom surprise bucket |
| Cost model | Preapproved default; not tuned |
| Required evidence | Net spread, leg-level returns, bucket monotonicity, OOS stability, bootstrap/permutation support |

The first hypothesis is **I/B/E/S analyst-surprise PEAD**, not pure **Compustat-RDQ PEAD**. Compustat `rdq` is allowed as event-date/provenance support, but it should not be the primary surprise definition.

---

## 2. PEAD features allowed first

Only these should be allowed as first-packet PEAD features:

| Feature | Role |
|---|---|
| `earnings_event_flag` | Defines event eligibility |
| `earnings_surprise_bucket` | Defines positive/negative surprise buckets |
| `liquidity_filter` | Enforces tradability and cost sanity |
| `price_return_window` | Measures post-event drift |

Allowed diagnostics, but **not signal features**:

| Diagnostic | Purpose |
|---|---|
| Event counts | Coverage sanity |
| Bucket counts | Balance and sparsity check |
| Row-count/hash checks | Provenance validation |
| Event-date lag audit | Leakage control |
| Sector/size exposure report | Interpretability only |
| Cost/turnover attribution | Tradability check |
| Leg-level CAR tables | Avoid hiding weak long/short legs |

Do **not** allow these in the first PEAD packet:

- analyst revisions
- announcement gap return
- volume shock
- pre-event runup
- short interest
- accrual quality
- revenue surprise
- estimate dispersion
- options features
- borrow/crowding features
- sector-neutral or industry-neutral construction
- dynamic holding period
- stop-loss / take-profit overlays
- ML/meta-labeling
- Orbis/BvD network features
- post-result best-cell selection
- broad universe tuning
- dashboard scoring or promotion logic

First packet should answer one narrow question:

> **Does a clean, liquid, PIT-safe I/B/E/S earnings-surprise bucket drift after earnings?**

---

## 3. Kill rule that would demote PEAD

Use this hard rule:

> **Demote PEAD if `PEAD_V2_001` cannot produce a PIT-safe, cost-surviving, liquid, OOS-stable analyst-surprise drift in the predeclared primary cell.**

Primary cell:

```text
signal: I/B/E/S analyst-surprise bucket
entry_lag: +1 trading day
hold: 5 trading days
liquidity_floor: ADV USD 20m
construction: top-surprise bucket vs bottom-surprise bucket
cost_model: preapproved default
```

### `PEAD_DEMOTION_RULE`

PEAD loses first-lane priority if **any** of these occur:

| Kill gate | Demotion condition |
|---|---|
| Data kill | I/B/E/S, CRSP/Compustat linkage, event timing, delisting handling, or PIT provenance cannot be audited. |
| Leakage kill | Announcement timing cannot be mapped safely to a tradable `+1` entry. |
| Primary-effect kill | Top-minus-bottom surprise spread is non-positive after costs in the primary cell. |
| Monotonicity kill | Surprise buckets do not rank in the expected direction. |
| OOS kill | Effect sign is unstable across walk-forward / OOS splits. |
| Liquidity/cost kill | Effect only exists below `ADV USD 20m` or flips negative under the approved cost model. |
| Scope kill | PEAD only works after adding disallowed features or choosing the best cell after seeing results. |

### Priority handoff

Move from PEAD to **Corporate Actions** when:

```text
PEAD hard gate fails
AND
official PIT corporate-action / capital-return data is authorized, cleaner, and auditable
```

Move from PEAD to **Meta-labeling** only when:

```text
PEAD has a gross edge
BUT
net survival depends on liquidity, cost, regime, or crowding states
```

So the clean decision language is:

> **First lane is `PEAD_V2_001`. The smallest hypothesis is I/B/E/S analyst-surprise PEAD with `+1` entry, 5-day hold, ADV USD 20m floor, and top-vs-bottom surprise buckets. Allowed first features are only event flag, surprise bucket, liquidity filter, and return window. Demote PEAD if the primary cell fails PIT/provenance, net effect, monotonicity, OOS stability, liquidity/cost, or scope gates.**

AI助手:


AI助手:


AI助手:


AI助手:
Got it — you want a **separate research packet** focusing on evidence hierarchy across quantitative research lanes once WRDS/PIT/provenance is authorized, rather than working with the uploaded zip itself. Let’s unpack your core question carefully.

You asked:

> “After WRDS/PIT/provenance is authorized, which research lane has the highest evidence value first: PEAD variants, corporate actions/capital return, meta-labeling, or Orbis/BvD network edge?”

Here’s a careful, expert-level breakdown:

---

## 1. **Context: “Evidence value” in Quant Research**

Evidence value refers to the **strength, robustness, and reproducibility** of insights that a research lane can deliver. Factors include:

- **Data reliability:** availability, granularity, and provenance (WRDS/PIT/provenance authorization ensures clean, auditable data).
- **Signal-to-noise ratio:** how strong the predictive signal is relative to the background.
- **Cross-validation and out-of-sample performance:** robustness across periods, sectors, and geographies.
- **Actionability:** ability to translate into implementable trading strategies or risk models.

---

## 2. **Assessment of Each Research Lane**

| Research Lane | Strengths | Weaknesses | Evidence Value After Data Authorization |
|---------------|-----------|------------|----------------------------------------|
| **PEAD Variants (Post-Earnings Announcement Drift)** | Large, well-documented literature; strong historical effect; easy to backtest across WRDS data | Signal decays quickly with modern market efficiency; sensitive to microstructure noise | **High** — strong historical replication potential; first go-to for clean WRDS/PIT datasets |
| **Corporate Actions / Capital Return** | Highly actionable; low-noise signals (e.g., dividends, buybacks); clean event windows | Less frequent events; may require careful adjustments for confounders | **High to Medium** — strong actionable signals, fewer events reduce statistical power |
| **Meta-Labeling** | Machine-learning-driven, enhances alpha extraction by labeling strategy success/failure | Requires robust historical data and careful ML model validation; overfitting risk | **Medium** — dependent on data quality and ML rigor; benefits from PIT/provenance |
| **Orbis / BvD Network Edge** | Unique corporate network and ownership insights; potential for rare-event alpha | Sparse, less frequently updated data; complex modeling | **Medium to Low** — high uniqueness, but limited historical statistical validation |

---

## 3. **Evidence Value Hierarchy (Post-WRDS/PIT/Provenance)**

Based on robustness, reproducibility, and historical validation:

1. **PEAD Variants** — first, due to clean, abundant event data and strong historical replication.
2. **Corporate Actions / Capital Return** — second, highly actionable with moderate event frequency.
3. **Meta-Labeling** — third, conditional on ML model design and rigorous validation.
4. **Orbis/BvD Network Edge** — last, unique but sparse and less validated historically.

> **Key Insight:** WRDS/PIT/provenance authorization dramatically strengthens lanes 1 and 2 (PEAD, corporate actions) because these benefit most from high-quality event and financial data. ML/meta-labeling improves with provenance but cannot surpass signal-limited lanes in raw evidence value. Network edges remain niche, complementary rather than primary.

---

If you want, I can **prepare a separate, clean “research packet” PDF** that:

- Summarizes each lane
- Shows the hierarchy with reasoning
- Provides an **implementation checklist** for using WRDS/PIT/provenance for highest evidence gain

This would be exactly the separate packet you mentioned, not the zip contents.  

Do you want me to create that packet?

AI助手:


AI助手:


AI助手:


AI助手:
Got it — you’re asking for a research lane prioritization based on evidence value after access to WRDS/PIT/provenance is granted. Let’s break this down carefully.

We’re comparing four research lanes:

1. **PEAD variants** – Post-Earnings Announcement Drift strategies. Evidence here is generally strong, with decades of academic replication. The strength depends on earnings announcement quality, drift horizon, and market microstructure adjustments.

2. **Corporate actions / capital return** – This covers dividends, buybacks, spin-offs, M&A. Empirical evidence is robust, particularly for buyback announcements and spin-offs. High signal-to-noise ratio if event timing is clean.

3. **Meta-labeling** – A machine-learning overlay on existing signals to improve trade selection. Evidence value is conditional: depends on out-of-sample rigor, cross-validation, and backtest fidelity. Historically, meta-labeling adds incremental value rather than producing standalone alpha.

4. **Orbis/BvD network edge** – Network analysis of firm connections from BvD/Orbis data. Evidence is thinner in mainstream quant literature but can yield unique insights in systemic risk, cross-ownership, and network contagion modeling. High novelty, lower replication base.

**Evidence value ranking (highest to lowest) after WRDS/PIT/provenance authorization**:

1. **Corporate actions / capital return** – Highly robust, easy to verify, widely replicated.
2. **PEAD variants** – Strong academic backing, predictable drift, but more dependent on microstructure adjustments.
3. **Meta-labeling** – Adds value but incremental; dependent on proper ML validation.
4. **Orbis/BvD network edge** – Novel and specialized; less replicated, more exploratory.

So, in practical terms: if your goal is **first-to-evidence reliability**, corporate actions beat PEAD, meta-labeling is conditional, and network edges are exploratory.

If you want, I can make a **one-page visual packet ranking these lanes with pros/cons and evidence depth**, suitable for a research team handoff, independent of your uploaded zip. This would be separate from the zip contents. Do you want me to do that?

用户:

AI助手:
Separatepacketcreated:

[DownloadtheDOCXresearchpacket](sandbox:/mnt/data/expert4_quant_research_lane_priority_packet_20260602.docx)
[DownloadtheMarkdownresearchpacket](sandbox:/mnt/data/expert4_quant_research_lane_priority_packet_20260602.md)

##1.Verdict:ADVISORY_PASS

Advisorypassonly.Thefirstpost-WRDS/PIT/provenanceresearchlaneshouldbe**PEAD**,butnarrowedtoabounded**PEAD_V2_001**packetbeforeanybroad“variantfactory”behavior.

##2.RecommendedFirstResearchLane:PEAD

**PEADvariants**havethehighestfirstevidencevalue.WRDShasdirectbuildingblocksforthislanethroughI/B/E/Sestimates/forecastsandWRDSlinkingpathsbetweenI/B/E/S,CRSP,andCompustat;PEADitselfisawell-documentedanomalydescribingpost-announcementdriftinthedirectionofearningssurprise.

##3.One-LineReason

PEADisthefastestlanetoconvertauthorizedWRDS/PIT/provenanceintodecision-qualityevidencebecauseithasexistingrepohooks,frequentevents,clearWRDSdependencies,acredibleeconomicprior,andlowerentity-resolution/PIT-driftburdenthanOrbisormeta-labeling.

##4.EvidenceRequiredBeforeStart

Minimumstartevidence:approvedpermissionrowswith`approval_ref`;PITsnapshotmanifestwithrowcounts,hashes,schemaversions,as-of/maxresearchdates,androllbackrules;earningsannouncementtimestamppolicy;IBES/CRSP/Compustatdatedlinkpolicy;feature/executionlagpolicy;fixedbenchmarkset;declaredcosts;andanOOS/robustnessmatrix.Thepacketshouldalsocontrolmultipletestingandbacktestoverfitting,sincefactorresearchhasdocumenteddata-mining,publication-decay,andbacktest-overfitrisks.

##5.KillCriteria

KillPEAD_V2_001ifeventtimestampsorestimatevintagesarenotobservableatdecisiontime,PIT/linkprovenanceisincomplete,thesignalonlyworkswithsame-dayleakageorfull-historynormalization,itfailsthePITequal-weighteligible-eventbenchmarkaftercosts,performanceisconcentratedinoneera/sector/liquiditybucket,oroutputsdriftintoscoring/ranking/recommendations.

##6.DeferredLanesWithReason

**Corporateactions/capitalreturn**issecond.Theliteraturearoundpayout/netpayoutandshareissuanceiscredible,buttheuploadedPhase57packetreportsthefirstboundedcorporate-actionsproxyunderperformedC3onSharpe/CAGR,sothenextstepshouldbetaxonomyrepair,notfirst-laneexecution.

**Meta-labeling**isthird/supporting.Itshouldfilterorsurvival-labelvalidatedprimarysleeves,notleadasastandalonealphalane.

**Orbis/BvDnetworkedge**islater.Ithashighoptionality,butfirstevidencevalueislowerbecauseaccess,entityresolution,datedownership/networklinks,andcoverage-biascontrolsdominatethefirstpacket.Moody’sdescribesOrbisasalargeglobalcompany/ownershipdatasource,whileOECDworkdocumentsrepresentativenesslimitationsthatwouldneedtobecontrolledbeforeusingitasanalphasource.

##7.Out-of-BoundaryConfirmed

NoWRDS/provideraccess,credentials,probes,queries,snapshotgeneration,datawrites,candidatescoring/ranking,dashboardsurfacing,alerts,broker/orderpaths,SafeBoot,BootReady,livetrading,orpromotionisauthorizedbythisanswerorbythenewpacket.

##8.Confidence:8/10

Confidenceis8/10conditionalonWRDS/PIT/provenanceactuallybeingauthorized.ItreatedtheuploadedPhase56/57testevidenceaspacket-reportedcontext,notfreshlyreproducedevidence,becausetheisolatedextractiondidnotincludethefullrepoenvironment/dependenciesneededtore-runthosetests.

##9.Nextaction

Opena**PEAD_V2_001_BOUNDARY_PACKET**withtheapprovedsnapshotID,permissionrows,sourcetables/fields,timestamp/linkingpolicy,onebaselinePEADhypothesispluslimitedablations,benchmark/cost/OOSplan,andhardkillrules.Noprovidercallorimplementationshouldoccurfromthispacketalone.

