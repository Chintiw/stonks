import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import schedule
import time
from datetime import datetime, time as dt_time
import os
import json

# Config (move to YAML later)
CONFIG = {
    'initial_cash': 100000,
    'brokerage_fee': 0.001,  # 0.1%
    'slippage': 0.0005,       # 0.05%
    'max_position_size': 0.1, # 10% of portfolio per trade
    'stop_loss_pct': 0.02,    # 2% stop-loss
    'tickers': ['RELIANCE.NS'], # Universe; expand via screener
    'strat': 'ma_crossover',  # 'ma_crossover', 'mean_reversion', 'momentum'
    'check_interval_min': 5,  # Run every 5 min
    'market_open': dt_time(9, 15),
    'market_close': dt_time(15, 30),
    'output_dir': 'output'
}

# Ensure output dir
os.makedirs(CONFIG['output_dir'], exist_ok=True)

# Portfolio state (global for simplicity; use class for multi-user)
portfolio = {
    'cash': CONFIG['initial_cash'],
    'positions': {ticker: {'shares': 0, 'avg_price': 0} for ticker in CONFIG['tickers']},
    'total_value': CONFIG['initial_cash'],
    'trades': []  # List of dicts: {'timestamp', 'action', 'ticker', 'shares', 'price', 'value'}
}

# Strat signal functions (import/adapt from your scripts)
def get_ma_crossover_signal(ticker, short_window=50, long_window=200):
    """Returns signal: 1=buy, -1=sell, 0=hold"""
    data = yf.download(ticker, period='6mo')  # Enough history
    data['SMA_Short'] = data['Close'].rolling(short_window).mean()
    data['SMA_Long'] = data['Close'].rolling(long_window).mean()
    if len(data) < long_window:
        return 0
    prev_short = data['SMA_Short'].iloc[-2]
    prev_long = data['SMA_Long'].iloc[-2]
    curr_short = data['SMA_Short'].iloc[-1]
    curr_long = data['SMA_Long'].iloc[-1]
    if prev_short <= prev_long and curr_short > curr_long:
        return 1  # Buy
    elif prev_short >= prev_long and curr_short < curr_long:
        return -1  # Sell
    return 0

def get_mean_reversion_signal(ticker, period=20, z_threshold=2):
    """Adapt from mean_reversion.py"""
    data = yf.download(ticker, period='6mo')
    data['Mean'] = data['Close'].rolling(period).mean()
    data['Std'] = data['Close'].rolling(period).std()
    data['Z_Score'] = (data['Close'] - data['Mean']) / data['Std']
    if len(data) < period:
        return 0
    z = data['Z_Score'].iloc[-1]
    if z < -z_threshold:
        return 1
    elif z > z_threshold:
        return -1
    return 0

def get_momentum_signal(tickers, lookback=10, top_n=1):
    """Adapt from momentum.py; returns dict of signals per ticker"""
    data = yf.download(tickers, period='3mo')['Adj Close']
    returns = data.pct_change().tail(lookback).mean()
    top = returns.nlargest(top_n).index.tolist()
    signals = {t: 1 if t in top else 0 for t in tickers}
    # Sell if not in top anymore (simplified)
    for t in tickers:
        if signals[t] == 0 and portfolio['positions'][t]['shares'] > 0:
            signals[t] = -1
    return signals

# Signal dispatcher
def get_signals():
    if CONFIG['strat'] == 'ma_crossover':
        return {t: get_ma_crossover_signal(t) for t in CONFIG['tickers']}
    elif CONFIG['strat'] == 'mean_reversion':
        return {t: get_mean_reversion_signal(t) for t in CONFIG['tickers']}
    elif CONFIG['strat'] == 'momentum':
        return get_momentum_signal(CONFIG['tickers'])
    raise ValueError("Unknown strat")

