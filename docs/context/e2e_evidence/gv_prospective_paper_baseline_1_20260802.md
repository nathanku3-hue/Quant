# Evidence — GV Prospective Paper Baseline 1 — 2026-08-02

Mode: `EXECUTION_PACKET`

## Identity

- Base: `5687a2c2ae61ef8b5de676cffad5b19df9224b01`
- Capability candidate: `9c7e75ac3a7b87f85d505a53e759594dd1d07b9d`; historical broader test receipts remain bound to this SHA.
- Executable candidate: `147397f669c81eb2ab3bfd5054d676d9d0c9c77f`
- Executable tree: `a43a6a83549c7824b99f3db171451075a871f289`
- Branch: `repair/gv-prospective-paper-baseline-1-r1`; local and remote equal at the executable SHA.
- Repair: prospective bootstrap moved from future September dates to `2026-08-01`, allowing current-date operation.
- Accepted score before and after this implementation round: `62/100`
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

## Validation receipts

| Scope | Bound SHA | Result |
|---|---|---:|
| Current-tip prospective core + Streamlit product | `147397f` | reported `15/15 PASS` (`12` core, `3` UI) |
| Retained operated/25/App | `9c7e75a` | historical `23/23 PASS` |
| Scale persistence/timestamp repair | `9c7e75a` | historical `13/13 PASS` |
| Book/allocation/execution/replay/strategy/vertical | `9c7e75a` | historical `104/104 PASS` |
| Historical bounded/scale/universe/challenger | `9c7e75a` | historical `24/24 PASS` |
| Exact-SHA Windows/Linux hosted proof | `147397f` | `ABSENT` |

No broader current-tip rerun is claimed. Hosted proof is required before terminal publication, not before a bounded paper-product smoke or non-authoritative Learn-lane reconciliation.

## Evidence boundary

Automated tests inject runtime values. They prove software capability and deterministic authority boundaries, but they are not genuine prospective evidence. A manually operated episode on the synthetic 25-security profile proves usability, custody, and restartability only. No score uplift is claimed. The forward evidence gate is one real source set entering one real instrument decision and surviving confirmation, persistence, and replay.

## Roadmap disposition

```text
executable candidate `147397f`
→ minimal six-file authority correction
→ one fresh-home synthetic no-change smoke
→ concurrent MU/NVDA reconciliation
→ one real MU identity and classified cash
→ deterministic ABSTAIN/NO_POSITION or ADMIT preview/confirmation
→ append-only persistence and fresh-process exact replay
→ independent shadow proposal on the same evidence
→ repeated 3–5 real-security prospective operation
→ Universe custody when broader membership is required
→ separately authorized Limited Live
```

The obsolete slot/cell Challenger is not adapted; its replacement begins only after the real-evidence seam works. Australian legal review is not a blocker for paper baseline or paper shadow work. It remains mandatory before broker credentials, automated submission, client assets, advice activity, or real-capital operation.
