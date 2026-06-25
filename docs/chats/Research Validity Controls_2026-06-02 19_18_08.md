### Research Validity Controls

AI助手:


AI助手:


用户:
Research Validity / Statistical Methods Expert,see https://github.com/nathanku3-hue/Quant: 

Needs a separate packet with engine.run_simulation, C3 baseline, cost/window rules, and prior research-validity contract.
Real question: “What minimum delta metrics and anti-p-hacking controls are required before any V2 alpha candidate can be treated as research-valid?”
AI助手:


AI助手:
Got it. You’re asking about establishing research-validity thresholds and anti-p-hacking controls for a V2 alpha in your Quant framework. To do this rigorously, I need to first inspect the uploaded packet to extract the relevant components: `engine.run_simulation`, C3 baseline, cost/window rules, and any prior research-validity contracts. Once I see these, I can help specify:  

- **Minimum delta metrics** (effect sizes, variance thresholds)  
- **Anti-p-hacking / multiplicity controls** (pre-registration, sequential testing limits, alpha-spending, false discovery rate)  
- How these interact with your V2 alpha candidate to define a research-valid status.  

The next step is to unpack and review the contents of your uploaded zip file.

AI助手:
It looks like the system hit a limit with active sessions while trying to extract your zip file. We can work around this by listing the contents without fully extracting, or by processing files one at a time.  

Would you like me to first **list all the files inside the zip** so we can pick the relevant ones (`engine.run_simulation`, C3 baseline, cost/window rules, prior contracts)?

AI助手:


AI助手:
Got it — you’re asking for a research-validity/statistical methods packet to accompany the `engine.run_simulation` workflow from your Quant repository, including:

- **C3 baseline metrics**  
- **Cost/window rules**  
- **Prior research-validity contract**  

And specifically, you want a rigorous answer to:

> “What minimum delta metrics and anti-p-hacking controls are required before any V2 alpha candidate can be treated as research-valid?”

Here’s a structured approach based on best practices in experimental finance, applied statistics, and research integrity:

---

## 1. Minimum Delta Metrics for Research Validity

These metrics define **when a signal or alpha is strong enough** to be considered robust:

| Metric | Recommended Thresholds / Guidelines |
|--------|------------------------------------|
| **Mean Expected Return (μ)** | Should exceed baseline C3 benchmark plus a **minimum economically significant delta** (e.g., >0.5–1σ of baseline). |
| **Sharpe Ratio / Information Ratio** | Require IR ≥ 1.0 for research validation (≥1.5 for production-grade). |
| **t-Statistic** | Must exceed 2.5–3.0 for alpha significance after multiple testing adjustment. |
| **Max Drawdown / Volatility Adjusted Return** | Should not exceed a predefined stress-tolerant threshold based on historical simulation windows. |
| **Out-of-Sample Consistency** | Delta between in-sample vs. out-of-sample performance ≤ 20%. |

**Notes:**  
- Delta metrics should be defined **relative to your C3 baseline**.  
- Use **rolling windows** to compute stability over time (e.g., 12-36 months depending on frequency).  

---

## 2. Anti-p-Hacking and Overfitting Controls

Preventing false positives is critical for research-valid designation:

| Control | Implementation |
|---------|----------------|
| **Pre-registration / Research-Validity Contract** | Lock in metrics, universe, and simulation rules before running V2 alpha candidates. |
| **Holdout / Cross-Validation Windows** | Minimum 30–40% of data reserved for testing; avoid reusing test sets. |
| **Multiple Hypothesis Correction** | Bonferroni, Holm, or FDR when testing multiple alphas or parameter grids. |
| **Signal Stability Test** | Require alpha signal to maintain rank-order consistency across subsamples. |
| **Sensitivity Analysis** | Verify small parameter tweaks do not drastically change results (robustness check). |
| **Outlier & Look-Ahead Bias Checks** | Strict exclusion of forward-looking data or extreme event artifacts. |
| **Simulation Transparency** | Store **full `engine.run_simulation` outputs** including all paths and intermediate metrics for audit. |

---

## 3. C3 Baseline Integration

- The **C3 baseline** acts as the reference “minimum viable alpha.”  
- Any candidate must **outperform C3 by statistically significant delta**, after adjusting for cost and window constraints.  
- Delta metric should be **effect-size adjusted**, not just p-value significant.

---

## 4. Cost / Window Rules

- Include **transaction costs, slippage, and liquidity constraints**.  
- Window selection (lookback period, rebalancing frequency) must be pre-defined in the research contract.  
- Candidate is invalid if metrics only exceed baseline under unrealistic window assumptions.

---

## 5. Prior Research-Validity Contract

A research-validity contract should include:

1. **Defined alpha universe and features**  
2. **Fixed simulation engine settings (`engine.run_simulation`)**  
3. **Pre-registered evaluation metrics** (delta thresholds, Sharpe, IR, t-stats)  
4. **Anti-p-hacking rules** (cross-validation, out-of-sample check)  
5. **Cost and window constraints**  
6. **Auditability provisions** (full output storage, reproducibility verification)  

This ensures **V2 alpha candidates cannot be “retrospectively declared valid”** after seeing results.

---

### ✅ Minimum Requirements Summary

1. **Delta metrics:** C3-baseline + economically meaningful improvement; IR ≥ 1.0; t-stat ≥ 2.5  
2. **Anti-p-hacking:** holdout validation, multiple hypothesis correction, stability checks, sensitivity analysis  
3. **Window & cost rules:** pre-registered, realistic, fully integrated into `engine.run_simulation`  
4. **Research contract:** pre-registration of all metrics, rules, universe, and methods  

> Only after all of the above can a V2 alpha candidate be considered research-valid.

---

If you want, I can **draft a ready-to-use “research-validity packet”** in Python and Markdown that integrates directly with your uploaded `Quant` repository. It would include `engine.run_simulation` hooks, C3 baselines, cost/window rules, and automatic anti-p-hacking reporting.  

Do you want me to generate that next?

用户:

AI助手:
##1.Verdict:**BLOCK**

NoV2alphacandidateshouldbetreatedas**research_valid**onthecurrentevidencealone.

Thecorrectoutcomeis:

**BLOCKforanycurrentV2alphavalidityclaim**
**ADVISORY_PASSforadoptingtheseparateresearch-validitycontract/gate**

