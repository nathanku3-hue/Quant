from __future__ import annotations

import re
from pathlib import Path


def test_dashboard_passes_drift_monitor_dependencies() -> None:
    source = Path("dashboard.py").read_text(encoding="utf-8")
    pattern = re.compile(r"render_drift_monitor_view\((?P<body>.*?)\n\s*\)", re.DOTALL)
    match = pattern.search(source)

    assert match is not None
    body = match.group("body")
    assert "alert_manager=drift_alert_manager" in body
    assert "drift_detector=drift_detector" in body
    assert "baseline_weights=baseline_weights" in body
    assert "baseline_metadata=baseline_metadata" in body
    assert "live_weights=live_weights" in body
    assert "macro=" in body
