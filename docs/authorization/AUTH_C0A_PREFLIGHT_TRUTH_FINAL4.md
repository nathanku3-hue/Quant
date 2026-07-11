# C0A-final4 — Preflight Truth Recovery

| Field | Value |
|-------|--------|
| RoundID | `ROUND-20260712-C0A-PREFLIGHT-TRUTH-FINAL4` |
| ScopeID | `C0A_PREFLIGHT_TRUTH_FINAL4` |
| Mode | `EXECUTION_PACKET` |
| Date | 2026-07-12 |
| Status | `AUTHORIZED_FOR_THREE_COMMIT_EXECUTION` |

## Purpose

Make `scripts/boot_preflight.py` report **honest** Git identity and dirty state when nested/broken gitlinks break default `git status`, without claiming planning-green while unregistered gitlinks remain.

## Success contract (explicit)

| Layer | Required outcome |
|--------|------------------|
| Focused tests | PASS |
| Live planning preflight on index with 41 unregistered gitlinks | **FAIL** (expected, correct) |
| Terminal SAW (Commit 3) | PASS after envelope binds Commit 2 |
| Planning-green primary dirty checkout | **Not required / not claimed** |

## Behavioral requirements

1. `git status --porcelain=v1 -z --ignore-submodules=all` (superproject porcelain only).
2. Non-status identity failures preserve every successful field: branch, HEAD, tree, upstream, upstream_head, ahead/behind, and porcelain entries.
3. Status command failure → `dirty_state=STATUS_UNAVAILABLE`, dirty `status=FAIL`, never plain `clean`.
4. Empty porcelain + remaining gitlinks → `dirty_state=clean_superproject_only`, never plain `clean`.
5. Enumerate mode-160000 via `git ls-files -s -z` (space-safe); unregistered = not in `.gitmodules` (absent ⇒ all unregistered).
6. Non-stage-0 gitlinks / other unmerged index entries → separate FAIL check.
7. `dirt_complete=true` only when status OK and **total gitlinks == 0** (no recursive submodule verification in C0A).

## Workspace / branch rules

- Isolated worktree created from current HEAD (includes local identity-repair history).
- Do **not** `git switch` the dirty primary checkout.
- Branch tracks `origin/main` via local upstream only; **no fetch/push** in this packet.

## Three-commit protocol

1. **Commit 1 (this brief + code + tests only).**
2. **Commit 2:** independent Reviewer A/B/C reports + required truth surfaces + `docs/lessonss.md`, all pinned to Commit 1; **no terminal SAW authority**.
3. **Commit 3:** detached envelope binding Commit 2 commit/tree/path hashes + terminal SAW validating Commits 1–2 and envelope bytes.  
   - `terminal_saw_self_binding=false`  
   - `commit3_identity_not_claimed=true`  
   - Envelope binds Commit 2 only; does not require self-binding Commit 3 unless separately needed.

## Stop rules

- Any code change after Commit 1 → restart from **new Commit 1**.
- Any Commit 2 byte change → new Commit 2 + **new** envelope and terminal SAW (Commit 3).
- Terminal SAW must **not** claim its own final commit/tree is self-attested.

## Forbidden

- C0B gitlink deindex, C1 quarantine, C2/C3 M7 work.
- Claiming preflight PASS while unregistered gitlinks remain.
- Blanket ignore of `root repo/` (50 snapshot files are legitimate history).
- Fetch/push; switching dirty primary onto this branch.

## Held successors

- **C0B:** remove exact 41 unregistered gitlinks; prove first clean isolated preflight; separate dirty inventory.
- **C1+:** P1 quarantine / M7 path (unchanged holds).