Reason:theuploadedpacketandrepoestablishtherightmechanicalfoundation—`core.engine.run_simulation`,strictmissing-returnhandling,C3/baselinediscipline,PITrequirements,costrules,evidencepackets—buttheydo**not**yetprovidecandidate-specificV2evidence:nofixedC3baselinerun,nosame-windowdeltas,nocompletetrialledger,nofamily-levelmultiple-testingadjustment,noOOS/walk-forwardproof,norobustness/costsensitivity,andnocapacity/liquidityevidence.

ThepublicrepocurrentlydescribesPhase61/C3comparatorremediationascompletewhilestillidentifyingopenWRDS/authrisk;theseparateresearch-validityrunnerappearsincommit`8716c51`,whichaddedtheV0evidencegatebutexplicitlydidnotpromoteanythingtoatrading/recommendationstate.

Icreatedtherequestedseparatepackethere:

[DownloadtheV2alpharesearch-validitypacket](sandbox:/mnt/data/v2_alpha_research_validity_stats_packet_20260602.zip)

---

##2.MinimumEvidenceContract

AV2alphacandidatecanenter**research_validreview**onlyafterallofthesearepresent:

|Requirement|Minimumrule|
|---|---|
|**Candidatecartridge**|ImmutableV2alphadefinitionwithsignalformula,universe,rebalancerule,constraints,parameters,costassumptions,andpre-registeredprimaryendpoint.|
|**Canonicalengine**|AllcandidateandbenchmarkPnLmustbeproducedthrough`core.engine.run_simulation(...,strict_missing_returns=True)`.NoalternatePnLpathcounts.|
|**Executionlag**|Candidateweightsmustbeexecutedwiththeengine’slagged-weightconvention,notsame-barlookaheadexecution.|
|**PITproof**|Dataloadermustprovepoint-in-timeinputs,release-datehandling,nocurrent-universeleakage,nofull-historynormalization,andnofuturelabels/features.|
|**C3/baselinelock**|TheC3baselinemustbeidentifiedbyrunID,codehash,datasnapshothash,window,universe,costpolicy,andmetricfile.|
|**Same-windowcomparison**|CandidateandC3mustusethesamedateindex,samereturnmatrix,samePITuniverse,samemissing-returnpolicy,samebenchmarkengine,andsamecostpolicy.|
|**Costrule**|Costsmustbedeclaredbeforetherunandappliedinsidetheengine.Thepacket’sruletreatstheengineargumentcurrentlynamed`cost_bps`asadecimalturnovercostrate,where`0.0010`means10bpsone-wayper1.0unitofrisky-assetturnover.|
|**Evidencepacket**|Outputsmustincludemetrics,returns,weights,turnover,costs,missing-returnreport,PITproof,inputsignatures,benchmarksignatures,andreproducibilityhashes.|
|**Statisticalvaliditylayer**|Same-windowpositivedeltasarenotenough;thecandidatealsoneedsmultiplicityadjustment,OOS/walk-forwardevidence,robustnesschecks,andanti-overfittingcontrols.|

Thepriorcontractisstrict:nocartridge,nocanonicalenginerun,noPITproof,nobenchmark,nocosts,andnoevidencepacketmeans“notresearch-valid.”Italsorequiresthesameengine,samedateindex,samemissing-returnpolicy,andsamecostpolicyforbenchmarks.Theengineitselfapplieslaggedweights,strictmissingexecuted-returnchecks,turnovercosts,andnet-returnaccounting,sotheserulesshouldbetreatedaspartofthestatisticaldesignratherthanoptionalimplementationdetails.

---

##3.RequiredDeltaMetricsvsBaseline/C3

TheminimumV2validitycomparisonshouldbedefinedonthealignednet-returnspread:

\[
d_t=r^{V2}_{t,\net}-r^{C3}_{t,\net}
\]

AV2alphacandidateshouldnotbecalled**research_valid**unlessitclearsthisminimumdeltatable.

|Deltametric|Requiredminimumbefore`research_valid`|
|---|---|
|**Netannualizedalphadelta**|Annualizedmeanof\(d_t\)mustbepositive,aboveapre-registeredeconomicmaterialityfloor,andhaveaone-sided95%HACorblock-bootstraplowerconfidenceboundabove0.|
|**DeltaCAGR**|CandidatenetCAGRminusC3netCAGRmustbepositiveafterallcosts.|
|**Informationratioofdeltareturns**|\(IR(d_t)\)mustbepositiveandstatisticallysignificantafterfamily-levelmultiple-testingadjustment.|
|**Sharpe/DeflatedSharpe**|CandidatemusthavepositivenetSharpe,andtheDeflatedSharpeRatioorequivalentmultiple-trialadjustmentmustpassthepre-registeredthreshold.Default:DSRconfidence≥0.95.|
|**Maxdrawdowndelta**|CandidatemaxdrawdownmustnotbemateriallyworsethanC3.Defaultguardrail:nomorethan10percentagepointsabsoluteworseor25%relativeworse,unlessthelanepre-registersastricterrule.|
|**Drawdowndurationdelta**|Candidatedrawdowndurationshouldnotexceed1.25×C3bydefault.|
|**Turnoverdelta**|Candidateturnovermustbereported.Higherturnoverisallowedonlyifnetalphasurvivescoststress.|
|**Costdragdelta**|CandidatemustbeatC3afterbasecostsandafteratleast2×coststress.|
|**Netalphaperturnover**|Improvementmustnotbepurelygeneratedbyexcessiverebalancing.Acandidatethatwinsonlybeforecosts,oronlyunderunrealisticallylowcosts,isblocked.|
|**Tail-riskdelta**|5%CVaR,worstmonth,andworsteventbucketmustnotbemateriallyworsethanC3unlessthiswasexplicitlypre-registered.Defaultguardrail:nomorethan20%relativedegradation.|
|**Benchmarkexcessreturn**|CandidatemustbeatC3andthePITequal-weighteligible-universebenchmarkonthesamereplaydates.Broad-marketorfamilybenchmarksshouldbeaddedwhenapplicable.|
|**Signal-levelevidence**|Forcross-sectionalalpha:meanrankICandtop-bottomspreadshouldhavelower95%confidenceboundsabove0.Foreventalpha:abnormalreturnversusC3/eventbenchmarkmusthavelowerboundabove0.|
|**Regimedelta**|Candidatemustshowpositivenetdeltainamajorityofpre-registeredregimes;oneregimecannotcarrytheentireresult.|
|**Concentrationdelta**|Leave-one-date,leave-one-asset,leave-one-sector,orleave-one-event-bucketremovalmustnoterasetheeffect.Defaultblock:anysinglebucketcontributes>30%oftotalalphaandremovingitflipstheresultnegative.|

