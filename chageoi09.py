# Import all important libraries
from nselib import derivatives
from nselib import capital_market
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import streamlit as st
import time
import pytz

# Initialize global variables to store captured data
if 'signal_data' not in st.session_state:
    st.session_state.signal_data = []
if 'buy_signal_data' not in st.session_state:
    st.session_state.buy_signal_data = []
if 'capture_times' not in st.session_state:
    st.session_state.capture_times = []

# Function to calculate moving average (SMA)
def calculate_moving_average(series, window):
    return series.rolling(window=window).mean()

# Function to capture buy/sell signals with added suggestions
def capture_signals(index, exp):
    try:
        option = derivatives.nse_live_option_chain(index, exp)
        o = option[['CALLS_OI', 'CALLS_Chng_in_OI', 'CALLS_LTP', 'Strike_Price', 'PUTS_LTP', 'PUTS_Chng_in_OI', 'PUTS_OI']].set_index('Strike_Price')

        # Calculate the Put-Call Ratio (PCR) for confirmation
        pcr = np.round(o.PUTS_OI.sum() / o.CALLS_OI.sum(), 2)

        # Fetch the current spot price
        cmp = capital_market.market_watch_all_indices().set_index('index').loc[f'NIFTY 50' if index == 'NIFTY' else f'NIFTY {index}', 'last']
        
        # Generate signals with dynamic thresholds based on PCR
        def generate_signal(row):
            if row['PUTS_Chng_in_OI'] > row['CALLS_Chng_in_OI'] * 2 and pcr < 0.7:  # Bullish signal with low PCR
                return "BUY CE"
            elif row['CALLS_Chng_in_OI'] > row['PUTS_Chng_in_OI'] * 2 and pcr > 1.2:  # Bearish signal with high PCR
                return "BUY PE"
            else:
                return "HOLD"
        
        o['Signal'] = o.apply(generate_signal, axis=1)
        
        # Sort by the absolute value of change in OI (largest change first)
        o_sorted = o.reindex(o[['CALLS_Chng_in_OI', 'PUTS_Chng_in_OI']].abs().sum(axis=1).sort_values(ascending=False).index)
        o_top_5 = o_sorted.head(5)

        # Get current time in IST
        ist = pytz.timezone('Asia/Kolkata')
        timestamp = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')

        # Append all signals
        for _, row in o_top_5.iterrows():
            st.session_state.signal_data.append([
                timestamp, row['CALLS_LTP'], row['CALLS_OI'], row['CALLS_Chng_in_OI'], 
                row['PUTS_LTP'], row['PUTS_OI'], row['PUTS_Chng_in_OI'], row['Signal']
            ])
        
        # Filter and append only "BUY" signals
        buy_signals = o_top_5[o_top_5['Signal'].str.contains('BUY')]
        for _, row in buy_signals.iterrows():
            st.session_state.buy_signal_data.append([
                timestamp, row['CALLS_LTP'], row['CALLS_OI'], row['CALLS_Chng_in_OI'], 
                row['PUTS_LTP'], row['PUTS_OI'], row['PUTS_Chng_in_OI'], row['Signal']
            ])

        # Add current time capture
        st.session_state.capture_times.append([timestamp, "Captured"])
    except Exception as e:
        st.text(f"An error occurred: {e}")

# Function for ATR-based stop-loss and take-profit
def calculate_atr(data, period=14):
    high_low = data['High'] - data['Low']
    high_close = np.abs(data['High'] - data['Close'].shift())
    low_close = np.abs(data['Low'] - data['Close'].shift())
    true_range = np.maximum(high_low, high_close, low_close)
    atr = true_range.rolling(window=period).mean()
    return atr

# Add title of the web-app
st.title(':red[NSE] **Option Dashboard**')
st.header('Option Analysis', divider='rainbow')

# Create tabs for option analysis
tab1, tab2, tab3, tab4 = st.tabs(["Option Chain", "OI Analysis", "Ratio Strategy", "OI-based Buy/Sell Signal"])

