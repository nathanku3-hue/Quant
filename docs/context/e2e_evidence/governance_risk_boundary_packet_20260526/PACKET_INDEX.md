# Governance / Risk Boundary Expert Packet

Date: 2026-05-26
Workspace: `E:\Code\Quant`
Purpose: focused context for expert review of Terminal Zero governance boundaries: labels, recommendations, scoring, ranking, alerts, broker/trading boundaries, and dashboard language.

## GitHub Alignment

- GitHub repo: https://github.com/nathanku3-hue/Quant
- Active branch: `codex/optimizer-core-structured-diagnostics`
- GitHub branch link: https://github.com/nathanku3-hue/Quant/tree/codex/optimizer-core-structured-diagnostics
- Local HEAD: `cec79312e091107e9a4bbd14ba855c59f2ca5a75`
- Commit link: https://github.com/nathanku3-hue/Quant/commit/cec79312e091107e9a4bbd14ba855c59f2ca5a75
- Alignment note: local HEAD matches the remote branch commit at packet creation time, but the workspace has substantial uncommitted local context. Treat this packet as a local review bundle anchored to GitHub, not a pure clean-branch snapshot.

## Recommended Read Order

1. `GITHUB_ALIGNMENT.txt`
2. `GOVERNANCE_RISK_QUESTIONS.md`
3. `docs/context/current_context.md`
4. `docs/context/planner_packet_current.md`
5. `docs/context/bridge_contract_current.md`
6. `docs/context/impact_packet_current.md`
7. `docs/context/done_checklist_current.md`
8. `docs/context/dirty_worktree_manifest.md`
9. `docs/architecture/dashboard_signal_taxonomy.md`
10. `docs/architecture/discovery_intake_vs_candidate_card.md`
11. `docs/architecture/g8_2_system_scouted_candidate_card_policy.md`
12. `docs/architecture/portfolio_construction_contract.md`
13. `docs/architecture/optimizer_core_policy_audit.md`
14. `dashboard.py`
15. `views/optimizer_view.py`
16. `opportunity_engine/candidate_card_schema.py`
17. `strategies/strategy_replay.py`

## Included Context Classes

- Current truth surfaces and dirty-worktree caveat.
- Product/spec canon and active Phase 65 governance docs.
- Candidate-card, discovery, state-machine, dashboard-signal, portfolio, optimizer, provider, and source-eligibility policies.
- Runtime files where labels, allocation states, replay rows, diagnostics, alerts, and dashboard views can imply actionability.
- Candidate-card and discovery JSON artifacts plus manifests.
- Focused tests that guard non-actionability, state mapping, optimizer policy, replay identity, and dashboard rendering.
- Selected SAW reports for candidate-card, optimizer policy, portfolio universe, replay role, and replay selection boundary rounds.

## Key Caveat For Expert

The repo is intentionally local-first and currently has a broad dirty worktree. The important governance question is not only "what does GitHub say?" but also "can local current truth be presented without becoming investment advice or an executable trading instruction?"

Do not assume `BUY`, `SELL`, `ENTER`, `EXIT`, `WATCH`, `STRONG BUY`, allocation weights, optimizer output, or replay output are permitted recommendations. The packet asks you to decide which terms must be renamed, gated, relabeled, or forbidden before the system is boot-ready.
