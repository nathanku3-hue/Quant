from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from core.release_metadata import (
    ReleaseMetadata,
    ReleaseRecord,
    extract_release_digest,
    require_digest_locked_release_ref,
)
from utils.process import pid_is_running


DEFAULT_METADATA_PATH = Path("data/processed/release_metadata.json")
DEFAULT_PROBE_TIMEOUT_SECONDS = 45.0
DEFAULT_DEPLOYMENT_MODE = "docker"
DEFAULT_SERVICE_NAME = "terminal_zero_orchestrator"
DEFAULT_STARTUP_WAIT_SECONDS = 45.0


@dataclasses.dataclass(frozen=True)
class StartupProbeResult:
    """Normalized startup probe output consumed by release transitions."""

    ok: bool
    details: str
    rollback_ok: bool | None = None


@dataclasses.dataclass(frozen=True)
class DockerContainerState:
    """Inspection payload for a single Docker container."""

    exists: bool
    running: bool
    exit_code: int | None
    health_status: str
    details: str


def _utc_now_iso() -> str:
    """Return deterministic UTC timestamps for metadata persistence."""
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _compact_text(value: Any, *, max_chars: int = 180) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    return text if len(text) <= max_chars else f"{text[: max_chars - 3]}..."


def _state_ready(state: DockerContainerState) -> bool:
    if not state.running:
        return False
    health = str(state.health_status or "none").strip().lower()
    return health in {"none", "healthy"}


def _read_lock_fields(lock_path: Path) -> dict[str, str]:
    try:
        raw = lock_path.read_text(encoding="utf-8")
    except OSError:
        return {}
    fields: dict[str, str] = {}
    for line in raw.splitlines():
        key, sep, value = line.partition("=")
        if sep == "=" and key.strip():
            fields[key.strip()] = value.strip()
    return fields


def _parse_lock_pid(raw_pid: str | None) -> int | None:
    if raw_pid is None:
        return None
    try:
        pid = int(raw_pid)
    except (TypeError, ValueError):
        return None
    return pid if pid > 0 else None


def _pid_is_alive(pid: int) -> bool:
    return pid_is_running(pid)


def _acquire_run_lock(lock_path: Path, *, stale_seconds: float) -> str:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    max_age = max(1.0, float(stale_seconds))
    now = time.time()
    if lock_path.exists():
        try:
            age = max(0.0, now - float(lock_path.stat().st_mtime))
        except OSError:
            age = 0.0
        if age <= max_age:
            raise RuntimeError(f"release controller lock already held: {lock_path}")

        lock_fields = _read_lock_fields(lock_path)
        owner_pid = _parse_lock_pid(lock_fields.get("pid"))
        if owner_pid is not None and _pid_is_alive(owner_pid):
            raise RuntimeError(f"release controller lock held by active pid={owner_pid}: {lock_path}")
        try:
            lock_path.unlink()
        except OSError as exc:
            raise RuntimeError(f"unable to clear stale release controller lock: {lock_path}") from exc

    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    try:
        fd = os.open(str(lock_path), flags)
    except FileExistsError as exc:
        raise RuntimeError(f"release controller lock already held: {lock_path}") from exc

    owner_token = uuid.uuid4().hex
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(f"token={owner_token}\n")
            handle.write(f"pid={os.getpid()}\n")
            handle.write(f"created_at_utc={_utc_now_iso()}\n")
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        _release_run_lock(lock_path, owner_token=owner_token, force=True)
        raise
    return owner_token


def _release_run_lock(lock_path: Path, owner_token: str | None = None, *, force: bool = False) -> bool:
    if not force and owner_token:
        lock_fields = _read_lock_fields(lock_path)
        lock_token = lock_fields.get("token")
        if lock_token != owner_token:
            return False
    try:
        lock_path.unlink()
    except FileNotFoundError:
        return True
    except OSError:
        return False
    return True


