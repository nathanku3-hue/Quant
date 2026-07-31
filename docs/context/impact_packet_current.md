# Impact Packet — Current

Date: 2026-07-31
Active slice: `GV-OPERATED-PORTFOLIO-10-TRANSITION-1R`

## Product impact

The candidate adds the first post-Replay operator capability that changes portfolio economics:

- ten permanent instrument identities across two economic clusters;
- instrument-owned evidence and Living Thesis Lite state;
- deterministic competition across all ten instruments with selected IDs as execution authority;
- one portfolio with four initially funded positions and classified residual cash;
- one explicit no-change observation;
- one authorized reduce-and-fund transition;
- operator-visible changed-why derived from decisions and the canonical book;
- confined atomic persistence and verified reopen;
- one append-only non-economic correction and fresh-process corrected reopen.

## Acceptance-kernel repair

The repaired validator rejects every reproduced contradictory state:

- empty selected funded IDs followed by execution;
- shared initial evidence across instruments;
- missing trade-authority chains;
- forged order instrument or fill price;
- false changed-why symbols, cash, or costs;
- transition legs that do not equal target deltas;
- forged historical certification objects or links;
- self-asserted certification-stability booleans;
- workspace paths beneath symlink or Windows-junction ancestors.

Orders, fills, authority chains, observations, changed-why, books, certifications, and correction links are now reconstructed or exactly validated from canonical events and decision state.

## Execution and accounting impact

Shared execution emits deterministic BUY or SELL paper order/fill chains. Shared accounting accepts SELL orders and fills, rejects missing or oversized positions, credits proceeds net of fees, reduces quantity, and preserves nonnegative cash/position and zero-residual rules.

The exercised transition remains:

```text
HARBOR 10 → 6 via SELL 4 @ 40, fee 2
MERID 0 → 5 via BUY 5 @ 30, fee 2
NAV 4992 → 4988
cumulative explicit costs 8 → 12
unexplained residual 0
```

## Persistence and custody impact

Persistence now resolves and inspects every existing ancestor, rejects symlinks and Windows junctions, enforces lexical and canonical same-or-within-root checks, and repeats confinement checks before creation, write, replace, and load. The persisted schema and workspace-hash domain were bumped to v2; no compatibility adapter was added.

## Verification state

Passed under a clean narrow Windows environment provisioned from `requirements-alpha.txt`:

- Python 3.12.10, pytest 9.0.2, Streamlit 1.54.0;
- `pip check`;
- operated domain and black-box AppTest: `15/15`;
- book/execution/replay/operated focused set: `70/70`;
- context/authority set: `33/33`;
- complete `tests/gv_portfolio_v0`: `145/145`;
- combined operated/context gate: `178/178`;
- correction plus fresh-process corrected reopen with network denied.

CI impact:

- `.github/workflows/gv-operated-portfolio.yml` adds `ubuntu-latest` and `windows-latest` Python 3.12 jobs;
- operated-product, test, CI, and current-authority paths now trigger the gate;
- the job installs only `requirements-alpha.txt`, validates context, and rejects tracked-byte drift after tests.

Blocked:

- hosted Windows/Linux parity against one pushed immutable candidate;
- immutable candidate/fresh-checkout proof;
- full repository regression/failset comparison;
- independent Reviewer A/B/C;
- commit, push, main fast-forward, or terminal tag.

## Score impact

Accepted endgame progress remains `52/100`. Local semantic enforcement, narrow pinned reproducibility, and CI coverage are materially stronger, but only exact-SHA hosted parity plus immutable terminal evidence can raise the accepted score to the expected `61–63/100` range.
