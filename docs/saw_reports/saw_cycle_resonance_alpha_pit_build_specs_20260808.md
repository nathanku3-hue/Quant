# Thin SAW — Cycle Resonance / Alpha PIT Build Specs

RoundID: `CYCLE-RESONANCE-ALPHA-PIT-BUILD-SPECS-20260808`
ScopeID: `DOCS-ONLY-POST-CLOCK-BUILD-SPECS`
Hierarchy Confirmation: Approved | Session: current-thread | Trigger: owner instruction to define exactly two thin post-Clock build specs without widening the current CIQ gate | Domains: Docs/Ops

## Scope

Create only the narrow implementation specifications needed before post-Clock coding:

1. `docs/architecture/alpha_pit_data_api_v1.md`
2. `docs/architecture/cycle_resonance_v1_build_spec.md`

Preserve:

```text
ACTIVE_GATE = PRE_SEAL_REAL_CIQ_ADMISSION
financial_alpha_evidence = 0
CLOCK_1_STARTED = FALSE
LIVE = CLOSED
```

No current CIQ admission architecture is changed.

## Required design properties

- old `godview_api_availability_matrix.md`, `data_readiness_gate_v0.md`, and provenance packets remain historical/planning surfaces rather than compatibility dependencies;
- one new narrow Alpha PIT API exposes `risk_set`, `observations`, `source_claims`, `expectations`, and discovery-only `outcomes`;
- every canonical response binds permanent identity, observed/available times, source/receipt hashes, schema, coverage/missingness, artifact hashes, and license/retention metadata;
- confirmatory/prospective mode mechanically lacks outcome capability rather than relying only on a mode flag;
- provider-specific CIQ/SEC adapters sit behind the canonical API and no generic provider framework is introduced;
- `CYCLE_RESONANCE_v1` uses the new Alpha PIT API as its sole data dependency;
- observed claims and AI/inferred claim features remain separate epistemic objects;
- scientific parameters have no runtime defaults after implementation freeze;
- MVA sequencing remains family-first/prospective-first rather than exhaustive-history-first;
- no broker, optimizer, provider, data artifact, or Alpha implementation is authorized before Clock #1.

## Acceptance checks

- `CHK-01` — exactly the two requested architecture build specs exist and are marked post-Clock / not implemented.
- `CHK-02` — Alpha PIT API defines the five requested surfaces and structurally separates discovery outcome capability from confirmatory/prospective read capability.
- `CHK-03` — provider boundary is explicit/narrow; old planning/readiness APIs are not compatibility dependencies.
- `CHK-04` — Cycle Resonance spec defines module seams, canonical inputs/outputs, clock/resonance/AI-claim boundaries, state machine, search semantics, and failure tests.
- `CHK-05` — current `PRE_SEAL_REAL_CIQ_ADMISSION` and `financial_alpha_evidence=0` remain unchanged; no current-truth/top-level architecture widening.
- `CHK-06` — docs structure/whitespace/context validation and SAW closure validation pass.

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| Material | Reusing old planning/readiness contracts would preserve incompatible identity/provider semantics. | New v1 API explicitly rejects compatibility/import dependency on those surfaces. | Architecture/Data | Closed |
| Material | A runtime mode flag alone could permit accidental future-label access in confirmatory research. | Discovery receives a distinct outcome-capable interface; confirmatory/prospective sessions lack the capability and reject the outcome module dependency. | Quant/Meta-Research | Closed |
| Advisory | Generic provider abstraction could become another platform-first project. | Only explicit first-family CIQ and SEC adapters are specified; Rule of Two remains in force. | Data/Architecture | Closed |
| Advisory | Family build could hide scientific defaults in implementation code. | Implementation manifest requires explicit coverage/sequence/model/search choices; omitted scientific values fail closed. | Quant | Closed |

## Scope split summary

In-scope: exact docs-only post-Clock module/API contracts for the first Alpha lane and its narrow PIT data boundary; lesson capture; SAW evidence.

Inherited/out-of-scope: current CIQ admission code/data, Clock #1 execution, provider fetching, historical Atlas reconstruction, SEC/CIQ adapters, AI model implementation, prediction runs, broker/order code, live capital, optimizer, commit/push/publication, and all unrelated pre-existing dirty-worktree changes.

## Forbidden-action scan

PASS if the final round changes documentation only. No source/test/data/provider/broker/Git-history action is authorized by this scope.

## Open Risks

- The specs intentionally do not choose scientific coverage thresholds, clock lag thresholds, model class, or calibration parameters; those must be frozen in the first implementation manifest before confirmatory use, not defaulted in code.
- Historical CIQ estimate/publication coverage and SEC filing reconstruction feasibility remain empirical post-Clock data questions.
- Real CIQ Security/Trading Item + completed market admission remains the only current pre-Clock blocker.

## Evidence check

- `docs/architecture/alpha_pit_data_api_v1.md` and `docs/architecture/cycle_resonance_v1_build_spec.md` exist and are explicitly `POST_CLOCK_ONLY / NOT_IMPLEMENTED`.
- Required five API surfaces are present; `outcomes` exists only on `AlphaPITDiscoveryAPIv1` while confirmatory/prospective sessions receive `AlphaPITReadAPIv1`.
- New specs explicitly reject compatibility authority from the old API/readiness/provenance surfaces and forbid direct provider imports in the Cycle package.
- `python3 scripts/build_context_packet.py --repo-root . --validate`: PASS; active context was not recut by this round.
- `python3 -m json.tool docs/context/current_context.json`: PASS.
- Scoped `git diff --check`: PASS.
- Markdown NUL/fence structural scan: PASS.
- Round status shows docs only: two new architecture specs, this SAW report, and required `docs/lessonss.md` round entry; no executable/data/provider/broker files were changed by this round.

Open Risks: scientific implementation parameters remain preregistered-at-build rather than code defaults; historical source coverage remains empirical; real CIQ bytes remain the only pre-Clock blocker.

ChecksTotal: 6
ChecksPassed: 6
ChecksFailed: 0
SAW Verdict: PASS

ClosurePacket: RoundID=CYCLE-RESONANCE-ALPHA-PIT-BUILD-SPECS-20260808; ScopeID=DOCS-ONLY-POST-CLOCK-BUILD-SPECS; ChecksTotal=6; ChecksPassed=6; ChecksFailed=0; Verdict=PASS; OpenRisks=Scientific implementation parameters remain preregistered-at-build rather than code defaults, historical source coverage remains empirical, real CIQ bytes remain the only pre-Clock blocker; NextAction=Continue current real-CIQ admission only until Clock #1, then implement the two frozen build specs without adding a compatibility or generic provider layer.

ClosureValidation: PASS
SAWBlockValidation: PASS

Next action: continue current real-CIQ admission only until Clock #1; then implement `alpha_pit_data_api_v1` and `CYCLE_RESONANCE_v1` without compatibility or generic-provider widening.