ThestatisticaltestfordeltareturnsshoulduseHAC/Newey-Westorblockbootstrapratherthanaplainiidt-test,becausedailystrategyreturnscommonlyhaveautocorrelationandheteroskedasticity.Newey-WestHACestimationisspecificallyintendedforcovarianceconsistencyunderbroadheteroskedastic/autocorrelatedconditions.

---

##4.Multiple-TestingandOverfittingControls

Minimumanti-p-hackingcontrols:

|Control|Requiredrule|
|---|---|
|**Pre-registration**|BeforeseeingfinalOOSresults,freezethecandidatecartridge,primaryendpoint,C3baseline,window,universe,costpolicy,andsuccessthresholds.|
|**Oneprimaryendpoint**|Exactlyoneprimarytestdecidesresearchvalidity.Suggesteddefault:annualizednetalphadeltaversusC3withHAC/block-bootstraplower95%bound>0andmultiplicity-adjustedp≤0.05.|
|**Completetrialledger**|EveryattemptedV2variant,parameterchange,featurefilter,universetweak,costassumption,andrejectedrunmustbelogged.Unloggedtrialsblockvalidity.|
|**Effectivetrialcount**|Correlatedvariantsmaybeclustered,buttheeffectivenumberofindependenttrialsmustbeestimatedanddisclosed.|
|**Trialbudget**|Defaultmaximum:25effectiveindependenttrialsperalphafamilybeforeanewresearchpacketorholdoutresetisrequired.|
|**Family-levelFDR**|AcrossV2variantsinthesamealphafamily,useBenjamini-Hochbergoramoreconservativemethodwithdefaultq≤0.05.FDRcontrolisdesignedtolimittheexpectedproportionoffalsediscoveriesamongrejectedhypotheses.|
|**DeflatedSharpeRatio**|RequiredwhenreportingSharpe-likeperformanceaftermanytrials.DSRexistsspecificallytocorrectSharpeselectionbiasundermultipletestingandnon-normalreturns.|
|**PBO/CSCV**|Estimateprobabilityofbacktestoverfitting.Defaultgate:PBO≤0.10for`research_valid`;PBO≤0.05for`candidate_ready`.PBO/CSCVwasproposedbecausestandardholdoutapproachescanbeunreliableforinvestmentbacktests.|
|**SPA/RealityCheck**|Ifmanystrategiesarecompared,useHansenSPAorequivalentdata-snoopingcorrection.SPAisdesignedformultiple-modelcomparisonunderdatasnoopingandimprovesonearlierRealityCheckprocedures.|
|**Purged/embargoedvalidation**|Walk-forwardandcross-validationsplitsmustpurgeoverlappinglabelsandembargoadjacentperiodswhereleakageispossible.|
|**Single-useOOSlockbox**|FinalOOSwindowcannotberepeatedlyqueried.Onceusedforselection,itbecomesin-sampleforlatervariants.|
|**Nomovinggoalposts**|Acandidatecannotchangeitsmetric,window,costrule,universe,orC3baselineafterseeingresults.|
|**Negativecontrols**|Includeplacebolabels,randomizedsignaltiming,orshuffledcross-sectionalranks.Acandidatethatalso“works”onplacebotestsisblocked.|
|**Leakageaudit**|Blockoncurrent-universehistoricalrows,futurefundamentals,full-historytransforms,dashboard/candidate-cardlabelsusedasalphainputs,replaysignaturemismatch,missingexecutedreturns,ornon-finiteinputs.|

TheexistingV0runner’smechanical`research_valid`stateisthereforetoopermissiveforV2alphaclaimsifitonlymeans“canonicalengineranandminimumtradingdaysweremet.”ForV2,**research_validmustrequirestatisticalvalidity**,notjustsuccessfulartifactgeneration.

---

##5.RequiredRobustness/OOS/Walk-ForwardGates

AV2alphacandidateneedsallofthefollowingbefore`research_valid`:

|Gate|Minimumrequirement|
|---|---|
|**OOSduration**|Dailyalpha:atleast252OOStradingdaysunlessexplicitlymarkedexploratory.Eventalpha:atleast100totaleventsandatleast20eventspervalidationfold,unlessthelanehasastricterrule.|
|**Walk-forwardfolds**|Atleast3chronologicalfolds.Eachfoldmusttrain/selectonlyonpriordataandtestonfuturedata.|
|**Purging/embargo**|Requiredwherelabels,returns,fundamentals,oreventwindowsoverlap.|
|**Windowsensitivity**|Resultmustsurvivereasonablestart/end-dateshiftsandrollingsubwindows.|
|**Costsensitivity**|Candidatemustpassbasecost,2×turnovercost,andlane-specificadversespread/slippagestress.|
|**Regimesensitivity**|Reportbull/bear,high/lowvolatility,high/lowliquidity,crisis,sector,andmacro/eventregimeswhenapplicable.|
|**Universesensitivity**|Resultmustnotdependonahiddenuniversefilterorsurvivorship-biasedsubset.|
|**Capacity/liquidity**|Defaultguardrail:mediantrade≤5%ADVandmaxtrade≤10%ADV,unlessalane-specificlowercapacitythresholdisrequired.|
|**Concentrationchecks**|Nosingledate,asset,sector,country,eventtype,orrebalancebucketshouldexplainthefullalpha.|
|**Independentrerun**|Acleanrerunfromcartridge+datasnapshot+codehashmustreproducemetricswithintolerance.|

Acandidatethatpassesin-sampleC3deltasbutfailsOOS,coststress,orconcentrationchecksis**exploratory**,not**research_valid**.

---

##6.StatusVocabularyCheck

Useonlythesestatuses:

|Status|Meaning|
|---|---|
|**diagnostic_only**|Infrastructure,smoketest,orcomparatordiagnostic.Notalphaevidence.|
|**exploratory**|Canonicalrunnercompletedandartifactsexist,butthecandidatelacksoneormorevalidityrequirementssuchasfixedC3,OOS,multiplicitycorrection,robustness,PITproof,orcostsensitivity.|
|**research_valid**|Candidatehascartridge,canonicalenginerun,PITproof,same-windowC3/baselinecomparison,declaredcosts,completeevidencepacket,requiredpositivedeltas,multiplicitycontrols,androbustness/OOSgates.Notalive-tradingorrecommendationclaim.|
|**candidate_ready**|`research_valid`plusproduction-readinessevidence:capacity,liquidity,operationalcontrols,monitoring,risklimits,kill-switches,andgovernanceapproval.|
|**blocked**|Anyhardvaliditygatefailedorrequiredevidenceismissing.|

Therepo-sidecontractalreadydefinesthesestatusesanddistinguishes`research_valid`from`candidate_ready`;theV2policyshouldpreservethatseparation.

---

##7.MissingEvidence

Thecurrentpacketissufficienttoevaluatethe**validityframework**,butnotsufficienttovalidateanyspecificV2alpha.

Missingitems:

|Missingitem|Consequence|
|---|---|
|SpecificV2alphacartridge|Cannotknowwhatsignal,parameters,universe,rebalancerule,orendpointisbeingtested.|
|LockedC3baselineID/hash|Cannotcomputevalidsame-windowdeltas.|
|CandidateandC3engineoutputs|Cannotverifynetalpha,turnover,costs,drawdowns,orbenchmarkexcessreturn.|
|PITdatasnapshotandproof|Cannotexcludelookahead,survivorship,orrelease-dateleakage.|
|Completetrialledger|Cannotcorrectforresearcherdegreesoffreedom.|
|Multiplicitycorrection|Cannotdistinguishrealalphafromrepeated-searchluck.|
|OOS/walk-forwardresults|Cannotevaluategeneralization.|
|Robustness/coststress|Cannotknowwhetheralphasurvivesrealisticfrictions.|
|Regime/concentrationanalysis|Cannotknowwhetherperformanceisdrivenbyoneperiod,asset,sector,oreventbucket.|
|Capacity/liquidityanalysis|Cannotknowwhethertheresultistradableevenasacandidate.|

ThereforetheminimumhonestlabelforanyV2alphacandidatewithoutthoseitemsis:

**blocked**ifitclaimsvalidity,or**exploratory**ifitisclearlylabeledaspreliminaryresearch.

---

##8.Confidence:**8/10**

Highconfidenceontherequiredvalidityarchitecture:canonicalengine,same-windowC3,PITproof,declaredcosts,deltametrics,multiple-testingcontrol,OOS/walk-forward,androbustnessgates.

Lowerconfidenceonexactnumericthresholdsbecausetheyshouldbecalibratedbyalphalane,assetclass,holdingperiod,liquidityregime,andthefinalC3baselinedefinition.ThedefaultsaboveareintentionallyconservativeenoughtopreventprematureV2promotion.

---

##9.Nextaction

Createacandidate-specific**V2_ALPHA_VALIDITY_PACKET**foreachV2alphawith:

`candidatecartridge+pre-registrationhash+C3baselinehash+run_simulationoutputs+same-windowdeltatable+trialledger+FDR/DSR/PBO/SPAresults+OOS/walk-forwardmanifest+cost/window/regimerobustness+PITproof+reproducibilityhashes+finalgateverdict`

Untilthatpacketexistsandpasses,thecorrectgovernanceansweris:

**NoV2alphacandidateisresearch-valid.**

用户:
What exact default thresholds should be used for V2 alpha validity: HAC lower bound, FDR q, DSR confidence, PBO, cost stress, drawdown degradation?
What should count as the locked C3 baseline for PEAD_V2_001?
What minimum evidence separates exploratory from research_valid for event-driven PEAD specifically?
用户:

AI助手:
##RecommendeddefaultthresholdsforV2alphavalidity

Usetheseas**fail-closeddefaults**.Alanecanmakethemstricter,butshouldnotloosenthemafterseeingresults.

|Gate|Defaultresearch-validthreshold|
|---|---:|
|**PrimaryHAClowerbound**|One-sided**95%HAClowerconfidencebound**onannualizednetalphadeltavslockedC3mustbe**strictly>0.00%**aftercosts.|
|**Primarypoint-estimatemateriality**|Annualizednetalphadeltapointestimatemustbe**≥+2.00%net/year**vsC3.|
|**PEADevent-levelmateriality**|MeanPEADevent-windowabnormalreturnovertheprimaryeventwindowmustbe**≥+25bpsnet/event**,withone-sided95%block-bootstrap/HAClowerbound**>0bps**.|
|**Primaryadjustedp-value**|**≤0.05**,one-sided,onthepre-registeredprimaryendpoint.|
|**FamilyFDRq**|**q≤0.05**acrossthePEAD/V2family.UseBHonlywhenpositivedependence/clusterhandlingisdefensible;otherwiseuseBYorastricterfamilywisemethod.|
|**DSRconfidence**|**DeflatedSharpeRatioconfidence≥0.95**aftereffective-trialandnon-normalityadjustment.|
|**PBO**|**PBO≤0.10**for`research_valid`;**PBO≤0.05**for`candidate_ready`.|
|**Effectivetrialbudget**|**≤25effectiveindependenttrials**peralphafamilybeforeanewfamilypacket/holdoutresetisrequired.|
|**Baseturnovercost**|`turnover_cost_rate=0.0010`,meaning**10bpsone-wayper1.0unitofrisky-assetturnover**.|
|**Coststress**|Candidatemuststillpassat**2.0×basecost**,sodefaultstressis`0.0020`,or**20bpsone-way**.|
|**PEADslippagestress**|Inadditionto2×cost,passaPEADeventstressof**+5bpsone-way**adverseslippage,orhalf-spread/spreadmodelifavailableandlarger.|
|**Maxdrawdowndegradation**|Candidatedrawdownmagnitudemustsatisfyboth:`candidate_MDD≤C3_MDD+10percentagepoints`and`candidate_MDD≤1.25×C3_MDD`.|
|**Drawdowndurationdegradation**|`candidate_DD_duration≤1.25×C3_DD_duration`.|
|**Tail-lossdegradation**|5%CVaR/worst-month/worst-eventlossmustbe**≤1.20×C3**lossmagnitude.|
|**Concentration**|Blockifanysingledate,issuer,sector,quarter,eventbucket,orregimecontributes**>30%**oftotalnetalphaandremovingitflipsalphanegative.|
|**Liquidity/capacity**|Mediantrade**≤5%ADV**andmaxtrade**≤10%ADV**underthePEADtargetweightpath.|

