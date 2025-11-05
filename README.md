# STONKS: Minimal Algo Trading System

**Overview**: Beginner NSE/BSE algo system with screener, strats (MA Crossover, Mean Reversion, Momentum), paper trading, and Streamlit dashboard. Dockerized.

## Quick Start
```bash
git clone https://github.com/yourusername/stonks.git
cd stonks
docker-compose up --build  # Runs all
```

- **Screener**: `python screener/screener.py` → Blue chips CSV.
- **Strats**: `python <strat>/<strat>.py` → Backtest/plot.
- **Paper Trader**: `cd paper-trader && docker-compose up` → Sim trades.
- **Dashboard**: `cd dashboard && streamlit run dashboard.py` → localhost:8501.

## Structure
```
STONKS/
├── [strat]/          # ma_crossover, mean_rev, momentum, screener
│   ├── *.py
│   ├── Dockerfile
│   └── docker-compose.yml
├── paper-trader/     # Simulation engine
├── dashboard/        # Streamlit UI
└── output/           # Shared CSVs/plots
```

## Features
- **Screener**: Nifty 50 filter (ROE>15%, Beta<1).
- **Strats**: Backtest signals; ~5-15% hyp. returns.
- **Paper Trader**: 5min checks, ₹1L start, fees/slippage.
- **Dashboard**: P&L metrics, trades table, equity plot.

## Deps
- Python: `pip install yfinance pandas numpy matplotlib schedule streamlit plotly`
- Docker: Compose for all.

