from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen

import numpy as np
import pandas as pd
from core.security_policy import assert_egress_url_allowed
from core.security_policy import redact_url_secrets

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from scripts.day5_ablation_report import _resolve_path  # noqa: E402

LOG = logging.getLogger("ingest_fmp_estimates")
# FMP deprecated all v3 endpoints on 2025-08-31. New stable API uses /stable/ base.
FMP_BASE_URL = "https://financialmodelingprep.com/stable/analyst-estimates"
FMP_PERIOD = "annual"  # free tier: annual only; upgrade for 'quarter'
DEFAULT_SECTOR_MAP_PATH = PROJECT_ROOT / "data" / "static" / "sector_map.parquet"
DEFAULT_RAW_OUTPUT = PROJECT_ROOT / "data" / "raw" / "fmp_estimates_raw.parquet"
DEFAULT_PROCESSED_OUTPUT = PROJECT_ROOT / "data" / "processed" / "estimates.parquet"
DEFAULT_CACHE_DIR = PROJECT_ROOT / "data" / "raw" / "fmp_cache"
DEFAULT_TICKERS = ("MU", "AMAT")
DEFAULT_MAX_TICKERS = 500
PROCESSED_SCHEMA = ["permno", "ticker", "published_at", "horizon", "metric", "value"]
DEDUP_KEYS = ["permno", "ticker", "published_at", "horizon", "metric"]


class RateLimitExhausted(RuntimeError):
    """Raised when FMP indicates request limit exhaustion (HTTP 429 / rate-limit message)."""


def _configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, str(level).upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def _atomic_parquet_write(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".{os.getpid()}.{int(time.time() * 1000)}.tmp")
    tries = 8
    try:
        df.to_parquet(tmp, index=False)
        for i in range(tries):
            try:
                os.replace(tmp, path)
                return
            except PermissionError:
                if i >= tries - 1:
                    raise
                time.sleep(0.15 * (i + 1))
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


def _clean_ticker(values: pd.Series) -> pd.Series:
    out = values.astype("string").str.strip().str.upper()
    out = out.mask(out.isna() | (out == "") | out.isin({"NAN", "NONE", "<NA>"}), pd.NA)
    return out


def _to_datetime_series(values: pd.Series) -> pd.Series:
    return pd.to_datetime(values, errors="coerce", utc=True)


def _coalesce_series(frame: pd.DataFrame, columns: list[str], *, as_datetime: bool = False) -> pd.Series:
    out = pd.Series(pd.NA, index=frame.index, dtype="object")
    for col in columns:
        if col not in frame.columns:
            continue
        candidate = frame[col]
        if as_datetime:
            candidate = _to_datetime_series(candidate)
        out = pd.Series(out).where(pd.Series(out).notna(), candidate)
    if as_datetime:
        out = pd.to_datetime(out, errors="coerce", utc=True)
    return pd.Series(out, index=frame.index)


def _load_ticker_permno_crosswalk(sector_map_path: Path) -> pd.DataFrame:
    if not sector_map_path.exists():
        raise FileNotFoundError(f"Missing sector map crosswalk at: {sector_map_path}")
    context = pd.read_parquet(sector_map_path)
    if context.empty:
        raise ValueError(f"Sector map is empty: {sector_map_path}")

    for col in ("ticker", "permno", "updated_at"):
        if col not in context.columns:
            context[col] = pd.NA
    work = context.copy()
    work["ticker_u"] = _clean_ticker(work["ticker"])
    work["permno"] = pd.to_numeric(work["permno"], errors="coerce")
    work["updated_at"] = pd.to_datetime(work["updated_at"], errors="coerce", utc=True)
    work = work.dropna(subset=["ticker_u", "permno"])

    multi_map = (
        work.groupby("ticker_u", sort=False)["permno"]
        .nunique(dropna=True)
        .reset_index(name="permno_n")
    )
    conflict = multi_map.loc[multi_map["permno_n"] > 1, "ticker_u"].astype(str).tolist()
    if conflict:
        LOG.warning(
            "Crosswalk has %d ticker(s) mapped to multiple permnos; using latest updated_at row per ticker. sample=%s",
            int(len(conflict)),
            ",".join(conflict[:10]),
        )

    work = work.sort_values(["updated_at", "permno", "ticker_u"], ascending=[False, True, True], na_position="last")
    work = work.drop_duplicates(subset=["ticker_u"], keep="first")
    out = work[["ticker_u", "permno"]].copy()
    out["permno"] = out["permno"].round().astype("int64")
    return out.reset_index(drop=True)


