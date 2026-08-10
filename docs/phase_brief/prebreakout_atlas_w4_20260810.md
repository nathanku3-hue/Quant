# W4 Phase Brief — PREBREAKOUT Discovery Atlas

> **Current real-run update — supersedes the dormant fixture-only state below as current truth.** W3 real authority is complete and Trial #1 is charged `1/8`; its flags were frozen before development label materialization, and W5 has completed with median recall lift `0.71570953472408605`. The real W4 census is the remaining incomplete step. The last real W4 attempt exposed only a nullable `pd.NA` handling bug for `INCOMPLETE_HORIZON` labels; that mechanical bug is fixed and the focused W4 suite is `17/17 PASS`, but no final real Atlas artifact has been materialized yet. Reuse the existing Trial #1 open and frozen artifacts, finish W4 only, then close Trial #1. **Do not consume W6.** Canonical current handover=`docs/handover/prebreakout_trial1_w4_handover_20260810.md`.

**Date:** 2026-08-10
**State:** `W4_MECHANICS_CLOSED / BYTES_FROZEN / DORMANT_UNTIL_REAL_DISCOVERY_DATA`
**Family:** `PREBREAKOUT_DISCOVERY_v1`
**Authority:** `DISCOVERY_ONLY / EXTERNAL_FROZEN_FLAGS_ONLY / FINANCIAL_ALPHA_EVIDENCE_0 / CAPITAL_AUTHORITY_NONE`

## Chosen scope

Close W4 mechanics and freeze the existing full true-winner / false-winner / missed-winner / matched-control census. **No more Atlas plumbing is authorized while dormant.**

W4 is allowed to consume frozen W2 methodology and W3 PIT authority, but it cannot redefine breakout B, TTFLD, horizons, labels, risk-set identity, availability/corporate-action law, search budget, walk-forward development, or untouched evaluation.

No real provider capture or real discovery-label opening was performed in this slice. All executable acceptance evidence is deterministic fixture evidence. The W2 closure adds one narrow W4 handoff hardening: `PrebreakoutMethodologyBinding` now rejects any breakout contract hash that differs from the single frozen W2 methodology seal. No Atlas census semantics changed.

## Shipped

Canonical W4 paths:

- `research/prebreakout_atlas_v1/atlas.py`
- `research/prebreakout_atlas_v1/__init__.py`
- `tests/prebreakout_atlas_v1/test_atlas.py`
- `docs/architecture/prebreakout_discovery_atlas_v1.md`
- `docs/phase_brief/prebreakout_atlas_w4_20260810.md`

### W2 binding

W4 consumes `PrebreakoutMethodologyBinding` rather than importing W2/W5 implementation ownership. Exact current binding is `PREBREAKOUT_W2_CONTRACT_v1`, with `methodology_contract_sha256 = breakout_contract_sha256 = 94c8756e11d4e31cbf4d6ca4953b63c83306f4b357a42f0b70c94ae3fd261e71`; the deterministic W4 envelope is `binding_sha256=080aba6676202e68d14aff405049a2422d231dd7b8335f3be32f376b049205ad`. Construction recomputes the W2 contract hash from the supplied preregistration snapshot and now fails closed on breakout/methodology hash divergence before sealing risk set, label, breakout spec, TTFLD spec, horizons/lead law, search family, and trial budget.

This was intentionally separated from `research/prebreakout_discovery_v1/` after concurrent W2/W5 edits briefly made that package initializer inconsistent during the work round. The final combined PREBREAKOUT test run is green; W4 remains isolated so future W2/W5 edits cannot silently change W4 semantics.

### External candidate flags / Trial-1

W4 consumes frozen flags; it does not develop them. A result-bearing run must receive an externally supplied charged candidate identity plus immutable date/security flag custody created before discovery labels were opened.

The first real candidate is **Trial-1**, a fully deterministic pre-fit rule. No real Trial-1 is currently open; real search remains `0/8`. Before W2 may issue `TRIAL_OPEN #1`, both the exact Trial-1 data/source manifest and exact Trial-1 implementation manifest must already be frozen. Trial-1 is then charged upstream before Atlas outcomes are joined. It must not depend on a fitted W5 model. This gives W4 a non-circular first census:

```text
deterministic Trial-1 rule → frozen flags → W4 census → later W5 development
```

W2/search custody owns Trial-1's rule and charge. W3 owns PIT inputs. W4 owns only the census of the supplied flags.

### Winner census

Winners are counted once per effective episode at exact B-1. Repeated daily winner-labelled rows are not separate winner successes.

- eligible B-1 + legal prebreakout flag => `TRUE_WINNER`;
- eligible B-1 + no legal prebreakout flag => `MISSED_WINNER`;
- excluded B-1 => `EXCLUDED_WINNER`, zero statistical weight.