ForHAC,usethenetdailydeltaseries\(d_t=r^{PEAD}_{t,net}-r^{C3}_{t,net}\).ForPEADwithoverlappingeventholdings,defaultHAClagshouldbe:

```text
hac_lag=min(63,max(5,primary_holding_horizon_trading_days))
```

SoforadefaultPEAD`[+1,+20]`trading-dayhold,use`hac_lag=20`.HACisappropriateherebecauseNewey-Weststylecovarianceestimationisdesignedforheteroskedasticity/autocorrelation-consistentinference,andPEADportfolioreturnscanbeseriallycorrelatedwheneventwindowsoverlap.

TheFDR/DSR/PBOthresholdsarenotdecorative.BH/BY-styleFDRisthefamily-levelanti-multiple-testinggate;DSRaddressesSharpeinflationfromselectionbiasandnon-normalreturns;PBO/CSCVestimateswhetherastrategyfamilyhasbeenoverfitduringbacktestsearch.

---

##WhatcountsasthelockedC3baselinefor`PEAD_V2_001`

For`PEAD_V2_001`,**lockedC3**shouldmeanthisandonlythis:

```text
C3_LOCK_PEAD_V2_001_v1
=
thelatestacceptedC3comparatoravailablebeforePEAD_V2_001finalevaluation,
rerunorre-materializedthroughcore.engine.run_simulation,
ontheexactsamePEAD_V2_001dateindex,returnmatrix,calendar,PITuniversepolicy,
executionlag,strict-missing-returnpolicy,andturnover-costpolicy,
withimmutablebaseline/runidentifiersandcontenthashes.
```

Itshould**not**mean:

```text
latest.jsonpointer
dashboardC3curve
sidecar-only/view-layercomparator
post-hocC3chosenafterPEADresults
PITequal-weightbenchmarkrenamedasC3
broad-marketETFbenchmarkrenamedasC3
eventCARspreadsheetoutsidethecanonicalengine
```

Therepocontractalreadysaysresearch-validevidencemustusethecartridge→PITloader/adapter→targetweights→`core.engine.run_simulation(...,strict_missing_returns=True)`path,andthatbenchmarksmustusethesameengine,dateindex,missing-returnpolicy,anddeclaredcostpolicy.ItalsodefinesthePITequal-weighteligible-universebenchmarkasrequired,butthatbenchmarkanswersadifferentquestionfromC3.Theengineitselfappliesone-barexecutionlag,strictmissingexecuted-returnfailurewhenenabled,turnovercost,andnet-returnaccounting,sotheC3lockmustbeexpressedinthatsameprimitive.

Thebaselinelockmanifestshouldcontainatminimum:

```yaml
candidate_id:PEAD_V2_001
baseline_role:C3_PRIMARY_COMPARATOR
baseline_lock_id:C3_LOCK_PEAD_V2_001_v1
baseline_id:<content-derivedbaselineid>
baseline_research_run_id:<canonicalC3runid>
baseline_source:latest_accepted_C3_as_of_lock_time
baseline_lock_time_utc:<timestampbeforefinalPEADevaluation>
code_commit:<gitcommithash>
engine:core.engine.run_simulation
strict_missing_returns:true
execution_lag:one_bar
turnover_cost_rate:0.0010
cost_stress_required:[0.0010,0.0020]
calendar_version:<NYSE/calendarid>
window_start:<sameasPEAD_V2_001>
window_end:<sameasPEAD_V2_001,includingholding-taildates>
data_snapshot_hash:<approvedPITsnapshothash>
returns_matrix_signature:<sha256>
target_weights_signature:<sha256>
c3_net_returns_signature:<sha256>
pit_universe_policy:<sameasPEAD_V2_001>
missing_return_policy:strict_fail_on_executed_exposure
```

ThepublicrepocurrentlysaysPhase61repairedasame-periodC3comparatorthroughboundedsidecar/view-layerlogicwhileleaving`core/engine.py`unchanged,anditalsonotesthatpromotion/coreinclusionremainedblocked.Thatisusefulcontext,butfor`PEAD_V2_001`itis**notenoughbyitself**;theC3comparatormustbepinnedasanimmutablecanonical-engineevidencerunforthePEADwindow.

IfnosuchcanonicalC3runexists,thecorrectstatusis:

```text
blockedforanyresearch_validclaim
exploratoryonlyifthePEADcandidatehascanonicalartifactsandisclearlylabeledpreliminary
```

ThePITequal-weightPEADeventuniverse,cash,broad-market,andPhase-56/PEAD-familybenchmarksarestillrequired,buttheyare**additionalcomparators**,notreplacementsforlockedC3.

---

##Minimumevidenceseparatingexploratoryfromresearch_validforevent-drivenPEAD

PEADisanevent-studyproblem,notjustadailyfactorbacktest.Theevidencehastoprovethattheearningseventtimestamp,surpriseinformation,tradableentrydate,holdingwindow,andabnormal-returncalculationwereallavailablepoint-in-time.PEADhasalongresearchhistoryasapost-earnings-announcementreturndriftanomaly,andevent-studymethodsarespecificallydesignedtomeasuresecurity-priceimpactarounddefinedevents.

###`exploratory`forPEAD

`PEAD_V2_001`canbelabeled**exploratory**onlyifithasallofthis:

|Exploratoryminimum|Requiredevidence|
|---|---|
|Candidatecartridge|Frozen`PEAD_V2_001`definition:eventsource,surprisemetric,entryrule,holdingwindow,filters,weighting,rebalance/overlappolicy,costpolicy,andprimaryendpoint.|
|Canonicalenginerun|Candidatetargetweightsrunthrough`core.engine.run_simulation(...,strict_missing_returns=True)`.|
|Declaredcosts|Basecost`0.0010`andstatedstressplan.|
|BasicPITeventpanel|Eventdates,issuerIDs,returns,surpriseinputs,andtimestamppolicydocumented,evenifnotyetfullyaudited.|
|Basicbenchmarks|AtleastcashandPITequal-weighteligible-eventbenchmark.|
|Evidenceartifacts|Returns,targetweights,executedweights,turnover,costs,metrics,eventledger,andrunmetadataemitted.|
|Honestlabel|MissingC3/OOS/multiplicity/robustnessitemsareexplicitlylisted.|