def _parse_tickers(arg: str | None) -> list[str]:
    if not arg:
        return []
    out = [x.strip().upper() for x in str(arg).split(",")]
    out = [x for x in out if x]
    return out


def _load_tickers_from_file(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"Ticker file not found: {path}")

    suffix = path.suffix.lower()
    if suffix in {".txt", ".lst"}:
        tickers = [x.strip().upper() for x in path.read_text(encoding="utf-8").splitlines()]
        return [x for x in tickers if x]
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        out: list[str] = []
        if isinstance(payload, list):
            out = [str(x).strip().upper() for x in payload]
        elif isinstance(payload, dict):
            for v in payload.values():
                if isinstance(v, list):
                    out.extend([str(x).strip().upper() for x in v])
        return [x for x in out if x]
    if suffix in {".csv"}:
        df = pd.read_csv(path)
        if "ticker" in df.columns:
            values = df["ticker"]
        else:
            values = df.iloc[:, 0] if not df.empty else pd.Series(dtype="object")
        return [x for x in _clean_ticker(values).dropna().astype(str).tolist() if x]
    if suffix in {".parquet"}:
        df = pd.read_parquet(path)
        if "ticker" in df.columns:
            values = df["ticker"]
        elif "ticker_u" in df.columns:
            values = df["ticker_u"]
        else:
            values = pd.Series(dtype="object")
        return [x for x in _clean_ticker(values).dropna().astype(str).tolist() if x]

    raise ValueError(f"Unsupported ticker file format: {path.suffix}")


def _resolve_target_tickers(
    tickers_arg: str | None,
    tickers_file: Path | None,
    max_tickers: int,
) -> list[str]:
    ordered: list[str] = []
    ordered.extend(_parse_tickers(tickers_arg))
    if tickers_file is not None:
        ordered.extend(_load_tickers_from_file(tickers_file))
    if not ordered:
        ordered = [x.upper() for x in DEFAULT_TICKERS]

    seen: set[str] = set()
    dedup: list[str] = []
    for t in ordered:
        if t not in seen:
            seen.add(t)
            dedup.append(t)
    return dedup[: int(max(1, max_tickers))]


def _cache_path(cache_dir: Path, ticker: str) -> Path:
    return cache_dir / f"{ticker.upper()}.json"


def _load_cached_rows(cache_file: Path, ticker: str) -> list[dict[str, Any]]:
    if not cache_file.exists():
        return []
    try:
        payload = json.loads(cache_file.read_text(encoding="utf-8"))
    except Exception as exc:
        LOG.warning("Failed reading cache for %s (%s): %s", ticker, str(cache_file), str(exc))
        return []

    rows: list[dict[str, Any]]
    if isinstance(payload, dict):
        # Support both old cache format {"historical": [...]} and new flat {"rows": [...]}
        hist = payload.get("rows") or payload.get("historical")
        rows = hist if isinstance(hist, list) else []
    elif isinstance(payload, list):
        rows = payload
    else:
        rows = []

    out: list[dict[str, Any]] = []
    changed = False
    for row in rows:
        if not isinstance(row, dict):
            continue
        rec = dict(row)
        # Ensure compat aliases present on cache load too
        rec.setdefault("estimatedRevenueAvg", rec.get("revenueAvg"))
        rec.setdefault("estimatedEpsAvg", rec.get("epsAvg"))
        rec["ticker"] = ticker.upper()
        for key in ("api_url", "url", "request_url"):
            if key in rec:
                clean_url = redact_url_secrets(str(rec.get(key, "")))
                if clean_url != rec.get(key):
                    changed = True
                rec[key] = clean_url
        out.append(rec)
    if changed:
        try:
            _save_cache_rows(cache_file, out)
        except Exception as exc:
            LOG.warning("Failed to rewrite sanitized cache for %s (%s): %s", ticker, str(cache_file), str(exc))
    return out


