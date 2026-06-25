# Candidate Scope Memo

## P0 - Pre-work Scope Selection
Add `.codex/skills/scope-selector/SKILL.md`.

Goal:
Choose the smallest valuable next product slice using CEO/Product, CTO/Architecture, COO/Ops, Quant Strategy, and Builder lenses.

Expected output:
- chosen scope
- why now
- why not alternatives
- low confidence questions
- out-of-boundary items
- stop rules
- demo target
- file budget

## P0 - Expert Context Packer
Add `.codex/skills/expert-context-packer/SKILL.md` and optionally `scripts/build_expert_packet.py`.

Goal:
Build curated expert packets instead of dumping the full repo or relying only on GitHub pushes.

## P0 - Worker Demo Contract
Add `docs/templates/worker_done_contract.md`.

Goal:
Workers must report where the user can audit the product: URL, route/page, what to click/look at, screenshot/AppTest proof, tests, known limits, and changed files.

## P1 - Multi-Expert Reconciliation
Add `docs/templates/expert_reconciliation_matrix.md`.

Goal:
Gather Product, Architecture, Quant, and Ops advice in a shared schema and let the orchestrator reconcile conflicts.

## P1 - Multi-Stream Contracts
Add `docs/templates/stream_contract.md`.

Goal:
Plan Research, Frontend/UI, Backend/Data, and Governance/Ops streams with dependencies, owned files, blocked files, acceptance checks, and integration gates.

## P2 - Harness Feedback in SAW
Add a small SAW section for repeated harness friction, not automatic rule changes every round.
