# Dashboard UI Fixes Brief

**Status**: Planning (patched with blocker constraints)  
**Date**: 2026-03-05  
**Owner**: UI stream

## Scope
Resolve dashboard discoverability and UX issues:
1. Data Health visibility
2. Drift Monitor prominence
3. Portfolio Builder auto strategy selection
4. Strategy boolean expression builder
5. Modular formula rendering responsiveness
6. Sniper-view label readability
7. Backtest Lab tab removal (only after baseline-export replacement path is live)

## Critical Blockers (Must Resolve First)

### B1: Runtime NameError in Backtest Lab
- Observed error:
  - `NameError: name '_render_legacy_backtest_table' is not defined`
  - call site executed before helper definition in `dashboard.py`.
- Constraint:
  - Helper functions must be defined before first invocation in script execution order.
- Resolution status:
  - Fixed in `dashboard.py` by moving `_render_legacy_backtest_table()` above the first call.

### B2: Preserve Baseline Export Before Backtest Tab Deletion
- Baseline export currently depends on backtest path via `run_backtest_with_baseline_export`.
- Constraint:
  - Do not remove Backtest Lab tab until an equivalent baseline-export trigger exists elsewhere (for example Drift Monitor baseline management action) and is validated.

## Sequencing Rules
1. Fix/validate execution-order blockers (B1).
2. Introduce replacement baseline-export path (B2) and validate it.
3. Only then remove Backtest Lab tab.
4. Ship non-breaking visibility upgrades first (Data Health tab + Drift Monitor promotion).

## Implementation Order
1. Navigation/discoverability updates
2. Baseline export replacement path
3. Portfolio Builder auto-selection + safe accounting display
4. Strategy expression engine with proper `NOT` universe semantics
5. Formula-loading optimization (cache data only, not UI rendering side effects)
6. Sniper-view deterministic label layout
7. Backtest Lab tab deletion (last)

## Blocker Resolution Contracts

### Contract 1: Baseline Export Data Source
**Problem**: Baseline export requires historical `target_weights` matrix + `returns_df`, not just live snapshot.

**Contract**:
```python
def get_baseline_export_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load data for baseline export.

    Returns:
        target_weights: DataFrame (date index × permno columns) with historical allocations
        returns_df: DataFrame (date index × permno columns) with returns

    Source Priority:
        1. Latest completed backtest artifacts (data/backtest_artifacts/<strategy>_weights.parquet)
        2. Fallback: Load from feature store + reconstruct weights from last 252 days
    """
    # Implementation: Read from most recent backtest artifact
    artifact_dir = Path("data/backtest_artifacts")
    latest_weights = max(artifact_dir.glob("*_weights.parquet"), key=lambda p: p.stat().st_mtime)
    target_weights = pd.read_parquet(latest_weights)

    # Load returns from feature store
    returns_df = load_returns_from_feature_store(target_weights.columns)

    return target_weights, returns_df
```

**Acceptance**: Function returns valid DataFrames with matching date ranges and permno columns.

---

### Contract 2: Strategy Metrics Source of Truth
**Problem**: Mixed sources (cache/registry) cause stale metrics.

**Contract**:
```python
def load_strategy_metrics() -> dict[str, dict]:
    """
    Load strategy performance metrics.

    Source of Truth: data/backtest_results.json
    Schema:
        {
            "strategy_name": {
                "cagr": float,
                "sharpe": float,
                "max_dd": float,
                "timestamp": str (ISO 8601),
                "script": str
            }
        }

    Fallback: STRATEGY_REGISTRY["backtest"] if strategy not in backtest_results.json
    """
    results_path = Path("data/backtest_results.json")

    if results_path.exists():
        with open(results_path) as f:
            metrics = json.load(f)
    else:
        metrics = {}

    # Fallback to registry for missing strategies
    for name, strat in STRATEGY_REGISTRY.items():
        if name not in metrics:
            bt_data = strat.get("backtest", {})
            metrics[name] = {
                "cagr": parse_cagr(bt_data.get("cagr", 0)),
                "sharpe": float(bt_data.get("sharpe", 0)),
                "max_dd": float(bt_data.get("max_dd", 0)),
                "timestamp": "registry",
                "script": "",
            }

    return metrics

def parse_cagr(value) -> float:
    """Parse CAGR from string '+12.3%' or float 0.123."""
    if isinstance(value, str):
        return float(value.strip("+%")) / 100.0 if value else 0.0
    return float(value)
```

**Acceptance**: Returns dict with all strategies, prioritizes `backtest_results.json`, falls back to registry.

