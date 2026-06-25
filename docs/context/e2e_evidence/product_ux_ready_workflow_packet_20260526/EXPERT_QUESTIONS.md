# Product / UX Expert Questions: Ready-To-Use Workflow And First Screen

GitHub repo: https://github.com/nathanku3-hue/Quant
GitHub branch: https://github.com/nathanku3-hue/Quant/tree/codex/optimizer-core-structured-diagnostics
Commit: https://github.com/nathanku3-hue/Quant/commit/cec79312e091107e9a4bbd14ba855c59f2ca5a75

Local packet caveat: local HEAD matches the remote branch at `cec79312e091107e9a4bbd14ba855c59f2ca5a75`, but this packet includes uncommitted local context and runtime surfaces. Please separate "already on GitHub" from "local current product truth."

## Mission

Define what Terminal Zero should feel like when it is genuinely ready to use after boot. The product should be a local-first quantitative research console that helps the operator inspect state, evidence, data health, replay status, and next safe research action without implying recommendations, rankings, alerts, or trades.

## Current Product Shape

- Current visible route shell has three pages: `Portfolio & Allocation`, `Discovery & Analysis`, and `Entry/Exit Strategy`.
- `Portfolio & Allocation` is currently the default route and carries the most integrated workflow: optimizer controls, replay allocation, YTD/performance, data freshness, and fail-closed diagnostics.
- Candidate cards currently exist as governed research objects, not dashboard-action objects.
- Dashboard legacy labels can still look action-shaped, so UX language and hierarchy matter.
- Boot/architecture expert recommendation says the first implementation slice should create one preflight verdict before staging feature work.
- Data expert sequence should ensure "boot ready" also means data-safe, not only app-startable.

## High-Value Real Questions

1. What should the first screen be immediately after boot: Portfolio & Allocation, Command Center, Research Queue, Data Health, or a hybrid readiness cockpit?
2. What is the user's first 60-second workflow after boot?
3. What single question should the first screen answer first: "Can I use this system today?", "What changed?", "What needs attention?", or "What research object should I inspect next?"
4. What are the minimum visible readiness states: Ready, Degraded, Blocked, Local Planning, Boot Candidate, Safe Boot?
5. What information must be above the fold without requiring tabs: boot verdict, data freshness, current portfolio/replay state, open blockers, next safe action, GitHub/local state?
6. What should be one click away rather than first screen: full data health, replay diagnostics, candidate-card detail, strategy lab, historical SAW evidence, dirty-worktree detail?
7. Should `Portfolio & Allocation` remain the default page, or should a new `Command Center` become default once boot preflight exists?
8. If `Command Center` becomes default, what exact cards or bands should it contain, and what should it intentionally omit?
9. How should the UI show candidate cards as research-only objects without making them look ranked, scored, recommended, or actionable?
10. How should the UI distinguish optimizer output, replay output, lifecycle audit intent, current holdings, cash-closed states, and unavailable states?
11. Which current labels are dangerous because they imply buy/sell/hold, recommendation, conviction, or model authority?
12. What should replace action-shaped labels in the dashboard: status language, evidence-state language, blocked-reason language, or workflow-stage language?
13. What is the product boundary between `Discovery & Analysis` and `Entry/Exit Strategy`?
14. What does a useful research queue look like before ranking/scoring is allowed?
15. How should the UI expose "why this is blocked" without turning blockers into advice?
16. How should boot status integrate with the Streamlit UI: pre-app gate, top banner, sidebar badge, dedicated page, or generated markdown panel?
17. What should happen visually when data is stale, replay is unavailable, saved artifact identity fails, or optimizer falls back?
18. What should be the one canonical "next safe action" pattern in the UI?
19. What information architecture should survive into the endgame: 3-page shell, 8-page target IA, or boot cockpit plus 3 workflows?
20. What should be removed, merged, or demoted because it creates product fragmentation?

## Desired Expert Output

Please return:

1. Recommended first screen.
2. Ready-to-use workflow in 5-7 steps.
3. Above-the-fold content inventory.
4. One-click secondary surfaces.
5. Copy/label rules that prevent advice-like interpretation.
6. Page map recommendation: keep 3 pages, move to Command Center, or hybrid.
7. First UX implementation slice with exact files to touch and tests to run.

## Boundaries

- Do not recommend broker actions, alerts, autonomous allocation, rankings, scores, buy/sell/hold labels, or provider ingestion.
- Do not require a visual redesign before the boot control plane exists.
- Prefer status, evidence, blocker, and workflow language over recommendation language.
- Treat GitHub-aligned commit state and local uncommitted truth as separate UX states.
