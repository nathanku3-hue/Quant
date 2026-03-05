# Dashboard UI Fixes - Final Executable Plan

**Status**: Planning (awaiting approval)
**Date**: 2026-03-05
**Owner**: UI stream

## Scope
Resolve 6 dashboard UX issues with zero baseline-export regression risk.

## Critical Constraints (From Code Investigation)

1. **Metrics Source**: `data/backtest_results.json` (dashboard.py:32), NOT `auto_backtest_cache.json`
2. **Baseline Path**: `data/backtest_baselines/latest.json` (dashboard.py:238)
3. **Optimizer Contract**: Fully-invested, long-only (optimizer.py:78: `sum(weights) == 1.0`)
4. **STRATEGY_REGISTRY**: Embedded in dashboard.py:1586 (cannot import from strategy modules)
5. **Baseline Export**: Requires historical `target_weights` + `returns_df` matrices (engine.py:156)
6. **Current Baseline Path**: `views/auto_backtest_view.py:184` → `engine.run_backtest_with_baseline_export()`

## Blocker Resolution Contracts

### Contract 1: Strategy Metrics Loader (Correct Source)

**File**: `strategies/strategy_metrics_loader.py` (NEW)

```python
"""
Strategy Metrics Loader

Source of Truth: data/backtest_results.json (dashboard.py:32)
NO imports from dashboard.py to avoid circular dependencies.
"""

from pathlib import Path
import json

def load_strategy_metrics(registry: dict) -> dict[str, dict]:
    """
    Load strategy performance metrics.

    Args:
        registry: STRATEGY_REGISTRY dict (injected, not imported)

    Returns:
        {
            "strategy_name": {
                "cagr": float,
                "sharpe": float,
                "max_dd": float,
                "timestamp": str,
                "source": "backtest_results" | "registry"
            }
        }
    """
    results_path = Path("data/backtest_results.json")
    metrics = {}

    # Priority 1: backtest_results.json
    if results_path.exists():
        with open(results_path) as f:
            data = json.load(f)
            for name, values in data.items():
                metrics[name] = {
                    "cagr": float(values["cagr"]),
                    "sharpe": float(values["sharpe"]),
                    "max_dd": float(values["max_dd"]),
                    "timestamp": values["timestamp"],
                    "source": "backtest_results",
                }

    # Priority 2: Fallback to registry
    for name, strat in registry.items():
        if name not in metrics:
            bt_data = strat.get("backtest", {})
            cagr_raw = bt_data.get("cagr", 0)

            # Parse string CAGR like "+12.3%" or float 0.123
            if isinstance(cagr_raw, str):
                cagr = float(cagr_raw.strip("+%")) / 100.0 if cagr_raw else 0.0
            else:
                cagr = float(cagr_raw)

            metrics[name] = {
                "cagr": cagr,
                "sharpe": float(bt_data.get("sharpe", 0)),
                "max_dd": float(bt_data.get("max_dd", 0)),
                "timestamp": "registry",
                "source": "registry",
            }

    return metrics
```

**Acceptance**: Returns all strategies, prioritizes `backtest_results.json`, no dashboard imports.

---

### Contract 2: Baseline Export - Keep Backtest Lab Until Replacement Ready

**Decision**: DO NOT remove Backtest Lab in this phase. Baseline export replacement requires:
1. Historical `target_weights` matrix (not just live snapshot)
2. Matching `returns_df` with same date range and permno columns
3. Integration with `core.engine.run_backtest_with_baseline_export()`

**Current proven path**: `views/auto_backtest_view.py:184`

**Action**: Keep Backtest Lab tab functional. Add baseline export to Drift Monitor in FUTURE phase after defining concrete data sources.

**This Phase**: Only promote tabs, do NOT delete Backtest Lab.

---

### Contract 3: Expression Parser Tokenization (Hardened)

**File**: `strategies/strategy_expression_parser.py` (NEW)

