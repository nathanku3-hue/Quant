# Expert Decision Card

RoundID: ROUND-20260530-HARNESS-PATCHING-SCOPE-SELECTION
Purpose: ask experts to resolve harness design questions before patching workflow rules/skills.

Current Problem:
- The current harness is strong at governance/closure after a scope is chosen.
- It is weak at choosing the next valuable scope.
- Expert prompts can become vague or over-governed.
- Workers often report artifacts instead of demo/audit proof.
- Multi-expert and multi-stream planning need explicit reconciliation.
- The repo has messy local state and GitHub/local truth mismatch risk.

Desired Decision:
Choose how to patch the harness so every major round starts with:
1. boot TODO/context,
2. orchestrator low-confidence + out-of-boundary packet,
3. expert review/guidance,
4. orchestrator reconciliation,
5. bounded subagent work,
6. demo-first proof and lean SAW.

Candidate P0 Harness Changes:
- Add scope-selector skill.
- Add expert-context-packer skill/script.
- Add worker demo contract.
- Add small AGENTS.md rules for expert advisory status, file budget, demo proof, and known inherited blockers.

Human/Expert Question:
What is the highest-leverage minimal harness patch that reduces over-governance, messy files, and poor next-scope choice without slowing shipping?
