import time
import warnings
import concurrent.futures

import pandas as pd
import yfinance as yf
import numpy as np

warnings.filterwarnings("ignore")

STRONG_BUY_THRESHOLD = 80

UNIVERSE = [
    "AAPL","MSFT","NVDA","AMZN","META","GOOGL","TSLA","AVGO","BRK-B","JPM",
    "LLY","UNH","V","XOM","MA","COST","HD","PG","JNJ","ABBV",
    "BAC","NFLX","CRM","CVX","MRK","KO","PEP","TMO","ACN","MCD",
    "LIN","CSCO","ABT","GE","DHR","TXN","ADBE","QCOM","WMT","IBM",
    "CAT","INTU","ISRG","AMGN","GS","SPGI","NOW","BKNG","RTX","HON",
    "AXP","NEE","VRTX","MS","LOW","BLK","UNP","AMAT","ETN","LRCX",
    "ADI","REGN","SYK","PLD","PANW","BSX","SBUX","GILD","ADP","MMC",
    "CB","CME","MO","TMUS","CI","SO","DUK","WM","ICE","EQIX",
    "AON","CL","ZTS","CDNS","SNPS","MCO","CSX","ITW","BDX","NOC",
    "EMR","FDX","CTAS","HCA","EW","NSC","TGT","USB","PNC","COF",
    "MU","KLAC","MRVL","MCHP","MPWR","ON","TER","ENTG","ANET","CRWD",
    "FTNT","DDOG","ZS","SNOW","MDB","PLTR","RBRK","NBIS","CLS","CEG",
    "VST","NRG","FSLR","ENPH","DECK","ONON","NKE","LULU","SPOT","DIS",
    "PINS","SNAP","RDDT","EBAY","ETSY","CVNA","KMX","URI","LMT","BA",
    "GD","LHX","AXON","CSGP","VRSK","FICO","IQV","ILMN","BIIB","IDXX",
    "ALGN","DXCM","HOLX","BAX","CF","MOS","ADM","KR","CVS","ELV",
    "HUM","MOH","CNC","PGR","TRV","MET","PRU","SWK","AME","GNRC",
    "PSA","SPG","EXR","AMH","INVH","ELS","SUI","UDR","CPT","MAA",
    "COIN","HOOD","SOFI","SQ","PYPL","AFFIRM","UPST","LC","OPFI","NU",
    "SMCI","HPE","DELL","WDC","STX","NTAP","PSTG","PRGS","ESTC","GTLB",
]
UNIVERSE = sorted(set(UNIVERSE))

CHUNK_SIZE = 25      # tickers per batch
CHUNK_DELAY = 8      # seconds between price batches
FINANCIAL_DELAY = 0.5  # seconds between individual financial fetches


def download_prices_chunked(tickers, period="1y"):
    """Download prices in chunks to avoid rate limits."""
    all_closes = {}
    chunks = [tickers[i:i+CHUNK_SIZE] for i in range(0, len(tickers), CHUNK_SIZE)]
    for i, chunk in enumerate(chunks):
        print(f"  Price chunk {i+1}/{len(chunks)} ({len(chunk)} tickers)...")
        try:
            raw = yf.download(chunk, period=period, progress=False, threads=False)
            if raw.empty:
                print(f"  Chunk {i+1} returned empty — rate limited, waiting 30s...")
                time.sleep(30)
                raw = yf.download(chunk, period=period, progress=False, threads=False)
            if not raw.empty:
                if isinstance(raw.columns, pd.MultiIndex):
                    col = "Adj Close" if "Adj Close" in raw.columns.get_level_values(0) else "Close"
                    closes = raw[col]
                else:
                    closes = raw
                for t in closes.columns:
                    s = closes[t].dropna()
                    if len(s) > 2:
                        all_closes[t] = s
        except Exception as e:
            print(f"  Chunk {i+1} failed: {e}")
        if i < len(chunks) - 1:
            time.sleep(CHUNK_DELAY)
    if not all_closes:
        return pd.DataFrame()
    return pd.DataFrame(all_closes)