def _save_cache_rows(cache_file: Path, rows: list[dict[str, Any]]) -> None:
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    sanitized_rows: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        rec = dict(row)
        for key in ("api_url", "url", "request_url"):
            if key in rec:
                rec[key] = redact_url_secrets(str(rec.get(key, "")))
        sanitized_rows.append(rec)
    payload = {"rows": sanitized_rows}  # new stable-API cache format (flat list under 'rows')
    tmp = cache_file.with_suffix(cache_file.suffix + f".{os.getpid()}.{int(time.time() * 1000)}.tmp")
    try:
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, cache_file)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


def _is_rate_limit_message(msg: str) -> bool:
    m = str(msg).strip().lower()
    return ("429" in m) or ("rate limit" in m) or ("too many request" in m) or ("limit reached" in m)


def _fetch_fmp_rows_once(ticker: str, api_key: str, timeout_sec: float) -> list[dict[str, Any]]:
    # New /stable/ endpoint: symbol is a query param, period=annual required for free tier.
    query = urlencode({"symbol": ticker, "period": FMP_PERIOD, "apikey": api_key})
    url = f"{FMP_BASE_URL}?{query}"
    assert_egress_url_allowed(url, context="ingest_fmp_estimates_fetch")
    with urlopen(url, timeout=float(timeout_sec)) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    # /stable/ returns a flat list; error responses are plain strings or dicts
    if isinstance(payload, dict):
        msg = str(payload.get("Error Message", payload.get("message", "")))
        if _is_rate_limit_message(msg):
            raise RateLimitExhausted(msg)
        raise ValueError(msg or str(payload))
    elif isinstance(payload, list):
        rows = payload
    elif isinstance(payload, str):
        msg = str(payload).strip()
        if _is_rate_limit_message(msg):
            raise RateLimitExhausted(msg)
        raise ValueError(msg or "Unexpected string payload from FMP API.")
    else:
        raise ValueError(f"Unexpected payload type from FMP API: {type(payload).__name__}")

    # Normalise field names: stable API uses 'revenueAvg'/'epsAvg' instead of
    # 'estimatedRevenueAvg'/'estimatedEpsAvg'. Add compat aliases so downstream
    # _build_processed_estimates still works without changes.
    fetched_at = pd.Timestamp.utcnow().isoformat()
    out: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        rec = dict(row)
        rec.setdefault("estimatedRevenueAvg", rec.get("revenueAvg"))
        rec.setdefault("estimatedEpsAvg", rec.get("epsAvg"))
        # 'symbol' field in response → normalise to 'ticker'
        rec["ticker"] = ticker.upper()
        clean_url = redact_url_secrets(url)
        rec["api_url"] = clean_url
        rec["request_url"] = clean_url
        rec["fetched_at_utc"] = fetched_at
        out.append(rec)
    return out