```python
"""
Strategy Boolean Expression Parser

Tokenization: Word-boundary operators, case-insensitive, full consumption validation
"""

import re
from typing import Set, Callable

class StrategyExpressionParser:
    def __init__(self, strategy_pool_loader: Callable[[str], Set[str]], universe_loader: Callable[[], Set[str]]):
        self.load_pool = strategy_pool_loader
        self.load_universe = universe_loader

    def tokenize(self, expression: str) -> list[str]:
        """
        Tokenize with word-boundary operators.

        Rules:
            - Operators: AND, OR, NOT (case-insensitive, word-bounded)
            - Parentheses: ( )
            - Strategy names: everything else (can contain spaces)

        Example:
            "(Infinity Governor OR Rule of 100) AND High Margin Gate"
            → ['(', 'Infinity Governor', 'OR', 'Rule of 100', ')', 'AND', 'High Margin Gate']
        """
        # Normalize operators to uppercase
        expr_normalized = expression.upper()

        # Split on word-bounded operators and parentheses
        pattern = r'(\(|\)|\bAND\b|\bOR\b|\bNOT\b)'
        tokens = re.split(pattern, expr_normalized)

        # Clean whitespace, filter empty
        tokens = [t.strip() for t in tokens if t.strip()]

        # Restore original case for strategy names (not operators)
        result = []
        expr_lower = expression.lower()
        pos = 0

        for token in tokens:
            if token in ('(', ')', 'AND', 'OR', 'NOT'):
                result.append(token)
            else:
                # Find original case in expression
                token_lower = token.lower()
                idx = expr_lower.find(token_lower, pos)
                if idx >= 0:
                    original = expression[idx:idx+len(token)]
                    result.append(original.strip())
                    pos = idx + len(token)
                else:
                    result.append(token)

        return result

    def parse(self, expression: str) -> Set[str]:
        """Parse and evaluate expression."""
        tokens = self.tokenize(expression)
        result, pos = self._parse_expr(tokens, 0)

        # Validate full token consumption
        if pos < len(tokens):
            raise ValueError(f"Unexpected token at position {pos}: '{tokens[pos]}'")

        return result

    def _parse_expr(self, tokens: list, pos: int) -> tuple[Set[str], int]:
        """Parse OR expression (lowest precedence)."""
        left, pos = self._parse_term(tokens, pos)

        while pos < len(tokens) and tokens[pos] == 'OR':
            pos += 1
            right, pos = self._parse_term(tokens, pos)
            left = left | right

        return left, pos

    def _parse_term(self, tokens: list, pos: int) -> tuple[Set[str], int]:
        """Parse AND expression (higher precedence)."""
        left, pos = self._parse_factor(tokens, pos)

        while pos < len(tokens) and tokens[pos] == 'AND':
            pos += 1
            right, pos = self._parse_factor(tokens, pos)
            left = left & right

        return left, pos

    def _parse_factor(self, tokens: list, pos: int) -> tuple[Set[str], int]:
        """Parse NOT, parentheses, or strategy name (highest precedence)."""
        if pos >= len(tokens):
            raise ValueError("Unexpected end of expression")

        token = tokens[pos]

        if token == 'NOT':
            pos += 1
            operand, pos = self._parse_factor(tokens, pos)
            universe = self.load_universe()
            return universe - operand, pos

        elif token == '(':
            pos += 1
            result, pos = self._parse_expr(tokens, pos)
            if pos >= len(tokens) or tokens[pos] != ')':
                raise ValueError(f"Missing closing parenthesis at position {pos}")
            pos += 1
            return result, pos

        else:
            # Strategy name
            try:
                pool = self.load_pool(token)
                return pool, pos + 1
            except Exception as e:
                raise ValueError(f"Unknown strategy: '{token}'") from e
```

**Acceptance**: Correctly tokenizes names with spaces, rejects trailing tokens, handles operator substrings.

---

### Contract 4: Cash Row Display (Optimizer Contract Aware)

**Current Optimizer Behavior**:
- Fully-invested constraint: `sum(weights) == 1.0` (optimizer.py:78)
- Weights normalized in `optimizer_view.py:241`

**Decision**: Show CASH row at 0.00% always for transparency, even when fully invested.

**File**: `views/optimizer_view.py` (after line 337)

```python
# Always show cash row for transparency (even if 0.00%)
total_weight = weights.sum()
cash_weight = 1.0 - total_weight
cash_allocation = portfolio_value * cash_weight

# Label based on sign
if abs(cash_weight) < 0.001:
    cash_label = "CASH (Fully Invested)"
elif cash_weight > 0:
    cash_label = "CASH (Uninvested)"
else:
    cash_label = "BORROWED (Leveraged)"

cash_row = pd.DataFrame([{
    "Permno": "CASH",
    "Ticker": "CASH",
    "Sector": "Cash/Leverage",
    "Weight": f"{cash_weight*100:+.2f}%",
    "Allocation ($)": f"${cash_allocation:+,.2f}",
    "Latest Price ($)": "-",
    "Estimated Shares": "-",
}])
allocation_df = pd.concat([allocation_df, cash_row], ignore_index=True)
```

**Acceptance**: Cash row always visible, shows 0.00% for fully-invested, negative for leverage.

---

### Contract 5: Tab Migration (Staged, No Backtest Deletion)

