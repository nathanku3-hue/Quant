# Boot Preflight Contract v0

Status: implementation contract
Scope: boot-core control plane only
Non-scope: data-readiness, governance preflight, context rebuilding, replay behavior, optimizer behavior, dashboard semantics, data repair, provider ingestion, broker actions, strategy logic

## Mission

Terminal Zero must expose one deterministic boot-status contract before broad
feature buckets are staged. The first slice is intentionally narrow: it proves
the status vocabulary, schema, launch dispatch, basic Git/dirty inspection, and
preflight pass/fail shell.

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
- boot-control tests pass in strict mode unless `--no-tests` is supplied,
- `--require-github` has a clean worktree and upstream-aligned HEAD.

Boot-core v0 must not import or execute:

- `core.data_readiness_gate`,
- `scripts.governance_preflight`,
- `scripts/build_context_packet.py --validate`,
- dashboard AppTest smoke paths,
- replay/dashboard focused-contract commands,
- optimizer, Rule100, replay, or data repair modules.

Those checks are represented as deferred readiness checks until their own slice
is approved.

## Status Artifact Policy

Committed schema:

```text
docs/context/boot_status_current.schema.json
```

Generated status:

```text
docs/context/boot_status_current.json
```

The status writer must resolve output paths inside the repository and allow only
`docs/context/boot_status_current.json` for durable v0 boot-status output.

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

The next slice may add the data-readiness/governance dependency set. It must be
staged separately and must not be retroactively mixed into this boot-core commit.
