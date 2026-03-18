# Phase 51 Factor Algebra Design Starting Point

**Status**: IMPLEMENTATION-AUTHORIZED DESIGN STARTING POINT
**Date**: 2026-04-10
**Authority Context**: Current CEO shipping disposition lifts the prior docs-only hold for Factor Algebra and authorizes implementation to begin from this design artifact.
**Execution State**: Implementation may now start from this document, but this file remains a design brief, not a runtime code spec or live execution contract.

## Governance Activation Note

The earlier docs-only planning lock for Factor Algebra is no longer the active state. This document is now the canonical starting point for bounded implementation work. That change authorizes implementers to derive code tasks and interfaces from this design, but it does **not** turn this brief into the source of truth for executed runtime behavior, production defaults, scheduler activation, or broker-linked semantics.

---

## Purpose

Define the design starting point for a Factor Algebra layer that can express composable ranking, normalization, filtering, and arithmetic over factor signals while remaining explainable, point-in-time disciplined, and implementation-ready.

This document exists to guide implementation, not to replace code, tests, or runtime governance artifacts.

---

## Boundary

### In Scope
- Interface examples for factor expressions
- Operator-overloading surface specification
- Node/type boundaries for an AST-style algebra
- Serialization and explainability expectations
- Design guidance that implementers can now use to start bounded Phase 51 work

### Out of Scope
- Executed runtime behavior guarantees
- Production selector defaults
- Broker, routing, or live capital semantics
- Automatic dashboard activation
- Silent code generation from this document without normal implementation/test/governance review

---

## Implementation Starting Rules

- Treat this file as the design anchor for Factor Algebra implementation.
- Convert these interfaces into bounded code/tasks with normal tests and review gates.
- Keep implementation decisions auditable when they deviate from the examples here.
- Do not read this file as permission to bypass runtime validation, SAW review, or later production governance.

---

## Design Intent

The API should let research users compose factors as readable algebra while preserving:
- point-in-time discipline
- explainable intermediate nodes
- vectorized evaluation over aligned pandas or polars series
- deterministic serialization to a normalized expression tree

The design target is a research and implementation layer that can later feed runtime systems, not a direct execution layer.

---

## Proposed Type Skeleton

```python
class FactorExpr:
    name: str
    dtype: str
    dependencies: tuple["FactorExpr", ...]

    def alias(self, name: str) -> "FactorExpr": ...
    def explain(self) -> dict[str, object]: ...


class Factor(FactorExpr):
    source_key: str
    lag_days: int = 0


class Scalar(FactorExpr):
    value: float


class UnaryExpr(FactorExpr):
    op: str
    operand: FactorExpr


class BinaryExpr(FactorExpr):
    op: str
    left: FactorExpr
    right: FactorExpr


class RollingExpr(FactorExpr):
    op: str
    operand: FactorExpr
    window: int
    min_periods: int
```

Notes:
- `FactorExpr` is a shape-preserving symbolic expression, not an eager series.
- Leaf `Factor` nodes identify governed research inputs such as value, quality, or momentum features.
- `Scalar` wraps literals so mixed scalar/factor algebra remains type-stable.

---

## Interface Examples

### Example 1: Simple Composite

```python
value = Factor("fcf_yield")
quality = Factor("gross_margin")
composite = rank(value) + 0.5 * zscore(quality)
```

### Example 2: Defensive Spread

```python
leverage = Factor("net_debt_to_ebitda")
cash_efficiency = Factor("cash_conversion")
defensive = zscore(cash_efficiency) - zscore(leverage)
```

### Example 3: Rolling Confirmation

```python
eps_revision = Factor("eps_revision_90d")
revision_trend = ts_mean(eps_revision, window=20) / ts_std(eps_revision, window=20)
alpha = clip(rank(revision_trend), lower=0.0, upper=1.0)
```

### Example 4: Explainable Alias

```python
profitability = alias(zscore(Factor("roic")) + zscore(Factor("gross_margin")), "profitability")
stability = alias(-rank(Factor("earnings_volatility")), "stability")
quality_stack = alias(profitability + stability, "quality_stack")
```

---