---

### Contract 3: Expression Parser Tokenization
**Problem**: Naive split breaks on operators inside strategy names.

**Contract**:
```python
def tokenize_expression(expression: str) -> list[str]:
    """
    Tokenize boolean expression with word-boundary operators.

    Grammar:
        TOKEN := '(' | ')' | 'AND' | 'OR' | 'NOT' | STRATEGY_NAME
        STRATEGY_NAME := any text not containing operators/parens

    Rules:
        - Operators must be uppercase and word-bounded
        - Strategy names can contain spaces
        - Parentheses are separate tokens

    Example:
        "(Infinity Governor OR Rule of 100) AND High Margin Gate"
        → ['(', 'Infinity Governor', 'OR', 'Rule of 100', ')', 'AND', 'High Margin Gate']
    """
    import re

    # Split on word-bounded operators and parentheses
    pattern = r'(\(|\)|\bAND\b|\bOR\b|\bNOT\b)'
    tokens = re.split(pattern, expression)

    # Clean whitespace, filter empty, preserve case for strategy names
    tokens = [t.strip() for t in tokens if t.strip()]

    return tokens

def validate_full_parse(tokens: list, final_pos: int):
    """Ensure all tokens consumed."""
    if final_pos < len(tokens):
        raise ValueError(f"Unexpected token at position {final_pos}: '{tokens[final_pos]}'")
```

**Acceptance**: Correctly tokenizes expressions with spaces in strategy names, rejects trailing tokens.

---

### Contract 4: Tab Migration Staged Rollout
**Problem**: Removing Backtest Lab before replacement breaks baseline export.

**Two-Step Deployment**:

**Step 1: Promote Tabs (Safe - No Deletion)**
```python
# dashboard.py:1033
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Ticker Pool & Proxies",
    "🏥 Data Health",           # NEW
    "🔍 Drift Monitor",          # PROMOTED
    "📈 Backtest Lab",           # KEEP for now
    "🔬 Daily Scan",
    "🧩 Modular Strategies",
    "💼 Portfolio Builder",
])
```

**Gate 1 Validation**:
- [ ] Dashboard launches without errors
- [ ] Data Health tab renders
- [ ] Drift Monitor tab renders
- [ ] Backtest Lab still functional

**Step 2: Add Baseline Export to Drift Monitor**
```python
# dashboard.py (in tab3 - Drift Monitor)
if st.button("📤 Export Baseline"):
    target_weights, returns_df = get_baseline_export_inputs()
    results, baseline_id = export_baseline(target_weights, returns_df)
    st.success(f"Baseline: {baseline_id}")
```

**Gate 2 Validation**:
- [ ] Export baseline from Drift Monitor succeeds
- [ ] `data/baselines/latest.json` updates
- [ ] Drift Monitor loads new baseline

**Step 3: Remove Backtest Lab (Only After Gates 1+2 Pass)**
```python
# dashboard.py:1033
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Ticker Pool & Proxies",
    "🏥 Data Health",
    "🔍 Drift Monitor",
    "🔬 Daily Scan",
    "🧩 Modular Strategies",
    "💼 Portfolio Builder",
])
# Remove tab4 (old Backtest Lab) code block
```

**Gate 3 Validation**:
- [ ] Dashboard launches without Backtest Lab
- [ ] Baseline export still works from Drift Monitor
- [ ] No broken references to tab4

---

## Test Matrix

| Test | Phase | Pass Criteria | Rollback Trigger |
|------|-------|---------------|------------------|
| Syntax check | All | `python -m py_compile dashboard.py` exits 0 | Syntax error |
| Dashboard launch | All | No exceptions in first 10s | Import/runtime error |
| Data Health tab | Step 1 | Tab renders, shows health status | Missing data/crash |
| Drift Monitor tab | Step 1 | Tab renders, shows alerts | Missing data/crash |
| Backtest Lab functional | Step 1 | Can trigger backtest | Broken after reorder |
| Baseline export (Drift) | Step 2 | Creates baseline, updates latest.json | Export fails |
| Drift loads new baseline | Step 2 | Drift Monitor shows new baseline | Stale baseline |
| Backtest Lab removed | Step 3 | Tab gone, no errors | Broken references |
| Baseline export still works | Step 3 | Export from Drift Monitor succeeds | Lost capability |

---

## Validation Minimum
1. `python -m py_compile dashboard.py`
2. Dashboard launch smoke test
3. Baseline-export smoke from replacement path
4. Drift monitor alert actions unaffected

