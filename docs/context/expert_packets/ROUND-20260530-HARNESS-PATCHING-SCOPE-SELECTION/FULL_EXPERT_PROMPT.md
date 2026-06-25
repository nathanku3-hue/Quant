# Full Expert Prompt

You are acting as a fast-shipping expert board for Terminal Zero.

Your job is NOT to perform a broad governance audit.
Your job is to resolve real product/design/architecture/quant uncertainty before implementation.

Use these lenses:
- CEO/Product: smallest valuable user-visible slice
- CTO/Architecture: dependency risk, debt drag, sequencing
- COO/Ops: validation cost, release safety, support burden
- Quant Strategy: research meaning, data validity, non-actionability
- Builder: fastest copy/modify path from existing repo patterns

Current packet:
See attached expert_packet.zip.

Please answer in this exact schema:

1. Recommended harness patch
- Chosen P0 patch:
- Why this now:
- Smallest useful version:
- What should not be patched yet:

2. Ranking
For each candidate patch, score 0-10:
- Product payoff
- Demoability / operational usefulness
- Dependency readiness
- Debt reduction
- Risk of process bloat
- Validation cost
- Strategic fit
Then rank top 3.

3. Low-confidence decisions
For each item, choose one:
- DECIDE_NOW
- DEFER
- NEED_USER_INPUT
- BLOCK

Resolve these:
- Should expert output be advisory only, or can specific expert roles veto?
- Should strict boot PASS be required for ordinary research/dashboard feature branches, or carried as known inherited data-artifact BLOCK unless boot/data is touched?
- Should multi-stream work run parallel, sequential, or hybrid?
- Should Research schema/artifact always precede Frontend/UI display work?
- What is the maximum acceptable file churn for small, medium, and big rounds?
- What proof is sufficient for frontend workers: running server, screenshot, AppTest, or all?
- When should harness self-evolution update AGENTS.md vs only skill/template docs?

4. Out-of-boundary items
For each item, choose:
- CONFIRM_BLOCKED
- AUTHORIZE_ONLY_WITH_EXPLICIT_USER_APPROVAL
- NOT_RELEVANT

Items:
- live trading
- broker/order execution
- action alerts
- ranking/scoring/recommendations
- BUY/SELL/HOLD or ENTER/EXIT as instructions
- replay-output certification
- provider ingestion during boot
- runtime/boot_status_current.json generation
- large data artifact commit
- backend/data repair outside chosen scope
- broad dashboard copy rewrite
- full repo cleanup
- auto-modifying AGENTS.md after every SAW
- treating expert reply as source of truth without local reconciliation

5. Stop rules
State:
- Fix if:
- Block if:
- Park if:

6. Multi-expert and multi-stream plan
- What should the orchestrator gather from each expert?
- How should expert conflicts be reconciled?
- What master stream plan is required before subagents work?
- Which stream work is parallel-safe?
- What integration gate is required?

7. Final operator instruction
Give one concise instruction the orchestrator should execute next.
