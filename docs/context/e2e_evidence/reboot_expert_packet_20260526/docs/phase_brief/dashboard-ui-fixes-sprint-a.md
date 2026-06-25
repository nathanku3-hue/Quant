# Dashboard UI Fixes - Final Executable Plan

**Status**: ✅ COMPLETE (Sprint A)
**Date**: 2026-03-05
**Completed**: 2026-03-05
**Scope**: Two sprints - Sprint A (ship now), Sprint B (deferred)

---

## Sprint A: Safe Executable Subset (Ship Now)

**Scope**: Tab discoverability, metrics source fix, formula optimization, sniper layout
**Risk**: Low - No baseline export changes, no Backtest Lab removal

### Changes

#### Change A1: Promote Tabs (Keep Backtest Lab)
**File**: `dashboard.py:1033`

**Current**:
```python
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Ticker Pool & Proxies",
    "🔬 Daily Scan",
    "📈 Backtest Lab",
    "🧩 Modular Strategies",
    "💼 Portfolio Builder",
    "🔍 Drift Monitor"
])
```

**New**:
```python
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Ticker Pool & Proxies",
    "🏥 Data Health",           # NEW
    "🔍 Drift Monitor",          # PROMOTED
    "🔬 Daily Scan",
    "📈 Backtest Lab",           # KEEP (moved to tab5)
    "🧩 Modular Strategies",
    "💼 Portfolio Builder",
])
```

**Content Mapping**:
- `tab1`: No change (Ticker Pool)
- `tab2`: NEW - Move Data Health from sidebar (lines 870-901)
- `tab3`: Drift Monitor (was tab6, lines 2017-2024)
- `tab4`: Daily Scan (was tab2, lines 1189-1506)
- `tab5`: Backtest Lab (was tab3, lines 1511-1579) - KEEP FUNCTIONAL
- `tab6`: Modular Strategies (was tab4, lines 1649-1894)
- `tab7`: Portfolio Builder (was tab5, lines 1899-1955)

**Acceptance**: All tabs render, Backtest Lab still functional at tab5

---

#### Change A2: Move Data Health to Tab
**File**: `dashboard.py:870-901` → move to `tab2`

**Sidebar** (keep compact badge):
```python
with st.sidebar:
    st.markdown(f"**Last Sync:** {time_str}")
    if st.button("🔄 Force Engine Refresh", type="primary"):
        run_and_save_scan()
        st.rerun()

    # Compact health badge
    badge_color = "#00cc66" if health_status == "HEALTHY" else "#ffb020"
    st.markdown(
        f'<span style="color:{badge_color};">● {health_status}</span>',
        unsafe_allow_html=True
    )

    st.divider()
    st.header("🛡️ Hedge Harvester")
    # ... existing hedge code
```

**Tab 2** (full Data Health view):
```python
with tab2:
    st.header("🏥 Data Health Monitor")

    # Move lines 870-901 here (health status, degraded signals table)
    health_pct = int(round(health_ratio * 100))
    badge_color = "#00cc66" if health_status == "HEALTHY" else "#ffb020"
    # ... rest of existing Data Health code
```

**Acceptance**: Sidebar shows compact badge, tab2 shows full details

---

#### Change A3: Fix Metrics Source (Correct Path)
**File**: `core/data_orchestrator.py`

**Helper function** (moved out of the view in the Portfolio Data Boundary Refactor):
```python
def load_strategy_metrics_from_results() -> dict[str, dict]:
    """
    Load strategy metrics from canonical source.

    Source: data/backtest_results.json (dashboard.py:32)

    Returns:
        {
            "strategy_name": {
                "cagr": float,
                "sharpe": float,
                "max_dd": float,
                "timestamp": str,
            }
        }
    """
    from pathlib import Path
    import json

    results_path = Path("data/backtest_results.json")

    if not results_path.exists():
        return {}

    try:
        with open(results_path) as f:
            data = json.load(f)

        # Coerce to expected types with guards
        metrics = {}
        for name, values in data.items():
            if not isinstance(values, dict):
                continue  # Skip malformed entries

            metrics[name] = {
                "cagr": float(values.get("cagr", 0)),
                "sharpe": float(values.get("sharpe", 0)),
                "max_dd": float(values.get("max_dd", 0)),
                "timestamp": str(values.get("timestamp", "unknown")),
            }

        return metrics

    except (json.JSONDecodeError, ValueError, KeyError) as e:
        # Fallback to empty on parse errors
        return {}
```

