import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Parameters
TICKERS = ['RELIANCE.NS', 'HDFCBANK.NS', 'TCS.NS', 'INFY.NS', 'ITC.NS', 
           'HINDUNILVR.NS', 'LT.NS', 'ICICIBANK.NS', 'SBIN.NS', 'BHARTIARTL.NS']  # Sample universe
LOOKBACK = 10          # Days for momentum ranking
TOP_N = 3              # Long top N stocks
REBALANCE_FREQ = 'W'   # Weekly rebalance (use 'D' for daily)
PERIOD_DATA = '1y'     # Backtest period

# Fetch data
print("Fetching data for universe...")
data = yf.download(TICKERS, period=PERIOD_DATA)['Adj Close']
if data.empty:
    print("No data fetched. Check tickers.")
    exit()

# Compute daily returns
returns = data.pct_change()

# Generate signals: Rank and select top N
portfolio_returns = pd.DataFrame(index=returns.index, columns=['Portfolio'])
positions = pd.DataFrame(index=returns.index, columns=TICKERS).fillna(0)

for date in returns.resample(REBALANCE_FREQ).first().index[LOOKBACK:]:
    # Momentum: Past returns up to previous period
    past_returns = returns.loc[:date - timedelta(days=1)].tail(LOOKBACK)
    if len(past_returns) < LOOKBACK:
        continue
    
    momentum_scores = past_returns.mean()  # Average return over lookback
    top_stocks = momentum_scores.nlargest(TOP_N).index.tolist()
    
    # Equal weight positions (1/TOP_N for selected)
    for ticker in TICKERS:
        weight = 1.0 / TOP_N if ticker in top_stocks else 0
        positions.loc[date:, ticker] = weight  # Forward fill until next rebalance
    
    # Forward fill positions to next rebalance
    positions = positions.fillna(method='ffill')

# Strategy returns: Weighted sum
strategy_returns = (positions * returns).sum(axis=1)
portfolio_returns['Portfolio'] = (1 + strategy_returns).cumprod().fillna(1)
benchmark_returns = (1 + returns.mean(axis=1)).cumprod().fillna(1)  # Equal-weight benchmark

# Print recent rebalances
print("\nRecent Rebalances (Top Stocks):")
rebalance_dates = returns.resample(REBALANCE_FREQ).first().index[LOOKBACK:]
for date in rebalance_dates[-5:]:  # Last 5
    past_returns = returns.loc[:date - timedelta(days=1)].tail(LOOKBACK).mean()
    top = past_returns.nlargest(TOP_N)
    print(f"{date.date()}: {top.to_dict()}")

# Performance
total_return = portfolio_returns['Portfolio'].iloc[-1] - 1
benchmark_return = benchmark_returns.iloc[-1] - 1
print(f"\nStrategy Total Return: {total_return*100:.2f}%")
print(f"Equal-Weight Benchmark: {benchmark_return*100:.2f}%")

# Plot
plt.figure(figsize=(12, 6))
plt.plot(portfolio_returns.index, portfolio_returns['Portfolio'], label='Momentum Portfolio', linewidth=2)
plt.plot(benchmark_returns.index, benchmark_returns, label='Benchmark', alpha=0.7)
plt.title('Momentum Trading Strategy Backtest')
plt.ylabel('Cumulative Returns')
plt.legend()
plt.savefig('momentum_plot.png')
plt.show()