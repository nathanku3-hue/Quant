# Packet Index

Packet: `quant_meta_harness_direction_packet_20260601`
Created: 2026-06-01
Purpose: external or specialist direction choice before any further Quant feature work.

## Start Here

1. `EXPERT_DIRECTION_PACKET.md`
2. `AUTHORITY_AND_BOUNDARIES.md`
3. `git_state/BRANCH_STATE_SUMMARY.txt`

## Included Evidence

```text
truth_surfaces/
  planner_packet_current.md
  impact_packet_current.md
  bridge_contract_current.md
  done_checklist_current.md
  multi_stream_contract_current.md
  post_phase_alignment_current.md
  observability_pack_current.md

harness/
  skills/
    scope-selector_SKILL.md
    expert-context-packer_SKILL.md
    harness-feedback_SKILL.md
  templates/
    worker_done_contract.md
    expert_reconciliation_matrix.md
    stream_contract.md

governance/
  AGENTS_local_dirty_non_authoritative.md

git_state/
  BRANCH_STATE_SUMMARY.txt
  git_status_short_branch.txt
  git_diff_name_status.txt
  git_diff_stat.txt
  git_untracked_files.txt
  git_branch_vv.txt
  git_upstream_commits_missing_locally.txt
  remote_optimizer_recent_log.txt
  remote_meta_harness_recent_log.txt
  remote_meta_harness_vs_optimizer_diff_stat.txt

sop/
  KERNEL_ACTIVATION_MATRIX.md
  SPEC_TO_MULTISTREAM_EXECUTION_CHECKLIST.md
  ENDGAME.md
```

## Exclusions

The packet intentionally excludes:

- Source-code dumps.
- Data files.
- Runtime boot-status files.
- Ignored governed data artifacts.
- Credentials or secrets.
- Broad chat logs.
- Historical packet directories except where summarized by current truth surfaces.

## Review Rule

If a file in this packet conflicts with clean remote branch truth, treat the clean remote branch as implementation truth and this packet as advisory decision context.

The `governance/AGENTS_local_dirty_non_authoritative.md` file is included for instruction context only because the local root reports `AGENTS.md` as modified.
