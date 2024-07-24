import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import datetime

st.title('Positional Trading Strategy with Backtesting')

# Nifty 50 stock symbols
nifty50_symbols = [
    'ADANIPORTS.NS', 'ASIANPAINT.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS',
    'BAJAJFINSV.NS', 'BHARTIARTL.NS', 'BPCL.NS', 'CIPLA.NS', 'COALINDIA.NS', 'DIVISLAB.NS',
    'DRREDDY.NS', 'EICHERMOT.NS', 'GRASIM.NS', 'HCLTECH.NS', 'HDFC.NS', 'HDFCBANK.NS',
    'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS',
    'INDUSINDBK.NS', 'INFY.NS', 'IOC.NS', 'ITC.NS', 'JSWSTEEL.NS', 'KOTAKBANK.NS', 'LT.NS',
    'M&M.NS', 'MARUTI.NS', 'NESTLEIND.NS', 'NTPC.NS', 'ONGC.NS', 'POWERGRID.NS',
    'RELIANCE.NS', 'SBILIFE.NS', 'SBIN.NS', 'SHREECEM.NS', 'SUNPHARMA.NS', 'TATAMOTORS.NS',
    'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'ULTRACEMCO.NS', 'UPL.NS', 'WIPRO.NS'
]

# Sidebar for input
st.sidebar.header('User Input')
tickers = st.sidebar.multiselect('Select Stock Tickers', nifty50_symbols, default=nifty50_symbols[:5])
timeframe = st.sidebar.selectbox('Select Timeframe', ['1d', '1wk', '1mo'])
start_date = st.sidebar.date_input('Start Date', pd.to_datetime('2022-01-01'))
end_date = st.sidebar.date_input('End Date', pd.to_datetime('today'))


# Fetch data
def fetch_data(ticker, start_date, end_date, interval='1d'):
    return yf.download(ticker, start=start_date, end=end_date, interval=interval)


# Calculate VWAP
def calculate_vwap(data):
    q = data['Volume'].values
    p = data['Close'].values
    vwap = (p * q).cumsum() / q.cumsum()
    return vwap


# Backtest Strategy
def backtest(data):
    signals = data['Unusual Volume'].shift(1)  # Signal occurs on the previous day
    data['Signal'] = signals
    data['Daily Return'] = data['Close'].pct_change()
    data['Strategy Return'] = data['Daily Return'] * data['Signal']
    data['Cumulative Market Return'] = (1 + data['Daily Return']).cumprod()
    data['Cumulative Strategy Return'] = (1 + data['Strategy Return']).cumprod()
    return data


# Swing Trading Signals
def swing_trade_signals(data):
    data = data.copy()
    data['Unusual Volume'].fillna(False, inplace=True)
    data['Close'].fillna(method='ffill', inplace=True)
    data['VWAP'].fillna(method='ffill', inplace=True)
    buy_signals = (data['Unusual Volume'] & (data['Close'] > data['VWAP'])).astype(bool)
    buy_signals.fillna(False, inplace=True)
    data['Buy Signal'] = buy_signals.shift(1)  # Signal occurs on the previous day
    return data


# Predict target holding period
def predict_holding_period(data):
    buy_signals = data[data['Buy Signal']]
    holding_periods = []
    for idx in buy_signals.index:
        buy_price = data.loc[idx, 'Close']
        target_price = buy_price * 1.05
        future_prices = data.loc[idx:]['Close']
        days_to_target = (future_prices >= target_price).idxmax() - idx
        holding_periods.append(days_to_target.days)
    if holding_periods:
        return int(np.mean(holding_periods))
    else:
        return 20  # Default to 20 days if no historical signals


# Forecast Prices
def forecast_prices(data, periods=5):
    model = ExponentialSmoothing(data['Close'], trend='add', seasonal=None)
    fit = model.fit()
    forecast = fit.forecast(periods)
    return forecast


# Tab Interface
tab1, tab2, tab3, tab4 = st.tabs(["Analysis", "Trading Signals", "Institutional Analysis", "Stock Screener"])