The legal flag scan is bounded by W2's lead-lookback/minimum-lead contract. A B or post-B flag cannot rescue a miss.

### False-winner census

Every eligible, flagged, nonwinner date/security row is retained as `FALSE_WINNER`. W4 does not collapse false-winner rows using a new heuristic.

### Controls

Every eligible, unflagged, nonwinner row enters the ordinary control pool. For each positive-weight true winner, missed winner, and false winner case, W4 emits all same-session ordinary controls matching the exact preregistered control strata.

No sampled-control count, nearest-neighbor fallback, relaxed rematch, or ticker-specific logic is permitted. A real run requires both the upstream-verified charged control-definition receipt SHA-256 and the immutable Trial-Ledger snapshot SHA-256 because W2 classifies control definition as a material search field. W4 binds but does not mutate that upstream ledger authority.

### W3 integration

Real mode verifies one W3 PIT packet per decision date and requires exact full-population equality between the Atlas grid and W3 date-local authority by canonical `CIQSEC:IQ... + numeric trading_item_id`. Eligibility/exclusion reason drift blocks.

### MU / SNDK

Named cases enter only through W3 B-1 proof objects. Display symbols are trace metadata and never logic. Resolved identities receive statistical and promotion-denominator weight zero across the Atlas.

The fixture acceptance suite proves both a zero-weight true-winner smoke trace and a zero-weight deterministic-exclusion smoke trace, and proves that a post-B-1 flag cannot rescue a smoke miss.

## Acceptance checks

| ID | Requirement | Result |
|---|---|---|
| W4-01 | cryptographically bind exact frozen W2 snapshot/hash without taking W2 ownership | PASS |
| W4-02 | fail on W2↔W3 family/risk-set drift | PASS |
| W4-03 | canonical CIQSEC + Trading Item identity only | PASS |
| W4-04 | one winner census row per effective episode | PASS |
| W4-05 | exact B-1 row required for winner episode | PASS |
| W4-06 | no B/post-B rescue of a missed winner | PASS |
| W4-07 | enumerate true/missed/excluded winner classes | PASS |
| W4-08 | enumerate full date-local false-winner census | PASS |
| W4-09 | enumerate full ordinary control pool and all exact matched controls | PASS |
| W4-10 | MU/SNDK generic trace path has zero statistical/promotion weight | PASS |
| W4-11 | real mode requires paired charged-control receipt + Trial-Ledger snapshot + W3 PIT authority | PASS |
| W4-12 | report hash/tamper and exclusion-state fail closed | PASS |
| W4-13 | W6 promotion metrics remain absent from W4 | PASS |
| W4-14 | real discovery Atlas run today | HELD by methodology/no-outcome-open boundary |

## Validation

Focused W4 on final single-seal binding bytes:

```text
14/14 PASS
```

Full current PREBREAKOUT mechanical/custody matrix:

```text
69/69 PASS
```

The matrix covers the 26-test W2/W5 discovery package (including the uncharged Trial-1 M0 source-manifest gate), W3 PIT authority (`17/17`), W4 Atlas (`14/14`), and W6 untouched evaluator (`12/12`). No real trial, provider capture, discovery-label open, or lockbox open occurs in this validation.

## Real-run gate

W4 is now dormant. Reopen it only for the first real Atlas run, and only when these four gates are simultaneously satisfied:

1. **W2 binding exact** — frozen methodology/breakout/TTFLD/risk-set/label/search identity is hash-exact.
2. **W3 full PIT authority exists** — source-complete date-local CIQSEC + trading-item + availability + corporate-action authority exists for every required Atlas date, with no survivor/fallback repair.
3. **Trial-1 and control definition are charged** — Trial-1 is the externally frozen deterministic pre-fit candidate; its flags are immutable before label open, and the control definition is bound to its charge receipt + Trial-Ledger snapshot.
4. **Discovery labels are legitimately open** — only matured discovery labels may be supplied to W4.

MU/SNDK, if traced, remain generic W3 B-1 proofs with statistical/promotion weight zero. W4 still must not open a W6 lockbox, fit W5, or use untouched/prospective outcomes for development.

## Claim boundary

This round closes W4 mechanics and freezes its bytes/semantics only. It adds no financial-alpha evidence, no prospective evidence, no promotion metrics, no VSB confirmation, no Sector Rotation or CRV1 result, no replication result, no PAPER order, and no capital authority. Clock #1/A2/Parent-Child remain untouched.

**Worker disposition:** `CLOSED / DORMANT`. Reopen only for the first real Atlas run after all four real-run gates are true.