def atomic_write_json(path: Path | str, payload: Mapping[str, Any]) -> None:
    """Persist JSON atomically (temp file + fsync + replace)."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=".tmp",
        dir=str(target.parent),
        text=True,
    )

    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        replace_error: Exception | None = None
        for _attempt in range(3):
            try:
                os.replace(tmp_name, target)
                replace_error = None
                break
            except PermissionError as exc:
                replace_error = exc
                time.sleep(0.05)
        if replace_error is not None:
            raise replace_error

        # Best-effort parent-dir fsync so rename metadata is persisted.
        try:
            dir_fd = os.open(str(target.parent), os.O_RDONLY)
        except OSError:
            dir_fd = None
        if dir_fd is not None:
            try:
                os.fsync(dir_fd)
            except OSError:
                pass
            finally:
                os.close(dir_fd)
    finally:
        if os.path.exists(tmp_name):
            try:
                os.unlink(tmp_name)
            except OSError:
                pass


def load_release_metadata(path: Path | str, *, now_utc: Callable[[], str] = _utc_now_iso) -> ReleaseMetadata:
    """Load release metadata or return an empty initialized state."""
    metadata_path = Path(path)
    if not metadata_path.exists():
        return ReleaseMetadata(updated_at=now_utc())

    try:
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"release metadata JSON is invalid: {exc}") from exc
    except OSError as exc:
        raise ValueError(f"unable to read release metadata: {exc}") from exc

    return ReleaseMetadata.from_dict(payload)


def write_release_metadata(path: Path | str, metadata: ReleaseMetadata) -> None:
    """Persist release metadata using atomic JSON replacement."""
    atomic_write_json(path, metadata.to_dict())


def _normalize_probe_output(result: Any) -> StartupProbeResult:
    if isinstance(result, StartupProbeResult):
        return result
    if isinstance(result, bool):
        return StartupProbeResult(ok=result, details="probe_bool_result")
    if isinstance(result, Mapping):
        ok = result.get("ok")
        details = result.get("details", "")
        rollback_ok = result.get("rollback_ok")
        if not isinstance(ok, bool):
            return StartupProbeResult(ok=False, details="probe_mapping_missing_bool_ok")
        if rollback_ok is not None and not isinstance(rollback_ok, bool):
            rollback_ok = None
        return StartupProbeResult(
            ok=ok,
            details=_compact_text(details) or "probe_mapping_result",
            rollback_ok=rollback_ok,
        )
    return StartupProbeResult(ok=False, details="probe_result_unrecognized")


def run_startup_diagnostic(startup_probe: Callable[[], Any]) -> StartupProbeResult:
    """Run startup diagnostics and contain probe exceptions as probe failures."""
    try:
        raw_result = startup_probe()
    except Exception as exc:
        return StartupProbeResult(
            ok=False,
            details=f"probe_exception:{exc.__class__.__name__}:{_compact_text(exc)}",
        )
    return _normalize_probe_output(raw_result)


def build_subprocess_probe(
    command: Sequence[str], *, timeout_seconds: float = DEFAULT_PROBE_TIMEOUT_SECONDS
) -> Callable[[], StartupProbeResult]:
    """Wrap a subprocess command as a startup-probe callback."""
    argv = [str(part) for part in command if str(part).strip()]
    if not argv:
        raise ValueError("probe command must contain at least one token.")
    timeout = max(0.1, float(timeout_seconds))

    def _probe() -> StartupProbeResult:
        try:
            proc = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return StartupProbeResult(ok=False, details=f"probe_timeout:{timeout:.1f}s")
        except OSError as exc:
            return StartupProbeResult(
                ok=False,
                details=f"probe_exec_error:{exc.__class__.__name__}:{_compact_text(exc)}",
            )

        details = [f"rc={int(proc.returncode)}"]
        stdout_text = _compact_text(proc.stdout)
        stderr_text = _compact_text(proc.stderr)
        if stdout_text:
            details.append(f"stdout={stdout_text}")
        if stderr_text:
            details.append(f"stderr={stderr_text}")
        return StartupProbeResult(ok=int(proc.returncode) == 0, details="; ".join(details))

    return _probe


def _run_command(
    command: Sequence[str],
    *,
    timeout_seconds: float | None,
) -> subprocess.CompletedProcess[str]:
    timeout = None if timeout_seconds is None else max(0.1, float(timeout_seconds))
    return subprocess.run(
        [str(part) for part in command],
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )


def _docker_remove_container(
    service_name: str,
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]],
) -> tuple[bool, str]:
    result = runner(["docker", "rm", "-f", service_name], timeout_seconds=20.0)
    if int(result.returncode or 0) == 0:
        return True, "container_removed"
    stderr = _compact_text(result.stderr)
    stdout = _compact_text(result.stdout)
    message = stderr or stdout or f"rc={int(result.returncode or 0)}"
    if "No such container" in message:
        return True, "container_absent"
    return False, f"remove_failed:{message}"


def _docker_start_container(
    *,
    service_name: str,
    release_ref: str,
    release_digest: str,
    runner: Callable[..., subprocess.CompletedProcess[str]],
    run_command: Sequence[str] | None = None,
) -> tuple[bool, str]:
    command = [
        "docker",
        "run",
        "-d",
        "--name",
        service_name,
        "--restart",
        "unless-stopped",
        "-e",
        f"TZ_RELEASE_DIGEST={release_digest}",
        release_ref,
    ]
    if run_command:
        command.extend(str(token) for token in run_command)
    result = runner(command, timeout_seconds=30.0)
    if int(result.returncode or 0) == 0:
        container_id = _compact_text(result.stdout) or "started"
        return True, f"started:{container_id}"
    stderr = _compact_text(result.stderr)
    stdout = _compact_text(result.stdout)
    message = stderr or stdout or f"rc={int(result.returncode or 0)}"
    return False, f"start_failed:{message}"


def _docker_rename_container(
    *,
    source_name: str,
    target_name: str,
    runner: Callable[..., subprocess.CompletedProcess[str]],
) -> tuple[bool, str]:
    result = runner(["docker", "rename", source_name, target_name], timeout_seconds=20.0)
    if int(result.returncode or 0) == 0:
        return True, "rename_ok"
    stderr = _compact_text(result.stderr)
    stdout = _compact_text(result.stdout)
    message = stderr or stdout or f"rc={int(result.returncode or 0)}"
    return False, f"rename_failed:{message}"


def _docker_inspect_container(
    service_name: str,
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]],
) -> DockerContainerState:
    result = runner(
        [
            "docker",
            "inspect",
            "--format",
            "{{.State.Running}}|{{.State.ExitCode}}|{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}",
            service_name,
        ],
        timeout_seconds=10.0,
    )
    if int(result.returncode or 0) != 0:
        stderr = _compact_text(result.stderr)
        stdout = _compact_text(result.stdout)
        message = stderr or stdout or f"inspect_rc={int(result.returncode or 0)}"
        if "No such object" in message or "No such container" in message:
            return DockerContainerState(
                exists=False,
                running=False,
                exit_code=None,
                health_status="none",
                details="container_missing",
            )
        return DockerContainerState(
            exists=False,
            running=False,
            exit_code=None,
            health_status="none",
            details=f"inspect_failed:{message}",
        )

    payload = str(result.stdout or "").strip()
    parts = payload.split("|", 2)
    if len(parts) != 3:
        return DockerContainerState(
            exists=True,
            running=False,
            exit_code=None,
            health_status="none",
            details=f"inspect_parse_failed:{payload}",
        )
    running = parts[0].strip().lower() == "true"
    exit_code_text = parts[1].strip()
    health_status = parts[2].strip().lower() or "none"
    try:
        exit_code = int(exit_code_text)
    except ValueError:
        exit_code = None
    return DockerContainerState(
        exists=True,
        running=running,
        exit_code=exit_code,
        health_status=health_status,
        details=f"running={running}|exit={exit_code}|health={health_status}",
    )


def _docker_tail_logs(
    service_name: str,
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]],
) -> str:
    result = runner(["docker", "logs", "--tail", "40", service_name], timeout_seconds=15.0)
    stderr = _compact_text(result.stderr)
    stdout = _compact_text(result.stdout)
    logs = stderr or stdout
    if logs:
        return logs
    return f"docker_logs_rc={int(result.returncode or 0)}"


def _watch_container_ready(
    *,
    container_name: str,
    wait_seconds: float,
    runner: Callable[..., subprocess.CompletedProcess[str]],
    monotonic: Callable[[], float],
    sleep_fn: Callable[[float], None],
) -> tuple[bool, DockerContainerState]:
    deadline = monotonic() + max(1.0, float(wait_seconds))
    last_state = DockerContainerState(
        exists=False,
        running=False,
        exit_code=None,
        health_status="none",
        details="not_checked",
    )
    while monotonic() < deadline:
        state = _docker_inspect_container(container_name, runner=runner)
        last_state = state
        if state.exists and not state.running:
            return False, state
        if (not state.exists) and state.details.startswith("inspect_failed"):
            return False, state
        sleep_fn(1.0)

    final_state = _docker_inspect_container(container_name, runner=runner)
    if _state_ready(final_state):
        return True, final_state
    return False, final_state


def _attempt_rollback_to_previous(
    *,
    service_name: str,
    rollback_ref: str | None,
    runner: Callable[..., subprocess.CompletedProcess[str]],
    rollback_wait_seconds: float = DEFAULT_STARTUP_WAIT_SECONDS,
    monotonic: Callable[[], float] = time.monotonic,
    sleep_fn: Callable[[float], None] = time.sleep,
    run_command: Sequence[str] | None = None,
) -> tuple[bool, str]:
    _docker_remove_container(service_name, runner=runner)
    if rollback_ref is None:
        return False, "rollback_unavailable"
    rollback_digest = extract_release_digest(rollback_ref)
    started, start_details = _docker_start_container(
        service_name=service_name,
        release_ref=rollback_ref,
        release_digest=rollback_digest,
        runner=runner,
        run_command=run_command,
    )
    if not started:
        return False, f"rollback_start_failed:{start_details}"
    ready, state = _watch_container_ready(
        container_name=service_name,
        wait_seconds=rollback_wait_seconds,
        runner=runner,
        monotonic=monotonic,
        sleep_fn=sleep_fn,
    )
    if ready:
        return True, f"rollback_started:{state.details}"
    logs = _docker_tail_logs(service_name, runner=runner)
    return False, f"rollback_not_ready:{state.details}; logs={logs}"


def _verify_active_or_rollback(
    *,
    service_name: str,
    rollback_ref: str | None,
    runner: Callable[..., subprocess.CompletedProcess[str]],
    rollback_wait_seconds: float,
    monotonic: Callable[[], float],
    sleep_fn: Callable[[float], None],
    run_command: Sequence[str] | None,
) -> tuple[bool, str]:
    active_state = _docker_inspect_container(service_name, runner=runner)
    if _state_ready(active_state):
        return True, f"active_container_ready:{active_state.details}"
    return _attempt_rollback_to_previous(
        service_name=service_name,
        rollback_ref=rollback_ref,
        runner=runner,
        rollback_wait_seconds=rollback_wait_seconds,
        monotonic=monotonic,
        sleep_fn=sleep_fn,
        run_command=run_command,
    )


def build_docker_startup_probe(
    *,
    service_name: str,
    candidate_ref: str,
    rollback_ref: str | None,
    startup_wait_seconds: float = DEFAULT_STARTUP_WAIT_SECONDS,
    rollback_wait_seconds: float = DEFAULT_STARTUP_WAIT_SECONDS,
    run_command: Sequence[str] | None = None,
    runner: Callable[..., subprocess.CompletedProcess[str]] = _run_command,
    monotonic: Callable[[], float] = time.monotonic,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> Callable[[], StartupProbeResult]:
    """
    Deploy candidate container and auto-rollback to N-1 if startup trap exits.

    The probe returns success only when the candidate container is still running
    after the startup watch window.
    """
    service = str(service_name or "").strip()
    if not service:
        raise ValueError("service_name must be non-empty.")
    candidate = require_digest_locked_release_ref(candidate_ref)
    rollback = require_digest_locked_release_ref(rollback_ref) if rollback_ref else None
    wait_seconds = max(1.0, float(startup_wait_seconds))
    rollback_wait = max(1.0, float(rollback_wait_seconds))
    candidate_digest = extract_release_digest(candidate)
    candidate_container = f"{service}__candidate"

    def _probe() -> StartupProbeResult:
        # Keep active service running until candidate survives startup window.
        _docker_remove_container(candidate_container, runner=runner)

        started, start_details = _docker_start_container(
            service_name=candidate_container,
            release_ref=candidate,
            release_digest=candidate_digest,
            runner=runner,
            run_command=run_command,
        )
        if not started:
            rollback_ok, rollback_details = _verify_active_or_rollback(
                service_name=service,
                rollback_ref=rollback,
                runner=runner,
                rollback_wait_seconds=rollback_wait,
                monotonic=monotonic,
                sleep_fn=sleep_fn,
                run_command=run_command,
            )
            return StartupProbeResult(
                ok=False,
                details=(
                    f"candidate_start_failed:{start_details}; "
                    f"rollback_ok={rollback_ok}; rollback_details={rollback_details}"
                ),
                rollback_ok=rollback_ok,
            )

        candidate_ready, candidate_state = _watch_container_ready(
            container_name=candidate_container,
            wait_seconds=wait_seconds,
            runner=runner,
            monotonic=monotonic,
            sleep_fn=sleep_fn,
        )
        if not candidate_ready:
            logs = _docker_tail_logs(candidate_container, runner=runner)
            _docker_remove_container(candidate_container, runner=runner)
            rollback_ok, rollback_details = _verify_active_or_rollback(
                service_name=service,
                rollback_ref=rollback,
                runner=runner,
                rollback_wait_seconds=rollback_wait,
                monotonic=monotonic,
                sleep_fn=sleep_fn,
                run_command=run_command,
            )
            return StartupProbeResult(
                ok=False,
                details=(
                    f"candidate_not_ready:{candidate_state.details}; logs={logs}; "
                    f"rollback_ok={rollback_ok}; rollback_details={rollback_details}"
                ),
                rollback_ok=rollback_ok,
            )

        removed_active, removed_details = _docker_remove_container(service, runner=runner)
        if not removed_active:
            _docker_remove_container(candidate_container, runner=runner)
            rollback_ok, rollback_details = _attempt_rollback_to_previous(
                service_name=service,
                rollback_ref=rollback,
                runner=runner,
                rollback_wait_seconds=rollback_wait,
                monotonic=monotonic,
                sleep_fn=sleep_fn,
                run_command=run_command,
            )
            return StartupProbeResult(
                ok=False,
                details=(
                    f"active_remove_failed:{removed_details}; "
                    f"rollback_ok={rollback_ok}; rollback_details={rollback_details}"
                ),
                rollback_ok=rollback_ok,
            )

        renamed, rename_details = _docker_rename_container(
            source_name=candidate_container,
            target_name=service,
            runner=runner,
        )
        if not renamed:
            _docker_remove_container(candidate_container, runner=runner)
            rollback_ok, rollback_details = _attempt_rollback_to_previous(
                service_name=service,
                rollback_ref=rollback,
                runner=runner,
                rollback_wait_seconds=rollback_wait,
                monotonic=monotonic,
                sleep_fn=sleep_fn,
                run_command=run_command,
            )
            return StartupProbeResult(
                ok=False,
                details=(
                    f"candidate_promote_rename_failed:{rename_details}; "
                    f"rollback_ok={rollback_ok}; rollback_details={rollback_details}"
                ),
                rollback_ok=rollback_ok,
            )

        final_ready, final_state = _watch_container_ready(
            container_name=service,
            wait_seconds=min(wait_seconds, 10.0),
            runner=runner,
            monotonic=monotonic,
            sleep_fn=sleep_fn,
        )
        if final_ready:
            return StartupProbeResult(
                ok=True,
                details=f"candidate_promoted:{candidate_state.details}; final_state={final_state.details}",
            )

        logs = _docker_tail_logs(service, runner=runner)
        rollback_ok, rollback_details = _attempt_rollback_to_previous(
            service_name=service,
            rollback_ref=rollback,
            runner=runner,
            rollback_wait_seconds=rollback_wait,
            monotonic=monotonic,
            sleep_fn=sleep_fn,
            run_command=run_command,
        )
        return StartupProbeResult(
            ok=False,
            details=(
                f"candidate_promoted_but_not_ready:{final_state.details}; logs={logs}; "
                f"rollback_ok={rollback_ok}; rollback_details={rollback_details}"
            ),
            rollback_ok=rollback_ok,
        )

    return _probe


def _derive_stable_release_history(prior_state: ReleaseMetadata) -> tuple[ReleaseRecord | None, ReleaseRecord | None]:
    """
    Derive last-known-good (N and N-1) from persisted metadata.

    If a prior run crashed in `pending_probe` after writing candidate into
    `current_release`, prefer `previous_release` as the stable rollback baseline.
    """
    stable_current = prior_state.current_release
    stable_previous = prior_state.previous_release

    pending = prior_state.pending_release
    if (
        prior_state.status == "pending_probe"
        and pending is not None
        and stable_current is not None
        and stable_current.release_ref == pending.release_ref
    ):
        stable_current = prior_state.previous_release
        stable_previous = None

    if (
        stable_current is not None
        and stable_previous is not None
        and stable_current.release_ref == stable_previous.release_ref
    ):
        stable_previous = None

    return stable_current, stable_previous


def execute_release_controller(
    *,
    metadata_path: Path | str,
    candidate_version: str,
    candidate_ref: str,
    startup_probe: Callable[[], Any],
    now_utc: Callable[[], str] = _utc_now_iso,
) -> dict[str, Any]:
    """
    Promote a digest-locked candidate release and rollback to N-1 on failed probe.

    The controller performs two atomic metadata writes: `pending_probe` stage and final
    `active`/`rolled_back`/`rollback_failed` state after diagnostic probe completion.
    """
    version = str(candidate_version or "").strip()
    if not version:
        raise ValueError("candidate_version must be non-empty.")
    normalized_ref = require_digest_locked_release_ref(candidate_ref)

    prior_state = load_release_metadata(metadata_path, now_utc=now_utc)
    stable_release, stable_previous_release = _derive_stable_release_history(prior_state)

    stage_ts = now_utc()
    candidate = ReleaseRecord(version=version, release_ref=normalized_ref, deployed_at=stage_ts)
    staged_state = dataclasses.replace(
        prior_state,
        current_release=stable_release,
        previous_release=stable_previous_release,
        pending_release=candidate,
        last_candidate_release=candidate,
        status="pending_probe",
        last_action="candidate_staged",
        last_probe=None,
        updated_at=stage_ts,
    )
    write_release_metadata(metadata_path, staged_state)

    probe_result = run_startup_diagnostic(startup_probe)
    finalize_ts = now_utc()
    probe_payload = {
        "ok": bool(probe_result.ok),
        "details": _compact_text(probe_result.details) or "probe_completed",
        "checked_at": finalize_ts,
    }
    if probe_result.rollback_ok is not None:
        probe_payload["rollback_ok"] = probe_result.rollback_ok

    if probe_result.ok:
        promoted_state = dataclasses.replace(
            staged_state,
            current_release=candidate,
            previous_release=stable_release or stable_previous_release,
            pending_release=None,
            status="active",
            last_action="promoted",
            last_probe=probe_payload,
            updated_at=finalize_ts,
        )
        write_release_metadata(metadata_path, promoted_state)
        return {
            "status": "promoted",
            "candidate_version": candidate.version,
            "candidate_ref": candidate.release_ref,
            "active_version": promoted_state.current_release.version if promoted_state.current_release else None,
            "active_ref": promoted_state.current_release.release_ref if promoted_state.current_release else None,
            "rollback_target": None,
            "rollback_verified": None,
            "probe_ok": True,
            "probe_details": probe_payload["details"],
        }

    if stable_release is not None:
        rollback_current = stable_release
        rollback_previous = stable_previous_release
        rollback_target = "n-1"
        rollback_action = "rolled_back_to_n_minus_1"
    elif stable_previous_release is not None:
        rollback_current = stable_previous_release
        rollback_previous = None
        rollback_target = "previous_only"
        rollback_action = "rolled_back_without_current"
    else:
        rollback_current = None
        rollback_previous = None
        rollback_target = "none"
        rollback_action = "rollback_target_unavailable"

    rollback_verified = bool(probe_result.rollback_ok) and rollback_current is not None
    if rollback_verified:
        final_status = "rolled_back"
        final_action = rollback_action
        final_current = rollback_current
        final_previous = rollback_previous
    else:
        final_status = "rollback_failed"
        if rollback_current is None:
            final_action = "rollback_target_unavailable"
        elif probe_result.rollback_ok is False:
            final_action = "rollback_not_verified"
        else:
            final_action = "rollback_verification_missing"
        final_current = None
        final_previous = rollback_previous

    finalized_state = dataclasses.replace(
        staged_state,
        current_release=final_current,
        previous_release=final_previous,
        pending_release=None,
        status=final_status,
        last_action=final_action,
        last_probe=probe_payload,
        updated_at=finalize_ts,
    )
    write_release_metadata(metadata_path, finalized_state)
    return {
        "status": final_status,
        "candidate_version": candidate.version,
        "candidate_ref": candidate.release_ref,
        "active_version": finalized_state.current_release.version if finalized_state.current_release else None,
        "active_ref": finalized_state.current_release.release_ref if finalized_state.current_release else None,
        "rollback_target": rollback_target,
        "rollback_verified": rollback_verified,
        "probe_ok": False,
        "probe_details": probe_payload["details"],
    }


def _build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Release controller with startup probe and N-1 rollback")
    parser.add_argument(
        "--metadata-path",
        default=str(DEFAULT_METADATA_PATH),
        help="Path to release metadata JSON file.",
    )
    parser.add_argument("--candidate-version", required=True, help="Candidate release version identifier.")
    parser.add_argument(
        "--candidate-ref",
        required=True,
        help="Digest-locked release reference (name[:tag]@sha256:<digest>).",
    )
    parser.add_argument(
        "--mode",
        choices=("docker", "metadata-only", "external-probe"),
        default=DEFAULT_DEPLOYMENT_MODE,
        help="Promotion mode: docker deploy/rollback, metadata-only, or external probe command.",
    )
    parser.add_argument(
        "--probe-command",
        nargs="+",
        default=None,
        help="External probe command tokens (required for --mode external-probe).",
    )
    parser.add_argument(
        "--allow-external-probe-promote",
        action="store_true",
        help=(
            "Required acknowledgement for --mode external-probe. Use only when runtime "
            "deployment/rollback is managed outside this controller."
        ),
    )
    parser.add_argument(
        "--probe-timeout-seconds",
        type=float,
        default=DEFAULT_PROBE_TIMEOUT_SECONDS,
        help="Timeout budget for the startup probe command.",
    )
    parser.add_argument(
        "--service-name",
        default=DEFAULT_SERVICE_NAME,
        help="Container service name used for docker mode deployment.",
    )
    parser.add_argument(
        "--startup-wait-seconds",
        type=float,
        default=DEFAULT_STARTUP_WAIT_SECONDS,
        help="Watch window to confirm candidate container remains running in docker mode.",
    )
    parser.add_argument(
        "--run-command",
        nargs="+",
        default=None,
        help="Optional override command appended to `docker run ... <image>`.",
    )
    parser.add_argument(
        "--lock-path",
        default=None,
        help="Optional lock-file path for single-flight release operations. Defaults to <metadata-path>.lock",
    )
    parser.add_argument(
        "--lock-stale-seconds",
        type=float,
        default=600.0,
        help="Stale lock age threshold before lock takeover is allowed.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint for release promotion and rollback control."""
    parser = _build_argument_parser()
    args = parser.parse_args(argv)
    if args.probe_timeout_seconds <= 0:
        parser.error("--probe-timeout-seconds must be > 0.")
    if args.startup_wait_seconds <= 0:
        parser.error("--startup-wait-seconds must be > 0.")
    if args.lock_stale_seconds <= 0:
        parser.error("--lock-stale-seconds must be > 0.")
    if args.mode == "external-probe":
        if not args.probe_command:
            parser.error("--probe-command is required for --mode external-probe.")
        if not args.allow_external_probe_promote:
            parser.error("--allow-external-probe-promote is required for --mode external-probe.")

    metadata_path = Path(args.metadata_path)
    lock_path = Path(args.lock_path) if args.lock_path else Path(f"{metadata_path}.lock")
    lock_token = _acquire_run_lock(lock_path, stale_seconds=args.lock_stale_seconds)
    try:
        prior_state = load_release_metadata(metadata_path)
        stable_release, stable_previous = _derive_stable_release_history(prior_state)

        if args.mode == "metadata-only":
            probe = lambda: StartupProbeResult(ok=True, details="metadata_only_probe_skipped")
        elif args.mode == "external-probe":
            probe = build_subprocess_probe(args.probe_command, timeout_seconds=args.probe_timeout_seconds)
        else:
            rollback_ref = None
            if stable_release is not None:
                rollback_ref = stable_release.release_ref
            elif stable_previous is not None:
                rollback_ref = stable_previous.release_ref
            probe = build_docker_startup_probe(
                service_name=args.service_name,
                candidate_ref=args.candidate_ref,
                rollback_ref=rollback_ref,
                startup_wait_seconds=args.startup_wait_seconds,
                rollback_wait_seconds=args.startup_wait_seconds,
                run_command=args.run_command,
            )

        result = execute_release_controller(
            metadata_path=metadata_path,
            candidate_version=args.candidate_version,
            candidate_ref=args.candidate_ref,
            startup_probe=probe,
        )
    except Exception as exc:
        print(f"release_controller_error: {exc}", file=sys.stderr)
        return 2
    finally:
        _release_run_lock(lock_path, owner_token=lock_token)

    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True))
    if result["status"] == "promoted":
        return 0
    if result["status"] == "rolled_back":
        return 3
    return 4


if __name__ == "__main__":
    raise SystemExit(main())
