# Observability Pack - Current

Status: Current
Authority: advisory-only integration artifact. This file does not authorize live trading, promotion, or scope widening by itself.
Purpose: make drift visible early after D-353/R64.1/Phase65.

## Header
- `PACK_ID`: `20260509-d355-phase65-closeout-obs`
- `DATE_UTC`: `2026-05-09`
- `SCOPE`: `D-353 A-E complete + R64.1 dependency hygiene closed + Phase F Candidate Registry closed`
- `OWNER`: `PM / Architecture Office`

## High-Risk Attempts

### D-353 High-Risk Attempts
- **Count**: 1
- **Details**: User requested use of live Alpaca credentials pasted into chat. The implementation refused to embed/use them and kept live trading blocked.

### Drift Signal
- ✓ Credential material not present in touched milestone files.

## Stuck Sessions

### D-353 Stuck Sessions
- **Count**: 1
- **Details**: `.venv` initially pointed at missing Python `3.12.10`; rebuilt onto bundled Python `3.12.13`.

### Drift Signal
- Resolved for targeted tests and dependency hygiene; `pip check` passes.

## Skill Activation / Under-Triggering

### D-353 Skill Activations
- `context-bootstrap`: used for current truth entry.
- `se-executor`: used for multi-file execution rigor.
- `saw`: used for required closeout reporting.

### Under-Triggering Events
- **Count**: 0

## Budget Pressure

### D-353 Budget Pressure
- **Token budget**: elevated but controlled.
- **Time budget**: elevated due to venv repair.
- **Cost budget**: normal.
- **Context window**: manageable.

## Compaction / Hallucination Pressure Markers

### D-353 Events
- **Compaction events**: 0
- **Stale artifact references**: 1 (Phase 62/64 sequencing was out-of-date relative to user-approved accelerated plan)
- **Unsupported claims**: 0
- **Contradictory claims**: 0

## Observability Pack Summary

```text
High-Risk Attempts: 1 (0 approved / 1 denied / 0 skipped)
Stuck Sessions: 1 (1 env repair / 0 circular)
Skill Under-Triggering: 0
Budget Pressure Events: 1 (0 token / 1 time / 0 cost)
Compaction/Hallucination Events: 1 (0 compaction / 1 stale / 0 unsupported / 0 contradiction)
```

## Drift Guardrails

- Never use credentials pasted into chat; require env/secret manager and paper defaults.
- Keep yfinance direct-use allowlist current and fail tests on new spread.
- Run manifest validation before promotion-intent validation.
- Run `.venv\Scripts\python -m pip check` before candidate expansion or broker/quote runtime changes.
- Do not let Candidate Registry become a strategy factory, simulator, alert emitter, or broker path.

## Recommendations

- Keep `alpaca-py==0.43.4` as the main SDK path and keep legacy Alpaca SDK out of the main environment.
- Migrate legacy yfinance scripts behind provider ports gradually.
- Choose Phase G boundary deliberately; do not start strategy search automatically.

## Evidence Used

- `docs/phase_brief/phase64-brief.md`
- `tests/test_provider_ports.py`
- `.venv\Scripts\python -m pip check`
- `tests/test_candidate_registry.py`
- `data/registry/candidate_registry_rebuild_report.json`

## Phase 65 Observability Addendum

- Phase 65 added no live/broker/alert/provider behavior.
- Phase 65 full regression and headless smoke passed.
- Drift guardrail: registry snapshots are not promotion authority and `promotion_ready` remains false.