def _fetch_with_backoff(
    ticker: str,
    api_key: str,
    timeout_sec: float,
    max_retries_429: int,
    backoff_initial_sec: float,
) -> list[dict[str, Any]]:
    for attempt in range(int(max_retries_429) + 1):
        try:
            return _fetch_fmp_rows_once(ticker=ticker, api_key=api_key, timeout_sec=timeout_sec)
        except HTTPError as exc:
            if int(getattr(exc, "code", 0)) == 429:
                if attempt >= int(max_retries_429):
                    raise RateLimitExhausted(f"HTTP 429 for {ticker}") from exc
                wait_sec = min(float(backoff_initial_sec) * (2 ** attempt), 300.0)
                LOG.warning("HTTP 429 for %s. Backoff %.1fs (attempt %d/%d).", ticker, wait_sec, attempt + 1, max_retries_429)
                time.sleep(wait_sec)
                continue
            raise
        except RateLimitExhausted:
            if attempt >= int(max_retries_429):
                raise
            wait_sec = min(float(backoff_initial_sec) * (2 ** attempt), 300.0)
            LOG.warning("Rate limit for %s. Backoff %.1fs (attempt %d/%d).", ticker, wait_sec, attempt + 1, max_retries_429)
            time.sleep(wait_sec)
    raise RateLimitExhausted(f"Rate limit exhausted for {ticker}")


def _derive_period_fields(raw: pd.DataFrame) -> pd.DataFrame:
    work = raw.copy()
    work["ticker"] = _clean_ticker(work.get("ticker", pd.Series(index=work.index, dtype="object")))
    work["published_at"] = _coalesce_series(
        work,
        ["publishedDate", "published_at", "acceptedDate", "updatedAt", "fetched_at_utc", "date"],
        as_datetime=True,
    )
    work["period_label"] = (
        _coalesce_series(work, ["period", "fiscalPeriod", "calendarYear", "year"], as_datetime=False)
        .astype("string")
        .str.strip()
        .str.upper()
    )
    work["period_end"] = _coalesce_series(
        work,
        ["fiscalDateEnding", "fiscalDate", "fiscal_date_end", "estimatedDate"],
        as_datetime=True,
    )

    year_source = work["year"] if "year" in work.columns else pd.Series(np.nan, index=work.index, dtype=float)
    year_from_field = pd.to_numeric(year_source, errors="coerce")
    year_from_period = pd.to_numeric(work["period_label"].str.extract(r"(20\d{2})")[0], errors="coerce")
    year_from_pub = pd.to_numeric(work["published_at"].dt.year, errors="coerce")
    year = year_from_field.copy()
    year = year.where(year.notna(), year_from_period)
    year = year.where(year.notna(), year_from_pub)

    quarter_num = pd.to_numeric(work["period_label"].str.extract(r"Q([1-4])")[0], errors="coerce")
    period_type = np.where(
        quarter_num.notna(),
        "Q",
        np.where(work["period_label"].str.contains("FY|ANNUAL|YEAR", na=False), "FY", "UNK"),
    )
    work["period_type"] = pd.Series(period_type, index=work.index, dtype="string")

    quarter_guess = pd.Series(pd.NaT, index=work.index, dtype="datetime64[ns, UTC]")
    q_mask = quarter_num.notna() & year.notna()
    if bool(q_mask.any()):
        q_year = year.loc[q_mask].round().astype("int64")
        q_month = (quarter_num.loc[q_mask] * 3.0).round().astype("int64")
        q_dates = pd.to_datetime(
            {"year": q_year, "month": q_month, "day": pd.Series(1, index=q_year.index, dtype="int64")},
            errors="coerce",
            utc=True,
        ) + pd.offsets.MonthEnd(0)
        quarter_guess.loc[q_mask] = q_dates

    fy_guess = pd.Series(pd.NaT, index=work.index, dtype="datetime64[ns, UTC]")
    fy_mask = year.notna()
    if bool(fy_mask.any()):
        fy_year = year.loc[fy_mask].round().astype("int64")
        fy_dates = pd.to_datetime(
            {
                "year": fy_year,
                "month": pd.Series(12, index=fy_year.index, dtype="int64"),
                "day": pd.Series(31, index=fy_year.index, dtype="int64"),
            },
            errors="coerce",
            utc=True,
        )
        fy_guess.loc[fy_mask] = fy_dates

    work["period_end"] = pd.to_datetime(work["period_end"], errors="coerce", utc=True)
    work["period_end"] = work["period_end"].where(
        work["period_end"].notna(),
        pd.Series(np.where(work["period_type"] == "Q", quarter_guess, np.where(work["period_type"] == "FY", fy_guess, pd.NaT)), index=work.index),
    )
    return work


