# Impact Packet — Current

Date: 2026-08-08
Gate: `PRE_SEAL_REAL_CIQ_ADMISSION`
Status: `WINNER/AUTHORITY RECUT DOCS PATCHED (~99/100); TOP-LEVEL DESIGN EFFECTIVELY CLOSED; V3 TEMPORAL + ADVERSARIAL AUTHORITY CLOSED LOCALLY; REAL CLOCK BLOCKED ONLY ON REAL CIQ SECURITY/TRADING + COMPLETED MARKET BYTES`

## Executable impact

Local commits created:

- `39f7be3894623c095994066b8f0ea2895b968643` — immutable Episode-2 executable/data/test candidate;
- `4b14846015c952242d4bf17819bc615435bda091` — destructive compatibility hard cut + AOV mechanical vertical;
- `dca69fc72dd3192913aa921323ff48f68610a925` — production insurance owner-decision boundary restored.

No push/hosted CI/main/tag/publication occurred.

## Hard-cut impact

Removed from current root authority:

- `alpha_app.py`;
- `launch_alpha.py`;
- `portfolio_app.py`;
- `launch_portfolio.py`;
- live root Alpha release build/smoke scripts;
- compatibility-only AppTests;
- legacy book projection;
- legacy/transitional dashboard authority.

Historical source was retained under `docs/archive/legacy_runtime_source/`; Alpha release truth is receipt integrity under `release/gv-alpha0/RECEIPT.json`.

## AOV/research impact

Touched authoritative executable interfaces:

- `dashboard.py`, `views/page_registry.py`;
- `gv_portfolio_v0/book.py`;
- `research/backtest_runner.py`, `benchmarks.py`, `strategy_cartridge.py`, `evidence_schema.py`;
- `research/adapters/rule100_replay_adapter.py`;
- new `research/aov0/*`;
- `scripts/aov_zero_compat_scan.py`;
- `scripts/aov0_first_seal.py`;
- AOV/research/product regression tests;
- future local/hosted workflow definitions.

Research behavior changed incompatibly by design: permanent IDs only, named benchmarks only, finite costs only, immutable evidence manifests, schedule-consistent PIT equal weight, no cash inconsistency tolerance. Active AOV permanent identity is specifically `CIQSEC:<Capital IQ Security ID>` and active risky-asset return authority is S&P Capital IQ Pro primary-security market data; legacy PERMNO/ticker/company-entity and dual-provider aliases are rejected. This round adds `research/aov0/ciq_market.py`, `scripts/aov0_build_ciq_market.py`, `scripts/aov0_fetch_nyfed_sofr.py`, and `scripts/aov0_build_decision_cut.py`: one bounded current-cut admission path from primary security/trading identity + total-return/price/volume bytes to the three risky-asset inputs, direct time-gated SOFR, and the exact cut envelope. Ambiguous identity, `<3` factor coverage, insufficient 200-day history, invalid market state, cross-entity identity collision, same-day U.S. daily retrieval before 16:00 ET, or a future-stamped source retrieval excludes/blocks rather than opening a fallback.

## Current blocker impact

Production insurance V0 remains frozen at materiality `0.05` and annual premium ceiling `0.0015`. Direct official SOFR is admitted. The former v2 open-execution contract remains immutable historical/mechanical evidence only and has no active reader/writer in the AOV runtime.

The former `run_2` retrieval-time, pre-admission SOFR, prior custody findings, destructive v3 temporal recut, and mandatory adversarial authority suite are closed locally. Active v3 uses `decision_cut_v3` / `seal_v3` / `clock_start_receipt_v1`, next-eligible 16:00 ET close evaluation, clock-false Seal Candidate construction, fresh-process verification proof, and a separate immutable Clock-Start Receipt. The sole remaining pre-clock blocker is real CIQ primary-security mapping plus completed post-16:00 ET market admission.