# Simulate execution
def execute_trade(ticker, action, price, shares):
    pos = portfolio['positions'][ticker]
    value = abs(shares * price * (1 + CONFIG['slippage']))
    value += value * CONFIG['brokerage_fee']  # Fee on value
    
    if action == 'buy' and portfolio['cash'] >= value:
        pos['shares'] += shares
        pos['avg_price'] = (pos['avg_price'] * pos['shares'] - shares * price + shares * price) / pos['shares']  # Weighted avg
        portfolio['cash'] -= value
        portfolio['trades'].append({
            'timestamp': datetime.now(),
            'action': 'BUY',
            'ticker': ticker,
            'shares': shares,
            'price': price,
            'value': -value
        })
        print(f"BUY {shares} {ticker} @ ₹{price:.2f} (Cash left: ₹{portfolio['cash']:.2f})")
    elif action == 'sell' and pos['shares'] >= shares:
        portfolio['cash'] += value
        pos['shares'] -= shares
        if pos['shares'] == 0:
            pos['avg_price'] = 0
        portfolio['trades'].append({
            'timestamp': datetime.now(),
            'action': 'SELL',
            'ticker': ticker,
            'shares': shares,
            'price': price,
            'value': value
        })
        print(f"SELL {shares} {ticker} @ ₹{price:.2f} (Cash: ₹{portfolio['cash']:.2f})")
    else:
        print(f"Trade rejected: Insufficient { 'cash' if action=='buy' else 'shares' }")

# Check stops
def check_stop_loss(ticker, current_price):
    pos = portfolio['positions'][ticker]
    if pos['shares'] > 0 and current_price < pos['avg_price'] * (1 - CONFIG['stop_loss_pct']):
        execute_trade(ticker, 'sell', current_price, pos['shares'])
        print(f"STOP-LOSS triggered for {ticker}")

# Main trading loop function
def run_paper_trade():
    now = datetime.now().time()
    if not (CONFIG['market_open'] <= now <= CONFIG['market_close']):
        print(f"Outside market hours: {now}")
        return
    
    print(f"\n--- Paper Trade Check: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
    
    # Fetch current prices
    prices = yf.download(CONFIG['tickers'], period='1d', interval='5m')['Close'].iloc[-1]
    
    # Update portfolio value
    portfolio['total_value'] = portfolio['cash']
    for ticker, pos in portfolio['positions'].items():
        if pos['shares'] > 0:
            current_price = prices[ticker]
            check_stop_loss(ticker, current_price)  # Check SL first
            portfolio['total_value'] += pos['shares'] * current_price
    
    print(f"Portfolio Value: ₹{portfolio['total_value']:.2f} (P&L: ₹{portfolio['total_value'] - CONFIG['initial_cash']:.2f})")
    
    # Generate & act on signals
    signals = get_signals()
    for ticker, signal in signals.items():
        if signal == 0:
            continue
        current_price = prices[ticker]
        pos = portfolio['positions'][ticker]
        max_shares = int((portfolio['total_value'] * CONFIG['max_position_size']) / current_price)
        
        if signal == 1 and pos['shares'] == 0:  # Buy if flat
            shares = min(max_shares, int(max_shares))  # Full size
            execute_trade(ticker, 'buy', current_price, shares)
        elif signal == -1 and pos['shares'] > 0:  # Sell if held
            execute_trade(ticker, 'sell', current_price, pos['shares'])
    
    # Export snapshot
    snapshot = {'timestamp': datetime.now().isoformat(), 'portfolio': portfolio.copy()}
    with open(f"{CONFIG['output_dir']}/portfolio_{datetime.now().strftime('%Y%m%d_%H%M')}.json", 'w') as f:
        json.dump(snapshot, f, default=str)
    pd.DataFrame(portfolio['trades']).to_csv(f"{CONFIG['output_dir']}/trades.csv", index=False)

# Plot equity curve (run manually or post-session)
def plot_equity_curve():
    trades_df = pd.DataFrame(portfolio['trades'])
    if trades_df.empty:
        return
    trades_df['cumulative_value'] = trades_df['value'].cumsum() + CONFIG['initial_cash']
    plt.figure(figsize=(10, 5))
    plt.plot(trades_df['timestamp'], trades_df['cumulative_value'])
    plt.title('Paper Trading Equity Curve')
    plt.xlabel('Time')
    plt.ylabel('Portfolio Value (₹)')
    plt.savefig(f"{CONFIG['output_dir']}/equity_curve.png")
    plt.close()
    print("Equity plot saved.")

# Scheduler
schedule.every(CONFIG['check_interval_min']).minutes.do(run_paper_trade)

# Run loop
if __name__ == "__main__":
    print("Starting Paper Trading Engine...")
    print(f"Strat: {CONFIG['strat']} | Tickers: {CONFIG['tickers']} | Initial Cash: ₹{CONFIG['initial_cash']}")
    run_paper_trade()  # Initial run
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check scheduler every min