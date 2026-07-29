# Impact Packet — Current

## Active — Micro-portfolio candidate plus replay implementation (2026-07-29)

### Product impact

- complete four-security operator loop under `gv_portfolio_v0`;
- principal, substitute, rejected competitor, abstained alternative, benchmark, and classified cash;
- thesis/scenario review, deterministic capital competition, aim, order/fill, certification, persist/reopen, and later WATCH explanation;
- broker-free Streamlit workspace.

### Truth and accounting impact

- `contracts/gv_portfolio/v0/**` owns permanent IDs and exact-byte evidence references;
- `core/gv_portfolio_v0/**` owns immutable canonical event custody;
- `gv_portfolio_v0/vertical.py` delegates exercised custody primitives and owns product orchestration;
- one value-preserving 2:1 split; terminal NAV 1499; unexplained split residual zero;
- missing valuation yields `VALUATION_PENDING` and null NAV.

### Replay impact

- exact state reconstruction from real Slice 0 events;
- duplicate-delivery idempotence;
- correction lineage and partial-fill residual state;
- prior certification byte stability;
- structural audit receipts remain non-authorizing without provider verification;
- the CLI verifies GitHub reviewer identity and exact remote report bytes before certification.

### Verification impact

- exact pinned environment reproduced;
- portfolio/replay suite: 34/34 PASS;
- provider-free focused matrix: 278/278 PASS;
- current-authority tests reject stale FS0-first queue language;
- runtime persist/reopen/replay smoke: PASS.

### Custody impact

The candidate is not terminally accepted until committed, pushed, remote-equal, clean, and independently audited. Released FS0/Alpha runtime remains unchanged. The dirty root checkout remains untouched.

### Open risk

Independent Reviewer A/B/C receipts do not yet exist. Replay certification and bounded portfolio therefore remain blocked.