## Operator Overloading Spec

The factor objects should overload operators into symbolic nodes instead of producing eager numeric outputs.

| Python Operator | Method | Output Node | Notes |
|---|---|---|---|
| `a + b` | `__add__` / `__radd__` | `BinaryExpr(op="add")` | Accept factor-scalar and factor-factor combinations |
| `a - b` | `__sub__` / `__rsub__` | `BinaryExpr(op="sub")` | Preserve operand order |
| `a * b` | `__mul__` / `__rmul__` | `BinaryExpr(op="mul")` | Allow scalar weighting |
| `a / b` | `__truediv__` / `__rtruediv__` | `BinaryExpr(op="div")` | Division-by-zero handling deferred to evaluator |
| `-a` | `__neg__` | `UnaryExpr(op="neg")` | Exact symbolic negation |
| `abs(a)` | `__abs__` | `UnaryExpr(op="abs")` | Useful for spread magnitude |
| `a ** p` | `__pow__` | `BinaryExpr(op="pow")` | Allow scalar exponents only in the initial implementation |
| `a > b` | `__gt__` | `BinaryExpr(op="gt")` | Returns symbolic boolean mask node |
| `a >= b` | `__ge__` | `BinaryExpr(op="ge")` | Symbolic comparison only |
| `a < b` | `__lt__` | `BinaryExpr(op="lt")` | Symbolic comparison only |
| `a <= b` | `__le__` | `BinaryExpr(op="le")` | Symbolic comparison only |
| `a == b` | `__eq__` | `BinaryExpr(op="eq")` | Structural equality stays separate from Python object identity |
| `mask_a & mask_b` | `__and__` | `BinaryExpr(op="and")` | Boolean mask composition only |
| `mask_a \| mask_b` | `__or__` | `BinaryExpr(op="or")` | Boolean mask composition only |
| `~mask` | `__invert__` | `UnaryExpr(op="not")` | Boolean mask inversion only |

Rules:
- Non-factor literals should be promoted to `Scalar`.
- Operators should never evaluate data at construction time.
- Expression trees should be immutable after construction.
- Unsupported mixed dtypes should fail loudly rather than silently coerce.

---

## Functional Helper Surface

The operator-overloading layer should be complemented by named helpers for common research transforms.

```python
rank(expr: FactorExpr) -> FactorExpr
zscore(expr: FactorExpr) -> FactorExpr
clip(expr: FactorExpr, lower: float, upper: float) -> FactorExpr
winsorize(expr: FactorExpr, lower_q: float, upper_q: float) -> FactorExpr
lag(expr: FactorExpr, periods: int) -> FactorExpr
ts_mean(expr: FactorExpr, window: int, min_periods: int | None = None) -> FactorExpr
ts_std(expr: FactorExpr, window: int, min_periods: int | None = None) -> FactorExpr
where(mask: FactorExpr, if_true: FactorExpr, if_false: FactorExpr) -> FactorExpr
```

Helper expectations:
- helpers return symbolic nodes
- helpers preserve explicit parameterization
- helpers expose `explain()` metadata for UI traceability

---

## Expression Metadata Contract

Each expression node should be able to describe itself without execution:

```python
{
  "name": "quality_stack",
  "node_type": "BinaryExpr",
  "op": "add",
  "dtype": "float",
  "dependencies": ["profitability", "stability"],
  "requires_pit_data": true
}
```

The future implementation should make this metadata available for explainability and audit trails.

---

## Open Design Questions

1. Whether boolean mask expressions should live in the same algebra namespace or a parallel filter namespace.
2. Whether rolling-window helpers should accept calendar windows, observation counts, or both.
3. Whether serialization should target plain JSON AST first or a stable mini-DSL round-trip format.

Preferred starting position:
- keep boolean masks in the same symbolic namespace
- use observation-count windows first
- serialize to JSON AST first

Reason: simplest starting point with the least hidden coercion risk.

---

## Guardrail

This design brief now authorizes bounded implementation to begin, but it is still not the source of truth for executed runtime behavior. Code, tests, telemetry, and later governance artifacts must carry the actual runtime contract once implementation starts.
