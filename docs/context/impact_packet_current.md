# Impact Packet — Current

Date: 2026-08-01
Phase: `GV-ENGINE-SCALE-CHARACTERIZATION-1`
Status: `FROZEN_FINDING; REVIEW_BLOCKED`

## Product impact

No new product capability is accepted. Diagnostic candidate `f9d271d2a67eca9d08bcc01fb3a5bf342bd8d283` is frozen and remote-equal. Synthetic 50/100 scenarios execute through the existing engine in memory, but neither can use the existing persistence/product path. Accepted progress remains `62/100`.

## Changed implementation surfaces

- `gv_portfolio_v0/operated_scenarios.py` — adds declarative 50/100 synthetic diagnostic inputs only.
- `scripts/characterize_gv_engine_scale.py` — fresh-process measurement and unchanged-persistence probe.
- `tests/gv_portfolio_v0/test_engine_scale_characterization.py` — scenario identity, existing-engine operation, deterministic repeat, persistence stop, timestamp stop, and accepted-25 non-mutation checks.

No engine selection, execution, accounting, replay, certification, correction, storage, application, view, workflow, dependency, broker, provider, or live-capital logic is changed.

## Evidence impact

- 50: 6.43–6.45 seconds, 30.1–30.3 MB peak working set, 48 events, 18 orders/fills, residual `0`, repeat hashes equal.
- 100: 11.77–11.96 seconds, 32.3–32.4 MB peak working set, 80 events, 34 orders/fills, residual `0`, repeat hashes equal.
- Both: existing persistence rejects the scenario ID before write.
- 100: 40 malformed timestamps from `12:60` to `12:99`.

## Documentation impact

The active brief, top-level roadmap, current truth surfaces, evidence packet, custody decision, handover, decision log, lesson log, and SAW report classify P1 as a frozen diagnostic finding with SAW BLOCK because independent Reviewer A/B/C and current hierarchy confirmation are unavailable. P0 terminal custody and score remain unchanged.

## Open impact

A later bounded repair would touch shared persistence naming/root selection and initial evidence timestamp generation. That repair is not included here. P2, Universe acceptance, Challenger, broker integration, and Limited Live remain closed.