APEADrunis**blocked**,notexploratory,ifitlacksPITproof,hasunresolvedeventtimestampleakage,usescurrent-universehistoricalmembership,ignoresmissingexecutedreturns,lacksacostpolicy,ordoesnotusethecanonicalengine.

###`research_valid`forPEAD

`PEAD_V2_001`becomes**research_valid**onlyifitalsohasthefollowing:

|Research-validPEADrequirement|Exactdefault|
|---|---|
|**LockedC3**|`C3_LOCK_PEAD_V2_001_v1`asdefinedabove,fixedbeforefinalevaluation.|
|**Same-windowdeltas**|Candidate,C3,cash,PITequal-weight,broad-marketifavailable,andPEAD-familybaselineifavailableallrunonthesamedailydateindexandcostpolicy.|
|**Primaryendpoint**|Default:annualizednetalphadeltavslockedC3,usingcanonicaldailynetreturns.|
|**Primaryeventwindow**|DefaultPEADeventwindow:executabledriftwindow`[+1,+20]`tradingdaysaftertheeventbecomespublic.|
|**Secondaryeventwindows**|`[+1,+5]`and`[+1,+60]`asrobustnesswindows,notalternateprimaryendpoints.|
|**Eventtimestamppolicy**|BMO/intradayannouncementstradenoearlierthannextenginebar;AMC/after-close/unknown-timeannouncementsusethenexttradingdayaspubliceventdate.|
|**MinimumPEADsample**|Atleast**500eligibleeventstotal**,**150OOSevents**,**50eventsperchronologicalfold**,**150uniqueissuers**,and**8OOScalendarquarters**afterallfilters.|
|**OOS/walk-forward**|Atleast**3chronologicalfolds**,purgedforoverlappingeventwindowsandembargoedbyatleasttheprimaryholdinghorizon.|
|**HAC/bootstrappass**|AnnualizedC3deltaHAClowerone-sided95%bound>0;eventabnormal-returnblock-bootstraplower95%bound>0.|
|**Materiality**|Annualizednetalphadelta≥+2.00%vsC3andmeaneventabnormalreturn≥+25bpsnet/event.|
|**FDR**|Family-levelq≤0.05acrossallPEADvariantstried.|
|**DSR**|DSRconfidence≥0.95aftereffective-trialcorrection.|
|**PBO**|PBO≤0.10foranytuned/optimizedPEADfamily.|
|**Coststress**|Passbase`0.0010`,pass2×`0.0020`,andpassPEADadverseslippagestress.|
|**Drawdown/tailguardrails**|Mustsatisfythedrawdown,duration,CVaR,andconcentrationthresholdsabove.|
|**Negativecontrols**|Atleastonepermuted-announcement-datecontrol,onesign-shuffledorsector/quarter-shuffledsurprisecontrol,andoneplaceboeventcontrol.Anysignificantplaceboresultblocksvalidity.|
|**Leakageaudit**|Eventtimestamp,analystforecastcutoff,actualEPSavailability,Compustat/IBES/CRSP/CCMlinkage,universemembership,split/corporate-actionadjustment,andreturnavailabilitymustbesigned.|
|**Delistingtreatment**|CRSPdelistingreturnsoranexplicitdelisting-returnpolicymustbeincluded;omitteddelistingreturnsareaknownsourceofbiasinCRSPreturnstudies.|
|**Robustnesssplits**|Passortransparentlyreportsector,size,liquidity,announcementtiming,fiscalquarter,calendaryear,earnings-seasondensity,volatilityregime,andcrisis/non-crisissplits.|
|**Concentration**|Leave-one-quarter,leave-one-year,leave-one-sector,leave-one-issuer,andleave-one-event-bucketremovalcannotfliptheresultnegative.|
|**Reproducibility**|Independentrerunfromcartridge+C3lock+datasnapshot+codehashreproducesmetricswithintolerance.|

Thecleandividinglineis:

```text
exploratory
=
canonicalPEADevidenceexists,butoneormoreoflockedC3,OOS,multiplicity,
PBO/DSR,eventtimestampproof,coststress,orrobustnessevidenceismissing.

research_valid
=
canonicalPEADevidence+lockedC3+PITeventproof+same-windowdeltas
+pre-registeredendpoint+completetrialledger+q/DSR/PBOcontrols
+OOS/walk-forward+cost/window/regime/concentrationrobustnessallpass.
```

Sothepracticalanswerfor`PEAD_V2_001`is:

```text
Donotallowresearch_validunless:
HACLCB95(deltanetalphavsC3)>0,
pointdeltaalpha>=+2.00%/yr,
eventAR>=+25bpsnet/event,
FDRq<=0.05,
DSR>=0.95,
PBO<=0.10,
2xcoststillpasses,
MDDisnot>10ppabsoluteor>25%relativeworsethanC3,
andC3_LOCK_PEAD_V2_001_v1existsasacanonical-engine,same-window,immutablebaseline.
```

用户:
Are the proposed default thresholds accepted: HAC LCB > 0, +2% annual net alpha, FDR q <= 0.05, DSR >= 0.95, PBO <= 0.10?
What exactly is C3_LOCK_PEAD_V2_001_v1?
What minimum evidence separates exploratory from research_valid for event-driven PEAD?
用户:

AI助手:
##1.Thresholds:**acceptedasdefaultV2research-validgates**

Yes.Adopttheproposeddefaultsasthe**minimumstatisticalthresholds**foraV2alphacandidatetobetreatedas`research_valid`:

|Gate|Accepteddefault|
|---|---:|
|**HAClowerbound**|One-sided**95%HAClowerconfidencebound>0**onannualizeddailynetalphadeltavslockedC3.|
|**Economicmateriality**|PointestimateofannualizednetalphadeltavsC3**≥+2.00%net/year**.|
|**FDR**|Family-leveladjusted**q≤0.05**onthepre-registeredprimaryendpoint.|
|**DSR**|**DeflatedSharpeRatioconfidence≥0.95**aftereffective-trialandnon-normalityadjustment.|
|**PBO**|**PBO≤0.10**for`research_valid`;use**≤0.05**onlyfor`candidate_ready`.|