**Step 1: Promote Tabs (Safe - Keep All Existing Tabs)**

```python
# dashboard.py:1033
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Ticker Pool & Proxies",
    "🏥 Data Health",           # NEW
    "🔍 Drift Monitor",          # PROMOTED
    "📈 Backtest Lab",           # KEEP (baseline export dependency)
    "🔬 Daily Scan",
    "🧩 Modular Strategies",
    "💼 Portfolio Builder",
])
```

**Step 2: Move Data Health Content**

Move `dashboard.py:870-901` (Data Health code) from sidebar to `tab2`.

Keep compact badge in sidebar:
```python
with st.sidebar:
    # ... existing code
    badge_color = "#00cc66" if health_status == "HEALTHY" else "#ffb020"
    st.markdown(f'<span style="color:{badge_color};">● {health_status}</span>', unsafe_allow_html=True)
```

**Step 3: DO NOT Delete Backtest Lab**

Backtest Lab remains at `tab4` until baseline export replacement is implemented and validated in future phase.

---

## Implementation Tasks

### Task 1: Create Strategy Metrics Loader
**File**: `strategies/strategy_metrics_loader.py`
- Implement `load_strategy_metrics(registry)` with dependency injection
- Read from `data/backtest_results.json`
- Fallback to registry for missing strategies
- Parse string CAGR formats

**Test**: Unit test with mock registry, verify priority order

### Task 2: Add Metrics Loader to Portfolio Builder
**File**: `views/optimizer_view.py:146`

```python
method = st.selectbox(
    "Method",
    [
        "Auto (Best CAGR)",  # NEW
        "Auto (Best Sharpe)",  # NEW
        "Inverse Volatility",
        "Mean-Variance (Max Sharpe)",
        "Mean-Variance (Min Volatility)",
        "Mean-Variance (Max Return)",
    ],
    index=2,  # Default to Inverse Volatility
)

if method == "Auto (Best CAGR)":
    from strategies.strategy_metrics_loader import load_strategy_metrics
    from dashboard import STRATEGY_REGISTRY  # Import at function scope

    metrics = load_strategy_metrics(STRATEGY_REGISTRY)
    best_strat = max(metrics.items(), key=lambda x: x[1]["cagr"])
    name, data = best_strat

    st.info(f"Using: {name} (CAGR: {data['cagr']*100:.1f}%, source: {data['source']}, updated: {data['timestamp']})")

    # Use strategy's preferred method
    method = STRATEGY_REGISTRY[name].get("optimization_method", "Inverse Volatility")

elif method == "Auto (Best Sharpe)":
    # Similar logic
    ...
```

**Test**: Verify auto-selection uses `backtest_results.json`, shows correct strategy

### Task 3: Add Cash Row to Portfolio Builder
**File**: `views/optimizer_view.py:337`
- Always show cash row (even at 0.00%)
- Label based on sign (Fully Invested / Uninvested / Leveraged)

**Test**: Verify cash row displays for fully-invested, partial, leveraged scenarios

### Task 4: Implement Expression Parser
**File**: `strategies/strategy_expression_parser.py`
- Implement tokenization with word-boundary operators
- Implement precedence (NOT > AND > OR)
- Validate full token consumption
- Handle unknown strategies gracefully

**Test**: Unit tests for `(A OR B) AND C`, `A AND NOT B`, trailing tokens, unknown strategies

### Task 5: Add Expression Builder UI
**File**: `dashboard.py` (before Modular Strategies table, ~line 1650)

```python
st.markdown("### 🎯 Strategy Combination Builder")

expression = st.text_input(
    "Boolean Expression",
    value="(Infinity Governor OR Rule of 100) AND High Margin Gate",
    help="Use AND, OR, NOT, and parentheses. Case-insensitive.",
)

if st.button("🔄 Evaluate Expression"):
    from strategies.strategy_expression_parser import StrategyExpressionParser

    def load_pool(name):
        strat = STRATEGY_REGISTRY.get(name)
        if not strat:
            raise ValueError(f"Unknown strategy: {name}")
        # Load ticker pool
        pool_name = strat.get("ticker_pool", "sovereign_pool")
        return set(load_tickers_for_pool(pool_name))

    def load_universe():
        # Full universe for NOT operations
        return set(load_all_available_tickers())

    parser = StrategyExpressionParser(load_pool, load_universe)

    try:
        result = parser.parse(expression)
        st.success(f"✅ Expression valid. {len(result)} tickers in combined pool.")
        st.dataframe(pd.DataFrame({"Ticker": sorted(result)}), height=300)
    except Exception as e:
        st.error(f"❌ {e}")
```

