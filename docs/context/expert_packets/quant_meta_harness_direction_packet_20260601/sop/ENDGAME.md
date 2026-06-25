# Operational Endgame v2

This document defines the target state for the SOP governance control plane.

Every patch, artifact, role, and process change should be judged against this endgame.

## 1. Core Thesis

The endgame is **not**:

- write perfect starter docs,
- hand them to a coding machine,
- and expect one-shot product delivery.

The endgame **is**:

- the human stays at the strategy, taste, and reality layer,
- the system runs bounded engineering loops with minimal friction,
- product and system truth stay aligned through explicit bridge artifacts,
- and information, decision, and engineering iterate fast enough that reality can change without breaking coherence.

In one line:

**SOP is a high-speed strategy-to-engineering operating system, not a documentation-first coding machine.**

## 2. Human Role

The human role is deliberately narrow and high-leverage.

The human should:

- understand the top-level situation,
- frame the real problem,
- challenge weak assumptions,
- compare alternatives aggressively,
- decide priorities, boundaries, and tradeoffs,
- and judge whether the product is becoming more coherent or more fragmented.

The human should **not** be the default:

- line-by-line implementer,
- manual status compiler,
- prompt babysitter,
- or the only entity responsible for keeping planning artifacts current.

The operating idea is:

- **humans own judgment**
- **the system owns bounded execution**

## 3. Dual-Loop Model

The endgame uses two connected loops.

### Loop A: Strategy / Information / Decision

Purpose:

- understand what is happening,
- understand what problem matters now,
- compare options,
- choose the next move.

Actors:

- Human
- CEO lens
- CTO lens
- COO lens
- Board lens when needed

Typical outputs:

- product direction
- product stage choice
- problem framing
- what not to do
- what to research next
- what engineering should execute next

### Loop B: Engineering / Execution / Verification

Purpose:

- turn the current decision into bounded, testable, reviewable output.

Actors:

- orchestrator
- planner
- workers
- auditor
- QA / DevOps / cleanup passes

Typical outputs:

- code
- tests
- evidence
- system deltas
- open risks
- implementation-ready next step options

### The Bridge Between A and B

This bridge is the heart of the system.

The engineering loop must not return only:

- confidence,
- PASS/BLOCK,
- diffs,
- or test counts.

It must return:

- what changed in the system,
- what changed in the product stage,
- what assumption got stronger or weaker,
- what bottleneck moved,
- what decision now matters,
- and what should not be done next.

Without this bridge, the system optimizes locally and fragments globally.

## 4. Full Loop

The intended full loop is:

### 0. Orientation

- load the smallest top-level truth
- understand the current system state
- understand the current product stage

Primary surfaces:

- `README.md`
- `ENDGAME.md`
- `ROADMAP.md`
- `KERNEL_ACTIVATION_MATRIX.md`
- `SPEC_TO_MULTISTREAM_EXECUTION_CHECKLIST.md`

### 1. Research and Reality Scan

- inspect current repo state
- inspect current product/system truth
- inspect current evidence and open risks
- inspect relevant external product/technical research when needed

Goal:

- do not start from stale assumptions.

### 2. Strategy Conversation

The human works with the decision lenses:

- **CEO**: what is the best next move?
- **CTO**: what system shape survives and compounds?
- **COO**: what smallest executable next step reduces risk and friction?
- **Board**: what are we missing, overconfident about, or failing to compare?

Goal:

- turn raw information into an explicit next decision.

### 3. Pre-Flight Planning

Before execution starts, the system defines:

- product stage now
- product problem this round
- non-goals
- stream map if multi-stream
- expected deliverables
- expected integration points
- expected new surfaces, if any
- expected “done”

Goal:

- make the round legible before work starts.

### 4. Kernel Activation

The system activates only the capabilities required by the current repo shape and trigger conditions.

Examples:

- bridge contract
- done checklist
- planner packet
- impact packet
- multi-stream contract
- post-phase alignment
- observability pack
- pruning rules

Goal:

- activate by trigger, not by habit.

### 5. Planner Entry

The planner starts from the smallest fresh packet:

- planner packet
- impact packet when active
- bridge truth
- done checklist
- multi-stream contract when active
- observability pack when active

Goal:

- plan from current truth, not from whole-repo rereads.

### 6. Bounded Execution

Workers execute one bounded slice.

They should:

- stay within scope,
- touch declared surfaces,
- collect evidence,
- avoid inventing product meaning locally.

Goal:

- high throughput without scope drift.

### 7. Worker Self-Loop

The engineering side can iterate internally:

- implement
- test
- fix
- re-test

This loop is for local engineering correctness.

Goal:

- avoid involving the human too early in local implementation churn.

### 8. Worker to Planner Return

After bounded execution, the output must be translated into planner truth:

- impact packet refreshed
- bridge contract refreshed
- post-phase alignment refreshed when needed
- planner packet refreshed for next entry

Goal:

- execution truth must become decision truth.

### 9. Organic Integration Check

If a new surface was added:

- classify it as core / temporary / replacement
- explain how it fits the end product
- explain what it should merge into or replace
- name one simplification step

Goal:

- prevent the “every phase adds another view” trap.

### 10. QA / DevOps / Cleanup

After engineering success, the system still needs:

- final validation
- release/readiness checks
- runtime checks
- cleanup / pruning / artifact hygiene

Goal:

- turn local success into operationally trustworthy output.

### 11. Orchestrator Synthesis

The orchestrator collects:

- planning truth
- execution truth
- bridge truth
- evidence truth
- current bottleneck
- active decision

Then it decides:

- what the system should do next,
- who needs to look at it,
- whether to stand by, continue, or escalate.

### 12. CEO / Board Re-entry

