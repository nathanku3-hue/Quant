# Evidence — GV Prospective Paper Baseline 1 — 2026-08-02

Mode: `EXECUTION_PACKET`

## Identity

- Base: `5687a2c2ae61ef8b5de676cffad5b19df9224b01`
- Capability candidate: `9c7e75ac3a7b87f85d505a53e759594dd1d07b9d`; historical broader test receipts remain bound to this SHA.
- Executable candidate: `147397f669c81eb2ab3bfd5054d676d9d0c9c77f`
- Executable tree: `a43a6a83549c7824b99f3db171451075a871f289`
- Authority synchronization: `dc6b022639a1fc8198c6a1b4109c80a700e2a609`, tree `a9735c2bcc9d2b2012a47b7f1ffbe0058c2293cf`.
- Real-evidence candidate: `ae615a237a2b5d62547d983b040ca8dd88248b98`, tree `4bc827abf504d063b41053e11e4ed6f192cb52c7`.
- Hosted-green closure: `d84c67557bf57a0a40b59a2a63b3ef2de2544261`, tree `63206de348c30584b8e8dbe5ddc7e41c5032567b`.
- Branch: `repair/gv-prospective-paper-baseline-1-r1`. Date-repair authority remains ancestor `147397f`; real-evidence code remains `ae615a2`; `d84c675` closes authority and generated context.
- Repair: prospective bootstrap moved from future September dates to `2026-08-01`, allowing current-date operation.
- Accepted score before and after this implementation round: `62/100`
- Nonbinding expected score after local real-evidence seam: `66–68/100`
- Real-evidence bytes are committed and pushed at `ae615a2`. Closure `d84c675` is fully green on Ubuntu and Windows in run `30750709296`. Genuine human operation and independent acceptance remain open.
- Limited Live: `CLOSED; NOT_AUTHORIZED`

## Product capability

The environment-selected operated app now supports one prospective 25-security profile derived from the accepted 25-security catalogue. The operator supplies runtime observation content, source locator, UTC timestamp, instrument ownership, explicit review proposals, and rationale. The system validates and previews the proposal without mutating persisted authority. The operator then confirms or rejects.

Confirmed episodes append evidence, review/thesis state, observation, decision snapshot, transition and execution when required, and certification. Rejected episodes append rejection custody and recertification but do not admit evidence or mutate reviews, snapshots, holdings, cash, orders, fills, or book economics.

## Episode coverage

### Episode 1 — confirmed no-change

- One runtime observation for one instrument.
- Explicit review proposal remains economically identical.
- Preview is non-authoritative and leaves persisted bytes unchanged.
- Confirmation appends observation and certification.
- Holdings, cash, orders, fills, NAV, residual, and book hash remain unchanged.

### Episode 2 — confirmed transition

- One runtime observation owns Harbor and Meridian.
- Explicit operator proposals reduce Harbor and fund Meridian.
- Preview derives one SELL/REDUCE and one BUY/FUND leg.
- Confirmation executes the transition, records costs, certifies, persists, and reopens.
- Residual remains `0`.

### Episode 3 — rejected proposal

- One runtime proposal is previewed and explicitly rejected.
- Rejection event and certification are append-only.
- Evidence, reviews, decision snapshots, holdings, cash, orders, fills, and book authority remain unchanged.
- Rejected proposal and rationale remain reconstructable.

## Authority rules

- Per-security review outcomes: `ADMIT`, `REJECT`, `ABSTAIN`.
- `CASH` is a portfolio capital candidate, not a per-security outcome.
- Non-`ADMIT` target quantity must be `0`.
- Score, quantity, thesis, and outcome are proposals until deterministic validation and explicit confirmation.
- Runtime observation content is absent from scenario code.
- Repeated state is reconstructed from one append-only event log rather than fixed scenario-authored status/count branches.

## Local execution receipts

### Machine-executed synthetic operability smoke

- Fresh `GV_OPERATED_PORTFOLIO_HOME`.
- Preview persisted bytes unchanged: `true`.
- Episode count: `1`; operator actions: `2`.
- Holdings, orders, fills, economics, and book hash unchanged.
- Event tail: `LATER_OBSERVATION_ADMITTED`, `CERTIFICATION_RECORDED`.
- Source locator and operator rationale reconstruct exactly.
- Separate-process exact workspace reconstruction: `true`.
- Classification: machine-executed usability, custody, and restartability only; not a genuine human episode and no product-score uplift.

### MU/NVDA Learn-lane reconciliation