def _normalize_ntm_for_metric(group: pd.DataFrame, metric_col: str) -> float:
    metric = group.get(metric_col, pd.Series(np.nan, index=group.index, dtype=float))
    if not pd.api.types.is_numeric_dtype(metric):
        metric = pd.to_numeric(metric, errors="coerce")
    if metric.isna().all():
        return float("nan")

    cutoff = pd.NaT
    if "published_at" in group.columns:
        cutoff = pd.to_datetime(group["published_at"].iloc[0], errors="coerce", utc=True)
    future_mask = pd.Series(True, index=group.index, dtype=bool)
    if pd.notna(cutoff):
        period_end = pd.to_datetime(group["period_end"], errors="coerce", utc=True)
        future_mask = period_end > cutoff

    q_mask = group["period_type"].eq("Q")
    q = group.loc[q_mask, ["period_end"]].copy()
    q[metric_col] = metric[q_mask].to_numpy(dtype=float)
    q = q.loc[future_mask[q_mask].to_numpy(dtype=bool)]
    q = q.dropna(subset=["period_end", metric_col]).drop_duplicates(subset=["period_end"]).sort_values("period_end")

    if len(q) >= 4:
        return float(pd.to_numeric(q[metric_col], errors="coerce").head(4).sum())
    if len(q) >= 2:
        q_sum = float(pd.to_numeric(q[metric_col], errors="coerce").sum())
        return float(q_sum * (4.0 / float(len(q))))

    fy_mask = group["period_type"].eq("FY")
    fy = group.loc[fy_mask, ["period_end"]].copy()
    fy[metric_col] = metric[fy_mask].to_numpy(dtype=float)
    fy = fy.loc[future_mask[fy_mask].to_numpy(dtype=bool)]
    fy = fy.dropna(subset=[metric_col]).sort_values("period_end")
    if not fy.empty:
        return float(pd.to_numeric(fy.iloc[0][metric_col], errors="coerce"))

    if len(q) == 1:
        qv = float(pd.to_numeric(q.iloc[0][metric_col], errors="coerce"))
        return float(qv * 4.0)

    fallback = metric.dropna()
    return float(fallback.iloc[0]) if not fallback.empty else float("nan")


