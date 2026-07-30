# SAW — Relocatable custody supersede + Replay 0 base promotion — 2026-07-30

## Verdict

`PASS_PROMOTION`

- Slice 0 immutable: `85e6601742710f03e6cced7377b4be426cd4892f`
- Replay 0 base: `03a5c922d250d615380bbd0d60e8fd636e4ec1c6`
- Opened: **only** `GV-DETERMINISTIC-REPLAY-0`

## Why Path 1

`bd07f61` improved relocatable G4/G5/G6 but broke banked V2-B0 intentional non-binding by aligning MU package hash. Path 1 restores MU historical hash, keeps G4/MSFT/resolver, and **explicitly retires** the conflicting G8 MU same-path hash-match PASS (replacement truth test + gate doc) rather than silently dropping the node.

## Proof

| Gate | Result |
|---|---|
| Remote equality | `origin/codex/repository-custody-repair` == `03a5c92` |
| Focused custody+V2B0+G8+portfolio | 149/149 PASS |
| Full suite | 2620 pass / 30 fail / 16 skip |
| Candidate-only vs `85e6601` | **0** |
| Reviewer A | PASS |
| Reviewer B | PASS |
| Reviewer C | PASS |

## Authority updates

- `docs/context/ACTIVE_BRIEF` → phase1 Replay 0 brief
- `PHASE_QUEUE.md` Replay 0 base promoted; Slice 0 accepted
- `docs/architecture/gv_relocatable_custody_gate.md`
- Decision log 2026-07-30 entry

## Next

Clean worktree from exact `03a5c92` → implement only exact deterministic replay certification from Slice 0 events.