# Create sidebar to select index instrument and expiry day
index = st.sidebar.selectbox("Select index name", ('NIFTY', "BANKNIFTY", "FINNIFTY"))
ex = st.sidebar.selectbox('Select expiry date', derivatives.expiry_dates_option_index()[index])
exp = datetime.strptime(ex, '%d-%b-%Y').strftime('%d-%m-%Y')

# Capture signals every 3 minutes
capture_signals(index, exp)

# Tab 1: Option Chain
with tab1:
    st.subheader('Option Chain')
    try:
        option = derivatives.nse_live_option_chain(index, exp)
        o = option[['CALLS_OI', 'CALLS_Chng_in_OI', 'CALLS_LTP', 'Strike_Price', 'PUTS_LTP', 'PUTS_Chng_in_OI', 'PUTS_OI']].set_index('Strike_Price')

        # Calculate spot price and set range for option analysis
        cmp = capital_market.market_watch_all_indices().set_index('index').loc[f'NIFTY 50' if index == 'NIFTY' else f'NIFTY {index}', 'last']
        range = (int(np.round(cmp / 50.0)) * 50) + 1000, (int(np.round(cmp / 50.0)) * 50) - 1000
        oi = o.loc[range[1]:range[0]]

        st.table(oi.style.format({
            'CALLS_LTP': '{:,.2f}', 'CALLS_OI': '{:,.2f}', 'CALLS_Chng_in_OI': '{:,.2f}', 
            'PUTS_LTP': '{:,.2f}', 'PUTS_OI': '{:,.2f}', 'PUTS_Chng_in_OI': '{:,.2f}'
        }).highlight_max(axis=0, subset=['CALLS_OI', 'PUTS_OI', 'CALLS_Chng_in_OI', 'PUTS_Chng_in_OI']))
    except Exception as e:
        st.text(f"An error occurred: {e}")

# Tab 2: OI Analysis
with tab2:
    st.subheader('Open Interest Analysis')
    try:
        fig, ax = plt.subplots(2, 1)
        ax[0].bar(oi.index, oi['CALLS_OI'], color='blue', width=20)
        ax[0].bar(oi.index - 10, oi['PUTS_OI'], color='red', width=20)
        ax[0].axvline(x=cmp, color='black', linestyle='--')
        ax[0].set_title('OI Position')
        ax[1].bar(oi.index, oi['CALLS_Chng_in_OI'], color='blue', width=20)
        ax[1].bar(oi.index - 10, oi['PUTS_Chng_in_OI'], color='red', width=20)
        ax[1].axvline(x=cmp, color='black', linestyle='--')
        ax[1].set_xlabel('Change in OI')
        st.pyplot(fig)
    except Exception as e:
        st.text(f"An error occurred: {e}")

# Tab 3: Ratio Strategy (unchanged)

# Tab 4: OI-based Buy/Sell Signal
with tab4:
    st.subheader('OI-based Buy/Sell Signal')

    # Create DataFrame from captured data
    df_signals = pd.DataFrame(
        st.session_state.signal_data, 
        columns=['Time', 'CALLS_LTP', 'CALLS_OI', 'CALLS_Chng_in_OI', 'PUTS_LTP', 'PUTS_OI', 'PUTS_Chng_in_OI', 'Signal']
    ).round(2)
    
    st.write("**Captured Buy/Sell Signals**")
    signal_table = df_signals.style.format({
        'CALLS_LTP': '{:,.2f}', 'CALLS_OI': '{:,.2f}', 'CALLS_Chng_in_OI': '{:,.2f}', 
        'PUTS_LTP': '{:,.2f}', 'PUTS_OI': '{:,.2f}', 'PUTS_Chng_in_OI': '{:,.2f}'
    }).applymap(
        lambda val: 'color: green' if val == 'BUY CE' else 'color: red' if val == 'BUY PE' else 'color: black',
        subset=['Signal']
    ).set_table_styles([
        dict(selector='th', props=[('text-align', 'center')]), 
        dict(selector='td', props=[('text-align', 'center')])
    ]).set_properties(**{'width': '80px'})
    
    st.write(signal_table)
