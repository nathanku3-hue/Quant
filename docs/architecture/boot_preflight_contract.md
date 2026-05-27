# Boot Preflight Contract v0

Status: implementation contract
Scope: boot-core control plane plus governance preflight integration
Non-scope: data-readiness execution, context rebuilding, replay behavior, optimizer behavior, dashboard semantics, research-validity claims, data repair, provider ingestion, broker actions, strategy logic

## Mission

Terminal Zero must expose one deterministic boot-status contract before broad
feature buckets are staged. The current slice keeps the boot path narrow: it
proves the status vocabulary, schema, launch dispatch, basic Git/dirty
inspection, preflight pass/fail shell, and the governance preflight boundary.
Data-readiness is reported as deferred in this proof and must not run from
`scripts/boot_preflight.py` until a separate slice approves it.

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
.\.venv\Scripts\python launch.py --preflight --strict --write-status
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
- `--require-github` has a clean worktree and either upstream-aligned HEAD or an explicit expected-ref/SHA proof.

Boot-core v0 may import:

- `scripts.governance_preflight.run_governance_preflight`.

Boot-core v0 must not import or execute:

- `core.data_readiness_gate.run_data_readiness_gate`,
- `scripts/run_data_readiness_gate.py`,
- `scripts/build_context_packet.py --validate`,
- dashboard AppTest smoke paths,
- replay/dashboard focused-contract commands,
- optimizer, Rule100, replay, or data repair modules.

Data-readiness, context-packet, smoke, replay/dashboard, optimizer, Rule100,
and data-repair checks remain deferred until their own slices are approved.

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

## Data-Readiness Deferral Policy

`scripts/boot_preflight.py` must not call the data-readiness gate in this
current governance slice. It emits `checks.data_readiness_gate.status =
DEFERRED`, and `make_boot_status_from_preflight(...)` maps that state to a
degraded non-safe boot candidate. A later data-readiness slice must update this
contract, the tests, and the runtime status mapping before the gate can execute
from boot preflight.

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

- `0`: boot-core PASS, possibly degraded by deferred checks.
- `1`: boot-core FAIL caused by failed checks.
- `2`: internal/configuration error.

## Deferred Scope

The next slice may add the data-readiness/context-packet dependency set. It must
be staged separately and must not be retroactively mixed into the boot-core or
governance integration commits.