**Update method dropdown**:
```python
method = st.selectbox(
    "Method",
    [
        "Auto (Best CAGR)",      # NEW
        "Auto (Best Sharpe)",    # NEW
        "Inverse Volatility",
        "Mean-Variance (Max Sharpe)",
        "Mean-Variance (Min Volatility)",
        "Mean-Variance (Max Return)",
    ],
    index=2,  # Default to Inverse Volatility
)

if method == "Auto (Best CAGR)":
    metrics = load_strategy_metrics_from_results()

    if not metrics:
        st.warning("No backtest results found. Using Inverse Volatility.")
        method = "Inverse Volatility"
    else:
        best_strat = max(metrics.items(), key=lambda x: x[1]["cagr"])
        name, data = best_strat

        st.info(
            f"Using: {name} "
            f"(CAGR: {data['cagr']*100:.1f}%, "
            f"Sharpe: {data['sharpe']:.2f}, "
            f"updated: {data['timestamp'][:10]})"
        )

        # Use Inverse Volatility as optimization method
        # (strategy-specific methods not in current optimizer)
        method = "Inverse Volatility"

elif method == "Auto (Best Sharpe)":
    metrics = load_strategy_metrics_from_results()

    if not metrics:
        st.warning("No backtest results found. Using Mean-Variance (Max Sharpe).")
        method = "Mean-Variance (Max Sharpe)"
    else:
        best_strat = max(metrics.items(), key=lambda x: x[1]["sharpe"])
        name, data = best_strat

        st.info(
            f"Using: {name} "
            f"(Sharpe: {data['sharpe']:.2f}, "
            f"CAGR: {data['cagr']*100:.1f}%, "
            f"updated: {data['timestamp'][:10]})"
        )

        method = "Mean-Variance (Max Sharpe)"
```

**Acceptance**: Auto-selection reads `data/backtest_results.json`, shows correct strategy

---

#### Change A4: Add Cash Row (Always Show 0.00%)
**File**: `views/optimizer_view.py` (before table rendering, after allocation_df construction)

**Location**: After line 327 (where allocation_df is built), before st.dataframe rendering

```python
# Always show cash row for transparency (optimizer is fully-invested)
# Append numeric values BEFORE formatting (not pre-formatted strings)
# Use internal lowercase schema (permno, ticker, weight, allocation_usd, latest_price, est_shares)
total_weight = weights.sum()
cash_weight = 1.0 - total_weight
cash_allocation = portfolio_value * cash_weight

# Cash row with numeric values (will be formatted by .style.format later)
cash_row = pd.DataFrame([{
    "permno": "CASH",
    "ticker": "CASH",
    "sector": "Cash",
    "weight": float(cash_weight),
    "allocation_usd": float(cash_allocation),
    "latest_price": np.nan,
    "est_shares": np.nan,
}])

allocation_df = pd.concat([allocation_df, cash_row], ignore_index=True)

st.caption("Note: Optimizer enforces fully-invested constraint (cash = 0.00%)")
```

**Acceptance**: Cash row always visible, shows 0.00% for fully-invested portfolios

---

#### Change A5: Optimize Formula Loading
**File**: `dashboard.py:1809` (Modular Strategies formula display)

**Add caching** (before formula display):
```python
# Cache formula strings only (not st.latex renders)
@st.cache_data
def get_strategy_formulas() -> dict[str, str]:
    """Cache formula strings from STRATEGY_REGISTRY."""
    return {name: strat["core_math"] for name, strat in STRATEGY_REGISTRY.items()}

# Load once per session
if "formulas_loaded" not in st.session_state:
    st.session_state.formula_cache = get_strategy_formulas()
    st.session_state.formulas_loaded = True
```

**Update formula rendering**:
```python
if show_all or clicked_col == "Strategy":
    st.markdown("**🎯 Strategy — Core Math:**")
    formula = st.session_state.formula_cache.get(sel_strat, "")
    if formula:
        st.latex(formula)  # Render fresh (not cached)
    else:
        st.caption("No formula available")
```