Thisshouldbetreatedasa**fail-closeddefault**:passingthesefivegatesisnecessarybutnotsufficient.PEADalsoneedslockedC3,PITeventproof,OOS/walk-forwardevidence,coststress,windowrobustness,concentrationchecks,andnegativecontrols.

FortheHACtest,theprimaryseriesis:

```text
d_t=PEAD_V2_001_net_return_t-C3_locked_net_return_t
```

Useaone-sided95%HAClowerboundonannualizedmean`d_t`.ForPEADwithoverlappingeventholds,defaulttheHAClagto:

```text
hac_lag=min(63,max(5,primary_holding_window_trading_days))
```

Forthedefault`[+1,+20]`PEADdriftwindow,thatmeans`hac_lag=20`.

HAC/Newey-Weststyleinferenceisappropriatebecausethedeltareturnseriescanhaveheteroskedasticityandautocorrelation,especiallywhenPEADeventwindowsoverlap.FDRcontrolistherequiredfamily-levelmultiple-testinggate;theBenjamini-Hochbergpaperdefinesaprocedureforcontrollingexpectedfalsediscoveriesacrosstestedhypotheses.DSRisrequiredbecauseitisdesignedtocorrectSharpe-likeclaimsforselectionbiasundermultipletestingandnon-normalreturns.PBOisrequiredbecauseitestimatesbacktest-overfittingriskininvestmentsimulationsusingCSCV-styleresampling.

---

##2.Whatexactlyis`C3_LOCK_PEAD_V2_001_v1`?

`C3_LOCK_PEAD_V2_001_v1`is**not**ageneric“latestC3”pointerandnotadashboardcurve.Itistherequiredimmutablebaseline-lockartifactforjudging`PEAD_V2_001`.

Exactdefinition:

```text
C3_LOCK_PEAD_V2_001_v1
=
theimmutable,content-addressed,pre-final-evaluationlockrecord
bindingPEAD_V2_001toonespecificC3comparatorrun,
wherethatC3runwasproducedthroughcore.engine.run_simulation
withstrict_missing_returns=True,
onthesameevaluationdateindex,calendar,costpolicy,
missing-returnpolicy,return-datasnapshot,andbenchmarkevidencepath
usedforPEAD_V2_001.
```

Itshouldbestoredasalockmanifest,forexample:

```text
evidence/locks/C3_LOCK_PEAD_V2_001_v1.json
```

Minimumlockmanifest:

```yaml
lock_id:C3_LOCK_PEAD_V2_001_v1
candidate_id:PEAD_V2_001
baseline_role:C3_PRIMARY_COMPARATOR

lock_status:locked
locked_before_final_candidate_evaluation:true
lock_created_at_utc:<timestamp>
lock_created_by:<governance/researchowner>

c3_source_rule:latest_accepted_C3_available_before_lock_time
c3_run_id:<canonicalC3researchrunid>
c3_strategy_id:<C3strategy/comparatorid>
c3_strategy_version:<immutableversion>
c3_cartridge_hash:<sha256>
c3_target_weights_hash:<sha256>
c3_net_returns_hash:<sha256>
c3_metrics_hash:<sha256>

engine_function:core.engine.run_simulation
strict_missing_returns:true
execution_lag:one_bar_shift_1
turnover_cost_rate:0.0010
turnover_cost_bps:10.0
cost_basis:per_unit_one_way_risky_asset_turnover

candidate_window_start:<PEAD_V2_001evaluationstart>
candidate_window_end:<PEAD_V2_001evaluationendincludingholding-taildates>
shared_date_index_hash:<sha256>
calendar_version:<calendarid>
returns_matrix_hash:<sha256>
data_snapshot_hash:<sha256>
pit_universe_policy_hash:<sha256>
missing_return_policy:strict_fail_on_executed_exposure

required_stress_runs:
-turnover_cost_rate:0.0010
-turnover_cost_rate:0.0020

forbidden_substitutes:
-latest_json_pointer
-dashboard_curve
-candidate_card_curve
-sidecar_only_comparator
-broad_market_proxy_only
-PIT_equal_weight_renamed_as_C3
-event_CAR_spreadsheet_outside_core_engine
```

Therepocontractrequiresresearch-validrunstousethecartridge→PITloader/adapter→targetweights→`core.engine.run_simulation(...,strict_missing_returns=True)`path,anditrequiresbenchmarkstousethesameengine,dateindex,missing-returnpolicy,andcostpolicy.Theengineitselfshiftstargetweightsbyonebar,raisesinstrictmodewhenexecutedexposureshavemissingreturns,andcalculatesnetreturnsafterturnovercosts.

CurrentrepocontextsaysPhase61repairedasame-periodC3comparatorthroughboundedsidecar/view-layerlogicwhileleaving`core/engine.py`unchanged.Thatisusefulplatformcontext,butfor`PEAD_V2_001`itis**notenough**unlesstheC3comparatorisre-materializedorpinnedasacanonical-engineevidencerunforthePEADevaluationwindow.

Sotheoperationalansweris:

```text
IfC3_LOCK_PEAD_V2_001_v1doesnotexistasacanonical-enginelockmanifest,
PEAD_V2_001cannotberesearch_valid.
```

Itmaystillbe`exploratory`onlyifthePEADcandidateitselfhascanonicalartifactsandnohardleakage/data-healthfailures.

---

##3.Minimumevidence:`exploratory`vs`research_valid`forevent-drivenPEAD

PEADisevent-driven,sothevalidityevidencemustprovemorethandailystrategyperformance.Itmustprovethattheearningsevent,surprisevariable,tradableentrydate,holdingwindow,andabnormal-returnmeasurementareallpoint-in-timeandexecutable.PEADisadocumentedpost-earnings-announcementdriftanomaly,andevent-studymethodsareusedtomeasuretheeffectofaneconomiceventonfirmvaluethroughsecuritypricesaroundtheevent.

###A.Minimumfor`exploratory`

`PEAD_V2_001`maybelabeled`exploratory`onlywhenallofthisexists:

|Requirement|Minimumexploratoryevidence|
|---|---|
|**Frozencartridge**|`PEAD_V2_001`cartridgewitheventsource,surprisedefinition,entryrule,holdingwindow,universe,filters,weights,rebalance/overlappolicy,costs,andprimaryendpoint.|
|**Canonicalenginerun**|Candidateweightsrunthrough`core.engine.run_simulation(...,strict_missing_returns=True)`.|
|**Executionpolicy**|Eventtimestampmappedtoexecutabletradedate:BMO/intradayannouncementstradenoearlierthannextenginebar;AMC/after-close/unknown-timeannouncementstradenexttradingday.|
|**BasicPITeventledger**|Eventdate/time,issuerID,announcementsource,EPSactual,forecast/expectedEPSsource,surprisevalue,dataavailabilitytimestamp,andtradableentrydate.|
|**Nohardleakagefailure**|NofutureEPS,futureanalystestimates,current-universebackfill,full-historynormalization,candidate-cardlabels,orpost-eventdatausedinsignalconstruction.|
|**Declaredcosts**|Base`turnover_cost_rate=0.0010`,reportedas10bpsperunitone-wayrisky-assetturnover.|
|**Minimumbenchmarks**|CashandPITequal-weighteligible-eventbenchmark,runthroughthesameengine/dateindex/costpolicy.|
|**Evidenceartifacts**|Cartridge,runmetadata,returns,targetweights,executedweights,turnover,costs,metrics,benchmarkmetrics,eventledger,inputsignatures,andgateresults.|
|**Honestmissing-evidencelist**|Theverdictmustexplicitlysaywhichresearch-validgatesaremissing:C3lock,OOS,FDR,DSR,PBO,coststress,robustness,etc.|

Hardrule:

```text
NoPITeventledgerornocanonicalenginerun=blocked,notexploratory.
```

TherepocontractalreadytreatsmissingPITproof,missingbenchmarkpolicy,missingcostpolicy,missingexecutedreturns,andnon-finiteexecutedreturnsashard-blockgates.

---

###B.Minimumfor`research_valid`

`PEAD_V2_001`becomes`research_valid`onlyifitsatisfiesallexploratoryrequirements**plus**thefollowing:

|Requirement|Defaultresearch-validrule|
|---|---|
|**LockedC3**|`C3_LOCK_PEAD_V2_001_v1`existsandwasfixedbeforefinalcandidateevaluation.|
|**Same-windowdeltas**|PEADandlockedC3usethesamedateindex,returnmatrixsnapshot,strictmissing-returnpolicy,calendar,andcostpolicy.|
|**Primaryendpoint**|AnnualizeddailynetalphadeltavslockedC3.|
|**Primarythreshold**|HACone-sided95%lowerboundonannualizednetdelta**>0**.|
|**Materiality**|Annualizednetalphadeltapointestimate**≥+2.00%/year**.|
|**Event-levelmateriality**|MeanPEADabnormalreturnoverprimaryeventwindow**≥+25bpsnet/event**,withbootstrap/HAClowerbound**>0**.|
|**Primaryeventwindow**|Defaultexecutabledriftwindow:`[+1,+20]`tradingdaysafterpubliceventavailability.|
|**Robustnesswindows**|`[+1,+5]`and`[+1,+60]`mustbereportedasrobustnesswindows,notalternativeprimaryendpoints.|
|**Minimumsample**|Atleast**500eligibleeventstotal**,**150OOSevents**,**50eventsperchronologicalfold**,**150uniqueissuers**,and**8OOScalendarquarters**afterfilters.|
|**Walk-forward/OOS**|Atleast**3chronologicalfolds**,trained/selectedonlyonpriordata.|
|**Purging/embargo**|Purgeoverlappingeventlabels/holdingwindowsandembargobyatleasttheprimaryholdinghorizon.|
|**FDR**|Family-leveladjusted**q≤0.05**acrossallPEADvariantstried.|
|**DSR**|DSRconfidence**≥0.95**aftereffective-trialadjustment.|
|**PBO**|PBO**≤0.10**forthePEADvariantfamily.|
|**Trialledger**|EveryPEADvariant,filter,parameter,universetweak,windowtweak,andrejectedrunloggedbeforefinalOOSselection.|
|**Coststress**|Passbase`0.0010`,pass2×cost`0.0020`,andpassPEADadverseslippagestressofatleast+5bpsone-wayunlessaspreadmodelsayslarger.|
|**Drawdownguardrail**|CandidatemaxdrawdowncannotbeworsethanC3bymorethan**10percentagepointsabsolute**or**25%relative**.|
|**Drawdownduration**|Candidatedrawdowndurationcannotexceed**1.25×C3**.|
|**Tailrisk**|5%CVaR,worstmonth,andworstevent-bucketlosscannotbemorethan**1.20×C3**lossmagnitude.|
|**Concentration**|Blockifonedate,issuer,sector,quarter,eventbucket,orregimecontributes**>30%**oftotalnetalphaandremovingitflipsalphanegative.|
|**Negativecontrols**|Mustincludepermutedannouncementdates,sign/sector/quarter-shuffledsurprises,andplaceboevents.Anysignificantplaceboalphablocksvalidity.|
|**Dataaudit**|Eventtimestamp,analystforecastcutoff,actualEPStimestamp,CRSP/Compustat/IBES/CCMlink,split/corporate-actionadjustment,delisting-returnpolicy,andPITuniversemembershipsignedoff.|
|**Capacity/liquidity**|Mediantrade≤**5%ADV**andmaxtrade≤**10%ADV**,unlesslane-specificpolicyisstricter.|
|**Reproducibility**|Cleanrerunfromcartridge+C3lock+datasnapshot+codehashreproducesmetricswithintolerance.|

Thedividinglineistherefore:

```text
exploratory
=
canonicalPEADevidenceexistsandnohardleakage/data-healthgatefailed,
butoneormoreresearch-validgatesaremissing.

research_valid
=
canonicalPEADevidence+lockedC3+PITeventaudit+same-windowdeltas
+acceptedstatisticalthresholds+completetrialledger+OOS/walk-forward
+cost/window/regime/concentrationrobustness+negativecontrolsallpass.
```

Finalgovernancerulefor`PEAD_V2_001`:

```text
Acceptedthresholds:
HACLCB95(deltavslockedC3)>0
annualizednetalphadelta>=+2.00%
FDRq<=0.05
DSRconfidence>=0.95
PBO<=0.10

ButPEAD_V2_001isnotresearch_validuntilC3_LOCK_PEAD_V2_001_v1
existsandthePEAD-specificevidencepacketpasseseveryrequiredgate.
```

用户:
What default thresholds: HAC, FDR, DSR, PBO, cost stress?
What is the locked C3 baseline for PEAD?
What separates exploratory from research_valid?
用户:

