from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import shutil
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
FREEZE_ROOT = PROCESSED_DIR / "phase23_freeze"
LATEST_POINTER = PROCESSED_DIR / "phase23_freeze_latest.json"

PHASE23_CODE_FILES: tuple[str, ...] = (
    "strategies/company_scorecard.py",
    "strategies/ticker_pool.py",
    "scripts/phase20_full_backtest.py",
    "scripts/optimize_softmax_temperature.py",
    "scripts/diagnostic_softmax_weights.py",
    "data/macro_loader.py",
    "data/orbis_loader.py",
    "scripts/align_orbis_macro.py",
    "scripts/orbis_signal_generator.py",
)

PRIMARY_ARTIFACTS: tuple[str, ...] = (
    "data/processed/phase23_wfo_temperature_summary.json",
    "data/processed/phase23_softmax_sizing_summary.json",
    "data/processed/phase23_final_rollback_slice_summary.json",
)

PRIMARY_ARTIFACT_DIRS: tuple[str, ...] = (
    "data/processed/phase23_wfo_temperature",
)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _atomic_write_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp.{datetime.now(timezone.utc).timestamp():.0f}")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def _repo_rel(path_like: str | Path) -> Path | None:
    p = Path(path_like)
    if not p.is_absolute():
        p = (PROJECT_ROOT / p).resolve()
    else:
        p = p.resolve()
    try:
        return p.relative_to(PROJECT_ROOT)
    except ValueError:
        return None


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return obj if isinstance(obj, dict) else None


def _extract_phase20_metrics(summary: dict[str, Any]) -> dict[str, float] | None:
    metrics = summary.get("metrics")
    if isinstance(metrics, dict):
        phase20 = metrics.get("phase20")
        if isinstance(phase20, dict):
            try:
                return {
                    "cagr": float(phase20.get("cagr")),
                    "sharpe": float(phase20.get("sharpe")),
                    "max_dd": float(phase20.get("max_dd")),
                }
            except Exception:
                return None
    return None


def _collect_best_summaries(limit: int = 10) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for p in PROCESSED_DIR.rglob("*summary*.json"):
        doc = _load_json(p)
        if not doc:
            continue
        m = _extract_phase20_metrics(doc)
        if not m:
            continue
        rows.append(
            {
                "path": str(p.relative_to(PROJECT_ROOT)),
                "cagr": float(m["cagr"]),
                "sharpe": float(m["sharpe"]),
                "max_dd": float(m["max_dd"]),
            }
        )
    rows.sort(key=lambda r: (r["cagr"], r["sharpe"]), reverse=True)
    return rows[: int(max(1, limit))]


def _collect_artifact_paths(best_results: list[dict[str, Any]]) -> list[Path]:
    out: set[Path] = set()

    for rel in PHASE23_CODE_FILES:
        rp = _repo_rel(rel)
        if rp is not None and (PROJECT_ROOT / rp).exists():
            out.add(rp)

    for rel in PRIMARY_ARTIFACTS:
        rp = _repo_rel(rel)
        if rp is not None and (PROJECT_ROOT / rp).is_file():
            out.add(rp)

    for rel in PRIMARY_ARTIFACT_DIRS:
        rp = _repo_rel(rel)
        if rp is None:
            continue
        abs_dir = PROJECT_ROOT / rp
        if not abs_dir.is_dir():
            continue
        for f in abs_dir.rglob("*"):
            if f.is_file():
                maybe_rel = _repo_rel(f)
                if maybe_rel is not None:
                    out.add(maybe_rel)

    # Include summary-linked artifacts for the ranked top results.
    for row in best_results:
        summary_rel = _repo_rel(row["path"])
        if summary_rel is None:
            continue
        summary_abs = PROJECT_ROOT / summary_rel
        if summary_abs.is_file():
            out.add(summary_rel)
        doc = _load_json(summary_abs)
        if not doc:
            continue
        artifacts = doc.get("artifacts")
        if not isinstance(artifacts, dict):
            continue
        for _, p in artifacts.items():
            if not isinstance(p, str):
                continue
            rel = _repo_rel(p)
            if rel is not None and (PROJECT_ROOT / rel).is_file():
                out.add(rel)

    return sorted(out)


def build_freeze_snapshot(*, top_results_limit: int = 10) -> Path:
    now = datetime.now(timezone.utc)
    snapshot_id = f"phase23_freeze_{now.strftime('%Y%m%d_%H%M%SZ')}"
    snapshot_dir = FREEZE_ROOT / snapshot_id
    payload_dir = snapshot_dir / "files"
    manifest_path = snapshot_dir / "manifest.json"

    best_results = _collect_best_summaries(limit=top_results_limit)
    artifacts = _collect_artifact_paths(best_results=best_results)

    entries: list[dict[str, Any]] = []
    for rel in artifacts:
        src = PROJECT_ROOT / rel
        if not src.is_file():
            continue
        dst = payload_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        entries.append(
            {
                "repo_rel": str(rel.as_posix()),
                "snapshot_rel": str((Path("files") / rel).as_posix()),
                "size_bytes": int(dst.stat().st_size),
                "sha256": _sha256_file(dst),
            }
        )

    manifest = {
        "snapshot_id": snapshot_id,
        "created_at_utc": now.isoformat(),
        "project_root": str(PROJECT_ROOT),
        "phase": "phase23_wrap",
        "code_files": list(PHASE23_CODE_FILES),
        "best_results": best_results,
        "entries": entries,
    }
    _atomic_write_json(manifest, manifest_path)

    pointer = {
        "snapshot_id": snapshot_id,
        "created_at_utc": now.isoformat(),
        "manifest_path": str(manifest_path),
        "entry_count": int(len(entries)),
        "best_result_path": best_results[0]["path"] if best_results else None,
    }
    _atomic_write_json(pointer, LATEST_POINTER)

    print(f"[FREEZE] Snapshot created: {snapshot_dir}")
    print(f"[FREEZE] Manifest: {manifest_path}")
    print(f"[FREEZE] Latest pointer: {LATEST_POINTER}")
    print(f"[FREEZE] Entries captured: {len(entries)}")
    if best_results:
        top = best_results[0]
        print(
            "[FREEZE] Top result preserved: "
            f"{top['path']} (cagr={top['cagr']:.6f}, sharpe={top['sharpe']:.6f}, max_dd={top['max_dd']:.6f})"
        )
    return snapshot_dir


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Create a revertible Phase 23 freeze snapshot.")
    p.add_argument("--top-results-limit", type=int, default=10)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    build_freeze_snapshot(top_results_limit=int(args.top_results_limit))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
