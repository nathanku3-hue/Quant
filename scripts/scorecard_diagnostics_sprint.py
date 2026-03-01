from __future__ import annotations

"""
Deprecated compatibility entrypoint.

Phase 19.7 renamed this runner to `regime_fidelity_sprint.py`.
"""

from scripts.regime_fidelity_sprint import main


if __name__ == "__main__":
    raise SystemExit(main())
