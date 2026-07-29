"""GV Portfolio V0 product tests without shadowing the product package."""

from pathlib import Path

_TEST_PACKAGE = Path(__file__).resolve().parent
_PRODUCT_PACKAGE = Path(__file__).resolve().parents[2] / "gv_portfolio_v0"
__path__ = [str(_PRODUCT_PACKAGE), str(_TEST_PACKAGE)]
