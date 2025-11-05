import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Parameters
TICKER = 'RELIANCE.NS'  # Example: Change to any NSE stock
SHORT_WINDOW = 50       # Short-term SMA
LONG_WINDOW = 200       # Long-term SMA
PERIOD = '1y'           # Data period (1 year)

# Fetch data
print(f"Fetching data for {TICKER}...")
data = yf.download(TICKER, period=PERIOD)
if data.empty:
    print("No data fetched. Check ticker.")
    exit()

# Compute SMAs
data['SMA_Short'] = data['Close'].rolling(window=SHORT_WINDOW).mean()
data['SMA_Long'] = data['Close'].rolling(window=LONG_WINDOW).mean()

# Generate signals
data['Signal'] = 0
data['Signal'][SHORT_WINDOW:] = np.where(
    data['SMA_Short'][SHORT_WINDOW:] > data['SMA_Long'][SHORT_WINDOW:], 1, 0
)
data['Position'] = data['Signal'].diff()  # 1: Buy, -1: Sell

# Backtest: Simple returns (buy/hold on signal)
data['Returns'] = data['Close'].pct_change()
data['Strategy_Returns'] = data['Returns'] * data['Signal'].shift(1)
data['Cumulative_Strategy'] = (1 + data['Strategy_Returns']).cumprod()
data['Cumulative_BuyHold'] = (1 + data['Returns']).cumprod()

# Print signals
buys = data[data['Position'] == 1].index
sells = data[data['Position'] == -1].index
print("\nBuy Signals (Dates):")
for date in buys[-5:]:  # Last 5 buys
    print(f"- {date.date()}: Price ₹{data.loc[date, 'Close']:.2f}")
print("\nSell Signals (Dates):")
for date in sells[-5:]:  # Last 5 sells
    print(f"- {date.date()}: Price ₹{data.loc[date, 'Close']:.2f}")

# Performance
total_return = data['Cumulative_Strategy'].iloc[-1] - 1
buyhold_return = data['Cumulative_BuyHold'].iloc[-1] - 1
print(f"\nStrategy Total Return: {total_return*100:.2f}%")
print(f"Buy & Hold Return: {buyhold_return*100:.2f}%")

# Plot
plt.figure(figsize=(12, 6))
plt.plot(data['Close'], label='Close Price', alpha=0.7)
plt.plot(data['SMA_Short'], label=f'SMA {SHORT_WINDOW}', alpha=0.8)
plt.plot(data['SMA_Long'], label=f'SMA {LONG_WINDOW}', alpha=0.8)
plt.plot(buys, data['Close'][buys], '^', markersize=10, color='g', label='Buy')
plt.plot(sells, data['Close'][sells], 'v', markersize=10, color='r', label='Sell')
plt.title(f'{TICKER} MA Crossover Strategy')
plt.legend()
plt.savefig('ma_crossover_plot.png')  # Saves plot
plt.show()  # Displays if running interactively