The earlier CRSP/PERMNO route is no longer an operational option: active AOV authority remains S&P Capital IQ Pro. The single `run_4.xlsx` object, SHA-256 `17f356e47c9e3ecf9600ad21db153338f4941272e0a1ffb9fd7b872c6636f056`, is now both the frozen 109-company universe receipt and current-cut quarterly-fundamentals receipt and normalizes into 1,203 absolute entity-quarter rows plus a 109-row current company-level factor state. `run_2.xlsx` is historical evidence only and is not an active decision-cut dependency. The current-cut limitation is preserved: the market builder uses historical market rows only as rolling-state warmup and emits no historical Rule100 target replay.

## Validation impact

- E2 exact `39f7be3`: `115/115 PASS` from archived commit bytes.
- AOV destructive v3 authority + adversarial suite: `75/75 PASS`; synthetic package proves clock-false Seal Candidate → actual fresh-process full-chain verification proof → separate immutable Clock-Start Receipt. Historical v2 remains baseline evidence only.
- Hardened research selected suite: `33/33 PASS`.
- Current dashboard/book/historical receipt: `33/33 PASS`.
- Hard-cut E2 regression: `107/107 PASS`.
- Historical Alpha runtime live checkout: `7/7 PASS`.
- ZERO-COMPAT: all seven counters zero, including archived/release executable-source import prohibition.
- Compile/YAML/`pip check`/whitespace: PASS.

## Documentation impact — 2026-08-08 Winner / authority recut

Latest roadmap verdict is `APPROVED_WITH_WINNER_AND_AUTHORITY_RECUT` at ~99/100 after recuts; prior strategic and sim-to-real decisions are retained and top-level design is effectively closed. The active execution gate remains exactly `PRE_SEAL_REAL_CIQ_ADMISSION`. This docs-only round preregisters `CYCLE_RESONANCE_v1` as `PREREGISTERED / NOT IMPLEMENTED`, recuts the Right-Tail Atlas to Minimum-Viable-Atlas-first, freezes capital-weighted right-tail capture per unit capital-time as the deeper CIO metric, adds the system-wide Destructive Authority Replacement Law, collapses owner governance to six constitutions, and chooses one incumbent at each implementation fork. No provider fetch, historical Atlas build, AI/source pipeline, real CIQ admission, real seal, broker execution, publication, commit, push, or live-capital action occurred.

After Clock #1 the first Alpha lane is `CYCLE_RESONANCE_v1`: enough legitimate PIT history for honest discovery/controls → freeze family/implementation/falsifiers/search budget → untouched PIT evaluation where available → seal prospectively as soon as honest, while deeper risk-set/false-winner/replication work continues under the running clock. Independent Ops/Engineering simultaneously runs the thin Alpaca PAPER Capitalization Vertical at `financial_alpha_evidence=0`; initial execution incumbent=`MOC_CLOSE_AUCTION_V1 = market + cls`. Required closure remains one promoted policy/seal→one `live_rebalance_id`, PIT `CIQSEC`↔broker account/instrument map, full broker lifecycle/open-orders, broker-first restart reconciliation + rebalance fencing + persistent `FREEZE_NEW_RISK`, and dual-ledger implementation-shortfall/fees/timing/cash-drag attribution. Existing broker submit/recovery, reconciliation quarantine, signed replay, and deterministic event/book/replay primitives are reused; no second OMS.

## Claim boundary

Canonical maturity remains `70/100`; portfolio-alpha evidence remains `0`. Prior architecture/scientific-bar, strategic and sim-to-real approvals remain valid; latest owner alignment=`~99/100`, verdict=`APPROVED_WITH_WINNER_AND_AUTHORITY_RECUT`, top-level design effectively closed. Execution gate remains `PRE_SEAL_REAL_CIQ_ADMISSION`: destructive v3 temporal authority and adversarial tests are closed locally, while real CIQ admission remains open. `CYCLE_RESONANCE_v1` preregistration creates no alpha evidence. Calibration=`INSUFFICIENT` (one historical row), not `DRIFT`. Compute performance is non-blocking. No real A1/A3, broker execution, or live-capital claim.
