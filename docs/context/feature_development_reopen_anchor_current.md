# Feature Development Reopen Anchor - Current

Status: Current
Authority: advisory-only feature-development anchor. This file does not authorize live trading, broker automation, investment recommendations, ranking, scoring, action alerts, provider refresh during boot, replay-output certification, or scope widening by itself.

## Round

- `RoundID`: `ROUND-20260528-FEATURE-DEVELOPMENT-REOPEN-ANCHOR`
- `ScopeID`: `SCOPE-SAFE-BOOT-GREENBASELINE-AND-FEATURE-GUARDRAILS`
- `Verdict`: `PASS_WITH_NOTES`
- `TargetBranch`: `codex/optimizer-core-structured-diagnostics`
- `TargetHEAD`: `adf882d9409e76ab7b3a65ae98e6df3e14233ac1`

## Baseline Truth

- `SafeBoot`: `TRUE`
- `RuntimeStatus`: `ready`, generated through strict preflight only, ignored and untracked.
- `GovernanceGateV0`: `PASS`
- `BootStatusPathContract`: `PASS`
- `DataReadinessGate`: `PASS`
- `ContextPacketValidation`: `PASS`
- `PortfolioAppTestSmoke`: `PASS`
- `FocusedReplayDashboardContract`: `PASS`
- `ExecutionInventoryGate GOV-009`: `PASS`
- `ReplaySelection`: `CERTIFIED`
- `ReplayOutput`: `UNCERTIFIED_OUTPUT_NOT_CLAIMED`

## Reopen Decision

Research-only feature development may resume from the target branch under strict pre/post checks. This does not clear live execution, investment recommendations, scoring, ranking, action alerts, autonomous allocation, provider refresh during boot, or replay-output certification.

Manual execution scripts remain classified outside default boot and are not importable or reachable from the `safe_boot` runtime. Any future branch that imports, calls, renames, relocates, exposes, or relaxes those scripts must reopen GOV-009 and strict boot validation.

## Feature Lanes

### Green Lane

Allowed as research-only work with normal governance checks:

- research-only candidate-card reader
- market-behavior signal card scaffolding
- dashboard research-state views
- rendered dataframe/AppTest governance expansion
- data provenance and manifest UX
- context packet improvements
- safe boot status display
- research-only portfolio/replay evidence displays
- research lab feature flags

### Yellow Lane

Allowed only with explicit governance tests and label scans:

- optimizer or allocation UI changes
- replay output displays
- dashboard labels and table columns
- scoring-like or ranking-like fields, even when renamed
- provider ingestion or export/download artifacts
- ops-health alert surfaces

Required evidence: governance scanner update when labels change, rendered AppTest scan for UI output, boot preflight compatibility, research-only allowed-use and forbidden-use evidence, and no broker/order path activation.

### Red Lane

Not clear under this anchor:

- live trading
- broker/order execution
- `submit_order` or rebalance flows
- investment action alerts
- BUY/SELL/HOLD recommendations
- ranked default dashboard lists
- certified replay-output claims
- autonomous allocation
- provider refresh during boot

## Mandatory Branch Checks

Before a feature branch starts:

```powershell
git checkout codex/optimizer-core-structured-diagnostics
git pull --ff-only
git checkout -b codex/<small-scope-name>
E:\Code\Quant\.venv\Scripts\python.exe scripts\governance_preflight.py --repo-root . --json
E:\Code\Quant\.venv\Scripts\python.exe scripts\boot_preflight.py --repo-root . --mode strict --require-github --smoke --run-focused-contract
```

Before merge:

```powershell
E:\Code\Quant\.venv\Scripts\python.exe -m pytest tests\test_boot_status_contract.py tests\test_boot_preflight.py tests\test_boot_preflight_governance.py tests\test_data_readiness_gate.py tests\test_data_readiness_gate_write_guard.py -q
E:\Code\Quant\.venv\Scripts\python.exe scripts\governance_preflight.py --repo-root . --json
E:\Code\Quant\.venv\Scripts\python.exe scripts\boot_preflight.py --repo-root . --mode strict --require-github --smoke --run-focused-contract
```

Regenerate `runtime/boot_status_current.json` only after target-branch validation, not inside ordinary feature branches.

## Open Risks

- Replay output remains intentionally uncertified until a real replay-output artifact has its own certificate.
- Manual execution scripts remain classified outside default boot, not removed.
- Certification refresh is required by `2026-06-11`.
- Any future broker/order/alert/recommendation/scoring/ranking work must reopen the relevant governance gate.

## Next Action

Resume research-only feature development from the clean target branch. Preferred next choices are rendered dataframe/AppTest governance expansion for safety or a G9 market-behavior signal card for product momentum.
