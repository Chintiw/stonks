import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Parameters
TICKER = 'HDFCBANK.NS'  # Example: Stable bank stock for range-bound testing
PERIOD = 20             # Lookback for mean/std (days)
Z_THRESHOLD = 2         # Oversold/overbought threshold
PERIOD_DATA = '1y'      # Data fetch period

# Fetch data
print(f"Fetching data for {TICKER}...")
data = yf.download(TICKER, period=PERIOD_DATA)
if data.empty:
    print("No data fetched. Check ticker.")
    exit()

# Compute rolling mean and std
data['Mean'] = data['Close'].rolling(window=PERIOD).mean()
data['Std'] = data['Close'].rolling(window=PERIOD).std()
data['Z_Score'] = (data['Close'] - data['Mean']) / data['Std']

# Bollinger Bands for visualization (mean ± 2*std)
data['Upper_Band'] = data['Mean'] + (data['Std'] * Z_THRESHOLD)
data['Lower_Band'] = data['Mean'] - (data['Std'] * Z_THRESHOLD)

# Generate signals: 1=Buy (oversold), -1=Sell (overbought or revert), 0=Hold
data['Signal'] = 0
data.loc[data['Z_Score'] < -Z_THRESHOLD, 'Signal'] = 1   # Buy oversold
data.loc[data['Z_Score'] > Z_THRESHOLD, 'Signal'] = -1   # Sell overbought
# Exit on mean revert (from position)
data['Position'] = data['Signal'].replace(to_replace=0, method='ffill').fillna(0)
data.loc[(data['Position'] != 0) & (abs(data['Z_Score']) < 0.5), 'Signal'] = -data['Position']  # Close on near-mean

# Backtest returns (simple: hold position until signal change)
data['Returns'] = data['Close'].pct_change()
data['Strategy_Returns'] = data['Returns'] * data['Position'].shift(1)
data['Cumulative_Strategy'] = (1 + data['Strategy_Returns']).cumprod().fillna(1)
data['Cumulative_BuyHold'] = (1 + data['Returns']).cumprod().fillna(1)

# Print recent signals
trades = data[data['Signal'] != 0].copy()
trades['Action'] = trades['Signal'].map({1: 'BUY', -1: 'SELL'})
print("\nRecent Trades:")
print(trades[['Action', 'Z_Score', 'Close']].tail(10).to_string())

# Performance
total_return = data['Cumulative_Strategy'].iloc[-1] - 1
buyhold_return = data['Cumulative_BuyHold'].iloc[-1] - 1
print(f"\nStrategy Total Return: {total_return*100:.2f}%")
print(f"Buy & Hold Return: {buyhold_return*100:.2f}%")

# Plot
plt.figure(figsize=(12, 6))
plt.plot(data['Close'], label='Close Price', alpha=0.7)
plt.plot(data['Upper_Band'], label='Upper Band', alpha=0.8)
plt.plot(data['Lower_Band'], label='Lower Band', alpha=0.8)
plt.plot(data['Mean'], label='Mean', alpha=0.8)
buys = data[data['Signal'] == 1].index
sells = data[data['Signal'] == -1].index
plt.plot(buys, data['Close'][buys], '^', markersize=10, color='g', label='Buy')
plt.plot(sells, data['Close'][sells], 'v', markersize=10, color='r', label='Sell')
plt.title(f'{TICKER} Mean Reversion Strategy (Z-Score Threshold: ±{Z_THRESHOLD})')
plt.legend()
plt.savefig('mean_reversion_plot.png')
plt.show()