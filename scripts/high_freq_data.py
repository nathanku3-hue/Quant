import yfinance as yf
import pandas as pd
import datetime
import requests
import json
import re
from core.security_policy import assert_egress_url_allowed


def _allow_egress_or_none(url: str, *, context: str) -> bool:
    try:
        assert_egress_url_allowed(url, context=context)
        return True
    except Exception as exc:
        print(f"[EgressBlocked] {context}: {exc}")
        return False


def _degraded_metric(*, reason: str, span: str = "DEGRADED") -> dict:
    return {"val": 0.0, "span": span, "degraded": True, "reason": reason}


class AutoFetcher:
    """Attempts to scrape or pull metrics automatically via API."""
    def __init__(self):
        pass
        
    def fetch_tsmc_yoy(self):
        """Pulls TSMC 1-Month vs 1-Month (MoM) leading edge data, falls back to QoQ if needed."""
        try:
            if not _allow_egress_or_none("https://query1.finance.yahoo.com", context="high_freq_fetch_tsmc"):
                return _degraded_metric(reason="egress_blocked")
            tsm_df = yf.download("TSM", period="3mo", progress=False)['Close']
            if len(tsm_df) >= 21: # Have at least 1 month
                current_price = tsm_df.iloc[-1].item()
                month_ago = tsm_df.iloc[-21].item()
                mom = (current_price / month_ago) - 1
                return {"val": round(mom, 4), "span": "MoM"}
            else:
                tsm = yf.Ticker("TSM")
                inc = tsm.quarterly_income_stmt
                rev_key = 'Total Revenue' if 'Total Revenue' in inc.index else 'Operating Revenue'
                if rev_key in inc.index:
                    rev = inc.loc[rev_key].dropna()
                    if len(rev) >= 2:
                        qoq_rev = (rev.iloc[0] / rev.iloc[1]) - 1
                        return {"val": round(qoq_rev, 4), "span": "QoQ"}
        except Exception as e:
            print(f"[AUTO-FAIL] TSMC: {e}")
        return _degraded_metric(reason="fetch_failed")

    def fetch_energy_trend(self):
        """Pulls URA ETF Weekly (WoW) or Monthly (MoM) trend."""
        try:
            if not _allow_egress_or_none("https://query1.finance.yahoo.com", context="high_freq_fetch_energy"):
                return {"val": 0.0, "span": "Trend"}
            ura = yf.download("URA", period="1mo", progress=False)['Close']
            if len(ura) >= 5: # Have at least 1 week
                current = ura.iloc[-1].item()
                week_ago = ura.iloc[-5].item()
                wow = (current - week_ago) / week_ago
                return {"val": round(wow, 4), "span": "WoW"}
            elif len(ura) >= 21:
                current = ura.iloc[-1].item()
                month_ago = ura.iloc[-21].item()
                mom = (current - month_ago) / month_ago
                return {"val": round(mom, 4), "span": "MoM"}
        except Exception as e:
            print(f"[AUTO-FAIL] Energy: {e}")
        return {"val": 0.0, "span": "Trend"}
        
    def fetch_cloud_growth(self):
        """Pulls AWS/Azure proxy: Cloud ETFs or Quarterlies."""
        try: # Try highly granular weekly MSFT price action as cloud proxy first
            if not _allow_egress_or_none("https://query1.finance.yahoo.com", context="high_freq_fetch_cloud"):
                return _degraded_metric(reason="egress_blocked")
            cloud_etf = yf.download("SKYY", period="1mo", progress=False)['Close']
            if len(cloud_etf) >= 5:
                current = cloud_etf.iloc[-1].item()
                week_ago = cloud_etf.iloc[-5].item()
                wow = (current - week_ago) / week_ago
                return {"val": round(wow, 4), "span": "WoW"}
        except:
            pass
            
        try: # Fallback to QoQ actual fundamental cloud revenue
            if not _allow_egress_or_none("https://query1.finance.yahoo.com", context="high_freq_fetch_cloud_fallback"):
                return _degraded_metric(reason="egress_blocked")
            msft = yf.Ticker("MSFT")
            inc = msft.quarterly_income_stmt
            rev_key = 'Total Revenue' if 'Total Revenue' in inc.index else 'Operating Revenue'
            if rev_key in inc.index:
                rev = inc.loc[rev_key].dropna()
                if len(rev) >= 2:
                    qoq_rev = (rev.iloc[0] / rev.iloc[1]) - 1
                    return {"val": round(qoq_rev, 4), "span": "QoQ"}
        except:
            pass
        return _degraded_metric(reason="fetch_failed")

    def fetch_dram_trend(self):
        """DRAM logic is heavily gated; return None to enforce prompt"""
        return None

