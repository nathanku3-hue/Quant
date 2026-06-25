from __future__ import annotations

import argparse
from collections import deque
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


CURRENT_TRUTH_FILES = (
    "planner_packet_current.md",
    "impact_packet_current.md",
    "bridge_contract_current.md",
    "done_checklist_current.md",
    "multi_stream_contract_current.md",
    "post_phase_alignment_current.md",
    "observability_pack_current.md",
)
DEFAULT_GIT_CAPTURE_PATHS = (
    "AGENTS.md",
    "docs/decision log.md",
    "docs/notes.md",
    "docs/lessonss.md",
    "scripts/build_expert_packet.py",
    "docs/templates/worker_done_contract.md",
    "docs/templates/expert_reconciliation_matrix.md",
    "docs/templates/stream_contract.md",
    ".codex/skills/scope-selector/SKILL.md",
    ".codex/skills/expert-context-packer/SKILL.md",
    ".codex/skills/boundary-gate/SKILL.md",
    ".codex/skills/harness-feedback/SKILL.md",
    *tuple(f"docs/context/{name}" for name in CURRENT_TRUTH_FILES),
)
ROOT_PACKET_FILES = (
    "README_DECISION_CARD.md",
    "candidate_scope_memo.md",
    "low_confidence_and_boundaries.md",
)
OPTIONAL_SCREENSHOT_EXTENSIONS = {
    ".avif",
    ".gif",
    ".jpeg",
    ".jpg",
    ".png",
    ".webp",
}
FORBIDDEN_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "processed",
    "runtime",
}
MAX_INCLUDED_FILE_BYTES = 2_000_000
GIT_OUTPUT_LINE_CAP = 200
GIT_OUTPUT_BYTE_CAP = 50_000
GIT_TIMEOUT_SECONDS = 20
TAIL_LINES = 300
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


class ExpertPacketError(RuntimeError):
    pass


def _repo_root_from_args(raw: str | None) -> Path:
    root = Path(raw).resolve() if raw else Path.cwd().resolve()
    if not (root / ".git").exists():
        raise ExpertPacketError(f"Repo root does not contain .git: {root}")
    return root


def _safe_round_id(round_id: str) -> str:
    cleaned = round_id.strip()
    if not cleaned:
        raise ExpertPacketError("Round ID cannot be blank.")
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-")
    if any(char not in allowed for char in cleaned):
        raise ExpertPacketError(
            "Round ID may contain only letters, numbers, dot, underscore, and hyphen."
        )
    if cleaned in {".", ".."}:
        raise ExpertPacketError("Round ID cannot be a relative-path marker.")
    return cleaned


def _resolve_repo_path(raw: str, repo_root: Path, label: str) -> Path:
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    resolved = candidate.resolve()
    _assert_inside(resolved, repo_root, label)
    return resolved


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _assert_inside(path: Path, root: Path, label: str) -> None:
    if not _is_relative_to(path.resolve(), root.resolve()):
        raise ExpertPacketError(f"{label} must stay inside {root}: {path}")


def _relative_posix(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _path_has_forbidden_part(path: Path, repo_root: Path) -> bool:
    try:
        parts = path.resolve().relative_to(repo_root.resolve()).parts
    except ValueError:
        return True
    lowered = {part.lower() for part in parts}
    if "data" in lowered and "processed" in lowered:
        return True
    return any(part in FORBIDDEN_PARTS for part in lowered)


def _copy_file(src: Path, dest: Path, repo_root: Path) -> None:
    src = src.resolve()
    _assert_inside(src, repo_root, "Source file")
    if _path_has_forbidden_part(src, repo_root):
        raise ExpertPacketError(f"Refusing forbidden source path: {src}")
    if not src.is_file():
        raise ExpertPacketError(f"Source file does not exist: {src}")
    size = src.stat().st_size
    if size > MAX_INCLUDED_FILE_BYTES:
        raise ExpertPacketError(
            f"Refusing large source file over {MAX_INCLUDED_FILE_BYTES} bytes: {src}"
        )
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)


def _copy_optional_or_stub(
    src: Path | None,
    dest: Path,
    repo_root: Path,
    *,
    title: str,
    round_id: str,
    stub_body: str,
) -> None:
    if src is None:
        dest.write_text(
            f"# {title}\n\n"
            f"RoundID: {round_id}\n\n"
            f"{stub_body.rstrip()}\n",
            encoding="utf-8",
            newline="\n",
        )
        return
    _copy_file(src, dest, repo_root)


