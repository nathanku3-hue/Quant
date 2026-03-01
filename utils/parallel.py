from __future__ import annotations

import logging
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from typing import Any, Callable, Iterable

try:
    from joblib import Parallel, delayed

    _HAS_JOBLIB = True
except Exception:  # pragma: no cover - optional dependency
    Parallel = None
    delayed = None
    _HAS_JOBLIB = False

logger = logging.getLogger(__name__)


def _resolve_worker_count(n_jobs: int, total_tasks: int, backend: str) -> int:
    if total_tasks <= 0:
        return 0
    if n_jobs == -1 or n_jobs == 0:
        cpu = max(1, multiprocessing.cpu_count())
        if backend == "threading":
            n_jobs = min(32, cpu * 2)
        else:
            n_jobs = cpu
    return max(1, min(int(n_jobs), int(total_tasks)))


def _invoke(func: Callable[..., Any], task: Any) -> Any:
    # Tuple tasks are treated as positional args for convenience.
    if isinstance(task, tuple):
        return func(*task)
    return func(task)


def parallel_execute(
    func: Callable[..., Any],
    tasks: Iterable[Any],
    n_jobs: int = -1,
    desc: str = "Processing",
    backend: str = "threading",
    fail_fast: bool = True,
    prefer_joblib: bool = True,
) -> list[Any]:
    """
    Execute tasks in parallel with stable output ordering.

    Args:
        func: Callable applied to each task.
        tasks: Iterable of task payloads; tuple payloads are unpacked as *args.
        n_jobs: Worker count (-1 or 0 means auto).
        desc: Human-readable label for logs.
        backend: "threading" or "multiprocessing".
        fail_fast: Raise immediately on task failures when True.
        prefer_joblib: Use joblib backend when available.
    """
    task_list = list(tasks)
    if not task_list:
        return []

    normalized_backend = str(backend or "threading").strip().lower()
    if normalized_backend not in {"threading", "multiprocessing"}:
        raise ValueError(f"Unsupported backend: {backend}")
    worker_count = _resolve_worker_count(n_jobs=n_jobs, total_tasks=len(task_list), backend=normalized_backend)

    if worker_count <= 1:
        logger.info("[Sequential] %s (%d tasks)", desc, len(task_list))
        results: list[Any] = []
        for task in task_list:
            try:
                results.append(_invoke(func, task))
            except Exception:
                logger.exception("Task failed during %s", desc)
                if fail_fast:
                    raise
                results.append(None)
        return results

    if prefer_joblib and _HAS_JOBLIB:
        logger.info("[Parallel/joblib:%s] %s (%d tasks)", worker_count, desc, len(task_list))
        joblib_backend = "threading" if normalized_backend == "threading" else "loky"
        try:
            return Parallel(n_jobs=worker_count, backend=joblib_backend)(
                delayed(_invoke)(func, task) for task in task_list
            )
        except Exception:
            logger.exception("Parallel execution failed for %s", desc)
            if fail_fast:
                raise
            return _run_futures(
                func=func,
                task_list=task_list,
                worker_count=worker_count,
                backend=normalized_backend,
                desc=desc,
                fail_fast=False,
            )

    logger.info("[Parallel/%s:%s] %s (%d tasks)", normalized_backend, worker_count, desc, len(task_list))
    return _run_futures(
        func=func,
        task_list=task_list,
        worker_count=worker_count,
        backend=normalized_backend,
        desc=desc,
        fail_fast=fail_fast,
    )


def _run_futures(
    func: Callable[..., Any],
    task_list: list[Any],
    worker_count: int,
    backend: str,
    desc: str,
    fail_fast: bool,
) -> list[Any]:
    executor_cls = ThreadPoolExecutor if backend == "threading" else ProcessPoolExecutor
    results: list[Any] = [None] * len(task_list)
    with executor_cls(max_workers=worker_count) as executor:
        future_to_index = {
            executor.submit(_invoke, func, task): idx for idx, task in enumerate(task_list)
        }
        for future in as_completed(future_to_index):
            idx = future_to_index[future]
            try:
                results[idx] = future.result()
            except Exception:
                logger.exception("Task %d failed during %s", idx, desc)
                if fail_fast:
                    raise
                results[idx] = None
    return results

