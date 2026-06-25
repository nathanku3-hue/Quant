# Kernel Activation Matrix

Status: Active
Date: 2026-03-18
Purpose: Define when each kernel capability becomes mandatory for a given repo shape. Connects capability building (W1–W6) to rollout sequencing to repo-specific subset selection.

## How to Read This Matrix

- **Capability**: the kernel artifact from W1–W6
- **Problem it solves**: the specific failure mode it prevents
- **Activation trigger**: the observable condition that makes it mandatory
- **Required repo shape**: what kind of repo needs this
- **Not needed when**: repos that should skip this
- **Minimum artifact set**: what to instantiate when activated

W1–W6 = build the toolbox.
Rollout sequence = decide where to use which tools.
This matrix = decide when a tool becomes mandatory.

---

## Matrix

### Bridge Contract

| Field | Value |
|-------|-------|
| **Capability** | Bridge Contract |
| **Wave** | W1 |
| **Problem it solves** | Execution truth exists but PM/planner cannot read it. Technical closeout state does not translate back into system-level next-step language. |
| **Activation trigger** | Planner or PM asks "what happened?" and the answer requires reading raw execution artifacts instead of a single summary. |
| **Required repo shape** | Any repo with execution truth (test results, build status, slice/phase completion reports) but weak or missing PM/planner translation layer. |
| **Not needed when** | Repo is small enough that the planner can read all execution state directly (< 5 active files, single-person project with no handoff). |
| **Minimum artifact set** | `bridge_contract_current.md` |

### Done Checklist

| Field | Value |
|-------|-------|
| **Capability** | Done Checklist |
| **Wave** | W1 (enhanced W5) |
| **Problem it solves** | Closure drifts from actual verification. "Looks done" but exit criteria are not mechanically checked. |
| **Activation trigger** | A scope closes and someone later discovers it did not actually meet its own stated criteria. Or: exit criteria exist in prose but nobody runs them. |
| **Required repo shape** | Any repo with scope boundaries (phases, slices, milestones) where closure matters. |
| **Not needed when** | Repo has no scope boundaries, or scope is trivial enough that "done" is obvious without a checklist. |
| **Minimum artifact set** | `done_checklist_current.md` + optional `check_done.sh` |

### Planner Packet

| Field | Value |
|-------|-------|
| **Capability** | Planner Packet |
| **Wave** | W3 |
| **Problem it solves** | Planner rereads the entire repo to propose a next step. Context gets stale or bloated. Fresh-context planning is expensive. |
| **Activation trigger** | Repo has > 10 design/governance documents, or planner demonstrably reads irrelevant files to propose next step, or context window pressure causes hallucination. |
| **Required repo shape** | Any repo with enough documents that a full reread is wasteful or risky. |
| **Not needed when** | Repo is small enough that the planner can read everything in one pass without waste (< 10 documents, < 50KB total governance surface). |
| **Minimum artifact set** | `planner_packet_current.md` |

### Impact Packet

| Field | Value |
|-------|-------|
| **Capability** | Impact Packet |
| **Wave** | W3 |
| **Problem it solves** | Planner does not know which files changed, which interfaces were touched, or which checks are failing. Change impact is invisible. |
| **Activation trigger** | A round produces changes that affect files outside the owned set, or failing checks go unnoticed because nobody tracks them. |
| **Required repo shape** | Mature repo with many files where change impact is non-obvious. Multiple subsystems with shared interfaces. |
| **Not needed when** | Repo is early (< 20 source files) or single-module. Change impact is obvious from the diff. |
| **Minimum artifact set** | `impact_packet_current.md` |

### Multi-Stream Contract

| Field | Value |
|-------|-------|
| **Capability** | Multi-Stream Contract |
| **Wave** | W1/W4 |
| **Problem it solves** | Two or more real work streams (backend, frontend, data, ops) drift into disconnected local loops. Nobody tracks which stream is active, blocked, or next. |
| **Activation trigger** | Work happens in 2+ streams that share interfaces or integration points, and at least one stream has been blocked or surprised by another stream's changes. |
| **Required repo shape** | Multi-stream repo where frontend/backend/data/ops (or equivalent) execute in parallel or alternation with shared dependencies. |
| **Not needed when** | Repo is single-stream. Only one kind of work happens at a time. No shared integration points between parallel efforts. |
| **Minimum artifact set** | `multi_stream_contract_current.md` |

### Post-Phase Alignment

| Field | Value |
|-------|-------|
| **Capability** | Post-Phase Alignment |
| **Wave** | W1/W4 |
| **Problem it solves** | System shape changes across streams between scope boundaries, but nobody updates the cross-stream map. Streams assume stale coordination state. |
| **Activation trigger** | A scope closes (phase, slice, sprint) and the cross-stream state has changed but the multi-stream contract has not been refreshed. |
| **Required repo shape** | Multi-stream repo with scope boundaries where stream status needs periodic resynchronization. |
| **Not needed when** | Single-stream repo. Or multi-stream repo where streams never change status between scope boundaries. |
| **Minimum artifact set** | `post_phase_alignment_current.md` (requires `multi_stream_contract_current.md` to exist) |

