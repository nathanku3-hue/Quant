import pandas as pd
import yfinance as yf
import datetime

class PhaseReversalMonitor:
    def __init__(self, ticker):
        self.ticker = ticker
        
    def fetch_price_data(self):
        end = datetime.datetime.now()
        start = end - datetime.timedelta(days=180)
        df = yf.download(self.ticker, start=start, end=end, progress=False)
        return df['Close']
        
    def calculate_divergence(self, hf_scalar_t0, hf_scalar_t1, hf_scalar_t2, mock_price_velocity=None):
        """
        Calculates Price Velocity and Price Acceleration,
        and compares it against Fundamental Acceleration.
        hf_scalar_t0: Current month
        hf_scalar_t1: 1 month ago
        hf_scalar_t2: 2 months ago
        """
        if mock_price_velocity is None:
            prices = self.fetch_price_data()
            if prices.empty:
                return "ERROR: No price data"
            monthly_prices = prices.resample('ME').last()
            if len(monthly_prices) < 3:
                return "ERROR: Not enough data"
            velocity = monthly_prices.pct_change().dropna()
            
            # Reformat to cleanly get latest
            if isinstance(velocity, pd.DataFrame):
                velocity = velocity[self.ticker]
        else:
            velocity = pd.Series(mock_price_velocity)
            
        accel = velocity.diff().dropna()
        current_price_accel = accel.iloc[-1]
        
        # Fundamental Deceleration: when the HF Scalar breaks trend downwards
        # Trend: 10 -> 5 -> 0
        is_fundamental_decelerating = (hf_scalar_t0 < hf_scalar_t1)
        
        print(f"\n--- {self.ticker} Phase Reversal Monitor ---")
        print(f"Price Velocity (1-Mo % Change): {velocity.iloc[-1]:.2%}")
        print(f"Price Acceleration (ΔVelocity): {current_price_accel:.2%}")
        print(f"HF Scalar Trend: {hf_scalar_t2} -> {hf_scalar_t1} -> {hf_scalar_t0}")
        
        if current_price_accel > 0 and is_fundamental_decelerating:
            print("\n[ALERT: ORANGE] Divergence Detected!")
            print("Stock is going parabolic (Price_Accel > 0) BUT Sensors are cooling off (Fundamental_Accel < 0).")
            print("ACTION: Stop Buying. Tighten Trailing Stop to 5%. Sell Covered Calls to harvest volatility.")
        elif current_price_accel > 0 and not is_fundamental_decelerating:
            print("\n[SAFE: GREEN] Physics confirm price action. Ride the wave.")
        elif current_price_accel <= 0 and is_fundamental_decelerating:
            print("\n[NORMAL: YELLOW] Both Price and Fundamentals are decelerating. Natural top forming.")
        else:
            print("\n[NORMAL: BLUE] Price is decelerating but fundamentals are strong. Dip buying opportunity.")

if __name__ == "__main__":
    print("Initiating Priority 3: The Lead-Lag Phase Reversal Monitor")
    monitor = PhaseReversalMonitor("MU")
    
    # HYPOTHETICAL SCENARIO:
    # DRAM prices flatline (10 -> 5 -> 0), but the stock rips (Acceleration is positive)
    # Velocity t-1 = 5%, Velocity t0 = +15%. Price Acceleration = +10%
    hypothetical_velocity = [0.05, 0.15]
    
    monitor.calculate_divergence(
        hf_scalar_t0=0, 
        hf_scalar_t1=5, 
        hf_scalar_t2=10, 
        mock_price_velocity=hypothetical_velocity
    )
