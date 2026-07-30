# Observability Pack — Current

## Active — terminal repair and repository-custody sentinels (2026-07-30)

- **Authority sentinel:** `docs/context/ACTIVE_BRIEF` selects `phase0-gv-micro-portfolio-vertical-0-brief.md`.
- **Base sentinel:** repair derives from remote-equal `9ebc973a8cc3cfbd4899ed724733cc22c606fbbf`.
- **Scope sentinel:** Product and Replay implementation are read-only; only Integrator/Accounting/Strategy invariants, stale test authority, and checkout custody changed.
- **Package sentinel:** unchanged `requirements.lock`, Python 3.12.10, and `pip check` PASS.
- **Affected-test sentinel:** portfolio 92/92; context + protocol 175/175; legacy product 263/263.
- **Collection sentinel:** 2664 tests across 201 files.
- **Checkout sentinel:** hash-bound text must resolve to LF; parquet/raw artifacts remain binary.
- **Full-suite sentinel:** LF-preserving clean clone = 2598 passed, 16 skipped, 50 failed.
- **Replay-custody sentinel:** G4 manifest embeds `E:\Code\Quant`; G4/G5/G6 are non-relocatable and remain read-only.
- **Artifact sentinel:** missing generated parquet/evidence files must not be mistaken for missing Python dependencies.
- **Review sentinel:** local role-separated audit is not independent A/B/C; GitHub exposes no inherited status checks.
- **Product sentinel:** score 39; observed 0; no alpha, broker, or live-capital claim.
- **Drift sentinel:** do not reopen Product features, Replay implementation, providers, optimizer, graph, adaptive execution, broker, score uplift, or live capital.

## Rating

- **GREEN:** affected slice gates, lock installation, adversarial invariant probes, stale legacy classification, LF fixture checkout authority.
- **AMBER:** repair commit publication and remote equality.
- **RED:** full repository suite and independent A/B/C acceptance.
