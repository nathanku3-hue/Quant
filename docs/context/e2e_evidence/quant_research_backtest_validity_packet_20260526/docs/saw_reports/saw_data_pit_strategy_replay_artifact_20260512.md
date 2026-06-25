# SAW Data/PIT Strategy Replay Artifact - 2026-05-12

SAW Verdict: BLOCK

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: inherited worker scope | Domains: Data/PIT Artifact | FallbackSource: docs/spec.md + docs/phase_brief/phase65-brief.md

## Scope

RoundID: DATA_PIT_ARTIFACT_20260512
ScopeID: strategy-replay-input-artifact

Owned files:
- core/data_orchestrator.py
- scripts/build_strategy_replay_artifact.py
- tests/test_data_orchestrator_portfolio_runtime.py
- tests/test_strategy_replay_artifact.py

Acceptance checks:
- CHK-01 local PIT price/return matrix is identified and loaded without provider calls.
- CHK-02 replay slices contain no rows after as-of date.
- CHK-03 cache key invalidates on source file signatures, method, controls, date range, and max_weight.
- CHK-04 artifacts are display-only and written temp-to-replace.
- CHK-05 canonical market data roots are not write targets for display-only replay artifacts.
- CHK-06 non-finite controls cannot create parquet/manifest half-bundles.
- CHK-07 focused pytest command passes.
- CHK-08 scoped compile passes.
- CHK-09 independent post-reconciliation SAW recheck completes.

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Default `top_liquid` replay universe could be future-informed. | `load_strategy_replay_inputs` now defaults to and requires `r3000_pit`; script default changed to `r3000_pit`; regression added. | Data/PIT worker | Fixed locally |
| High | Display-only `--output-path` could target canonical-looking `data/processed` path. | Artifact writer rejects repo `data/` paths outside configured runtime cache; regression added. | Data/PIT worker | Fixed locally |
| High | Non-finite CLI/control input could replace parquet before manifest serialization failed. | Finite validation added; manifest pre-serializes before parquet replace; half-bundle regression added. | Data/PIT worker | Fixed locally |
| Medium | Long artifact flattening could create large repeated row intermediates. | Artifact format changed to compact wide rows, one matrix row per date for price/return; ticker map stored in manifest. | Data/PIT worker | Fixed locally |
| Governance | Independent SAW recheck after reconciliation could not complete because subagent usage limit was reached. | Carry as open governance risk; rerun independent recheck after limit reset if formal milestone PASS is required. | Parent orchestration | Open |

## Scope Split Summary

in-scope findings/actions: all Critical/High implementation findings reported by initial Implementer and Reviewers A/B/C were reconciled in the owned files and covered by focused tests.

inherited out-of-scope findings/actions: broad dirty worktree, broader dashboard/runtime governance updates, and phase-close full regression remain outside this Data/PIT artifact worker slice.

## Document Changes Showing

| Path | Change summary | Reviewer status |
|---|---|---|
| core/data_orchestrator.py | Added PIT-safe replay input dataclass, cache signatures, compact display-only artifact writer, finite validation, and output path confinement. | Initial SAW blockers reconciled locally; independent recheck blocked by usage limit |
| scripts/build_strategy_replay_artifact.py | Added CLI wrapper for local replay artifact builds; default universe is `r3000_pit`. | Initial SAW blockers reconciled locally; independent recheck blocked by usage limit |
| tests/test_data_orchestrator_portfolio_runtime.py | Added cache invalidation, PIT slicing, no-provider, non-PIT rejection, and patch precedence metadata tests. | Passing |
| tests/test_strategy_replay_artifact.py | Added atomic write, canonical path rejection, half-bundle, compact artifact, no-provider script, and PIT default tests. | Passing |
| docs/notes.md | Added explicit replay input formulas, cache key formula, PIT universe guard, and atomic artifact rules. | Passing |
| docs/decision log.md | Added Data/PIT Strategy Replay Artifact decision record and contract lock. | Passing |
| docs/lessonss.md | Added PIT-boundary lesson for row slicing plus universe membership. | Passing |
| docs/saw_reports/saw_data_pit_strategy_replay_artifact_20260512.md | Published SAW reconciliation report with usage-limit recheck risk. | Passing |

## Evidence

- `.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py tests\test_strategy_replay_artifact.py -q` -> PASS, 22 passed.
- `.venv\Scripts\python -m py_compile core\data_orchestrator.py scripts\build_strategy_replay_artifact.py tests\test_data_orchestrator_portfolio_runtime.py tests\test_strategy_replay_artifact.py` -> PASS.
- `.venv\Scripts\python scripts\build_strategy_replay_artifact.py --as-of-date 2026-01-05 --max-weight NaN --output-path data\runtime_cache\strategy_replay\bad_nan.parquet` -> expected ValueError before artifact write; no artifact remains.
- `validate_se_evidence.py` -> VALID.
- `validate_closure_packet.py` -> VALID.

Open Risks: Independent post-reconciliation SAW recheck is blocked by account usage limit; formal milestone PASS should rerun reviewer rechecks after reset.

Next action: Rerun independent SAW recheck after usage reset if formal milestone PASS is required; otherwise this worker slice is locally implemented and verified.

ClosureValidation: PASS
SAWBlockValidation: PASS
ClosurePacket: RoundID=DATA_PIT_ARTIFACT_20260512; ScopeID=strategy-replay-input-artifact; ChecksTotal=9; ChecksPassed=8; ChecksFailed=1; Verdict=BLOCK; OpenRisks=SAW recheck blocked by account usage limit after initial blockers were reconciled; NextAction=Rerun independent SAW recheck after usage reset if formal milestone PASS is required
