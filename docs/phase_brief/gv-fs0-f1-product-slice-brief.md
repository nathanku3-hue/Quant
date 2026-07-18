# Phase Brief: GV-FS0-F1 — Product Slice (Corrected)

Mode: `EXECUTION_PACKET`
Status: `P0_5_BANKED; V1_1_VERIFIER_IO_COMPAT_BANKED; F1A_UNBLOCKED`
Date: 2026-07-18
RoundID: `ROUND-20260718-GV-FS0-F1-PRODUCT-SLICE`
ScopeID: `GV_FS0_F1_REPAIR_AND_SHIP_CURRENT_SLICE`
Authority:
- `docs/architecture/godview_endgame_vision.md`
- `docs/architecture/godview_portfolio_first_operating_model.md`
- `docs/architecture/godview_portfolio_p0_owner_freeze.md`
- `docs/architecture/top_level_roadmap.md` (GV-FS0-First; replaces obsolete UOE roadmap)
- frozen protocol: `docs/architecture/gv_fs0_certification_and_data_authority_contract.md` (terminal freeze at `c007895`)
- V1.1 verifier I/O: `docs/architecture/gv_fs0_protocol_v1_1_verifier_io.md` (engine compatibility only; frozen V1 schemas byte-immutable)
- terminal freeze evidence: `docs/phase_brief/phase-E0-brief.md` (historical/terminal; do not rewrite)
Hierarchy: L1 Terminal Zero; L2 active Backend product accounting + Frontend read-only presentation; L2 held Data admission / Research / PEAD / FS1; L3 flow P0 custody → **atomic P0.5 bank** → F1A OPEN vertical → F1B NO_POSITION → F1C permanent bundle → F1D both on default screen + product CI + full suite + A/B/C.

## Decision

```text
STRATEGY = REPAIR_AND_SHIP_CURRENT_SLICE
PROTOCOL_REDESIGN = FORBIDDEN
CURRENT_CHECKOUT_GIT_REPAIR = FORBIDDEN
F1A = UNBLOCKED after V1.1 verifier I/O compatibility
SHIPPED_PRODUCT_SCORE = 39/100 (unchanged until certified visible screen on final adapter)
```

Audit verdict absorbed: `APPROVE_WITH_MANDATORY_REPAIR`, plus bankability repairs for P0.5 atomicity.

**V1.1 blocker closed:** schema-valid `gv_fs0_verifier_input_v1` is accepted by `validation/gv_fs0_reconstruction.py`. Legacy `prices`/`events` inputs fail closed. Frozen V1 schemas under `contracts/gv_fs0/v1/` were already correct and remain byte-immutable (no freeze regen required).

## Endgame Intent

Endgame is a portfolio OS that turns an explicit decision into auditable paper economics with independent certification. GV-FS0-F1 is the first functional product slice:

```text
DecisionEnvelope
→ PortfolioBook
→ Fs0PortfolioSnapshot series
→ two independent verifier attempts (frozen reconstruction; process-only)
→ Fs0Certification
→ certification-reference event
→ certified decision result
→ final read-only Streamlit adapter (injected OPEN first; later both components)
→ permanent two-component certified bundle (F1C)
→ default screen reads permanent bundle (F1D)
```

No allocation authority, providers, real data, MU/E0 research, benchmarks, optimizers, or GV-FS1.

## Custody Topology

```text
PRODUCT_ROOT = isolated worktree or clean clone rooted exactly at c007895
PRODUCT_BRANCH = codex/gv-fs0-f1-product
FORBIDDEN = repairing E:\Code\Quant\.git worktree administration as part of F1
```

### Worktree topology (product tests)

```text
PRODUCT_ROOT/
  contracts/gv_fs0/v1/**                 # frozen; consume only
  core/gv_fs0_canonical.py               # frozen load surface
  validation/gv_fs0_reconstruction.py    # frozen verifier; process-only; never edit in F1
  tests/test_gv_fs0_*.py                 # frozen protocol suite only
  tests/gv_fs0_product/                  # product tests only (never top-level test_gv_fs0_*)
  docs/architecture/
    godview_endgame_vision.md            # REQUIRED product canon
    godview_portfolio_first_operating_model.md
    godview_portfolio_p0_owner_freeze.md
    top_level_roadmap.md                 # GV-FS0-First (replaces UOE roadmap)
    unified_opportunity_engine.md        # SUPERSEDED historical only
  views/gv_fs0_portfolio_adapter.py      # ONE final adapter (F1A+); injection-first
  .github/workflows/
    gv-fs0-protocol-freeze.yml           # leave protocol-only
    gv-fs0-product.yml                   # NEW at F1D (or earlier CI bank if needed)
```