**Acceptance**: Formulas load <1s, no caching warnings in logs

---

#### Change A6: Fix Sniper View Stacking (Deterministic Jitter)
**File**: `dashboard.py:1255-1294` (Sniper view collision detection)

**Replace `calculate_plot_y` function**:
```python
def calculate_plot_y_deterministic(df):
    """
    Calculate Y positions with deterministic jitter.

    Prevents label flicker across Streamlit reruns by using
    ticker hash + date seed for stable positioning.

    Returns:
        display_y: List of Y positions
        labels: List of ticker labels
    """
    import hashlib
    from datetime import datetime as dt

    display_y = []
    placed_points = []
    labels = []

    # Deterministic seed from date (stable within day)
    date_seed = dt.now().strftime("%Y-%m-%d")

    for _, r in df.iterrows():
        ticker = r['Ticker']
        base_y = r['Score']
        fund_bonus = (r.get('Delta_Margin', 0) * 100) + (r.get('Delta_Demand', 0) * 20)
        target_y = base_y + fund_bonus

        x_pos = float(r['Tech_Support_Dist'])

        # Deterministic jitter from ticker hash
        ticker_hash = int(hashlib.md5(f"{ticker}{date_seed}".encode()).hexdigest(), 16)
        x_jitter = (ticker_hash % 100) / 100.0 - 0.5  # Range: [-0.5, 0.5]

        # Reduced collision detection (prevent tall stacking)
        max_iter = 10  # Was 30
        collision_threshold = 1.5
        vertical_bump = 1.5

        for _ in range(max_iter):
            collision = False
            for (px, py) in placed_points:
                if abs(px - x_pos) < collision_threshold and abs(py - target_y) < collision_threshold:
                    collision = True
                    target_y += vertical_bump
                    x_pos += x_jitter * 0.3  # Horizontal spread on collision
                    break
            if not collision:
                break

        placed_points.append((x_pos, target_y))
        display_y.append(target_y)
        labels.append(ticker)

    return display_y, labels
```

**Update call site** (line 1291):
```python
display_ys, text_labels = calculate_plot_y_deterministic(combined_df)
```

**Acceptance**: No label flicker across reruns, labels readable

---

### Sprint A Automated Tests

**File**: `tests/test_dashboard_sprint_a.py` (NEW)

**Note**: Tests below are pseudocode templates. Convert to executable tests with proper mocks/fixtures before running.

```python
# Pseudocode - requires implementation

def test_tab_count():
    """Verify 7 tabs after promotion."""
    # TODO: Mock st.tabs, import dashboard, verify tab_names length
    # assert len(tab_names) == 7
    pass

def test_tab_order():
    """Verify tab order."""
    # TODO: Mock st.tabs, verify tab_names[1] == "🏥 Data Health"
    # assert tab_names[2] == "🔍 Drift Monitor"
    # assert tab_names[4] == "📈 Backtest Lab"
    pass

def test_metrics_source():
    """Verify metrics loaded from backtest_results.json."""
    from core.data_orchestrator import load_strategy_metrics_from_results
    metrics = load_strategy_metrics_from_results()
    # Verify structure (may be empty if file doesn't exist)
    assert isinstance(metrics, dict)

def test_cash_row_numeric_types():
    """Verify cash row uses numeric values, not pre-formatted strings."""
    # TODO: Mock optimizer output, build allocation table
    # cash_row = allocation_df[allocation_df["Ticker"] == "CASH"]
    # assert isinstance(cash_row["Weight"].iloc[0], (int, float))
    # assert isinstance(cash_row["Allocation ($)"].iloc[0], (int, float))
    pass

def test_sniper_deterministic():
    """Verify sniper layout stable across calls."""
    # TODO: Create mock DataFrame with Ticker, Score, Tech_Support_Dist
    # y1, labels1 = calculate_plot_y_deterministic(df)
    # y2, labels2 = calculate_plot_y_deterministic(df)
    # assert y1 == y2  # Same input → same output
    # assert labels1 == labels2
    pass
```

---

### Sprint A Manual Smoke Checklist

