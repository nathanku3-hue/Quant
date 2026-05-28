from __future__ import annotations

import html
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Iterable

import pandas as pd
from pandas.io.formats.style import Styler


RENDERED_ALLOWED_EXACT_LABELS = frozenset(
    {
        "Current Weight",
        "Current allocation",
        "Current allocation snapshot",
        "ENTER event",
        "ENTER/EXIT Events",
        "Entry/Exit Events",
        "EXIT event",
        "Historical Replay Lifecycle Events",
        "Portfolio & Allocation",
        "Replay Allocation",
        "Replay Decision-Code Audit Log",
        "Replay Weight",
        "Replay allocation",
        "Replay allocation snapshot",
        "Research Bucket",
        "Research Optimizer - Simulation Only",
        "Research Portfolio / Replay Allocation",
        "Rows Passing Research Filter",
        "Simulation Weight Table",
        "Strategy Research Replay",
        "Target Weight",
        "Target weight",
    }
)

RENDERED_FORBIDDEN_PHRASES = (
    "Strong Buy",
    "BUY AGGRESSIVE",
    "ENTER: BUY",
    "ENTER: STRONG BUY",
    "Latest Buys/Sells",
    "Buy/Sell Decision Log",
    "Entry/Exit Strategy",
    "Action Status",
    "Estimated Shares",
    "EXECUTE IF",
    "Qualifying Tickers",
    "Max Alpha",
    "Generate Option Yield",
    "Action Report",
    "Portfolio Optimizer",
    "Buy Zone",
    "investment recommendation",
    "recommendation",
    "trade alert",
    "broker order",
    "order action",
    "options trade",
    "option yield",
    "submit_order",
    "broker_call",
    "broker_action",
    "order_action",
    "buy_alert",
    "sell_alert",
    "entry_alert",
    "exit_alert",
    "rebalance_alert",
    "ticker_action_alert",
)

RENDERED_FORBIDDEN_EXACT_LABELS = frozenset(
    {
        "Alpha Score",
        "BUY",
        "Candidate Score",
        "Entry_Price",
        "Factor Score",
        "Leverage",
        "Rank",
        "Ranking",
        "Rating",
        "Score",
        "Signal Score",
        "SELL",
        "Stop_Loss",
        "Target_Price",
        "broker_action",
        "buy_sell_signal",
        "buying_range",
        "price_target",
    }
)

RENDERED_ALLOWED_VARIANT_DANGEROUS_TERMS = (
    "action panel",
    "action status",
    "recommendation",
    "broker",
    "order",
    "alert",
    "submit",
    "buy",
    "sell",
    "rank",
    "ranking",
    "score",
    "scoring",
)

_TEXT_COLLECTION_NAMES = (
    "title",
    "header",
    "subheader",
    "markdown",
    "caption",
    "text",
    "info",
    "warning",
    "error",
    "success",
    "metric",
    "button",
    "button_group",
    "checkbox",
    "toggle",
    "radio",
    "selectbox",
    "multiselect",
    "slider",
    "select_slider",
    "number_input",
    "text_input",
    "text_area",
    "date_input",
    "time_input",
    "tabs",
    "expander",
    "status",
)

_TABLE_COLLECTION_NAMES = ("dataframe", "table")


@dataclass(frozen=True)
class RenderedText:
    source: str
    text: str


@dataclass(frozen=True)
class RenderedGovernanceFinding:
    source: str
    text: str
    pattern: str