When the round changed system meaning or product direction, return to the strategy loop.

This is where fast iteration happens:

- new information,
- new evidence,
- new design tension,
- new options.

Then the next round starts.

## 5. Truth Model

The system stays coherent through these truth layers:

### 1. Static Truth

Long-lived intent and constraints.

Examples:

- PM docs
- PRD / architecture docs
- decision log
- operating contract

### 2. Live Truth

What is active now.

Examples:

- current context
- active phase or slice
- blocked next step
- active stream

### 3. Bridge Truth

What recent execution means for the product/system and planner.

Examples:

- system delta
- PM delta
- open decision
- recommended next step
- bottleneck

### 4. Evidence Truth

What actually happened and what proves it.

Examples:

- tests
- review packets
- runtime artifacts
- logs / metrics / traces

### 5. Planner Truth

The compact fresh-context packet the planner uses to avoid full-repo rereads.

Examples:

- planner packet
- impact packet
- escalation rules

The system becomes reliable when these layers stay:

- thin,
- distinct,
- connected,
- and current.

## 6. Product Cohesion Rule

A round is not successful just because:

- code works,
- tests pass,
- or evidence exists.

A round is successful when it also improves the product/system shape.

Every major round must answer:

- what product problem did this solve?
- what surface changed?
- is that surface core, temporary, or replacement?
- what should merge, hide, or retire because of this round?
- did the overall system become more integrated, unchanged, or more fragmented?

This is the protection against local technical success creating global product fragmentation.

## 7. Multi-Stream Model

Multi-stream is optional, not default.

When it is active, use this division:

### Pre-Flight Planning

Defines:

- streams
- stream purpose
- stream deliverables
- stream dependencies
- shared success condition
- active vs deferred streams

### Worker / Auditor Loop

Moves one bounded piece on the map.

### Post-Phase Alignment

Updates:

- stream status
- bottleneck
- interface drift
- next active stream
- PM decision required

This is the least-drifty pattern for complex systems.

## 8. Orchestrator State Model

The orchestrator should be ultra state aware, but this does **not** mean reading the whole repo every time.

It should always know:

- what system is active now,
- what stream is active now,
- what is blocked,
- what changed last round,
- what bottleneck matters most now,
- what PM decision is still open,
- what evidence is fresh versus stale.

The orchestrator should get this from small authoritative artifacts, not from accumulated chat memory.

## 9. Further Honing Possibilities

These are optional strengthening roles or passes.
They should activate by trigger, not by habit.

### 1. Librarian

Purpose:

- maintain research quality,
- deepen product/technical comparison work,
- track sources,
- keep “copy / modify / reject” research from staying shallow.

Useful when:

- product research quality is weak,
- too many external references accumulate,
- research conclusions are repeated but not improved.

### 2. Folder Cleanup / Artifact Janitor

Purpose:

- reduce status sprawl,
- archive stale artifacts,
- enforce one-current-artifact-per-truth-layer.

Useful when:

- too many `current` or near-current files exist,
- stale docs mislead planners or operators,
- evidence artifacts accumulate faster than they are pruned.

### 3. Product Research Analyst

Purpose:

- deepen product/system comparison beyond shallow 2-axis analysis,
- compare operating model, hidden costs, org design assumptions, and MVP migration path.

Useful when:

- current product research is too shallow,
- strategic decisions are being made from insufficient comparison depth.

### 4. Surface Integrator

Purpose:

- detect when a new view/tab/report should merge into an existing surface instead of surviving as another layer.

Useful when:

- each phase keeps adding another diagnostic or operator surface,
- system feels like a patchwork of local views.

### 5. Cleanup / DevOps Pass

Purpose:

- turn local engineering success into operationally usable output,
- keep environment, release, tests, and runtime clean.

Useful when:

- technical work is correct but handoff or operation remains messy.

### 6. Memory / Drift Curator

Purpose:

- monitor compaction pressure,
- stale references,
- unsupported claims,
- repeated drift markers.

Useful when:

- context windows grow,
- planner starts rereading too much,
- hallucination pressure rises.

These are **honing roles**, not mandatory permanent bureaucracy.

## 10. Anti-Goals

The system is **not** trying to:

- become a hosted autonomous agent platform,
- become a consumer chat product,
- become a plugin marketplace,
- become a zero-human autopilot,
- create a second authority plane outside the documented control flow,
- replace human judgment on direction or priority,
- hide execution state in chat history,
- accumulate overlapping status surfaces,
- reread the whole repo every time the planner runs,
- add more prompts when artifacts can solve the problem,
- add more ceremony when the kernel is sufficient.

## 11. Success Criteria

The endgame is reached when:

- the human can explain the system in 5 minutes without phase-specific examples,
- strategy loop and engineering loop are both explicit,
- the planner enters from small packets by default,
- worker output reliably becomes planner truth,
- new surfaces are integrated or retired instead of silently accumulating,
- same truth vocabulary works across repos,
- status stays thin,
- repeated misses become clearer guardrails,
- and models need less guidance over time, not more.

## 12. Optimization Direction

The standing rule remains:

- build on top of the existing kernel,
- do not do a large refactor unless repeated evidence shows the additive layer cannot solve the conflict,
- make the orchestrator more state aware through better artifacts, not more prompt text,
- reduce human effort to the smallest set of decisions that still preserve product truth.

## 13. Futureproofing Principle

As models improve, the system should need:

- fewer prompts,
- fewer reminders,
- fewer manual restatements,
- more reliance on clear artifacts and mechanical checks.

So the futureproof path is:

- less hidden prompt cleverness,
- more explicit truth hierarchy,
- more mechanical validation,
- thinner but clearer artifacts,
- and a simpler human role.

The system should become easier to run as models get stronger, not more ritual-heavy.