- [ ] `python -m py_compile dashboard.py`
- [ ] `python -m py_compile views/optimizer_view.py`
- [ ] Dashboard launches without errors
- [ ] Tab 1: Ticker Pool renders
- [ ] Tab 2: Data Health shows full details
- [ ] Tab 3: Drift Monitor renders
- [ ] Tab 4: Daily Scan renders
- [ ] Tab 5: Backtest Lab still functional (can trigger backtest)
- [ ] Tab 6: Modular Strategies renders
- [ ] Tab 7: Portfolio Builder renders
- [ ] Sidebar: Compact health badge visible
- [ ] Portfolio Builder: "Auto (Best CAGR)" selects correct strategy
- [ ] Portfolio Builder: Cash row shows 0.00%
- [ ] Modular Strategies: Formulas load quickly (<1s)
- [ ] Daily Scan Sniper: Labels don't flicker on rerun
- [ ] Baseline export: Still works from Backtest Lab (tab5)

---

### Sprint A Rollback

If any issue:
1. Revert specific file changes via git
2. Keep earlier changes that passed
3. Dashboard remains functional throughout

**Critical**: Backtest Lab remains at tab5, baseline export unchanged

---

## Sprint B: Deferred (Blocked Until Contracts Ready)

**Scope**: Boolean expression engine, Backtest Lab removal
**Blockers**:
1. Baseline export replacement requires concrete data source contract
2. Expression parser needs full specification

### Deferred Changes

#### Change B1: Boolean Expression Engine
**Status**: BLOCKED - Needs specification

**Requirements**:
- Tokenization: `\bAND\b|\bOR\b|\bNOT\b` (case-insensitive, word-bounded)
- Full token consumption validation
- Unknown strategy → fail closed
- Tests for operator-inside-word edge cases
- Universe definition for NOT semantics

**File**: `strategies/strategy_expression_parser.py` (NEW)

**Acceptance Criteria**:
- [ ] Tokenizes `(Infinity Governor OR Rule of 100) AND High Margin Gate` correctly
- [ ] Rejects trailing tokens: `A AND B OR` → error
- [ ] Handles unknown strategies: `Unknown Strategy` → error
- [ ] Handles operator substrings: `Governor` (contains OR) → parses as name
- [ ] NOT requires universe: `A AND NOT B` → A - B

---

#### Change B2: Backtest Lab Removal
**Status**: BLOCKED - Baseline export replacement not ready

**Requirements**:
1. Define baseline export data sources:
   - `target_weights`: Historical matrix (date × permno)
   - `returns_df`: Matching returns matrix
   - Source: Latest backtest artifacts or feature store
2. Implement baseline export in Drift Monitor (tab3)
3. Validate: Export from Drift Monitor → `data/backtest_baselines/latest.json` updates
4. Only then remove Backtest Lab tab

**Acceptance Criteria**:
- [ ] Baseline export works from Drift Monitor
- [ ] `data/backtest_baselines/latest.json` updates correctly
- [ ] Drift Monitor loads new baseline
- [ ] Backtest Lab tab removed
- [ ] No broken references

---

## Summary

**Sprint A (Ship Now)**:
- 6 changes: Tab promotion, Data Health tab, metrics fix, cash row, formula cache, sniper fix
- Low risk: No baseline export changes, Backtest Lab kept functional
- Automated tests + manual smoke checklist
- Independent rollback per change

**Sprint B (Deferred)**:
- 2 changes: Expression engine, Backtest Lab removal
- Blocked: Needs contracts for baseline export and parser specification
- Will be planned separately once blockers resolved

**Critical Paths Preserved**:
- Baseline export: Still works from Backtest Lab (tab5)
- Drift monitoring: Unchanged
- Strategy metrics: Fixed to use correct source (`backtest_results.json`)

---

## File Summary

**Modified**:
- `dashboard.py`: Tab promotion (line 1033), Data Health move (870-901 → tab2), formula cache (1809), sniper fix (1255-1294)
- `views/optimizer_view.py`: Metrics loader (top), auto-selection (146), cash row (337)

**Created**:
- `tests/test_dashboard_sprint_a.py`: Automated tests

**Unchanged**:
- `core/engine.py`: Baseline export unchanged
- `views/auto_backtest_view.py`: Backtest Lab unchanged
- `data/backtest_baselines/latest.json`: Pointer path unchanged

---

**Ready for Approval**: Sprint A only (Sprint B deferred)
