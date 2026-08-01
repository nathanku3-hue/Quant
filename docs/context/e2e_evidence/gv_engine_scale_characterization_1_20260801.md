# GV Engine Scale Characterization 1 — Evidence

Date: 2026-08-01
Mode: `CLOSURE_REPORT`
Status: `FROZEN_FINDING; REVIEW_BLOCKED`
Branch: `codex/gv-engine-scale-characterization-1`
Base: `e564cd9dfa45eb02ef8d7eb94b662543fb3776c9`
Diagnostic candidate: `f9d271d2a67eca9d08bcc01fb3a5bf342bd8d283`
Diagnostic tree: `e048f2483c64fcf7a9cae58e8454b70d7e993e78`
Remote equality: PASS
Accepted score: `62/100`
Terminal tag: `gv-operated-portfolio-25-1-terminal` unchanged

## Claim boundary

This packet characterizes the existing engine with synthetic 50- and 100-security declarations. It is not Portfolio Scale acceptance, Universe Scale acceptance, historical universe custody, challenger evidence, alpha evidence, legal clearance, or live-capital authority.

## Method

- Added only declarative synthetic scenarios to the existing scenario registry.
- Used the accepted engine for draft, initial confirmation, no-change, transition, correction, validation, accounting, replay, and canonical hashes.
- Ran each size twice in separate Python processes.
- Polled child-process peak working set externally.
- Probed the existing persistence implementation without modifying it.
- Parsed every timestamp-like field using ISO 8601 parsing.
- Stopped when shared persistence and engine timestamp behavior required repair.

Primary harness:

```text
python scripts/characterize_gv_engine_scale.py --sizes 50 100 --runs 2 --output <ignored-output.json>
```

## 50-security measurements

| Measure | Run 1 | Run 2 |
|---|---:|---:|
| Wall-clock | 6.431448 s | 6.447865 s |
| Peak working set | 30,105,600 bytes | 30,273,536 bytes |
| Funded positions | 17 | 17 |
| Events | 48 | 48 |
| Orders | 18 | 18 |
| Fills | 18 | 18 |
| NAV | 21964 | 21964 |
| Unexplained residual | 0 | 0 |
| Timestamp issues | 0 | 0 |

Canonical identities were equal across both fresh processes:

```text
scenario_hash         ac8c71fecb4b069c127a3f7db28b475a61f8161c8b1b95ac218b3c796964a656
canonical_state_hash  aa2d5bb30d8e544bb75ec654a9c565f48e6bd602169d6a01f9bace89a6225176
canonical_event_hash  efac2ad8b9edb04eb9632876d65e042174026f584589fd9205dfa8bf4faabcb0
book_hash             374cccb00da80b3cd71e91031b516d34dc15b7077147f911c2f0deaad172468f
```

The persistence probe failed before any workspace write:

```text
OperatedPortfolioError:UNKNOWN_OPERATED_SCENARIO:GV_ENGINE_SCALE_CHARACTERIZATION_50
```

## 100-security measurements

| Measure | Run 1 | Run 2 |
|---|---:|---:|
| Wall-clock | 11.765482 s | 11.956654 s |
| Peak working set | 32,280,576 bytes | 32,395,264 bytes |
| Funded positions | 33 | 33 |
| Events | 80 | 80 |
| Orders | 34 | 34 |
| Fills | 34 | 34 |
| NAV | 43932 | 43932 |
| Unexplained residual | 0 | 0 |
| Timestamp issues | 40 | 40 |

Canonical identities were equal across both fresh processes:

```text
scenario_hash         a0e26b72c1222ffed2c5546f9a7fd1929703a5e9a35afa3687095a74837daeb2
canonical_state_hash  7b5f6674bb48fbbacb25728810fb696269a1541e62da6d681d9117088086a335
canonical_event_hash  99276818913b5d0ef31f7497879c0c891068aca6f4aace220b4816b4a68067f4
book_hash             1c6dc9550483d9c81b0468b89ede6657abd31e95faaf3a0177c0bce7b26fbf83
```

The first invalid timestamp was:

```text
root.evidence_references[60].observed_at=2026-09-01T12:60:00.000000Z
```

The invalid range continues through `12:99`, yielding 40 malformed timestamps.

The persistence probe also failed before any workspace write:

```text
OperatedPortfolioError:UNKNOWN_OPERATED_SCENARIO:GV_ENGINE_SCALE_CHARACTERIZATION_100
```

## Acceptance matrix

| Check | 50 | 100 |
|---|---|---|
| Existing engine completes in memory | PASS | PASS |
| Fresh-process scenario/state/event/book equality | PASS | PASS |
| Unexplained accounting residual `0` | PASS | PASS |
| Valid timestamps | PASS | FAIL |
| Existing persistence supports scenario | FAIL | FAIL |
| Exact save/reopen | NOT REACHED | NOT REACHED |
| Correction after fresh-process reopen | NOT REACHED | NOT REACHED |
| Product UI operator path | NOT EXECUTABLE | NOT EXECUTABLE |
| Universe acceptance | NOT CLAIMED | NOT CLAIMED |

## Required stop

Two changes would be required to continue:

1. shared persistence must derive safe scenario-specific paths instead of hard-coding only 10 and 25; and
2. initial evidence times must advance as real timestamps rather than treating every index as a minute in one fixed hour.

Both alter accepted shared behavior. The spike therefore ends with a finding and does not implement either repair. The implementation/test candidate is immutable at `f9d271d`; it is not accepted product evidence.

## Focused validation

```text
python -m pytest -q \
  tests/gv_portfolio_v0/test_engine_scale_characterization.py \
  tests/gv_portfolio_v0/test_operated_25.py
```

Result: PASS. Additional split regression groups covering the shared operated product, accounting/replay substrate, legacy scale/universe/challenger paths, FS0 authority, and context generation also pass. Combined calls lost to DevSpace HTTP 502 were discarded and not counted.

## Review disposition

Local implementation and validation evidence is complete, but independent Reviewer A/B/C cannot be run through the currently exposed tool surface. The persisted hierarchy fallback is stale for the new scale/custody scope. SAW therefore returns BLOCK rather than fabricating independent review.

The retained 25-security regression remains green. No terminal tag was moved. No Universe, Challenger, Limited Live, provider, optimizer, or broker path was opened.