def process(t, rs_rank):
    try:
        time.sleep(FINANCIAL_DELAY)
        tkr = yf.Ticker(t)
        inc = tkr.quarterly_income_stmt
        if inc is None or inc.empty:
            inc = tkr.quarterly_financials
        if inc is None or inc.empty:
            return None
        rev_key = "Total Revenue" if "Total Revenue" in inc.index else "Operating Revenue"
        if rev_key not in inc.index:
            return None
        rev = inc.loc[rev_key].dropna()
        op_key = "Operating Income" if "Operating Income" in inc.index else "Net Income"
        if op_key not in inc.index:
            return None
        op = inc.loc[op_key].dropna()
        if len(rev) < 3 or len(op) < 3:
            return None
        if len(rev) >= 6:
            g1 = (rev.iloc[0] / rev.iloc[4]) - 1
            g2 = (rev.iloc[1] / rev.iloc[5]) - 1
        else:
            g1 = (rev.iloc[0] / rev.iloc[1]) - 1
            g2 = (rev.iloc[1] / rev.iloc[2]) - 1
        accel = g1 - g2
        m1 = op.iloc[0] / rev.iloc[0] if rev.iloc[0] != 0 else 0
        m2 = op.iloc[1] / rev.iloc[1] if rev.iloc[1] != 0 else 0
        gp_key = "Gross Profit" if "Gross Profit" in inc.index else None
        if gp_key:
            gp = inc.loc[gp_key].dropna()
            gm1 = gp.iloc[0] / rev.iloc[0] if len(gp) >= 1 and rev.iloc[0] != 0 else 0
            gm2 = gp.iloc[1] / rev.iloc[1] if len(gp) >= 2 and rev.iloc[1] != 0 else 0
            pricing = gm1 - gm2
        else:
            pricing = 0.0
        return {
            "Ticker": t,
            "Accel": accel,
            "Margin_Delta": m1 - m2,
            "Pricing_Delta": pricing,
            "RS_Rank": rs_rank.loc[t],
        }
    except Exception:
        return None


def main():
    print("=== Strong Buy Scan - March 30, 2026 ===")
    print(f"Universe: {len(UNIVERSE)} tickers")
    print("Downloading prices in chunks (rate-limit safe)...")

    closes = download_prices_chunked(UNIVERSE + ["SPY"])
    print(f"Price matrix: {closes.shape[1]} tickers x {closes.shape[0]} days")

    if closes.shape[0] < 2 or closes.shape[1] < 5:
        print("ERROR: Not enough price data retrieved. yfinance still rate-limited.")
        print("Please wait 5-10 minutes and try again.")
        return

    ret_1y = (closes.iloc[-1] / closes.iloc[0]) - 1
    spy_ret = float(ret_1y.get("SPY", 0.0))
    rs = (ret_1y - spy_ret).drop("SPY", errors="ignore").dropna()
    rs_rank = rs.rank(pct=True) * 100

    top_tickers = rs_rank.sort_values(ascending=False).head(150).index.tolist()
    print(f"Top RS candidates: {len(top_tickers)}. Fetching financials (sequential, rate-limit safe)...")

    results = []
    for i, t in enumerate(top_tickers):
        r = process(t, rs_rank)
        if r:
            results.append(r)
        if (i + 1) % 25 == 0:
            print(f"  {i+1}/{len(top_tickers)} processed, {len(results)} valid...")
            time.sleep(3)  # brief pause every 25 financial fetches

    df = pd.DataFrame(results).dropna()
    if df.empty:
        print("No valid financial results.")
        return

    df["Accel_Rank"] = df["Accel"].rank(pct=True) * 100
    df["Margin_Rank"] = df["Margin_Delta"].rank(pct=True) * 100
    df["Pricing_Rank"] = df["Pricing_Delta"].rank(pct=True) * 100
    df["Score"] = (
        df["RS_Rank"] * 0.40
        + df["Accel_Rank"] * 0.25
        + df["Margin_Rank"] * 0.20
        + df["Pricing_Rank"] * 0.15
    )

    strong = df[df["Score"] >= STRONG_BUY_THRESHOLD].sort_values("Score", ascending=False)

    print(f"\n=== STRONG BUY LIST - March 30, 2026 ({len(strong)} names) ===")
    print(f"{'Ticker':<8} | {'RS Rank':>8} | {'Rev Accel':>10} | {'Margin D':>9} | {'Pricing D':>10} | {'Score':>7}")
    print("-" * 70)
    for _, r in strong.iterrows():
        print(
            f"{r['Ticker']:<8} | {r['RS_Rank']:>8.1f} | "
            f"{r['Accel']*100:>+9.2f}% | {r['Margin_Delta']*100:>+8.2f}% | "
            f"{r['Pricing_Delta']*100:>+9.2f}% | {r['Score']:>7.1f}"
        )

    if strong.empty:
        print("No strong buys at Score >= 80. Top 15 closest:")
        top15 = df.sort_values("Score", ascending=False).head(15)
        for _, r in top15.iterrows():
            print(
                f"{r['Ticker']:<8} | {r['RS_Rank']:>8.1f} | "
                f"{r['Accel']*100:>+9.2f}% | {r['Margin_Delta']*100:>+8.2f}% | "
                f"{r['Pricing_Delta']*100:>+9.2f}% | {r['Score']:>7.1f}"
            )


if __name__ == "__main__":
    main()
