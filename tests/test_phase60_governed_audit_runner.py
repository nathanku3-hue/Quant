from __future__ import annotations

import pandas as pd
import pytest

from scripts import phase60_governed_audit_runner as mod


def test_validate_config_rejects_end_date_beyond_approved_max():
    cfg = mod.AuditConfig(
        start_date=pd.Timestamp("2023-01-01"),
        end_date=pd.Timestamp("2025-01-01"),
        cost_bps=5.0,
        sensitivity_bps=10.0,
    )
    with pytest.raises(ValueError, match="2024-12-31"):
        mod.validate_config(cfg)


def test_enforce_kill_switches_blocks_allocator_overlay():
    with pytest.raises(RuntimeError, match="KS-05"):
        mod._enforce_kill_switches(
            preflight={"passed": True},
            cube_summary={"phase50_reference_only_excluded": True},
            weights=pd.DataFrame({1: [1.0]}),
            allocator_overlay_applied=True,
            core_included=False,
        )


def test_enforce_kill_switches_blocks_phase50_fill():
    with pytest.raises(RuntimeError, match="KS-01"):
        mod._enforce_kill_switches(
            preflight={"passed": True},
            cube_summary={"phase50_reference_only_excluded": False},
            weights=pd.DataFrame({1: [1.0]}),
            allocator_overlay_applied=False,
            core_included=False,
        )


def test_build_daily_evidence_includes_turnover_and_exposure():
    idx = pd.DatetimeIndex(pd.to_datetime(["2023-01-03", "2023-01-04"]), name="date")
    weights = pd.DataFrame({1: [1.0, 0.5], 2: [0.0, 0.5]}, index=idx)
    sim_5 = pd.DataFrame({"net_ret": [0.01, -0.02]}, index=idx)
    sim_10 = pd.DataFrame({"net_ret": [0.009, -0.021]}, index=idx)

    out = mod._build_daily_evidence(weights, sim_5, sim_10)

    assert list(out.columns) == [
        "date",
        "book_id",
        "gross_exposure",
        "turnover_total",
        "n_active_permnos",
        "net_ret_5bps",
        "net_ret_10bps",
    ]
    assert float(out.loc[0, "gross_exposure"]) == pytest.approx(1.0)
    assert float(out.loc[1, "turnover_total"]) == pytest.approx(1.0)
