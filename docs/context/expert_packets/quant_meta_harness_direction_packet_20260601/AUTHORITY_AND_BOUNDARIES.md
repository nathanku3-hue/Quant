# Authority and Boundaries

Status: Required packet guardrail

## Dirty/Local Artifact Classification

The current local root is evidence, not authority.

Non-authoritative artifacts include:

- All dirty tracked files reported in `git_state/git_status_short_branch.txt`.
- All untracked files reported in `git_state/git_untracked_files.txt`.
- Local `.codex/skills/` harness files unless and until reviewed and merged into the chosen clean branch.
- Local `docs/context/expert_packets/` packet contents, including this packet, for implementation truth.
- Local runtime status artifacts.
- Ignored or local governed data artifacts.
- Historical packet zip files, patch files, and copied evidence directories.
- Any local context copy that conflicts with a clean remote branch or an approved source-of-truth packet.

## Authoritative Inputs For Direction Only

- Current user request.
- Git evidence generated during packet creation.
- Current truth surfaces copied into this packet, treated as advisory governance state.
- SOP governance references copied into this packet.
- Clean remote branch refs available locally at packet creation time.

## Required Separation

An implementation round must not run from this dirty root unless the user explicitly approves a dirty-root repair or classification round.

Preferred implementation surface, if feature development is selected, is a clean isolated worktree based on the chosen clean remote branch.

## Forbidden Claims

This packet must not be cited as proof of:

- BootReady.
- SafeBoot.
- DataReadyStrict PASS.
- Research-valid strategy output.
- Candidate ranking, scoring, recommendation, alerting, or allocation authority.
- Runtime or dashboard behavior readiness.

## Approval Gates

Explicit user approval is required before:

- Creating or switching implementation branches/worktrees.
- Merging `origin/codex/meta-harness-install`.
- Generating or accepting governed data artifacts.
- Editing boot preflight or boot-status paths.
- Running provider refreshes or any boot-time data generation.
- Promoting strategy, ranking, scoring, recommendation, alert, broker, or live execution behavior.