def _build_processed_estimates(raw: pd.DataFrame, crosswalk: pd.DataFrame) -> pd.DataFrame:
    if raw.empty:
        return pd.DataFrame(columns=PROCESSED_SCHEMA)

    work = _derive_period_fields(raw)
    work["estimatedRevenueAvg"] = pd.to_numeric(work.get("estimatedRevenueAvg"), errors="coerce")
    work["estimatedEpsAvg"] = pd.to_numeric(work.get("estimatedEpsAvg"), errors="coerce")
    work = work.dropna(subset=["ticker", "published_at"]).copy()
    if work.empty:
        return pd.DataFrame(columns=PROCESSED_SCHEMA)

    work["ticker_u"] = _clean_ticker(work["ticker"])
    mapped = work.merge(crosswalk, left_on="ticker_u", right_on="ticker_u", how="left")
    requested_tickers = sorted(set(work["ticker_u"].dropna().astype(str).tolist()))
    mapped_tickers = sorted(set(mapped.loc[pd.to_numeric(mapped.get("permno"), errors="coerce").notna(), "ticker_u"].astype(str).tolist()))
    unmapped_tickers = sorted(set(requested_tickers) - set(mapped_tickers))
    if unmapped_tickers:
        LOG.warning("Dropping %d ticker(s) with no permno mapping. sample=%s", int(len(unmapped_tickers)), ",".join(unmapped_tickers[:10]))

    mapped = mapped.dropna(subset=["permno"]).copy()
    if mapped.empty:
        return pd.DataFrame(columns=PROCESSED_SCHEMA)
    mapped["permno"] = pd.to_numeric(mapped["permno"], errors="coerce").round().astype("int64")
    mapped["ticker"] = mapped["ticker_u"].astype(str)

    rows: list[dict[str, Any]] = []
    grouped = mapped.groupby(["permno", "ticker", "published_at"], sort=True, dropna=False)
    for (permno, ticker, published_at), g in grouped:
        rev_ntm = _normalize_ntm_for_metric(g, "estimatedRevenueAvg")
        eps_ntm = _normalize_ntm_for_metric(g, "estimatedEpsAvg")
        if np.isfinite(rev_ntm):
            rows.append(
                {
                    "permno": int(permno),
                    "ticker": str(ticker),
                    "published_at": pd.Timestamp(published_at),
                    "horizon": "NTM",
                    "metric": "estimatedRevenueAvg",
                    "value": float(rev_ntm),
                }
            )
        if np.isfinite(eps_ntm):
            rows.append(
                {
                    "permno": int(permno),
                    "ticker": str(ticker),
                    "published_at": pd.Timestamp(published_at),
                    "horizon": "NTM",
                    "metric": "estimatedEpsAvg",
                    "value": float(eps_ntm),
                }
            )

    out = pd.DataFrame(rows, columns=PROCESSED_SCHEMA)
    if out.empty:
        return out
    out["published_at"] = pd.to_datetime(out["published_at"], errors="coerce", utc=True)
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    out = out.dropna(subset=["permno", "ticker", "published_at", "metric", "value"])
    out = out.sort_values(["permno", "ticker", "published_at", "metric"]).drop_duplicates(subset=DEDUP_KEYS, keep="last")
    return out.reset_index(drop=True)