def get_construction_scalar():
    """ Returns scalar (-10 to +10) based on FRED TLPWRCONS """
    start_date = datetime.datetime.now() - datetime.timedelta(days=400)
    if not _allow_egress_or_none("https://fred.stlouisfed.org", context="high_freq_fetch_fred"):
        return 0
    try:
        import pandas_datareader as pdr  # local import to avoid global deprecation noise on unrelated paths
    except Exception as e:
        print(f"[INFRA] pandas_datareader unavailable: {e}")
        return 0
    try:
        infra_data = pdr.get_data_fred('TLPWRCONS', start_date)
        if len(infra_data) >= 13:
            current_infra = infra_data.iloc[-1, 0]
            prev_infra = infra_data.iloc[-13, 0]
            infra_delta = (current_infra - prev_infra) / prev_infra
            
            if infra_delta > 0.05:
                return 10
            elif infra_delta < 0:
                return -10
            elif infra_delta > 0:
                return 5
    except Exception as e:
        print(f"[INFRA] Sensor Fail: {e}")
    return 0

def get_commodity_scalar(ticker, manual_data):
    """
    Returns the HF Scalar (-10 to +10) based on the specific COMMODITY 
    that drives the ticker's physics.
    """
    def extract_val(key):
        val = manual_data.get(key, 0)
        return val['val'] if isinstance(val, dict) else val

    # --- MEMORY PHYSICS (MU) ---
    if ticker == 'MU':
        dram_trend = extract_val('dram_spot_trend')
        if dram_trend > 0.05: return 10   # Exploding Up
        if dram_trend > 0.02: return 5    # Trending Up
        if dram_trend < -0.02: return -10 # Crashing (Kill)
        return 0

    # --- STORAGE PHYSICS (WDC) ---
    elif ticker == 'WDC':
        nand_trend = extract_val('nand_spot_trend')
        if nand_trend > 0.02: return 10
        if nand_trend < -0.02: return -10
        return 0

    # --- INFRA PHYSICS (VRT/CEG/ETN/CLS) ---
    elif ticker in ['VRT', 'CEG', 'ETN', 'CLS']:
        return get_construction_scalar() 

    # --- COMPUTE PHYSICS (NVDA/AMD) ---
    elif ticker in ['NVDA', 'AMD']:
        tsmc_yoy = extract_val('tsmc_monthly_yoy')
        if tsmc_yoy > 0.20: return 10
        if tsmc_yoy < 0: return -10
        return 5

    # --- CUSTOM CYBER/SOFTWARE PHYSICS (RBRK) ---
    elif ticker in ['RBRK']:
        # Proxy: AWS/Azure YoY Growth Rate
        cloud_yoy = extract_val('cloud_growth_yoy')
        if cloud_yoy > 0.30: return 10
        if cloud_yoy < 0.15: return -10
        return 0
        
    # --- CUSTOM BIOTECH PHYSICS (NBIS) ---
    elif ticker in ['NBIS']:
        # Proxy: XBI Options Skew / Funding appetite
        xbi_trend = manual_data.get('xbi_funding_trend', 0)
        if xbi_trend > 0.10: return 10
        if xbi_trend < 0: return -10
        return 0

    return 0

# --- PM CONSOLE INPUT ---
# Update this monthly from: https://investor.tsmc.com/english/monthly-revenue
if __name__ == "__main__":
    test_manual = {'dram_spot_trend': 0.06, 'tsmc_monthly_yoy': 25.0}
    print("MU Score:", get_commodity_scalar('MU', test_manual))
    print("VRT Score:", get_commodity_scalar('VRT', test_manual))
