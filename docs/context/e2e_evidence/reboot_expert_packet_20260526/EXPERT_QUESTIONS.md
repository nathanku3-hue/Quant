# Expert Questions: Rebooting Terminal Zero Into a Boot-Ready Self-Maintaining System

GitHub anchor: https://github.com/nathanku3-hue/Quant/tree/codex/optimizer-core-structured-diagnostics

Local packet caveat: HEAD is aligned with that GitHub branch at `cec79312e091107e9a4bbd14ba855c59f2ca5a75`, but this packet includes local uncommitted current-truth context. Please distinguish "already on GitHub" from "local reboot material."

## Mission

We want Terminal Zero to reboot into a fully self-maintaining, ready-to-use local-first quantitative research console. The goal is not more ceremony. The goal is a system that starts cleanly, knows its own current truth, protects data/research integrity, and guides the next bounded execution without the human manually reconstructing state.

## High-Value Questions

1. What is the smallest boot sequence that should become non-negotiable?
   - Which commands/artifacts must run or validate before any coding, replay, data repair, or dashboard work starts?
   - Which current steps are governance noise and should be collapsed?

2. What is the correct "single source of boot truth"?
   - Should `docs/context/current_context.md/json` become the boot entry, or should the system promote a new `BOOT.md` / `quant.md` / command output as the canonical user-facing boot surface?
   - What should be machine-generated versus human-authored?

3. What dirty-worktree strategy gets us from current local state to GitHub-safe reality?
   - Which local changes should be staged first?
   - Which generated evidence should be archived or ignored?
   - Which uncommitted artifacts are dangerous to lose because they encode current truth not yet on GitHub?

4. What is the self-maintenance loop?
   - What should automatically refresh after a work round: context packet, bridge, impact, done checklist, lessons, SAW, GitHub status?
   - What should fail closed if stale?
   - What should be allowed to stay advisory-only?

5. What is the minimal "ready to use" runtime definition?
   - Is ready defined by Streamlit boot, focused pytest, full pytest, replay artifact freshness, data health, or a smaller operator checklist?
   - Which endpoint/page must prove the system is usable after reboot?

6. What should the project stop doing?
   - Which docs, reports, evidence logs, or repeated handoff surfaces should be retired, archived, or merged?
   - Which current workflows are creating fragmentation instead of self-maintenance?

7. What should GitHub become in the operating model?
   - Should every boot-ready state require a clean branch pushed to GitHub?
   - Should local uncommitted context packets be acceptable for planning?
   - What branch/commit/tag convention would make "latest safe boot" obvious?

8. What should be automated first?
   - A `reboot.py` or `launch.py --preflight`?
   - A GitHub alignment checker?
   - A dirty-worktree classifier?
   - A context packet validator plus stale-artifact pruner?
   - A Streamlit smoke runner?

9. What are the highest-risk integrity failures right now?
   - PIT leakage?
   - stale local market data?
   - replay artifact identity drift?
   - optimizer fallback being misread as valid allocation?
   - dashboard labels implying recommendations?
   - local uncommitted truth diverging from GitHub?

10. What is the 1-week reboot plan?
    - Please propose 3-5 bounded milestones with acceptance checks.
    - Each milestone should say what becomes more self-maintaining and what human decision burden is removed.

## Desired Expert Output

- One recommended reboot architecture.
- One minimal boot command/checklist.
- One GitHub alignment policy.
- One dirty-worktree triage plan.
- One list of artifacts to keep, merge, archive, or delete.
- One first implementation slice with exact files to touch and tests to run.

