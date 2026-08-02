# Evidence — GV Prospective Paper Baseline 1 — 2026-08-02

Mode: `EXECUTION_PACKET`

## Identity

- Base: `5687a2c2ae61ef8b5de676cffad5b19df9224b01`
- Candidate: `9c7e75ac3a7b87f85d505a53e759594dd1d07b9d`
- Candidate tree: `20d5eb712799555003b2efcf6aed96ca89db9f67`
- Branch: `product/gv-prospective-paper-baseline-1`; local and remote equal at the candidate SHA.
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

| Scope | Result |
|---|---:|
| Prospective core | `11/11 PASS` |
| Prospective Streamlit product | `3/3 PASS` |
| Retained operated/25/App | `23/23 PASS` |
| Scale persistence/timestamp repair | `13/13 PASS` |
| Book/allocation/execution/replay/strategy/vertical | `104/104 PASS` |
| Historical bounded/scale/universe/challenger | `24/24 PASS` |

All reported runs used Python 3.12. The repository emits an inherited `PytestConfigWarning` for unknown `cache_dir`; it does not affect test outcomes.

## Evidence boundary

Automated tests inject runtime values. They prove the software capability and deterministic authority boundaries, but they are not genuine prospective evidence. No score uplift is claimed. Three real operator-supplied episodes remain required before prospective baseline acceptance and real shadow Challenger opening.

## Roadmap disposition

```text
frozen remote candidate `9c7e75a`
→ exact-SHA hosted CI
→ three genuine operator-supplied episodes
→ real shadow Challenger on the same certified 25-security set
→ Universe custody when broader membership is required
→ separately authorized Limited Live
```

Australian legal review is not a blocker for paper baseline or paper Challenger work. It remains mandatory before broker credentials, automated submission, client assets, advice activity, or real-capital operation.