### Observability Pack

| Field | Value |
|-------|-------|
| **Capability** | Observability Pack |
| **Wave** | W5 |
| **Problem it solves** | Drift is invisible until it causes a failure. High-risk attempts, stuck sessions, skill under-triggering, budget pressure, and compaction/hallucination pressure are not tracked. |
| **Activation trigger** | Drift risk is non-trivial: repo has had at least one stuck session, one high-risk attempt, or one budget overrun. Or: cost/risk matters enough to justify proactive monitoring. |
| **Required repo shape** | Any repo where AI-assisted execution runs long enough for drift to accumulate. Typically after 5+ phases/slices of execution. |
| **Not needed when** | Repo is early (< 5 scope boundaries completed). Drift risk is trivial. Single short execution with clear outcome. |
| **Minimum artifact set** | `observability_pack_current.md` |

### Artifact Pruning Rules

| Field | Value |
|-------|-------|
| **Capability** | Artifact Pruning Rules |
| **Wave** | W5 |
| **Problem it solves** | Status surfaces multiply. Multiple "current" files answer the same question. Stale artifacts confuse planners and operators. |
| **Activation trigger** | Repo has > 1 artifact per truth layer answering the same question. Or: planner reads a stale artifact and makes a wrong decision. Or: `git status` shows > 20 untracked governance files. |
| **Required repo shape** | Any repo with enough governance artifacts that sprawl is a real risk. |
| **Not needed when** | Repo has < 5 governance artifacts. Sprawl is not yet a problem. |
| **Minimum artifact set** | `artifact_pruning_rules_template.md` (applied as a practice, not necessarily instantiated as a `*_current.md`) |

### Planning Loop Integration Guide

| Field | Value |
|-------|-------|
| **Capability** | Planning Loop Integration Guide |
| **Wave** | W4 |
| **Problem it solves** | Multi-stream pre-flight planning, bounded execution, and post-phase alignment are not connected into a coherent loop. Each artifact exists in isolation. |
| **Activation trigger** | Repo uses multi-stream contract + post-phase alignment but the handoff between them is ad-hoc or inconsistent. |
| **Required repo shape** | Multi-stream repo with active pre-flight/post-phase cycle. |
| **Not needed when** | Single-stream repo. Or multi-stream repo that does not yet use the full coordination cycle. |
| **Minimum artifact set** | Reference document only (not a `*_current.md` artifact). |

### Planner Escalation Rules

| Field | Value |
|-------|-------|
| **Capability** | Planner Escalation Rules |
| **Wave** | W3 |
| **Problem it solves** | Planner always reads the whole repo, or never reads enough. No explicit criteria for when to escalate from small packets to wider surfaces. |
| **Activation trigger** | Planner packet exists but planner still reads full repo by default, or planner misses critical context because it never escalates. |
| **Required repo shape** | Any repo using planner packets. |
| **Not needed when** | Repo does not use planner packets (too small, or planner can read everything). |
| **Minimum artifact set** | Embedded in `planner_packet_current.md` (escalation rules section). Standalone `planner_escalation_rules_template.md` only if escalation logic is complex enough to warrant separation. |

---

## Current Repo Activation Status

| Capability | Quant | Eureka | ToolLauncher |
|------------|-------|--------|--------------|
| Bridge Contract | ✅ Active | ✅ Active | ✅ Active |
| Done Checklist | ✅ Active | ✅ Active | ✅ Active |
| Planner Packet | ✅ Active | ✅ Active | ❌ Not needed (small repo) |
| Impact Packet | ✅ Active | ❌ Not needed (early) | ❌ Not needed (small repo) |
| Multi-Stream Contract | ✅ Active | ❌ Not needed (single-stream) | ❌ Not needed (single-stream) |
| Post-Phase Alignment | ✅ Active | ❌ Not needed (single-stream) | ❌ Not needed (single-stream) |
| Observability Pack | ✅ Active | ❌ Not needed (early) | ❌ Not needed (not enough drift evidence) |
| Artifact Pruning Rules | ✅ Applied | ❌ Not needed (early) | ❌ Not needed (minimal artifact set) |
| Planning Loop Integration | ✅ Reference | ❌ Not needed (single-stream) | ❌ Not needed (no planner or multi-stream layer) |
| Planner Escalation Rules | ✅ Embedded | ✅ Embedded | ❌ Not needed (no planner packet) |

## Writing Rules

- Update the "Current Repo Activation Status" table when a new repo is assessed or when a repo's shape changes.
- A capability should move from "Not needed" to "Active" only when its activation trigger is observed, not when the capability exists in the toolbox.
- Do not activate capabilities preemptively. The cost of a missing artifact is lower than the cost of maintaining an unused one.
