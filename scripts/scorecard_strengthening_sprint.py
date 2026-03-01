from __future__ import annotations

"""
Deprecated compatibility entrypoint.

Phase 19.6 renamed this runner to `scorecard_diagnostics_sprint.py`.
"""

from scripts.scorecard_diagnostics_sprint import main


if __name__ == "__main__":
    raise SystemExit(main())
