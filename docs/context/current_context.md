## What Was Done
- Fast-forwarded `main` from `e4cf949` to exact `9af5259` (C+P only).
- Verified remote `main == 9af5259`.
- Tagged `pit-alpha-authority-cut-1-terminal` at that exact SHA.
- Opened `codex/pit-source-authority-1` from `9af5259`.
- Reassessed canonical maturity to `70/100` for operability/custody/replay only.

## What Is Locked
- `dashboard.py` sole product.
- Published tip `9af5259` and terminal tag must not be rewritten.
- Score claim boundary: operability/custody/replay only.
- Limited Live closed.
- No provider, optimizer, broker, historical repair, or compatibility work.

## What Is Next
- Ship one narrow functional slice: immutable market packet through the existing operated loop.
- Keep all other programmes closed.

## First Command
```text
`python -m pytest -q tests/test_gv_pit_transaction.py tests/test_gv_pit_operated_capital.py tests/test_gv_pit_operated_rotation.py tests/test_dash_1_page_registry_shell.py`
```