with tab1:
    st.subheader('Analysis')
    for ticker in tickers:
        data = fetch_data(ticker, start_date, end_date, interval='1d')
        if data.empty:
            continue

        # Calculate indicators
        data['VWAP'] = calculate_vwap(data)
        data['Average Volume'] = data['Volume'].rolling(window=20).mean()
        data['Average Volume'].fillna(method='bfill', inplace=True)
        data['Unusual Volume'] = data['Volume'] > 2 * data['Average Volume']
        data['Unusual Volume'].fillna(False, inplace=True)

        # Backtest and Forecast
        backtested_data = backtest(data)
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
        ax[2].plot(backtested_data.index, backtested_data['Cumulative Market Return'], label='Market Return',
                   color='blue')
        ax[2].plot(backtested_data.index, backtested_data['Cumulative Strategy Return'], label='Strategy Return',
                   color='green')
        ax[2].set_title(f'{ticker} - Cumulative Returns')
        ax[2].legend()

        # Plot Forecast
        ax[3].plot(data.index, data['Close'], label='Close Price')
        ax[3].plot(forecast_index, forecast, label='Forecast', color='green', linestyle='--')
        ax[3].set_title(f'{ticker} - Forecast')
        ax[3].legend()

        st.pyplot(fig)

with tab2:
    st.subheader('Trading Signals')
    for ticker in tickers:
        data = fetch_data(ticker, start_date, end_date, interval='1d')
        if data.empty:
            continue

        # Calculate indicators
        data['VWAP'] = calculate_vwap(data)
        data['Average Volume'] = data['Volume'].rolling(window=20).mean()
        data['Average Volume'].fillna(method='bfill', inplace=True)
        data['Unusual Volume'] = data['Volume'] > 2 * data['Average Volume']
        data['Unusual Volume'].fillna(False, inplace=True)

        swing_data = swing_trade_signals(data)
        swing_data['Buy Signal'].fillna(False, inplace=True)

        # Display Swing Trade Signals
        st.write(f'*{ticker} - Swing Trade Signals*')
        st.write(swing_data[['Close', 'VWAP', 'Buy Signal']].dropna())
        buy_signals = swing_data[swing_data['Buy Signal']].dropna()
        st.write("Buy Signals:")
        st.write(buy_signals[['Close', 'VWAP']])
        hold_period = predict_holding_period(swing_data)  # Predict hold period for swing trades
        st.write(f"Suggested Hold Period: {hold_period} days")

with tab3:
    st.subheader('Institutional Analysis')
    st.write("Institutional analysis tab is under construction.")

with tab4:
    st.subheader('Stock Screener')

    screener_data = []

    for symbol in nifty50_symbols:
        data = fetch_data(symbol, start_date, end_date, interval='1d')
        if data.empty:
            continue

        # Ensure 'Unusual Volume' and 'VWAP' are calculated
        data['VWAP'] = calculate_vwap(data)
        data['Average Volume'] = data['Volume'].rolling(window=20).mean()
        data['Average Volume'].fillna(method='bfill', inplace=True)
        data['Unusual Volume'] = data['Volume'] > 2 * data['Average Volume']
        data['Unusual Volume'].fillna(False, inplace=True)

        swing_data = swing_trade_signals(data)
        swing_data['Buy Signal'].fillna(False, inplace=True)

        if swing_data['Buy Signal'].any():
            recent_signal = swing_data[swing_data['Buy Signal']].tail(1)
            if not recent_signal.empty:
                last_signal_date = recent_signal.index[-1]
                buy_price = recent_signal['Close'].values[0]
                holding_target = buy_price * 1.05  # Assuming a 5% holding target
                current_price = data['Close'][-1]
                target_achieved = current_price >= holding_target
                profit_loss = (current_price - buy_price) * 20  # Qty = 20
                screener_data.append({
                    'Symbol': symbol,
                    'Buy Signal Date': last_signal_date,
                    'Buy Price': buy_price,
                    'Holding Target': holding_target,
                    'Current Price': current_price,
                    'Qty': 20,
                    'Profit/Loss': profit_loss,
                    'Target Achieved': target_achieved
                })

    screener_df = pd.DataFrame(screener_data,
                               columns=['Symbol', 'Buy Signal Date', 'Buy Price', 'Holding Target', 'Current Price',
                                        'Qty', 'Profit/Loss', 'Target Achieved'])
    st.write("Stocks with Active Buy Signals:")
    st.write(screener_df)
