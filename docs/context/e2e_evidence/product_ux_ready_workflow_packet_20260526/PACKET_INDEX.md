# Terminal Zero Product / UX Ready-Workflow Expert Packet

Date: 2026-05-26
Workspace: `E:\Code\Quant`
Subject: Product / UX expert review for defining the ready-to-use workflow and first screen of Terminal Zero.

## GitHub Alignment

- GitHub repo: https://github.com/nathanku3-hue/Quant
- Active branch: `codex/optimizer-core-structured-diagnostics`
- GitHub branch link: https://github.com/nathanku3-hue/Quant/tree/codex/optimizer-core-structured-diagnostics
- Local HEAD: `cec79312e091107e9a4bbd14ba855c59f2ca5a75`
- Remote branch HEAD: `cec79312e091107e9a4bbd14ba855c59f2ca5a75`
- Commit link: https://github.com/nathanku3-hue/Quant/commit/cec79312e091107e9a4bbd14ba855c59f2ca5a75
- Caveat: local HEAD matches GitHub, but the workspace has substantial uncommitted local context. Treat this packet as a review snapshot for product workflow design, not a pure GitHub release artifact.

## Recommended Read Order

1. `EXPERT_QUESTIONS.md`
2. `docs/context/current_context.md`
3. `docs/context/planner_packet_current.md`
4. `docs/context/bridge_contract_current.md`
5. `docs/context/impact_packet_current.md`
6. `docs/architecture/dashboard_information_architecture.md`
7. `docs/architecture/dashboard_product_spec.md`
8. `views/page_registry.py`
9. `views/discovery_view.py`
10. `views/strategy_view.py`
11. `tests/test_dash_1_page_registry_shell.py`
12. `tests/test_dash_2_portfolio_ytd.py`

## Included Context Classes

- Product canon: `PRD.md`, `PRODUCT_SPEC.md`, `docs/prd.md`, `docs/spec.md`.
- Current truth: context, planner, bridge, impact, done, multi-stream, post-phase, observability, and dirty-worktree manifest.
- Dashboard/Product UX docs: information architecture, product spec, page registry plan, migration plan, signal taxonomy, GodView wireframe, and daily brief spec.
- Runtime surfaces: `dashboard.py`, `views/page_registry.py`, `views/discovery_view.py`, `views/strategy_view.py`, `views/optimizer_view.py`.
- Product-state objects: candidate-card schema, opportunity states/transitions, MU/MSFT candidate cards, discovery/scout sample inputs.
- UX regression tests: dashboard route shell, Portfolio & Allocation, optimizer view, timeline AppTest, candidate-card tests, and context-packet tests.

## What This Packet Is For

Use this packet to answer:

- What should the first screen be after a successful boot?
- What is the ready-to-use workflow for a research operator?
- What must be visible immediately versus one click away?
- How should the UI communicate research status without implying advice, scoring, ranking, alerts, or trades?

## What This Packet Is Not For

- Do not decide optimizer math.
- Do not approve provider ingestion.
- Do not authorize ranking, scoring, buy/sell/hold, alerts, broker actions, or autonomous allocation.
- Do not treat local uncommitted packet context as safe-boot GitHub truth.
