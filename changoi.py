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

# Function to capture buy/sell signals
def capture_signals(index, exp):
    try:
        option = derivatives.nse_live_option_chain(index, exp)
        o = option[['CALLS_OI', 'CALLS_Chng_in_OI', 'CALLS_LTP', 'Strike_Price', 'PUTS_LTP', 'PUTS_Chng_in_OI', 'PUTS_OI']].set_index('Strike_Price')

        # Generate signals
        def generate_signal(row):
            if row['PUTS_Chng_in_OI'] > row['CALLS_Chng_in_OI'] * 2:
                return "BUY CE"
            elif row['CALLS_Chng_in_OI'] > row['PUTS_Chng_in_OI'] * 2:
                return "BUY PE"
            else:
                return "HOLD"
        
        o['Signal'] = o.apply(generate_signal, axis=1)
        
        # Sort by the absolute value of change in OI (largest change first)
        o_sorted = o.reindex(o[['CALLS_Chng_in_OI', 'PUTS_Chng_in_OI']].abs().sum(axis=1).sort_values(ascending=False).index)
        # Select only the top 5 strikes with the most significant change in OI
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
        
        # Append only "BUY" signals
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

# Add title of the web-app
st.title(':red[NSE] **Option Dashboard**')
st.header('Option Analysis', divider='rainbow')

# Create some tabs for option analysis
tab1, tab2, tab3, tab4 = st.tabs(["Option Chain", "OI Analysis", "Ratio Strategy", "OI-based Buy/Sell Signal"])

# Create sidebar to select index instrument and for expiry day selection
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

        # Calculating spot price and setting up range for option analysis
        if index == 'NIFTY':
            cmp = capital_market.market_watch_all_indices().set_index('index').loc['NIFTY 50', 'last']
            range = (int(np.round(cmp / 50.0)) * 50) + 1000, (int(np.round(cmp / 50.0)) * 50) - 1000
            oi = o.loc[range[1]:range[0]]
        elif index == 'BANKNIFTY':
            cmp = capital_market.market_watch_all_indices().set_index('index').loc['NIFTY BANK', 'last']
            range = (int(np.round(cmp / 100.0)) * 100) + 1500, (int(np.round(cmp / 100.0)) * 100) - 1500
            oi = o.loc[range[1]:range[0]]
        else:
            cmp = capital_market.market_watch_all_indices().set_index('index').loc['NIFTY FINANCIAL SERVICES', 'last']
            range = (int(np.round(cmp / 50.0)) * 50) + 900, (int(np.round(cmp / 50.0)) * 50) - 900
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

# Tab 3: Ratio Strategy (This part remains unchanged)
# Continue with the same code for Ratio Strategy

# Tab 4: OI-based Buy/Sell Signal
with tab4:
    st.subheader('OI-based Buy/Sell Signal')

    # Create DataFrame from captured data
    df_signals = pd.DataFrame(
        st.session_state.signal_data, 
        columns=['Time', 'CALLS_LTP', 'CALLS_OI', 'CALLS_Chng_in_OI', 'PUTS_LTP', 'PUTS_OI', 'PUTS_Chng_in_OI', 'Signal']
    ).round(2)
    
    # Display the signal table
    st.write("**Captured Buy/Sell Signals**")
    signal_table = df_signals.style.format({
        'CALLS_LTP': '{:,.2f}', 'CALLS_OI': '{:,.2f}', 'CALLS_Chng_in_OI': '{:,.2f}', 
        'PUTS_LTP': '{:,.2f}', 'PUTS_OI': '{:,.2f}', 'PUTS_Chng_in_OI': '{:,.2f}'
    }).applymap(
        lambda val: 'color: green' if val == 'BUY CE' else 'color: red' if val == 'BUY PE' else 'color: black',
        subset=['Signal']
    ).set_table_styles([
        dict(selector='th', props=[('text-align', 'center')]),  # Center-align header text
        dict(selector='td', props=[('text-align', 'center')])   # Center-align cell text
    ]).set_properties(**{'width': '100px'})  # Adjust column width

    st.table(signal_table)

    # Create DataFrame from captured buy signals
    df_buy_signals = pd.DataFrame(
        st.session_state.buy_signal_data, 
        columns=['Time', 'CALLS_LTP', 'CALLS_OI', 'CALLS_Chng_in_OI', 'PUTS_LTP', 'PUTS_OI', 'PUTS_Chng_in_OI', 'Signal']
    ).round(2)

    # Display the buy signal table
    st.write("**Captured Buy Signals Only**")
    buy_signal_table = df_buy_signals.style.format({
        'CALLS_LTP': '{:,.2f}', 'CALLS_OI': '{:,.2f}', 'CALLS_Chng_in_OI': '{:,.2f}', 
        'PUTS_LTP': '{:,.2f}', 'PUTS_OI': '{:,.2f}', 'PUTS_Chng_in_OI': '{:,.2f}'
    }).applymap(
        lambda val: 'color: green' if val == 'BUY CE' else 'color: red' if val == 'BUY PE' else 'color: black',
        subset=['Signal']
    ).set_table_styles([
        dict(selector='th', props=[('text-align', 'center')]),  # Center-align header text
        dict(selector='td', props=[('text-align', 'center')])   # Center-align cell text
    ]).set_properties(**{'width': '100px'})  # Adjust column width
    
    st.table(buy_signal_table)
    
    # Display the time capture table
    df_times = pd.DataFrame(st.session_state.capture_times, columns=['Time', 'Reason'])
    st.write("**Capture Times**")
    time_capture_table = df_times.style.set_table_styles([
        dict(selector='th', props=[('text-align', 'center')]),  # Center-align header text
        dict(selector='td', props=[('text-align', 'center')])   # Center-align cell text
    ]).set_properties(**{'width': '150px'})  # Adjust column width
    
    st.table(time_capture_table)

# Adding additional metrics: Spot price and PCR (Put-Call Ratio)
try:
    st.write(index)
    col1, col2 = st.columns(2)
    col1.metric('**Spot price**', cmp)
    pcr = np.round(o.PUTS_OI.sum() / o.CALLS_OI.sum(), 2)
    col2.metric('**PCR:**', pcr)
except Exception as e:
    st.text(f"An error occurred: {e}")

# Refresh every 3 minutes
time.sleep(180)  # Wait for 180 seconds (3 minutes)
st.experimental_rerun()  # Re-run the script to refresh the data
