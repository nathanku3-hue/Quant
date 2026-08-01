"""Launch the 25-security scenario through the shared operated-portfolio app."""

from __future__ import annotations

import os

from gv_portfolio_v0.operated_scenarios import PORTFOLIO_25_SCENARIO_ID
from launch_operated_portfolio import main


if __name__ == "__main__":
    os.environ["GV_OPERATED_SCENARIO_ID"] = PORTFOLIO_25_SCENARIO_ID
    raise SystemExit(main())
