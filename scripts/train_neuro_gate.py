import pandas as pd
import numpy as np
import yfinance as yf
import xgboost as xgb
import shap
import os
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import warnings

warnings.filterwarnings("ignore")

def compute_rsi(series, window=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def main():
    print("Executing Phase 30: Neuro-Gating Engine")
    tickers = ['NVDA', 'TSM', 'AMD', 'MU', 'CIFR', 'MARA', 'COIN', 'QQQ', 'SPY']
    
    # Download data
    print("Building Data Construct (The Truth Dataset)...")
    data = yf.download(tickers + ['^VIX'], start="2020-01-01", end="2025-02-25", progress=False)['Close']
    if isinstance(data.columns, pd.MultiIndex):
        # We handled it roughly below if necessary, but 'Close' natively slices it to SingleIndex
        pass

    vix = data['^VIX']
    qqq = data['QQQ']
    qqq_ma200 = qqq.rolling(200).mean()
    qqq_trend = qqq / qqq_ma200
    
    spy_rets = data['SPY'].pct_change()

    features_list = []
    
    for t in tickers:
        p = data[t]
        rets = p.pct_change()
        
        # Features
        var_spy = spy_rets.rolling(60).var()
        cov = rets.rolling(60).cov(spy_rets)
        beta_60 = cov / var_spy
        vol_20 = rets.rolling(20).std() * np.sqrt(252)
        rsi_14 = compute_rsi(p, 14)
        
        high_20 = p.rolling(20).max().shift(1)
        low_20 = p.rolling(20).min().shift(1)
        ma_20 = p.rolling(20).mean()
        
        df = pd.DataFrame({
            'Price': p,
            'Beta_60': beta_60,
            'Vol_20': vol_20,
            'RSI_14': rsi_14,
            'QQQ_Trend': qqq_trend,
            'VIX': vix,
            'High_20': high_20,
            'Low_20': low_20,
            'MA_20': ma_20
        })
        
        df = df.dropna().copy()
        
        df['Beta_x_VIX'] = df['Beta_60'] * df['VIX']
        df['RSI_x_Trend'] = df['RSI_14'] * df['QQQ_Trend']
        
        # Extract numpy arrays for speed
        prices_arr = df['Price'].values
        h20_arr = df['High_20'].values
        l20_arr = df['Low_20'].values
        ma20_arr = df['MA_20'].values
        
        n = len(df)
        pnl_sprinter = np.zeros(n)
        pnl_sniper = np.zeros(n)
        
        # PnL Simulation logic per day
        for i in range(n):
            price = prices_arr[i]
            
            # Simulated Sprinter Entry
            if price > h20_arr[i]:
                highest = price
                pnl_sp = 0
                for j in range(i + 1, n):
                    curr_p = prices_arr[j]
                    if curr_p > highest:
                        highest = curr_p
                    if curr_p <= highest * 0.95:
                        pnl_sp = (curr_p - price) / price
                        break
                else:
                    if i < n - 1:
                        pnl_sp = (prices_arr[-1] - price) / price
                pnl_sprinter[i] = pnl_sp
                
            # Simulated Sniper Entry
            if price < l20_arr[i]:
                pnl_sn = 0
                for j in range(i + 1, n):
                    curr_p = prices_arr[j]
                    curr_ma = ma20_arr[j]
                    if curr_p > curr_ma:
                        pnl_sn = (curr_p - price) / price
                        break
                else:
                    if i < n - 1:
                        pnl_sn = (prices_arr[-1] - price) / price
                pnl_sniper[i] = pnl_sn
                
        df['PnL_Sprinter'] = pnl_sprinter
        df['PnL_Sniper'] = pnl_sniper
        
        # Create Label (y)
        # 1 if Sniper beats Sprinter, else 0.
        df['Label'] = np.where(df['PnL_Sniper'] > df['PnL_Sprinter'], 1, 0)
        df['Ticker'] = t
        features_list.append(df)
        
    full_df = pd.concat(features_list)
    
    print("Training Explainable XGBoost Model...")
    feature_cols = ['Beta_60', 'Vol_20', 'RSI_14', 'QQQ_Trend', 'VIX', 'Beta_x_VIX', 'RSI_x_Trend']
    
    X = full_df[feature_cols]
    y = full_df['Label']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=False)
    
    model = xgb.XGBClassifier(eval_metric='logloss', random_state=42)
    model.fit(X_train, y_train)
    
    preds = model.predict(X_test)
    acc = accuracy_score(y_test, preds)
    
    print("\n--- Neuro-Gating Model Stats ---")
    print(f"Test Accuracy: {acc*100:.2f}%")
    
    # SHAP Generation
    explainer = shap.Explainer(model)
    shap_values = explainer(X_train)
    
    # Feature Importance Extract
    mean_abs_shap = np.abs(shap_values.values).mean(axis=0)
    shap_imp = pd.Series(mean_abs_shap, index=feature_cols).sort_values(ascending=False)
    
    print("\n--- Top 5 Features Driving Execution Logic ---")
    for idx, (col, val) in enumerate(shap_imp.head(5).items()):
        print(f"{idx+1}. {col:15} | SHAP Impact: {val:.4f}")
        
    print(f"\n#1 Driver: {shap_imp.index[0]}")
    
    # Save model
    os.makedirs('models', exist_ok=True)
    model.save_model('models/neuro_gate.model')
    print("Saved model to models/neuro_gate.model")
    
    # Live Prediction NVDA
    nvda_data = full_df[full_df['Ticker'] == 'NVDA'].iloc[-1]
    
    # To pass features to predict_proba securely, pass as dataframe exactly shaped like X
    input_df = pd.DataFrame([nvda_data[feature_cols].values], columns=feature_cols)
    prob_sniper = model.predict_proba(input_df)[0][1]
    
    print("\n--- Live Prediction for NVDA ---")
    print(f"Current Regime Probability (Sniper Wins): {prob_sniper*100:.2f}%")
    if prob_sniper > 0.5:
        print("Decision: SNIPER (Limit Orders - Wait for the Dip)")
    else:
        print("Decision: SPRINTER (Market Orders - Play the Momentum)")

if __name__ == '__main__':
    main()