- Source families: MU official filing `SEC:0000723125-26-000015`; NVDA independent filing `SEC:0001045810-26-000052`.
- Corroboration: `PARTIAL_INDIRECT` for a broad memory-price and supply-constrained environment.
- Contradiction: `NO_DIRECT_CONTRADICTION_IDENTIFIED`.
- Disposition: `HOLD`; research action: `HOLD_FOR_EVIDENCE`; portfolio action: `NO_POSITION`.
- Missing discriminator: independent Micron-specific physical supply evidence with point-in-time custody across more than one period.
- Reconciliation hash: `89cc062783ae367c1bf259cfb7b355e0812ca162995b7ce05743a39e99592017`.
- Boundary: no network/provider work, score, rank, alpha, investability, trade recommendation, or portfolio mutation.

### Machine-executed real MU evidence-to-portfolio receipt

- Real identity namespace: `SEC_CIK_LISTING_V1`.
- Permanent key: `SEC_CIK:0000723125:NASDAQ:MU:COMMON_STOCK`.
- Outcome: `ABSTAIN`; target quantity: `0`; portfolio action: `NO_POSITION`.
- Preview persisted bytes unchanged: `true`; preview authoritative: `false`.
- Episode count: `1`; operator actions: `2`.
- Classified cash: AVAILABLE `10000`, RESEARCH_RESERVE `1000`.
- Positions: `0`; orders: `0`; fills: `0`; NAV: `11000`; residual: `0`.
- Book hash before and after: `074a47c7cdb7755a34c1d257e4e2ff99552cf9419033828b304cc5cf16016c22`.
- Certification: `CRT_c8e44e6fc1c18de406eefd5f076b4bdc2a5e14d2424306a0a2df456b80153ada`.
- Separate-process exact reconstruction: `true`.
- Workspace/reconstructed SHA-256: `59f75a10875add2dcd8d4018f6c3952955a33da4c20da56e9769b3df1abec980`.
- Classification: product-seam capability and deterministic restart evidence; not human operation, research-quality proof, or market-facing prospective evidence.

## Validation receipts

| Scope | Identity | Result |
|---|---|---:|
| Current-tip prospective core + Streamlit product | `147397f` | reported `15/15 PASS` (`12` core, `3` UI) |
| Local reconciliation + real MU + retained prospective/UI | `ae615a2` candidate tree | `24/24 PASS` |
| Full operated-portfolio package | `ae615a2` candidate tree | `185/185 PASS` |
| Full FS0 product package | `ae615a2` candidate tree | `268/268 PASS` |
| Context and hygiene tests | documentation working tree | `33/33 PASS` |
| MU official-source + NVDA independent-source + reconciliation | `ae615a2` candidate tree | `32/32 PASS` |
| Static compilation and whitespace check | `ae615a2` candidate tree | `PASS` |
| Retained operated/25/App | `9c7e75a` | historical `23/23 PASS` |
| Scale persistence/timestamp repair | `9c7e75a` | historical `13/13 PASS` |
| Book/allocation/execution/replay/strategy/vertical | `9c7e75a` | historical `104/104 PASS` |
| Historical bounded/scale/universe/challenger | `9c7e75a` | historical `24/24 PASS` |
| Exact-SHA Windows/Linux proof | `147397f`; runs `30740333853`, `30748842695` | `PASS` |
| Authority-sync hosted suite | `dc6b022`; run `30749002860` | `484 passed, 2 skipped`; generated context stale |
| Real-evidence hosted suite | `ae615a2`; run `30750230766` | product/tests pass; generated context stale |
| Hosted-green closure | `d84c675`; run `30750709296` | Ubuntu/Windows `PASS`; context valid; tracked bytes unchanged |
| Genuine human smoke episode | not run | `ABSENT` |
| Independent terminal review for new slice | not run | `ABSENT` |

Hosted and independent proof remain required before terminal publication or accepted-score movement.

## Evidence boundary

Automated tests and machine-executed receipts prove software capability and deterministic authority boundaries. No genuine human episode has been banked. The real MU receipt proves that already-banked real source evidence can enter a real identity, reach the explicit confirmation boundary for a cash-only decision, persist, and replay exactly. It does not prove human operability, research quality beyond bounded `HOLD_FOR_EVIDENCE`, repeated prospective performance, alpha, investability, or live readiness. Accepted score remains `62/100`; the evidence supports only a nonbinding `66–68/100` reassessment range.

## Roadmap disposition

```text
hosted-green real-evidence closure `d84c675`
→ genuine human smoke episode
→ independent terminal review
→ independent shadow proposal on the exact same evidence
→ repeated 3–5 real-security prospective operation
→ Universe custody when broader membership is required
→ separately authorized Limited Live
```

The obsolete slot/cell Challenger is not adapted; its replacement begins only after the real-evidence seam works. Australian legal review is not a blocker for paper baseline or paper shadow work. It remains mandatory before broker credentials, automated submission, client assets, advice activity, or real-capital operation.
