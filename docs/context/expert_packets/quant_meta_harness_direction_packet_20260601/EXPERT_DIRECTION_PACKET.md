# Quant Meta-Harness Direction Packet

Status: Expert review packet
Date: 2026-06-01
Repository root: E:\Code\Quant
Packet purpose: choose the next safe direction without authorizing implementation.

## Not Authorized

This packet does not authorize feature development, data generation, provider refresh, boot readiness claims, live trading, broker/order execution, recommendations, ranking, scoring, action alerts, autonomous allocation, or dashboard/runtime behavior changes.

## Question

Given the current dirty local root, the clean remote optimizer branch, and the local meta-harness artifacts, which direction should the project take next?

Choose one primary direction and name required preconditions:

1. Start a clean isolated worktree from `origin/codex/optimizer-core-structured-diagnostics`, then continue one research-only feature lane.
2. Review or merge `origin/codex/meta-harness-install` first, then create the clean isolated feature worktree.
3. Stop feature work and quarantine or classify the dirty root before any new worktree.
4. Hold feature work and move to governed data/source authorization before boot or data readiness can progress.
5. Reject all listed options and propose a safer bounded alternative.

## Scope

Allowed expert action: direction selection and risk review only.

Owned evidence in this packet:

- Current truth surfaces copied under `truth_surfaces/`.
- Meta-harness skill/template surfaces copied under `harness/`.
- Branch and dirty-worktree evidence copied under `git_state/`.
- SOP governance references copied under `sop/`.
- Lessons and authority notes in this packet.

Non-goals:

- No code edits.
- No branch switching, pulls, merges, resets, or commits.
- No generation of `data/processed` artifacts.
- No runtime boot-status edit.
- No boot preflight patch.
- No product authority expansion.

## Scope Selector Output

Chosen Scope: package an advisory expert direction packet from current truth surfaces and meta-harness evidence.
Why Now: dirty root is unsafe for feature work, but it contains decision evidence for choosing a clean next lane.
Why Not Alternatives: direct feature work is blocked; boot/data repair needs explicit authorization; branch/worktree creation should wait for expert direction.
Low-Confidence Items: whether `origin/codex/meta-harness-install` should be reviewed or merged before the next feature lane.
Out-of-Boundary Items: live trading, broker/order execution, recommendations, ranking/scoring, alerts, autonomous allocation, provider refresh during boot, replay certification, data generation, BootReady claims.
Stop Rules: stop if expert needs evidence not included here, if current truth surfaces conflict, or if the proposed next step requires unapproved governed data or runtime mutation.
Demo Target: zip packet with enough evidence for a direction decision.
File Budget: packet files only under `docs/context/expert_packets/quant_meta_harness_direction_packet_20260601`.

## Current Truth

Branch state from `git_state/BRANCH_STATE_SUMMARY.txt`:

- Branch: `codex/optimizer-core-structured-diagnostics`.
- Local HEAD: `b3f3f40c7a8e6874084bf3a37ca4e20e89696621`.
- Upstream: `eb3b0ec05201fcb8b26924b631ad502e9f7fb255`.
- Ahead/behind vs upstream: `0 30`, meaning local root is behind remote by 30 commits.
- Tracked dirty count: 55.
- Untracked count: 181.
- `origin/codex/meta-harness-install` exists at local remote ref `25341e5d980a016dca35a1e05a00fae65b9b07c5`.

Governed data and boot truth from current truth surfaces:

- DataReadyStrict remains `BLOCKED_MISSING_GOVERNED_ARTIFACTS`.
- SafeBoot remains `false`.
- BootReady remains `BLOCKED`.
- Missing governed artifacts include `prices.parquet`, `prices_tri.parquet`, `tickers.parquet`, `universe_r3000_daily.parquet`, and `rule100_softmax_v1_history.csv`.
- Source provenance, manifests, hashes, generated artifacts, and validation proof remain required before strict data readiness can pass.

Research and feature-lane boundary:

- Research Validity Runner v0 exists in a pushed historical commit, but current local root is dirty and behind remote.
- Clean remote branch evidence is preferred over dirty local root state for implementation decisions.
- The packet is intended to choose a direction before any new work starts.

## Authority Model

Authoritative for decision framing:

- User-provided instruction to build an expert packet and mark dirty/local artifacts non-authoritative.
- Current truth surfaces as advisory governance context.
- Git command outputs in `git_state/`.
- SOP governance files in `sop/`.

Non-authoritative for implementation:

- Dirty tracked files in the local root.
- Untracked local files, including local `.codex/skills/*` harness artifacts unless reviewed/merged.
- Ignored/local governed data artifacts.
- Runtime boot status artifacts.
- Prior packet zips, patch files, local evidence captures, and copied historical packet directories.
- Any current packet copy if it conflicts with clean remote branch truth.

## Evidence Map

Read first:

- `PACKET_INDEX.md`
- `AUTHORITY_AND_BOUNDARIES.md`
- `git_state/BRANCH_STATE_SUMMARY.txt`
- `truth_surfaces/planner_packet_current.md`
- `truth_surfaces/bridge_contract_current.md`
- `truth_surfaces/impact_packet_current.md`
- `truth_surfaces/done_checklist_current.md`

Read for harness decision:

- `harness/skills/scope-selector_SKILL.md`
- `harness/skills/expert-context-packer_SKILL.md`
- `harness/skills/harness-feedback_SKILL.md`
- `harness/templates/worker_done_contract.md`
- `harness/templates/expert_reconciliation_matrix.md`
- `harness/templates/stream_contract.md`

Read for process/governance:

- `sop/KERNEL_ACTIVATION_MATRIX.md`
- `sop/SPEC_TO_MULTISTREAM_EXECUTION_CHECKLIST.md`
- `sop/ENDGAME.md`

## Boundaries

Do not re-decide these inside the expert packet:

- Dirty root is not an implementation surface for new feature work.
- Local dirty or ignored artifacts are not clean GitHub truth.
- Boot readiness remains blocked until strict data readiness and boot-control proof pass through approved paths.
- Governed data artifacts require approved provenance, manifest/hash policy, validation proof, and explicit authorization before use.
- Research-only feature work must stay separate from live trading, broker/order, recommendation, scoring, alerting, and autonomous allocation behavior.

## Expected Expert Output

Return exactly these sections:

1. Recommendation
   - Primary direction: one of option 1, 2, 3, 4, or 5.
   - Confidence: `Y/10`.
   - One-line reason.

2. Preconditions
   - Required checks before execution starts.
   - Required branch or worktree state.
   - Required approvals.

3. Rejected Options
   - One line per rejected option with the blocker.

4. Execution Contract
   - Active stream.
   - Owned files or file categories.
   - Forbidden files/actions.
   - Acceptance checks.
   - Stop rules.

5. Open Risks
   - Inherited dirty-root risks.
   - Data/boot risks.
   - Harness-integration risks.

6. Next Action
   - Single next action that the orchestrator should take.

7. Closure
   - `Verdict: PASS` if a direction is selected and bounded.
   - `Verdict: BLOCK` if evidence is insufficient.
   - If `BLOCK`, include missing evidence and the next verification step.
