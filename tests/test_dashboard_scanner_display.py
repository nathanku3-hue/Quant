from __future__ import annotations

from pathlib import Path

import pandas as pd

from strategies.scanner import enrich_scan_frame
from views.scanner_display import ACTION_SHAPED_SCANNER_DISPLAY_COLUMNS
from views.scanner_display import build_scanner_research_display_frame
from views.scanner_display import style_scanner_research_display_frame


DASHBOARD = Path("dashboard.py")


def _real_enriched_scan_frame(sample_ticker_map: dict[int, str]) -> pd.DataFrame:
    df_scan = pd.DataFrame(
        [
            {"Ticker": sample_ticker_map[101], "Score": 100.0, "Action": "BUY"},
            {"Ticker": "CCC", "Score": 92.0, "Action": "BUY"},
            {"Ticker": sample_ticker_map[202], "Score": 80.0, "Action": "KILL"},
        ]
    )
    technicals = {
        "AAA": {"price": 97.0, "ema21": 95.0, "sma50": 90.0, "sma200": 80.0, "atr": 2.0, "convexity": 1.0},
        "CCC": {"price": 40.0, "ema21": 39.0, "sma50": 38.0, "sma200": 35.0, "atr": 1.0, "convexity": 1.1},
        "BBB": {"price": 50.0, "ema21": 48.0, "sma50": 47.0, "sma200": 45.0, "atr": 3.0, "convexity": 1.2},
    }
    proxy_db = {
        "Compute": {"type": "Sector Only", "conf": "p=82%", "name": "TSMC", "span": "YoY", "key": "tsmc"},
        "Software": {"type": "None", "conf": "NA", "name": "[NO PROXY]", "span": "", "key": None},
    }

    return enrich_scan_frame(
        df_scan,
        technicals=technicals,
        sector_map={"AAA": "Compute", "BBB": "Software", "CCC": "Compute"},
        proxy_db=proxy_db,
        proxy_data={"tsmc": {"val": 0.08, "span": "YoY"}},
        macro={"score": 85},
    )


def test_scanner_display_quarantines_action_shaped_columns(sample_ticker_map: dict[int, str]) -> None:
    enriched = _real_enriched_scan_frame(sample_ticker_map)
    assert ACTION_SHAPED_SCANNER_DISPLAY_COLUMNS.issubset(enriched.columns)

    display = build_scanner_research_display_frame(enriched, time_label="just now")

    assert ACTION_SHAPED_SCANNER_DISPLAY_COLUMNS.isdisjoint(display.columns)
    assert list(display["Research_State"]) == [
        "Setup evidence review",
        "Evidence gap review",
        "Risk review only",
    ]
    assert "Support_Reference" in display.columns
    assert "Research_Risk_Context" in display.columns

    display_text = " ".join(display.astype(str).to_numpy().ravel()).upper()
    for token in ("ENTER:", "STRONG BUY", "BUY", "HOLD", "EXIT", "STOP", "TARGET", "LEAPS", "SCORE"):
        assert token not in display_text


def test_scanner_display_style_path_uses_research_labels(sample_ticker_map: dict[int, str]) -> None:
    display = build_scanner_research_display_frame(
        _real_enriched_scan_frame(sample_ticker_map),
        time_label="just now",
    )

    html = style_scanner_research_display_frame(display).to_html()

    assert "Research_State" in html
    assert "Setup evidence review" in html
    assert "Risk review only" in html
    for token in ("ENTER:", "STRONG BUY", "Target_Price", "Stop_Loss", "Entry_Price", "Leverage"):
        assert token not in html


def test_dashboard_dataframe_path_uses_scanner_display_quarantine() -> None:
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _render_opportunities_page()")
    end = source.index("# ==========================================\n# TAB 2", start)
    section = source[start:end]

    assert "build_scanner_research_display_frame(df_scan, time_label=time_str)" in section
    assert "style_scanner_research_display_frame(view_df)" in section
    assert "st.dataframe(" in section
    assert source.count("build_scanner_research_display_frame(") == 2
    assert "SortWeight" not in source
    assert "Prioritize Actionable Ratings" not in source
    assert 'qual_cols = ["Ticker", "Score", "Rating", "Current_Price"]' not in source

    for column in ACTION_SHAPED_SCANNER_DISPLAY_COLUMNS:
        assert f"'{column}'" not in section
        assert f'"{column}"' not in section