## Atomic P0.5 bank (single reviewable commit)

F1A is blocked until **one** commit lands all of:

1. **Three product-canon files** (path-level present + non-empty + Active status):
   - `docs/architecture/godview_endgame_vision.md`
   - `docs/architecture/godview_portfolio_first_operating_model.md`
   - `docs/architecture/godview_portfolio_p0_owner_freeze.md`
2. **Revised roadmap** replacing obsolete Unified Opportunity Engine roadmap text in `docs/architecture/top_level_roadmap.md` (GV-FS0-First).
3. **UOE adjacent-scope breadcrumbs demoted** (`unified_opportunity_engine.md` / state machine marked SUPERSEDED historical only).
4. **Hardened integrity gate** (not hash-only): missing canon fails closed; freeze manifest hashes; runtime external import of `core.gv_fs0_canonical` and runtime load of frozen tables/registries.
5. **Authority-chain test**: machine proof of intended import/authority boundaries before any F1A product module lands.
6. **This successor brief** without invented unregistered operational codes.
7. **No throwaway temporary UI architecture** in plan: one final adapter with injected OPEN data.

Nothing else belongs in the P0.5 commit (no F1A book/cert/publication modules).

## Canonical Integrity Gate (hard, non-lazy)

```text
P0.5_CANONICAL_INTEGRITY:
  1. REQUIRED product-canon paths exist (three files above) — missing => fail closed
  2. top_level_roadmap.md is GV-FS0-First (not UOE active roadmap)
  3. freeze manifest SHA-256 + byte_length for every entry
  4. import core.gv_fs0_canonical at product-test import time (non-lazy)
  5. runtime-load frozen ranks, slots, ownership, both registries, vectors via Path
  6. external import discipline: product suite must not in-process import
     validation.gv_fs0_reconstruction as a library; frozen verifier stays process-only
  7. FAIL CLOSED on any missing path / hash / import / load error — block F1A
```

Do **not** recreate frozen tables as Python constants. Consume `core/gv_fs0_canonical.py` and `contracts/gv_fs0/v1/**`.

## Corrected Functional Gate Order

```text
P0   Clean execution custody at exact c007895
P0.5 Atomic bank: three canons + revised roadmap + integrity + authority-chain + brief
F1A  OPEN vertical end-to-end into ONE final adapter via injected OPEN presentation/snapshot/cert
F1B  NO_POSITION through the identical implementation path (inject second component)
F1C  Permanent two-component bundle publication with full recovery semantics
F1D  Default screen reads permanent bundle; product CI; full suite; A/B/C + truth
```

### F1A detail — OPEN only (starts only after P0.5 green)

1. Immutable synthetic `DecisionEnvelope` + source fixture (OPEN).
2. Append-only `PortfolioBook` using frozen event ranks/slots/ownership.
3. Immutable `Fs0PortfolioSnapshot` series (5–10 sessions).
4. Verifier input **exactly**:
   ```text
   original fixture
   + DecisionEnvelope
   + source prices
   + source economic intents
   + protocol bindings
   ```
   Never: primary generated events, book ledger, snapshots, certifications, components, or bundle data.
5. Two supervised independent verifier attempts (`sys.executable -I` on V1.1-compatible `validation/gv_fs0_reconstruction.py` with schema-valid `gv_fs0_verifier_input_v1` only).
6. Immutable `Fs0Certification`; CERTIFIED only if all ten checks TRUE.
7. Certification-reference event + certified decision result + presentation projection.
8. **Final adapter only:** `views/gv_fs0_portfolio_adapter.py` renders §16 fields from **injected** validated presentation/snapshot/certification objects (OPEN). No disposable temp route, no env-flag throwaway page, no second adapter to delete later. Permanent bundle is still forbidden until F1C (contract §14.2: no partial final bundle file).

### Final adapter injection contract (replaces throwaway temp UI)

```text
ADAPTER = views/gv_fs0_portfolio_adapter.py
SHAPE   = single read-only render function(s) accepting injected artifacts
F1A     = inject OPEN certified presentation/snapshot/cert only
F1B     = inject NO_POSITION through same functions
F1C     = publish permanent two-component bundle (not adapter responsibility)
F1D     = adapter default path loads permanent bundle then injects both components
FORBIDDEN
  - temporary / throwaway routes, disposable pages, or second adapters scheduled for deletion
  - adapter-owned accounting, certification, or verifier execution
  - publishing data/gv_fs0/gv_fs0_certified_bundle.json before both components CERTIFIED
```