def _merge_existing_processed(new_df: pd.DataFrame, processed_output: Path) -> pd.DataFrame:
    existing: pd.DataFrame | None = None
    if processed_output.exists():
        try:
            existing = pd.read_parquet(processed_output)
        except Exception as exc:
            LOG.warning("Failed reading existing processed parquet (%s): %s", str(processed_output), str(exc))
            existing = None
    if existing is None or existing.empty:
        return new_df

    for col in PROCESSED_SCHEMA:
        if col not in existing.columns:
            existing[col] = pd.NA
    existing = existing[PROCESSED_SCHEMA].copy()
    existing["_source_rank"] = 0
    new_work = new_df.copy()
    new_work["_source_rank"] = 1
    combined = pd.concat([existing, new_work], axis=0, ignore_index=True)
    combined["permno"] = pd.to_numeric(combined["permno"], errors="coerce")
    combined["ticker"] = _clean_ticker(combined["ticker"])
    combined["published_at"] = pd.to_datetime(combined["published_at"], errors="coerce", utc=True)
    combined["value"] = pd.to_numeric(combined["value"], errors="coerce")
    combined["horizon"] = combined["horizon"].astype("string").fillna("NTM")
    combined["metric"] = combined["metric"].astype("string")
    combined = combined.dropna(subset=["permno", "ticker", "published_at", "horizon", "metric", "value"])
    combined["permno"] = combined["permno"].round().astype("int64")
    combined = combined.sort_values(
        ["permno", "ticker", "published_at", "metric", "_source_rank"],
        kind="mergesort",
    ).drop_duplicates(subset=DEDUP_KEYS, keep="last")
    combined = combined.drop(columns=["_source_rank"], errors="ignore")
    return combined.reset_index(drop=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rate-aware FMP historical analyst-estimates ingestion with local cache and PIT schema transform."
    )
    parser.add_argument("--tickers", default=",".join(DEFAULT_TICKERS), help="Comma-separated ticker list (scoped universe).")
    parser.add_argument("--tickers-file", default=None, help="Optional path to txt/json/csv/parquet with ticker universe.")
    parser.add_argument("--max-tickers", type=int, default=DEFAULT_MAX_TICKERS, help="Hard cap for scoped universe pull.")
    parser.add_argument("--sector-map-path", default=str(DEFAULT_SECTOR_MAP_PATH))
    parser.add_argument("--cache-dir", default=str(DEFAULT_CACHE_DIR), help="Local JSON cache directory for per-ticker payloads.")
    parser.add_argument("--refresh-cache", action="store_true", help="Ignore cache and force network fetch when possible.")
    parser.add_argument("--cache-only", action="store_true", help="Build outputs from cache only (no network).")
    parser.add_argument("--raw-output", default=str(DEFAULT_RAW_OUTPUT))
    parser.add_argument("--processed-output", default=str(DEFAULT_PROCESSED_OUTPUT))
    parser.add_argument("--merge-existing", action="store_true", default=True, help="Merge new rows with existing processed estimates parquet.")
    parser.add_argument("--no-merge-existing", action="store_true", help="Disable merging with existing processed estimates.")
    parser.add_argument("--timeout-sec", type=float, default=30.0)
    parser.add_argument("--max-retries-429", type=int, default=5)
    parser.add_argument("--backoff-initial-sec", type=float, default=1.0)
    parser.add_argument("--log-level", default="INFO")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    _configure_logging(args.log_level)

    do_merge_existing = bool(args.merge_existing) and (not bool(args.no_merge_existing))

    tickers_file = _resolve_path(args.tickers_file, PROJECT_ROOT / "dummy") if args.tickers_file else None
    tickers = _resolve_target_tickers(
        tickers_arg=args.tickers,
        tickers_file=tickers_file,
        max_tickers=int(max(1, args.max_tickers)),
    )
    if not tickers:
        LOG.warning("No tickers resolved from args/file. Nothing to ingest.")
        return 0
    LOG.info("Scoped target universe size: %d", int(len(tickers)))

    api_key = str(os.getenv("FMP_API_KEY", "")).strip()
    cache_only = bool(args.cache_only)
    if (api_key == "") and (not cache_only):
        LOG.warning("FMP_API_KEY missing. Switching to cache-only mode for this run.")
        cache_only = True

    sector_map_path = _resolve_path(args.sector_map_path, DEFAULT_SECTOR_MAP_PATH)
    cache_dir = _resolve_path(args.cache_dir, DEFAULT_CACHE_DIR)
    raw_output = _resolve_path(args.raw_output, DEFAULT_RAW_OUTPUT)
    processed_output = _resolve_path(args.processed_output, DEFAULT_PROCESSED_OUTPUT)
    cache_dir.mkdir(parents=True, exist_ok=True)

    try:
        crosswalk = _load_ticker_permno_crosswalk(sector_map_path=sector_map_path)
    except Exception as exc:
        LOG.error("Failed loading crosswalk (%s): %s", str(sector_map_path), str(exc))
        return 1
    if crosswalk.empty:
        LOG.error("Ticker->permno crosswalk is empty; aborting ingestion.")
        return 1

    crosswalk_set = set(crosswalk["ticker_u"].dropna().astype(str).tolist())
    requested_set = set([t.upper() for t in tickers])
    unmapped_requested = sorted(requested_set - crosswalk_set)
    if unmapped_requested:
        LOG.warning(
            "Skipping %d requested ticker(s) with no permno crosswalk mapping before API calls. sample=%s",
            int(len(unmapped_requested)),
            ",".join(unmapped_requested[:10]),
        )
    tickers = [t for t in tickers if t.upper() in crosswalk_set]
    if not tickers:
        LOG.warning("No mapped tickers remain after crosswalk filter. Nothing to ingest.")
        return 1

    fetched_rows: list[dict[str, Any]] = []
    cache_hits = 0
    fetch_errors = 0
    rate_limited = False

    for ticker in tickers:
        cpath = _cache_path(cache_dir, ticker)
        cached_rows = _load_cached_rows(cpath, ticker)
        if cached_rows and (not bool(args.refresh_cache)):
            fetched_rows.extend(cached_rows)
            cache_hits += 1
            continue

        if cache_only or rate_limited:
            if cached_rows:
                fetched_rows.extend(cached_rows)
                cache_hits += 1
            else:
                LOG.warning("Cache miss for %s in cache-only/rate-limited mode.", ticker)
            continue

        try:
            rows = _fetch_with_backoff(
                ticker=ticker,
                api_key=api_key,
                timeout_sec=float(args.timeout_sec),
                max_retries_429=int(max(0, args.max_retries_429)),
                backoff_initial_sec=float(max(0.1, args.backoff_initial_sec)),
            )
            _save_cache_rows(cpath, rows)
            fetched_rows.extend(rows)
            LOG.info("Fetched %d estimate rows for %s", int(len(rows)), ticker)
        except RateLimitExhausted as exc:
            rate_limited = True
            LOG.warning(
                "Daily rate limit likely exhausted at ticker %s (%s). "
                "Switching to cache-only for remaining tickers and exiting cleanly.",
                ticker,
                str(exc),
            )
            if cached_rows:
                fetched_rows.extend(cached_rows)
                cache_hits += 1
            continue
        except HTTPError as exc:
            fetch_errors += 1
            LOG.warning("HTTP error while fetching %s: %s", ticker, str(exc))
            if cached_rows:
                fetched_rows.extend(cached_rows)
                cache_hits += 1
        except URLError as exc:
            fetch_errors += 1
            LOG.warning("Network error while fetching %s: %s", ticker, str(exc))
            if cached_rows:
                fetched_rows.extend(cached_rows)
                cache_hits += 1
        except Exception as exc:
            fetch_errors += 1
            LOG.warning("Fetch failure for %s: %s", ticker, str(exc))
            if cached_rows:
                fetched_rows.extend(cached_rows)
                cache_hits += 1

    raw = pd.DataFrame(fetched_rows)
    if raw.empty:
        LOG.warning(
            "No rows available from cache/network for target scope. "
            "No writes performed. cache_hits=%d fetch_errors=%d rate_limited=%s",
            int(cache_hits),
            int(fetch_errors),
            str(rate_limited),
        )
        if rate_limited:
            return 0
        return 1

    raw["ticker"] = _clean_ticker(raw.get("ticker", pd.Series(index=raw.index, dtype="object")))
    processed = _build_processed_estimates(raw=raw, crosswalk=crosswalk)
    if processed.empty:
        if do_merge_existing and processed_output.exists():
            LOG.warning(
                "New processed rows are empty, but existing processed parquet exists. "
                "Preserving existing dataset without overwrite."
            )
            return 0
        LOG.warning("Processed estimates are empty after mapping/normalization. No writes performed.")
        return 0 if rate_limited or cache_only else 1

    final_processed = _merge_existing_processed(processed, processed_output) if do_merge_existing else processed
    _atomic_parquet_write(raw, raw_output)
    _atomic_parquet_write(final_processed, processed_output)

    LOG.info(
        "Ingestion complete | target_tickers=%d raw_rows=%d processed_new_rows=%d processed_final_rows=%d cache_hits=%d fetch_errors=%d rate_limited=%s",
        int(len(tickers)),
        int(len(raw)),
        int(len(processed)),
        int(len(final_processed)),
        int(cache_hits),
        int(fetch_errors),
        str(rate_limited),
    )
    LOG.info("Raw output: %s", str(raw_output))
    LOG.info("Processed output: %s", str(processed_output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
