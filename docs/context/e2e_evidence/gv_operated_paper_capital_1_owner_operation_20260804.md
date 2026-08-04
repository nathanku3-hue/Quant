# GV Operated Paper Capital 1 — Owner Operation Evidence

Date: 2026-08-04
Gate: `GV-OPERATED-PAPER-CAPITAL-1`
Base: `2d95cdf9e033f7d8b6f1d9c18aea2e46bed6ec72`
Custody branch: `codex/gv-operated-paper-capital-1-custody`
Custody worktree: `/mnt/e/Code/Quant/.worktrees/gv-operated-paper-capital-1-custody`

## Operation

The production `dashboard.py` Command Center interaction surface was exercised with a
fresh owner-authored packet after the isolated-custody hardening pass. The packet was
not copied from the fixture request used by unit tests. In-app browser control was
unavailable because the browser runtime rejected the WSL-mounted sandbox cwd; the
equivalent production Streamlit Command Center `AppTest` surface was used and the
limitation is recorded here rather than hidden.

Owner packet:

- Evidence content: `Owner review 2026-08-04: the supplied MU packet supports a bounded paper entry for this exact episode; this remains an owner assertion, not provider evidence.`
- Source locator: `operator://2026-08-04/mu/owner-packet-20260804-01`
- Evidence observed at: `2026-08-04T14:01:00.000000Z`
- Market price: `101.25`
- Market observed at: `2026-08-04T14:00:00.000000Z`
- Market source identity: `operator://2026-08-04/mu/owner-market-20260804-01`
- Target quantity: `7`
- Net score: `575` bps
- Principal claim: `Owner confirms the packet supports one bounded MU paper position; no live or broker authority is requested.`
- Operator rationale: `I explicitly authorize the reviewed seven-unit paper target at the owner-identified market observation, using only certified available cash; this decision is not provider-verified and does not authorize live capital.`

The packet persisted the typed PIT identity tuple:

- Certified book ID: `074a47c7cdb7755a34c1d257e4e2ff99552cf9419033828b304cc5cf16016c22`
- Certified book head event ID: `EVT_9e7435f4b14d9cfb2b0220129a8515b034926c89394dd096564585a727b2efc1`
- Evidence set ID: `a50ed0441a3f8811374159c1a922dddfa1312e194d7e1576ce7b111fc6eb6a30`
- Market snapshot kind: `NO_MARKET_DEPENDENCY_CASH_ONLY_V1`
- PIT as-of: `2026-08-02T12:06:00.000000Z`

## Results

- Preview rendered `Mutation-free paper-capital preview` and the persisted workspace file bytes were unchanged before confirmation.
- Explicit confirmation rendered the changed certified book and `Certified paper fills`.
- Confirmed episode count: `1`; event count: `10`.
- Confirmed position: `7` units of the MU instrument at valuation/fill price `101.25`.
- Available classified cash: `9289.25`; total classified costs: `2`.
- Unexplained residual: `0`.
- Certification ID: `CRT_0463f7c8adf920d79de19739f65f57852ddeba9c0e2eaee59a03f4a24c61b53f`.
- Resulting book hash: `ddfdd7aed7cef0b272e3ec420e629b078f8f1f3f1ceed885aafa25758a50957e`.
- Persisted workspace file: `C:\Users\Lenovo\AppData\Local\Temp\gv-owner-final-8ewfugtb\operated_portfolio_scenario_28a2a139a248e7e9e63ed6d11f3d1fd48ce8c595676f8fee24c230f7ab373861.json`.
- Workspace file SHA-256: `a844721cef80f030a945dcbf7959cc99aa830203b3c6e27266cefa312454a35f`.
- Canonical workspace SHA-256: `ebdab5f3b6a920aae6542942721784a64f562b0e8504df8ed0a04bffb7856bc4`.
- Persisted baseline book hash: `074a47c7cdb7755a34c1d257e4e2ff99552cf9419033828b304cc5cf16016c22`.

## Fresh-process reopen

A separate Python 3.12 process loaded the persisted workspace and reconstructed it from
the event log. The canonical reconstructed workspace hash matched the loaded workspace
hash exactly:

`ebdab5f3b6a920aae6542942721784a64f562b0e8504df8ed0a04bffb7856bc4`

The separate process reproduced certification ID `CRT_0463f7c8adf920d79de19739f65f57852ddeba9c0e2eaee59a03f4a24c61b53f`, book hash
`ddfdd7aed7cef0b272e3ec420e629b078f8f1f3f1ceed885aafa25758a50957e`, 7-unit position,
available cash `9289.25`, costs `2`, and residual `0`.

This is bounded paper authority only. It is not provider verification, investment advice,
broker authority, live capital, or a score uplift; the accepted product score remains
`62/100`.
