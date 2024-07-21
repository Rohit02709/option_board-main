import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import datetime

st.title('Institutional Moves Detector and Backtester')

# Nifty 50 stock symbols
nifty50_symbols = [
    'ADANIPORTS.NS', 'ASIANPAINT.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS',
    'BAJAJFINSV.NS', 'BHARTIARTL.NS', 'BPCL.NS', 'CIPLA.NS', 'COALINDIA.NS', 'DIVISLAB.NS',
    'DRREDDY.NS', 'EICHERMOT.NS', 'GRASIM.NS', 'HCLTECH.NS', 'HDFC.NS', 'HDFCBANK.NS',
    'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS',
    'INDUSINDBK.NS', 'INFY.NS', 'IOC.NS', 'ITC.NS', 'JSWSTEEL.NS', 'KOTAKBANK.NS', 'LT.NS',
    'M&M.NS', 'MARUTI.NS', 'NESTLEIND.NS', 'NTPC.NS', 'ONGC.NS', 'POWERGRID.NS',
    'RELIANCE.NS', 'SBILIFE.NS', 'SBIN.NS', 'SHREECEM.NS', 'SUNPHARMA.NS', 'TATAMOTORS.NS',
    'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'ULTRACEMCO.NS', 'UPL.NS', 'WIPRO.NS', 'NSEI^'
]

# Sidebar for input
st.sidebar.header('User Input')
ticker = st.sidebar.selectbox('Select Stock Ticker', nifty50_symbols)
timeframe = st.sidebar.selectbox('Select Timeframe', ['15m', '1d', '1wk', '1mo'])
start_date = st.sidebar.date_input('Start Date', pd.to_datetime('2022-01-01'))
end_date = st.sidebar.date_input('End Date', pd.to_datetime('today'))


# Fetch data
def fetch_data(ticker, start_date, end_date, interval='1d'):
    return yf.download(ticker, start=start_date, end=end_date, interval=interval)


data = fetch_data(ticker, start_date, end_date, interval=timeframe)

# Handle missing data
data.dropna(inplace=True)


# Calculate VWAP
def calculate_vwap(data):
    q = data['Volume'].values
    p = data['Close'].values
    vwap = (p * q).cumsum() / q.cumsum()
    return vwap


data['VWAP'] = calculate_vwap(data)

# Calculate average volume over a period (e.g., 20 days)
data['Average Volume'] = data['Volume'].rolling(window=20).mean()

# Handle NaNs in Average Volume
data['Average Volume'].fillna(method='bfill', inplace=True)

# Identify unusual volume spikes
data['Unusual Volume'] = data['Volume'] > 2 * data['Average Volume']

# Handle NaNs in Unusual Volume
data['Unusual Volume'].fillna(False, inplace=True)


# Backtest Strategy
def backtest(data):
    signals = data['Unusual Volume'].shift(1)  # Signal occurs on the previous day
    data['Signal'] = signals
    data['Daily Return'] = data['Close'].pct_change()
    data['Strategy Return'] = data['Daily Return'] * data['Signal']
    return data


backtested_data = backtest(data)

# Calculate cumulative returns
backtested_data['Cumulative Market Return'] = (1 + backtested_data['Daily Return']).cumprod()
backtested_data['Cumulative Strategy Return'] = (1 + backtested_data['Strategy Return']).cumprod()


# Forecast Prices
def forecast_prices(data, periods=5):
    model = ExponentialSmoothing(data['Close'], trend='add', seasonal=None)
    fit = model.fit()
    forecast = fit.forecast(periods)
    return forecast


forecast = forecast_prices(data)
forecast_index = pd.date_range(start=data.index[-1], periods=len(forecast) + 1, closed='right')

# Plotting
fig, ax = plt.subplots(4, 1, figsize=(14, 18))

# Plot Close Price and VWAP
ax[0].plot(data.index, data['Close'], label='Close Price')
ax[0].plot(data.index, data['VWAP'], label='VWAP', color='orange')
ax[0].set_title(f'{ticker} - Price and VWAP Analysis')
ax[0].legend()

