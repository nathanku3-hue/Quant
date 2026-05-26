# Boot Preflight Contract v0

Status: implementation contract
Scope: boot-core control plane plus standalone data-readiness gate integration
Non-scope: governance preflight, context rebuilding, replay behavior, optimizer behavior, dashboard semantics, research-validity claims, data repair, provider ingestion, broker actions, strategy logic

## Mission

Terminal Zero must expose one deterministic boot-status contract before broad
feature buckets are staged. The current slice keeps the boot path narrow: it
proves the status vocabulary, schema, launch dispatch, basic Git/dirty
inspection, preflight pass/fail shell, and the already-pushed standalone
data-readiness gate.

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

## v0 Behavior

Boot-core v0 may check:

- required boot-core files are present,
- `docs/context/boot_status_current.schema.json` matches the boot-status vocabulary,
- Git state is readable,
- dirty files are classified at a basic safety level,
- the data-readiness gate runs in read-only mode and reports structured readiness,
- boot-control tests pass in strict mode unless `--no-tests` is supplied,
- `--require-github` has a clean worktree and upstream-aligned HEAD.

Boot-core v0 may import:

- `core.data_readiness_gate.run_data_readiness_gate`.

Boot-core v0 must not import or execute:

- `scripts.governance_preflight`,
- `scripts/build_context_packet.py --validate`,
- dashboard AppTest smoke paths,
- replay/dashboard focused-contract commands,
- optimizer, Rule100, replay, or data repair modules.

Governance, context-packet, smoke, replay/dashboard, optimizer, Rule100, and
data-repair checks remain deferred until their own slices are approved.

## Data-Readiness Gate Policy

`scripts/boot_preflight.py` calls `run_data_readiness_gate(repo_root, mode=...)`
directly. It does not call the CLI wrapper and does not write status files unless
the operator explicitly supplies `--write-status`. Even with `--write-status`,
failed preflight does not refresh the runtime status artifact; it reports
`blocked-until-pass` in the transient result instead.

Gate status maps into boot status as:

- `PASS`: readiness check `pass`, severity `ready`,
- `WARN`: readiness check `warn`, severity `degraded`, boot preflight exit code remains `0`,
- `FAIL`: readiness check `fail`, severity `blocked`, boot preflight exit code is `1`,
- `DEFER` or `DEFERRED`: readiness check `deferred`, severity `degraded`.

Required data-readiness contract failures must not be silently downgraded to
warnings. Optional missing artifacts may degrade the boot status when the gate
reports `WARN`.

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

The next slice may add the governance/context-packet dependency set. It must be
staged separately and must not be retroactively mixed into the boot-core or
data-readiness integration commits.
