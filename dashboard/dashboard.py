import streamlit as st
import pandas as pd
import json
import os
import glob
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np

# Config
OUTPUT_DIR = 'output'
STRATS = ['ma_crossover', 'mean_reversion', 'momentum', 'screener']

@st.cache_data(ttl=30)  # Cache for 30s
def load_data(strat=None):
    """Load portfolio, trades, and strat-specific data."""
    # Portfolio: Latest JSON snapshot
    json_files = glob.glob(f"{OUTPUT_DIR}/portfolio_*.json")
    if json_files:
        latest_json = max(json_files, key=os.path.getctime)
        with open(latest_json, 'r') as f:
            snapshot = json.load(f)
        portfolio = snapshot['portfolio']
    else:
        portfolio = {'cash': 100000, 'positions': {}, 'total_value': 100000, 'trades': []}
    
    # Trades CSV
    trades_df = pd.read_csv(f"{OUTPUT_DIR}/trades.csv") if os.path.exists(f"{OUTPUT_DIR}/trades.csv") else pd.DataFrame()
    
    # Strat-specific: Load signals CSV or run quick fetch
    if strat == 'screener':
        # Run quick Nifty screener (adapt from screener.py)
        import sys
        sys.path.append('..')  # Assuming parent dir has screener.py
        from screener.screener import nifty_50_tickers  # Hypothetical import; adjust
        # Or hardcoded fetch
        data = yf.download(['TCS.NS', 'INFY.NS'], period='1d')  # Placeholder
        screener_df = pd.DataFrame({'Ticker': ['TCS.NS'], 'ROE (%)': [45.2], 'Beta': [0.85]})
    else:
        signals_csv = glob.glob(f"{OUTPUT_DIR}/signals_*.csv")
        screener_df = pd.read_csv(signals_csv[0]) if signals_csv else pd.DataFrame()
    
    # Plot files
    plot_files = glob.glob(f"{OUTPUT_DIR}/*plot.png")
    
    return portfolio, trades_df, screener_df, plot_files

# Sidebar: Controls
st.sidebar.title("Dashboard Controls")
selected_strat = st.sidebar.selectbox("Select Strategy", STRATS)
refresh = st.sidebar.button("Refresh Data")
if refresh:
    st.cache_data.clear()

# Main Header
st.title("🛡️ STONKS Algo Trading Dashboard")
st.subheader(f"Strategy: {selected_strat} | Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")

# Load data
portfolio, trades_df, signals_df, plot_files = load_data(selected_strat)

# 1. Portfolio Overview (Metrics)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Value", f"₹{portfolio['total_value']:.2f}")
col2.metric("Cash", f"₹{portfolio['cash']:.2f}")
col3.metric("P&L", f"₹{portfolio['total_value'] - 100000:.2f}", delta=f"{((portfolio['total_value']/100000 - 1)*100):.1f}%")
col4.metric("Positions", len([p for p in portfolio['positions'].values() if p['shares'] > 0]))

# Positions Table
if portfolio['positions']:
    pos_df = pd.DataFrame.from_dict(portfolio['positions'], orient='index')
    pos_df['Value'] = pos_df['shares'] * [yf.Ticker(t.split('.')[0]).info.get('regularMarketPrice', 0) for t in pos_df.index]  # Approx current price
    st.subheader("Current Positions")
    st.dataframe(pos_df)

# 2. Recent Trades Table
st.subheader("Recent Trades")
if not trades_df.empty:
    trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'])
    trades_df = trades_df.sort_values('timestamp', ascending=False).head(20)
    st.dataframe(trades_df, use_container_width=True)
else:
    st.info("No trades yet. Run paper trader!")

# 3. Equity Curve Plot
st.subheader("Equity Curve")
if not trades_df.empty:
    trades_df['cumulative'] = trades_df['value'].cumsum() + 100000
    fig = px.line(trades_df, x='timestamp', y='cumulative', title="Portfolio Growth")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No equity data. Accumulate trades first.")

# 4. Strategy Signals & Plot
st.subheader(f"{selected_strat.upper()} Signals")
if not signals_df.empty:
    st.dataframe(signals_df.head(10))
    
    # Display latest plot
    strat_plot = [p for p in plot_files if selected_strat in p.lower()]
    if strat_plot:
        st.image(strat_plot[0], caption=f"{selected_strat} Plot")
else:
    if selected_strat == 'screener':
        st.dataframe(signals_df)  # Blue chips table
    else:
        st.warning("Run strategy script to generate signals.")

# Footer
st.sidebar.markdown("---")
st.sidebar.info("Powered by Streamlit | Integrate with paper_trader.py outputs.")