def _limit_git_output(text: str) -> str:
    normalized = text.replace("\r\n", "\n")
    encoded_size = len(normalized.encode("utf-8"))
    lines = normalized.splitlines()
    if encoded_size <= GIT_OUTPUT_BYTE_CAP and len(lines) <= GIT_OUTPUT_LINE_CAP:
        return normalized
    trimmed = "\n".join(lines[:GIT_OUTPUT_LINE_CAP])
    if trimmed:
        trimmed += "\n"
    trimmed += (
        f"... truncated after {GIT_OUTPUT_LINE_CAP} lines "
        f"or {GIT_OUTPUT_BYTE_CAP} bytes ...\n"
    )
    return trimmed


def _run_git(repo_root: Path, args: list[str], pathspecs: list[str]) -> str:
    command = ["git", *args]
    if pathspecs:
        command.extend(["--", *pathspecs])
    try:
        result = subprocess.run(
            command,
            cwd=repo_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            shell=False,
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        command_text = " ".join(command)
        raise ExpertPacketError(
            f"{command_text} timed out after {GIT_TIMEOUT_SECONDS}s"
        ) from exc
    if result.returncode != 0:
        command_text = " ".join(command)
        raise ExpertPacketError(f"{command_text} failed: {result.stderr.strip()}")
    return _limit_git_output(result.stdout)


def _collect_git_capture_paths(
    repo_root: Path,
    blocked_root: Path,
    extra_paths: list[str] | None,
) -> list[Path]:
    candidate_paths = list(DEFAULT_GIT_CAPTURE_PATHS)
    if extra_paths:
        candidate_paths.extend(extra_paths)

    resolved: list[Path] = []
    seen: set[Path] = set()
    for raw in candidate_paths:
        path = _resolve_repo_path(raw, repo_root, "Git capture path")
        if not path.exists():
            raise ExpertPacketError(f"Git capture path does not exist: {path}")
        if _is_relative_to(path, blocked_root):
            raise ExpertPacketError(
                f"Refusing git capture path inside packet output root: {path}"
            )
        if path in seen:
            continue
        seen.add(path)
        resolved.append(path)
    return resolved


def _write_git_files(
    packet_dir: Path,
    repo_root: Path,
    git_capture_paths: list[Path],
) -> None:
    pathspecs = [path.relative_to(repo_root).as_posix() for path in git_capture_paths]
    captures = {
        "git_status.txt": ["status", "--short"],
        "git_diff_name_status.txt": ["diff", "--name-status"],
        "git_log_oneline_20.txt": ["log", "--oneline", "-20"],
    }
    for filename, git_args in captures.items():
        content = _run_git(repo_root, git_args, pathspecs)
        if filename == "git_log_oneline_20.txt":
            content = (
                "# Scope-specific provenance note\n"
                "# git log is limited to declared expert-packet paths.\n\n"
                f"{content}"
            )
        (packet_dir / filename).write_text(
            content, encoding="utf-8", newline="\n"
        )


def _copy_current_truth_files(packet_dir: Path, repo_root: Path) -> list[str]:
    copied: list[str] = []
    source_root = repo_root / "docs" / "context"
    target_root = packet_dir / "docs" / "context"
    for filename in CURRENT_TRUTH_FILES:
        src = source_root / filename
        if src.exists():
            dest = target_root / filename
            _copy_file(src, dest, repo_root)
            copied.append(_relative_posix(src, repo_root))
    return copied


def _tail_file(src: Path, dest: Path, repo_root: Path) -> None:
    _assert_inside(src, repo_root, "Tail source")
    if not src.is_file():
        raise ExpertPacketError(f"Tail source does not exist: {src}")
    tail_lines: deque[str] = deque(maxlen=TAIL_LINES)
    with src.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            tail_lines.append(line)
    tail = "".join(tail_lines)
    dest.write_text(tail, encoding="utf-8", newline="\n")


def _copy_optional_screenshots(
    packet_dir: Path,
    repo_root: Path,
    screenshots_dir: Path | None,
) -> list[str]:
    if screenshots_dir is None:
        return []

    screenshots_dir = _resolve_repo_path(str(screenshots_dir), repo_root, "Screenshots directory")
    if _path_has_forbidden_part(screenshots_dir, repo_root):
        raise ExpertPacketError(f"Refusing forbidden screenshots path: {screenshots_dir}")
    if not screenshots_dir.is_dir():
        raise ExpertPacketError(f"Screenshots directory does not exist: {screenshots_dir}")

    copied: list[str] = []
    target_root = packet_dir / "optional_screenshots"
    for src in sorted(path for path in screenshots_dir.rglob("*") if path.is_file()):
        if _path_has_forbidden_part(src, repo_root):
            continue
        if src.suffix.lower() not in OPTIONAL_SCREENSHOT_EXTENSIONS:
            continue
        if src.stat().st_size > MAX_INCLUDED_FILE_BYTES:
            continue
        rel = src.relative_to(screenshots_dir)
        dest = target_root / rel
        _copy_file(src, dest, repo_root)
        copied.append(_relative_posix(src, repo_root))
    return copied


def _write_manifest(
    packet_dir: Path,
    repo_root: Path,
    round_id: str,
    git_capture_paths: list[Path],
    copied_truth_files: list[str],
    copied_screenshots: list[str],
    zip_path: Path | None,
) -> None:
    lines = [
        "# Expert Packet Manifest",
        "",
        f"RoundID: {round_id}",
        "Builder: scripts/build_expert_packet.py",
        "",
        "Included root files:",
        *[f"- {name}" for name in ROOT_PACKET_FILES],
        "- git_status.txt",
        "- git_diff_name_status.txt",
        "- git_log_oneline_20.txt",
        "- decision_log_tail.md",
        "- lessonss_tail.md",
        "",
        "Git capture scope:",
        *[f"- {path.relative_to(repo_root).as_posix()}" for path in git_capture_paths],
        "",
        "Included current truth files:",
        *[f"- {path}" for path in copied_truth_files],
        "",
        "Optional screenshots:",
        *([f"- {path}" for path in copied_screenshots] or ["- none"]),
        "",
        "Excluded by design:",
        "- runtime/",
        "- data/processed/",
        "- .venv/",
        "- caches and __pycache__ directories",
        "- full repository dumps",
        "- files larger than the packet size cap",
    ]
    if zip_path is not None:
        lines.extend(["", f"Zip: {zip_path.name}"])
    packet_dir.joinpath("PACKET_MANIFEST.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8", newline="\n"
    )


def _replace_directory(src: Path, dest: Path, overwrite: bool) -> None:
    if dest.exists():
        if not overwrite:
            raise ExpertPacketError(f"Packet directory already exists: {dest}")
        if not dest.is_dir():
            raise ExpertPacketError(f"Packet path exists and is not a directory: {dest}")
        shutil.rmtree(dest)
    src.rename(dest)


def _make_zip(packet_dir: Path, overwrite: bool) -> Path:
    zip_path = packet_dir.with_suffix(".zip")
    if zip_path.exists():
        if not overwrite:
            raise ExpertPacketError(f"Zip already exists: {zip_path}")
        zip_path.unlink()

    entries = sorted(path for path in packet_dir.rglob("*") if path.is_file())
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in entries:
            arcname = packet_dir.name + "/" + path.relative_to(packet_dir).as_posix()
            info = zipfile.ZipInfo(arcname, ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())
    return zip_path


def build_packet(args: argparse.Namespace) -> tuple[Path, Path | None, list[str]]:
    repo_root = _repo_root_from_args(args.repo_root)
    round_id = _safe_round_id(args.round)
    output_root = (repo_root / args.output_root).resolve()
    _assert_inside(output_root, repo_root, "Output root")
    if _path_has_forbidden_part(output_root, repo_root):
        raise ExpertPacketError(f"Refusing forbidden output root: {output_root}")

    packet_dir = output_root / round_id
    _assert_inside(packet_dir, output_root, "Packet directory")
    output_root.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        planned = [
            str(packet_dir),
            *(str(repo_root / "docs" / "context" / name) for name in CURRENT_TRUTH_FILES),
            str(repo_root / "docs" / "decision log.md"),
            str(repo_root / "docs" / "lessonss.md"),
        ]
        return packet_dir, packet_dir.with_suffix(".zip") if args.zip else None, planned

    git_capture_paths = _collect_git_capture_paths(repo_root, output_root, args.git_path)
    temp_parent = Path(tempfile.mkdtemp(prefix=f".{round_id}.tmp-", dir=output_root)).resolve()
    try:
        staging_dir = temp_parent / round_id
        staging_dir.mkdir()

        source_map = {
            "README_DECISION_CARD.md": args.decision_card,
            "candidate_scope_memo.md": args.candidate_scope_memo,
            "low_confidence_and_boundaries.md": args.low_confidence_and_boundaries,
        }
        stubs = {
            "README_DECISION_CARD.md": (
                "Expert Decision Card",
                "Purpose: curated packet for expert review.\n\n"
                "Current Problem: supplied by orchestrator or packet consumer.\n\n"
                "Desired Decision: supplied by orchestrator or packet consumer.\n",
            ),
            "candidate_scope_memo.md": (
                "Candidate Scope Memo",
                "No candidate scope memo source was supplied. Use this packet with the "
                "current truth files and git captures to fill the decision scope.\n",
            ),
            "low_confidence_and_boundaries.md": (
                "Low Confidence And Boundaries",
                "No low-confidence memo source was supplied. Treat live trading, broker "
                "actions, provider ingestion, data generation, full repo cleanup, and large "
                "artifact commits as out of boundary unless explicitly approved.\n",
            ),
        }
        for filename, raw_src in source_map.items():
            title, body = stubs[filename]
            src = _resolve_repo_path(raw_src, repo_root, "Optional memo source") if raw_src else None
            _copy_optional_or_stub(
                src,
                staging_dir / filename,
                repo_root,
                title=title,
                round_id=round_id,
                stub_body=body,
            )

        _write_git_files(staging_dir, repo_root, git_capture_paths)
        copied_truth_files = _copy_current_truth_files(staging_dir, repo_root)
        _tail_file(repo_root / "docs" / "decision log.md", staging_dir / "decision_log_tail.md", repo_root)
        _tail_file(repo_root / "docs" / "lessonss.md", staging_dir / "lessonss_tail.md", repo_root)
        copied_screenshots = _copy_optional_screenshots(
            staging_dir,
            repo_root,
            _resolve_repo_path(args.screenshots_dir, repo_root, "Screenshots directory")
            if args.screenshots_dir
            else None,
        )

        _write_manifest(
            staging_dir,
            repo_root,
            round_id,
            git_capture_paths,
            copied_truth_files,
            copied_screenshots,
            None,
        )
        _replace_directory(staging_dir, packet_dir, args.overwrite)
    finally:
        if temp_parent.exists():
            shutil.rmtree(temp_parent, ignore_errors=True)

    zip_path = _make_zip(packet_dir, args.overwrite) if args.zip else None
    if zip_path is not None:
        _write_manifest(
            packet_dir,
            repo_root,
            round_id,
            git_capture_paths,
            copied_truth_files,
            copied_screenshots,
            zip_path,
        )
        zip_path = _make_zip(packet_dir, True)

    included = [
        path.relative_to(packet_dir).as_posix()
        for path in sorted(packet_dir.rglob("*"))
        if path.is_file()
    ]
    return packet_dir, zip_path, included


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a small curated expert packet under docs/context/expert_packets/<ROUND>/."
    )
    parser.add_argument("round", help="Round ID used as the packet directory name.")
    parser.add_argument("--repo-root", help="Repository root. Defaults to current working directory.")
    parser.add_argument(
        "--output-root",
        default="docs/context/expert_packets",
        help="Repo-relative packet output root. Defaults to docs/context/expert_packets.",
    )
    parser.add_argument("--decision-card", help="Optional source for README_DECISION_CARD.md.")
    parser.add_argument(
        "--candidate-scope-memo",
        help="Optional source for candidate_scope_memo.md.",
    )
    parser.add_argument(
        "--low-confidence-and-boundaries",
        help="Optional source for low_confidence_and_boundaries.md.",
    )
    parser.add_argument(
        "--git-path",
        action="append",
        help="Optional extra repo-relative path to include in the scoped git captures.",
    )
    parser.add_argument(
        "--screenshots-dir",
        help="Explicit repo-local directory of screenshots to copy into optional_screenshots/.",
    )
    parser.add_argument("--zip", action="store_true", help="Also create a deterministic .zip.")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing packet directory/zip.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned outputs without writing.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        packet_dir, zip_path, included = build_packet(args)
    except ExpertPacketError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    action = "Would build" if args.dry_run else "Built"
    print(f"{action} expert packet: {packet_dir}")
    if zip_path is not None:
        print(f"{action} zip: {zip_path}")
    if args.dry_run:
        print("Planned inputs:")
    else:
        print("Included files:")
    for item in included:
        print(f"- {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
