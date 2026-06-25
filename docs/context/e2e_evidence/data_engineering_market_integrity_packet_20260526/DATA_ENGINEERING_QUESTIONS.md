# Data Engineering / Market-Data Integrity Expert Questions

GitHub repo: https://github.com/nathanku3-hue/Quant
GitHub branch: https://github.com/nathanku3-hue/Quant/tree/codex/optimizer-core-structured-diagnostics
Commit: https://github.com/nathanku3-hue/Quant/commit/cec79312e091107e9a4bbd14ba855c59f2ca5a75

Local packet caveat: HEAD is aligned with that GitHub branch at `cec79312e091107e9a4bbd14ba855c59f2ca5a75`, but this packet includes local uncommitted current-truth context. Please distinguish "already on GitHub" from "local data-integrity reboot material."

## Mission

We need a practical `Data Readiness Gate v0` that can plug into the proposed boot preflight command:

```text
.\.venv\Scripts\python launch.py --preflight --mode planning
.\.venv\Scripts\python launch.py --preflight --strict
```

The goal is not broad data-platform theory. The goal is to decide which data checks make Terminal Zero safe to use as a local-first quantitative research console before strategy review, replay rebuilds, or Portfolio & Allocation output are trusted.

## Requested Expert Output

Please return:

1. One recommended `Data Readiness Gate v0` architecture.
2. One minimal machine-checkable data-health JSON schema for `docs/context/boot_status_current.json`.
3. A PASS/WARN/FAIL classification for each proposed check.
4. A data artifact taxonomy: canonical, derived, cache-only, evidence-only, disposable.
5. A repair policy: automatic, manual approval, or never during boot.
6. A provider-boundary policy for boot.
7. A first implementation slice with exact files to touch and tests to run.

## High-Value Real Questions

### A. Dataset Authority

1. Which local datasets are canonical research inputs, derived artifacts, cache-only accelerators, evidence-only records, and disposable runtime outputs?
2. Which files must never be silently regenerated during boot?
3. Which files can be regenerated automatically because they are pure derived artifacts?
4. Which data directories should be excluded from GitHub by policy even if they are useful locally?
5. Which evidence files are worth committing because they prove a data contract?

### B. Freshness And Availability

1. What does "fresh enough for research" mean for prices, returns, benchmarks, PIT membership, fundamentals, candidate cards, discovery outputs, and replay artifacts?
2. Which freshness failures should block all research output?
3. Which freshness failures should only degrade the dashboard with visible warnings?
4. Which freshness failures should allow planning but block strict boot?
5. Should boot use calendar-aware freshness checks or simple max-date checks?

### C. PIT Discipline

1. Can every strategy input prove both row-date availability and asset-universe availability as of the replay date?
2. Is the current full-window `r3000_pit` membership proof sufficient for selected-price loading?
3. Which functions must fail closed if PIT membership or ticker mapping is unavailable?
4. What minimum PIT audit should be included in boot without running a full replay?
5. What local evidence would prove that future membership cannot leak through columns?

### D. Price / Return Integrity

1. How should boot detect slot corruption, such as TRI/price levels and daily returns being swapped?
2. What numeric sanity checks are safe and useful: monotonic dates, nonnegative levels, bounded returns, finite values, duplicate columns, duplicate dates, endpoint parity?
3. What should boot do when one weighted asset is stale but live overlay cannot refresh it?
4. What overlap-anchor invariant should be checked for scaled live overlays?
5. Which checks should run on selected current assets versus the full local matrix?

### E. Replay Artifact Identity

1. What fields must be nonblank and exactly matched for saved replay artifacts: `run_id`, `source_id`, `method_id`, `dashboard_cache_signature`, source signatures, controls, date window, row counts?
2. Should boot validate only latest selected-method artifacts or all artifacts under runtime cache?
3. What should happen when a saved artifact is a wider proven superset of the requested horizon?
4. Which artifact mismatches are `FAIL`, and which are `WARN` because dashboard can rebuild transitionally?
5. What minimum artifact probe is enough for boot without triggering a replay rebuild?

### F. Provider Boundaries

1. Should boot ever call yfinance or any live provider?
2. If provider calls are allowed in planning mode, what guardrails prevent canonical writes or hidden ingestion?
3. Which modules are allowed to import provider libraries directly?
4. Should provider-port tests be part of strict boot?
5. How should boot report "local data stale but provider refresh not authorized"?

### G. Candidate / Evidence Manifests

1. Should candidate-card manifests be part of data readiness or evidence readiness?
2. Which hash/signature checks should run in boot?
3. What prevents discovery outputs or candidate cards from being overread as validated strategy evidence?
4. Which manifest failures should block boot?
5. How should boot distinguish static research objects from live market-data inputs?

### H. Dirty Worktree And GitHub Alignment

1. Which local uncommitted data artifacts are dangerous to lose?
2. Which untracked files are generated noise and should be ignored or archived?
3. Should dirty data source/test files fail strict boot even when current context validates?
4. What is the safest staging order for data-related dirty buckets?
5. What minimum GitHub alignment should be required before declaring "safe boot"?

### I. Data Repair Policy

1. What can boot repair automatically: derived context, generated data-health JSON, display-only cache, stale overlay cache, pure manifests?
2. What requires explicit approval: canonical parquet rewrite, provider ingestion, feature-store rebuild, replay artifact promotion, ticker-map edits?
3. What should never happen during boot: broker calls, alerts, ranking/scoring, canonical write from live provider, strategy promotion?
4. What rollback evidence is needed for any automatic repair?
5. How should repair results be recorded back into current truth surfaces?

### J. Minimal First Slice

1. What is the smallest `Data Readiness Gate v0` we can add without touching optimizer/replay behavior?
2. Which exact tests should prove it?
3. Which existing checks should be reused instead of rewriting?
4. What should `boot_status_current.json` say when data is usable for planning but not strict research?
5. What should be the next data slice after v0?

## Proposed Starting Point For Review

Initial hypothesis to challenge:

```text
Data Readiness Gate v0 should validate:
- context freshness from scripts/build_context_packet.py --validate,
- data artifact taxonomy and dirty-worktree classification,
- canonical parquet/source file presence via signatures,
- price/return slot sanity for loaded local matrices,
- endpoint freshness for selected Portfolio & Allocation assets,
- PIT universe loader and pinned thesis universe manifest,
- provider-port boundaries,
- candidate-card/discovery manifest hashes,
- saved replay artifact identity if present,
- no provider ingestion or canonical writes during boot.
```

Please mark each as `PASS`, `WARN`, `FAIL`, or `DEFER`, and explain the minimum implementation needed.