### F1B — NO_POSITION

Identical code path; separate decision/book/trail/certification; zero execution intents normative.

### F1C — permanent publication

Target: `data/gv_fs0/gv_fs0_certified_bundle.json`  
Lock: `data/gv_fs0/.gv_fs0_certified_bundle.lock`

Implement contract §15 using **only registered operational codes**:

```text
PUBLICATION_LOCKED
PUBLICATION_TARGET_CHANGED
PUBLICATION_POST_REPLACE_VERIFICATION_FAILED
PUBLICATION_RECOVERY_RECORD_FAILED
```

**Do not invent** new operational registry codes. Use only the four frozen publication codes above.  
Age/PID automatic lock removal remains forbidden by implementing only §15.6 normal release paths and requiring explicit operator recovery for `RECOVERY_REQUIRED` locks. Prove with product tests in F1C; no unregistered error surface in P0.5/F1A.

Publication tests under `tests/gv_fs0_product/` (F1C):

- `PUBLICATION_LOCKED`
- idempotent identical candidate
- `PUBLICATION_TARGET_CHANGED`
- pre-replace failure preserves target
- post-replace verification failure → durable recovery lock
- recovery-record write failure retains existing lock
- no age- or PID-based automatic lock removal (behavior tests against real release paths)

### F1D

§16 fields only (no separate fee column). Separate product CI. Complete repository pytest. Reviewer A/B/C as defined below.

## Verifier Input Boundary + import enforcement

Consume: original fixture + DecisionEnvelope + source prices + source economic intents + protocol bindings.  
Never: primary generated events, ledger, snapshots, certifications, components, bundle.

Machine checks (P0.5 authority-chain + integrity):

- frozen reconstruction remains process-only (`sys.executable -I`); product tests must not import it as an in-process library
- product modules (when added) AST-scanned for forbidden imports: `strategies.*` for cert truth, primary book from verifier, views from book, etc.
- freeze surfaces loaded via path, not duplicated constants

## CI / Test Separation

| Suite | Path | Workflow |
|---|---|---|
| Protocol freeze | `tests/test_gv_fs0_*.py` | `gv-fs0-protocol-freeze.yml` |
| Product | `tests/gv_fs0_product/**` | `gv-fs0-product.yml` (add by F1D; protocol as regression) |

## F1D A/B/C criteria

| Reviewer | Domain | Must verify |
|---|---|---|
| **A** | Strategy/economics | Exact OPEN/NO_POSITION economics; NAV; dividend once; certification mapping; no legacy replay authority |
| **B** | Runtime/ops | Verifier isolation; publication recovery; single adapter injection; no provider |
| **C** | Data integrity | Freeze hashes; three canons present; product/protocol CI split; full suite green |

## Forbidden Scope

```text
protocol redesign / freeze-byte edits
current-checkout .git repair
provider / yfinance / WRDS / PEAD reopen
legacy strategy_replay conversion as FS0 truth
benchmarks / optimizers / real data / MU / FS1
invented operational error codes not in frozen registry
throwaway temporary UI routes
F1A before atomic P0.5 green
```

## Acceptance

### P0.5 (this commit)

- [x] Three product-canon files banked with path-level verification
- [x] `top_level_roadmap.md` is GV-FS0-First
- [x] UOE roadmap/architecture demoted to SUPERSEDED historical
- [x] Integrity gate fails closed on missing canon + validates external imports/runtime loads
- [x] Authority-chain test present and green
- [x] No invented unregistered publication/error codes in brief/code
- [x] Final-adapter injection plan (no throwaway temp route)
- [x] Atomic commit banked on `codex/gv-fs0-f1-product`

### F1A+

See gate sections above; start only after P0.5 commit is banked and product tests green.

## First Commands

```text
# product root at c007895 ancestry
git rev-parse HEAD
python -m pytest -q tests/gv_fs0_product
python -c "import glob,pytest,sys; sys.exit(pytest.main(['-q',*glob.glob('tests/test_gv_fs0_*.py')]))"
# only then F1A modules + final adapter with injected OPEN data
```

## Next Action

GO F1A: final adapter + injected OPEN + schema-valid V1 verifier input into the V1.1 reconstruction engine.
