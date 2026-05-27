# Boot Preflight Contract v0

Status: implementation contract
Scope: boot-core control plane plus safe-boot gate truth
Non-scope: context rebuilding, replay rebuilding, optimizer behavior changes, dashboard semantic redesign, research-validity claims, data repair, provider ingestion, broker actions, strategy logic

## Mission

Terminal Zero must expose one deterministic boot-status contract before broad
feature buckets are staged. The current slice converts previously deferred
boot-status dependencies into real gates or explicit safe-boot blockers. Safe
boot is earned only from current gate truth; missing, warning, skipped,
deferred, or failed required gates keep `safe_boot=false`.

## Commands

Normal strict boot-core check:

```powershell
.\.venv\Scripts\python launch.py --preflight --strict
```

Planning-mode check for local dirty work:

```powershell
.\.venv\Scripts\python launch.py --preflight --mode planning
```

Intentional status write:

```powershell
.\.venv\Scripts\python launch.py --preflight --strict --require-github --smoke --run-focused-contract --write-status
```

Final read-only GitHub proof after intentional status evidence is committed:

```powershell
.\.venv\Scripts\python launch.py --preflight --strict --require-github
```

Detached clean-worktree GitHub proof when the worktree has no upstream:

```powershell
.\.venv\Scripts\python launch.py --preflight --strict --require-github --expected-ref <branch> --expected-sha <sha>
```

## v0 Behavior

Boot-core v0 may check:

- required boot-core files are present,
- `docs/context/boot_status_current.schema.json` matches the boot-status vocabulary,
- Git state is readable,
- dirty files are classified at a basic safety level,
- governance preflight runs and reports structured PASS/WARN/FAIL state,
- boot-control tests pass in strict mode unless `--no-tests` is supplied,
- data-readiness runs through `core.data_readiness_gate.run_data_readiness_gate` in read-only mode,
- context packet validation runs through `scripts/build_context_packet.py --validate` without implicit rebuild,
- Portfolio AppTest smoke runs only when `--smoke` is supplied,
- focused replay/dashboard governance contract runs only when `--run-focused-contract` is supplied,
- `--require-github` has a clean worktree and either upstream-aligned HEAD or an explicit expected-ref/SHA proof.

Boot-core v0 may import:

- `scripts.governance_preflight.run_governance_preflight`.
- `core.data_readiness_gate.run_data_readiness_gate`.

Boot-core v0 must not import or execute:

- `scripts/run_data_readiness_gate.py`,
- optimizer, Rule100, replay, or data repair modules.

Context-packet validation, dashboard AppTest smoke, and focused
replay/dashboard checks run as subprocess gates and must not rebuild or repair
artifacts implicitly. Optimizer, Rule100, replay rebuilds, and data repair remain
outside boot preflight.

## GitHub Proof Policy

`--require-github` is a proof gate, not a branch-shape gate. It passes when the
worktree is clean and one of these is true:

- `HEAD` matches the configured upstream and the ahead/behind count is zero,
- or `--expected-ref` / `--expected-sha` prove that detached local `HEAD`
  matches `git ls-remote origin refs/heads/<expected-ref>`.

If a detached worktree has no upstream and no expected ref/SHA, the gate must
fail as proof unavailable. If expected proof is supplied but the remote ref,
remote SHA, expected SHA, or local `HEAD` disagree, the gate fails as expected
proof mismatch.

## Safe-Boot Gate Policy

`safe_boot=true` only when all required gates pass in strict mode with
`--require-github`: Git state, governance preflight, boot-control tests,
data-readiness gate, context packet validation, Portfolio AppTest smoke,
focused replay/dashboard contract, and the post-write Git check when status
writing is attempted.

If any required gate is missing, warning, skipped, deferred, or failed,
`make_boot_status_from_preflight(...)` maps the boot status to degraded or
blocked with `safe_boot=false`. A data-readiness `WARN` remains a safe-boot
blocker even when the transient preflight verdict is `PASS`.

The boot preflight writer does not write status files unless the operator
explicitly supplies `--write-status`. Even with `--write-status`, failed
preflight does not refresh the runtime status artifact; it reports
`blocked-until-pass` in the transient result instead.

## Status Artifact Policy

Committed schema:

```text
docs/context/boot_status_current.schema.json
```

Generated status:

```text
runtime/boot_status_current.json
```

The status writer must resolve output paths inside the repository and allow only
`runtime/boot_status_current.json` for durable v0 boot-status output.

`boot_status_current.md` is outside v0. JSON plus schema is enough for the first
boot-core slice.

## Dirty Classifier v0 Policy

The classifier is a safety filter, not a cleanup engine.

Fail closed:

- unclassified `*.py`,
- unclassified `tests/**`,
- unclassified `core/**`, `scripts/**`, `strategies/**`, `views/**`, `opportunity_engine/**`,
- unclassified `dashboard.py`, `launch.py`, `pyproject.toml`, `requirements*.txt`,
- unclassified `data/**/*.py`.

Advisory only:

- approved boot-core files,
- generated context/evidence outputs,
- `docs/context/e2e_evidence/**`,
- `docs/saw_reports/**`,
- expert packet zips,
- runtime stdout/stderr/pid/status files,
- docs/context and architecture governance surfaces.

## Exit Codes

- `0`: preflight PASS, possibly degraded by explicit safe-boot blockers.
- `1`: boot-core FAIL caused by failed checks.
- `2`: internal/configuration error.

## Deferred Scope

Optimizer, Rule100, replay rebuilds, data repair, provider ingestion, broker
behavior, and research-validity promotion remain outside this boot gate.