**Test**: Verify expressions evaluate correctly, error messages clear

### Task 6: Optimize Formula Loading
**File**: `dashboard.py:1809`

```python
# Cache formula strings only (not st.latex renders)
@st.cache_data
def get_strategy_formulas(registry: dict) -> dict[str, str]:
    return {name: strat["core_math"] for name, strat in registry.items()}

# Load once
if "formulas_loaded" not in st.session_state:
    st.session_state.formula_cache = get_strategy_formulas(STRATEGY_REGISTRY)
    st.session_state.formulas_loaded = True

# Render on demand (not cached)
if show_all or clicked_col == "Strategy":
    st.markdown("**🎯 Strategy — Core Math:**")
    formula = st.session_state.formula_cache.get(sel_strat, "")
    st.latex(formula)  # Fresh render each time
```

**Test**: Verify formulas load quickly, no caching warnings

### Task 7: Fix Sniper View Stacking
**File**: `dashboard.py:1252-1294`

```python
def calculate_plot_y_deterministic(df):
    """Deterministic jitter to prevent flicker."""
    import hashlib

    display_y = []
    placed_points = []
    date_seed = datetime.now().strftime("%Y-%m-%d")

    for _, r in df.iterrows():
        ticker = r['Ticker']
        base_y = r['Score']
        x_pos = float(r['Tech_Support_Dist'])

        # Deterministic jitter from ticker hash
        ticker_hash = int(hashlib.md5(f"{ticker}{date_seed}".encode()).hexdigest(), 16)
        x_jitter = (ticker_hash % 100) / 100.0 - 0.5

        target_y = base_y
        max_iter = 10  # Reduced from 30
        collision_threshold = 1.5
        vertical_bump = 1.5

        for _ in range(max_iter):
            collision = False
            for (px, py) in placed_points:
                if abs(px - x_pos) < collision_threshold and abs(py - target_y) < collision_threshold:
                    collision = True
                    target_y += vertical_bump
                    x_pos += x_jitter * 0.3  # Horizontal spread
                    break
            if not collision:
                break

        placed_points.append((x_pos, target_y))
        display_y.append(target_y)

    return display_y
```

**Test**: Verify no flicker across reruns, labels readable

### Task 8: Promote Tabs (No Deletion)
**File**: `dashboard.py:1033`
- Add Data Health tab
- Promote Drift Monitor
- Keep Backtest Lab

**Test**: All tabs render, Backtest Lab still functional

---

## Test Matrix

| Test | Pass Criteria | Rollback Trigger |
|------|---------------|------------------|
| Syntax check | `python -m py_compile dashboard.py` exits 0 | Syntax error |
| Dashboard launch | No exceptions in first 10s | Import/runtime error |
| Metrics loader | Returns all strategies from `backtest_results.json` | Wrong source/missing strategies |
| Auto strategy | Selects best CAGR from `backtest_results.json` | Wrong strategy/stale data |
| Cash row | Always visible, shows 0.00% for fully-invested | Missing/wrong value |
| Expression parser | `(A OR B) AND C` evaluates correctly | Tokenization error |
| Expression UI | Valid expressions succeed, invalid show error | Crash on invalid input |
| Formula cache | Formulas load <1s, no warnings | Slow load/cache warnings |
| Sniper view | No flicker across reruns | Labels flicker/overlap |
| Tab promotion | Data Health + Drift Monitor visible | Missing tabs/broken layout |
| Backtest Lab | Still functional after tab reorder | Broken baseline export |

---

## Validation Checklist

- [ ] `python -m py_compile dashboard.py`
- [ ] `python -m py_compile views/optimizer_view.py`
- [ ] `python -m py_compile strategies/strategy_metrics_loader.py`
- [ ] `python -m py_compile strategies/strategy_expression_parser.py`
- [ ] Dashboard launches without errors
- [ ] Data Health tab renders
- [ ] Drift Monitor tab renders
- [ ] Backtest Lab still functional
- [ ] Auto (Best CAGR) selects correct strategy
- [ ] Cash row displays at 0.00%
- [ ] Expression `(A OR B) AND C` evaluates
- [ ] Sniper view labels don't flicker

---

## Out of Scope (Future Phase)

- Baseline export replacement in Drift Monitor (requires data source definition)
- Backtest Lab tab deletion (blocked until baseline export replacement)
- Partial-investment optimizer mode (requires optimizer contract change)

---

## Rollback Plan

Each task is independently revertible via git. If any task fails validation:
1. Revert specific commit
2. Keep earlier tasks that passed
3. Fix issue and retry

No breaking changes to baseline export or drift monitoring workflows.
