from __future__ import annotations

import pytest

from utils.parallel import parallel_execute


def test_parallel_execute_preserves_order_threading():
    def square(x: int) -> int:
        return x * x

    out = parallel_execute(
        func=square,
        tasks=[3, 1, 2],
        n_jobs=4,
        backend="threading",
        fail_fast=True,
    )
    assert out == [9, 1, 4]


def test_parallel_execute_unpacks_tuple_tasks():
    def add(a: int, b: int) -> int:
        return a + b

    out = parallel_execute(
        func=add,
        tasks=[(1, 2), (3, 4), (5, 6)],
        n_jobs=2,
        backend="threading",
        fail_fast=True,
    )
    assert out == [3, 7, 11]


def test_parallel_execute_fail_fast_false_returns_none_for_failed_tasks():
    def maybe_fail(x: int) -> int:
        if x == 2:
            raise RuntimeError("boom")
        return x

    out = parallel_execute(
        func=maybe_fail,
        tasks=[1, 2, 3],
        n_jobs=3,
        backend="threading",
        fail_fast=False,
    )
    assert out == [1, None, 3]


def test_parallel_execute_rejects_unknown_backend():
    with pytest.raises(ValueError):
        parallel_execute(lambda x: x, tasks=[1], backend="gpu")