# Plot Volume and Average Volume
ax[1].bar(data.index, data['Volume'], label='Volume', color='grey')
ax[1].plot(data.index, data['Average Volume'], label='20-day Average Volume', color='orange')
ax[1].scatter(data.index, data['Volume'], label='Unusual Volume', color='red', s=data['Unusual Volume'] * 50)
ax[1].set_title(f'{ticker} - Volume Analysis')
ax[1].legend()

# Plot Cumulative Returns
ax[2].plot(backtested_data.index, backtested_data['Cumulative Market Return'], label='Market Return', color='blue')
ax[2].plot(backtested_data.index, backtested_data['Cumulative Strategy Return'], label='Strategy Return', color='green')
ax[2].set_title(f'{ticker} - Cumulative Returns')
ax[2].legend()

# Plot Forecast
ax[3].plot(data.index, data['Close'], label='Close Price')
ax[3].plot(forecast_index, forecast, label='Forecast', color='green', linestyle='--')
ax[3].set_title(f'{ticker} - Forecast')
ax[3].legend()

# Display the plot
st.pyplot(fig)

# Display performance metrics
total_trades = backtested_data['Signal'].sum()
winning_trades = (backtested_data['Strategy Return'] > 0).sum()
losing_trades = (backtested_data['Strategy Return'] < 0).sum()
win_rate = winning_trades / total_trades if total_trades > 0 else 0

st.subheader('Performance Metrics')
st.write(f'Total Trades: {total_trades}')
st.write(f'Winning Trades: {winning_trades}')
st.write(f'Losing Trades: {losing_trades}')
st.write(f'Win Rate: {win_rate:.2%}')

# Capital Management
capital = 20000
num_stocks = len(nifty50_symbols)  # Assuming you are considering all stocks in Nifty 50
investment_per_stock = capital / num_stocks

# Display Capital Allocation
st.subheader('Capital Allocation')
st.write(f'Total Capital: Rs {capital}')
st.write(f'Number of Stocks: {num_stocks}')
st.write(f'Investment per Stock: Rs {investment_per_stock:.2f}')


# Swing Trading Strategy
# Ensure 'Buy Signal' is boolean and handle NaN values
def swing_trade_signals(data):
    data = data.copy()
    data['Unusual Volume'].fillna(False, inplace=True)
    data['Close'].fillna(method='ffill', inplace=True)
    data['VWAP'].fillna(method='ffill', inplace=True)

    # Ensure that buy_signals is boolean
    buy_signals = (data['Unusual Volume'] & (data['Close'] > data['VWAP'])).astype(bool)
    # Ensure buy_signals does not contain NaNs
    buy_signals.fillna(False, inplace=True)
    data['Buy Signal'] = buy_signals.shift(1)  # Signal occurs on the previous day
    return data

swing_data = swing_trade_signals(data)

# Ensure 'Buy Signal' is boolean and handle NaN values before filtering
swing_data['Buy Signal'].fillna(False, inplace=True)

# Tab Interface
tab1, tab2, tab3 = st.tabs(["Analysis", "Trading Signals", "Institutional Analysis"])

with tab1:
    st.subheader(f'{ticker} - Analysis')
    st.pyplot(fig)

with tab2:
    st.subheader(f'{ticker} - Swing Trade Signals')

    # Display Swing Trade Signals
    st.write(swing_data[['Close', 'VWAP', 'Buy Signal']].dropna())

    # Buy price and hold period
    buy_signals = swing_data[swing_data['Buy Signal']].dropna()
    st.write("Buy Signals:")
    st.write(buy_signals[['Close', 'VWAP']])
    hold_period = 5  # Define hold period for swing trades
    st.write(f"Suggested Hold Period: {hold_period} days")

with tab3:
    st.subheader(f'{ticker} - Institutional Investor Analysis')

    # Sample Institutional Investor Data Display
    st.write("FII and DII data not available for this example.")
    st.write("To analyze FII and DII data, upload your data file or fetch it from sources like Moneycontrol.")