def _normalize_rendered_text(value: Any) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[`*_#>~]+", " ", text)
    text = "".join(
        " " if unicodedata.category(char) in {"So", "Sk"} else char
        for char in text
    )
    return re.sub(r"\s+", " ", text).strip()


def _phrase_regex(phrase: str) -> re.Pattern[str]:
    normalized = _normalize_rendered_text(phrase)
    escaped = re.escape(normalized).replace(r"\ ", r"\s+")
    return re.compile(rf"(?<![A-Za-z0-9_]){escaped}(?![A-Za-z0-9_])", re.IGNORECASE)


_FORBIDDEN_PHRASE_PATTERNS = tuple(
    (phrase, _phrase_regex(phrase)) for phrase in RENDERED_FORBIDDEN_PHRASES
)
_FORBIDDEN_EXACT_LABELS_NORMALIZED = {
    _normalize_rendered_text(label).casefold(): label
    for label in RENDERED_FORBIDDEN_EXACT_LABELS
}
_ALLOWED_EXACT_LABELS_NORMALIZED = {
    _normalize_rendered_text(label).casefold(): label
    for label in RENDERED_ALLOWED_EXACT_LABELS
}
_ALLOWED_EXACT_LABEL_PATTERNS = tuple(
    (label, _phrase_regex(label)) for label in RENDERED_ALLOWED_EXACT_LABELS
)
_ALLOWED_VARIANT_DANGEROUS_TERM_PATTERNS = tuple(
    (term, _phrase_regex(term)) for term in RENDERED_ALLOWED_VARIANT_DANGEROUS_TERMS
)


def _iter_collection(app: Any, name: str) -> Iterable[Any]:
    try:
        collection = getattr(app, name)
    except Exception:
        return ()
    try:
        return tuple(collection)
    except TypeError:
        return ()


def _iter_tree_nodes(node: Any, *, seen: set[int]) -> Iterable[Any]:
    node_id = id(node)
    if node_id in seen:
        return
    seen.add(node_id)
    yield node

    children = getattr(node, "children", None)
    if isinstance(children, dict):
        child_iterable = children.values()
    elif children is None:
        child_iterable = ()
    else:
        child_iterable = children

    for child in child_iterable:
        if not hasattr(child, "proto") and not hasattr(child, "children"):
            continue
        yield from _iter_tree_nodes(child, seen=seen)


def _add_text(items: list[RenderedText], source: str, value: Any) -> None:
    if isinstance(value, (pd.DataFrame, pd.Series, Styler)):
        return
    text = _normalize_rendered_text(value)
    if text:
        items.append(RenderedText(source=source, text=text))


def _collect_element_text(items: list[RenderedText], source: str, element: Any) -> None:
    for attr in ("label", "value", "body", "text"):
        try:
            value = getattr(element, attr)
        except Exception:
            continue
        _add_text(items, f"{source}.{attr}", value)

    proto = getattr(element, "proto", None)
    if proto is None:
        return
    for attr in ("label", "body", "value", "text", "caption", "help"):
        try:
            value = getattr(proto, attr)
        except Exception:
            continue
        _add_text(items, f"{source}.proto.{attr}", value)


def _as_dataframe(value: Any) -> pd.DataFrame | None:
    if isinstance(value, Styler):
        value = value.data
    if isinstance(value, pd.Series):
        return value.to_frame()
    if isinstance(value, pd.DataFrame):
        return value
    return None


def _collect_table_text(items: list[RenderedText], source: str, value: Any) -> None:
    frame = _as_dataframe(value)
    if frame is None:
        return

    for column in frame.columns:
        _add_text(items, f"{source}.column", column)
    for cell in frame.astype(str).to_numpy().ravel():
        _add_text(items, f"{source}.cell", cell)


def collect_rendered_text(app: Any) -> list[RenderedText]:
    """Collect governance-relevant text visible through Streamlit AppTest."""
    items: list[RenderedText] = []

    for collection_name in _TEXT_COLLECTION_NAMES:
        for index, element in enumerate(_iter_collection(app, collection_name)):
            _collect_element_text(items, f"{collection_name}[{index}]", element)

    for collection_name in _TABLE_COLLECTION_NAMES:
        for index, element in enumerate(_iter_collection(app, collection_name)):
            _collect_element_text(items, f"{collection_name}[{index}]", element)
            if hasattr(element, "value"):
                _collect_table_text(items, f"{collection_name}[{index}]", element.value)

    for block_name in ("main", "sidebar"):
        block = getattr(app, block_name, None)
        if block is None:
            continue
        for node in _iter_tree_nodes(block, seen=set()):
            element_type = getattr(node, "type", type(node).__name__)
            _collect_element_text(items, f"{block_name}.{element_type}", node)

    deduped: list[RenderedText] = []
    seen_pairs: set[tuple[str, str]] = set()
    for item in items:
        key = (item.source, item.text)
        if key in seen_pairs:
            continue
        seen_pairs.add(key)
        deduped.append(item)
    return deduped


def scan_rendered_governance(app: Any) -> list[RenderedGovernanceFinding]:
    findings: list[RenderedGovernanceFinding] = []
    for item in collect_rendered_text(app):
        normalized = _normalize_rendered_text(item.text)
        if not normalized:
            continue
        folded = normalized.casefold()
        if folded in _ALLOWED_EXACT_LABELS_NORMALIZED:
            continue
        variant_finding = _scan_allowed_label_variant(item, normalized)
        if variant_finding is not None:
            findings.append(variant_finding)
            continue
        exact_pattern = _FORBIDDEN_EXACT_LABELS_NORMALIZED.get(folded)
        if exact_pattern is not None:
            findings.append(
                RenderedGovernanceFinding(
                    source=item.source,
                    text=item.text,
                    pattern=exact_pattern,
                )
            )
            continue
        for phrase, pattern in _FORBIDDEN_PHRASE_PATTERNS:
            if pattern.search(normalized):
                findings.append(
                    RenderedGovernanceFinding(
                        source=item.source,
                        text=item.text,
                        pattern=phrase,
                    )
                )
    return findings


def _scan_allowed_label_variant(
    item: RenderedText,
    normalized: str,
) -> RenderedGovernanceFinding | None:
    for allowed_label, allowed_pattern in _ALLOWED_EXACT_LABEL_PATTERNS:
        match = allowed_pattern.search(normalized)
        if match is None:
            continue

        remainder = f"{normalized[:match.start()]} {normalized[match.end():]}".strip()
        if not remainder:
            continue

        for term, term_pattern in _ALLOWED_VARIANT_DANGEROUS_TERM_PATTERNS:
            if term_pattern.search(remainder):
                return RenderedGovernanceFinding(
                    source=item.source,
                    text=item.text,
                    pattern=f"{allowed_label} variant with {term}",
                )
    return None


def assert_rendered_governance_safe(app: Any) -> None:
    findings = scan_rendered_governance(app)
    if not findings:
        return

    detail = "\n".join(
        f"- {finding.source}: matched {finding.pattern!r} in {finding.text!r}"
        for finding in findings
    )
    raise AssertionError(f"Rendered governance scan found forbidden labels:\n{detail}")
