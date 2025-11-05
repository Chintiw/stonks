import yfinance as yf
import pandas as pd

# Latest Nifty 50 constituents (as of Nov 4, 2025; update if needed via NSE site)
nifty_50_tickers = [
    'RELIANCE.NS', 'HDFCBANK.NS', 'BHARTIARTL.NS', 'TCS.NS', 'ICICIBANK.NS',
    'SBIN.NS', 'BAJFINANCE.NS', 'INFY.NS', 'HINDUNILVR.NS', 'LT.NS',
    'ITC.NS', 'MARUTI.NS', 'M&M.NS', 'KOTAKBANK.NS', 'HCLTECH.NS',
    'SUNPHARMA.NS', 'AXISBANK.NS', 'ULTRACEMCO.NS', 'BAJAJFINSV.NS', 'TITAN.NS',
    'NTPC.NS', 'ONGC.NS', 'ADANIPORTS.NS', 'ZOMATO.NS', 'BEL.NS',
    'JSWSTEEL.NS', 'ADANIENT.NS', 'POWERGRID.NS', 'WIPRO.NS', 'BAJAJ-AUTO.NS',
    'NESTLEIND.NS', 'ASIANPAINT.NS', 'COALINDIA.NS', 'TATASTEEL.NS', 'INDIGO.NS',
    'SBILIFE.NS', 'GRASIM.NS', 'JIOFIN.NS', 'EICHERMOT.NS', 'HINDALCO.NS',
    'TRENT.NS', 'HDFCLIFE.NS', 'TATAMOTORS.NS', 'SHRIRAMFIN.NS', 'TECHM.NS',
    'CIPLA.NS', 'TATACONSUM.NS', 'APOLLOHOSP.NS', 'MAXHEALTH.NS', 'DRREDDY.NS'
]

# Screen results
results = []

for ticker in nifty_50_tickers:
    try:
        stock = yf.Ticker(ticker)
        info = stock.info  # Fetches latest fundamentals
        
        # Extract key metrics
        net_income = info.get('netIncomeToCommon', 0)  # In actual currency units (INR)
        roe = info.get('returnOnEquity', 0) * 100  # Convert to percentage
        beta = info.get('beta', float('inf'))  # Market beta
        
        # Apply filters
        if net_income > 0 and roe > 15 and beta < 1:
            results.append({
                'Ticker': ticker,
                'ROE (%)': round(roe, 2),
                'Beta': round(beta, 2),
                'Net Income (₹ Cr)': round(net_income / 1e7, 2)  # Convert to Crores for readability
            })
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        continue

# Display results as a table
if results:
    df = pd.DataFrame(results)
    print("Low-Risk Blue Chip Stocks (Nifty 50 Screen):")
    print(df.to_string(index=False))
else:
    print("No stocks matched the criteria today. Try adjusting thresholds!")