from nselib import derivatives
from nselib import capital_market
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import pandas as pd
import streamlit as st
import time
import pytz  # For handling Indian timezone
# from nselib import greeks

# Add title of the web-app
st.title(':red[NSE] **Option Dashboard**')
st.header('Option Analysis', divider='rainbow')

# Initialize Indian timezone
indian_tz = pytz.timezone('Asia/Kolkata')  # Set Indian Time Zone

# Create some tabs for option analysis
tab1, tab2, tab4, tab5, tab6, tab7 = st.tabs([
    "Option Chain", "OI Analysis", "OI-based Buy/Sell Signal", "Signal History", 
    "Enhanced OI-based Buy/Sell Signal", "Virtual Trading Terminal"
])

# Create side bar to select index instrument and for expiry day selection
index = st.sidebar.selectbox("Select index name", ('NIFTY', "BANKNIFTY", "FINNIFTY"))
ex = st.sidebar.selectbox('Select expiry date', derivatives.expiry_dates_option_index()[index])
exp = datetime.strptime(ex, '%d-%b-%Y').strftime('%d-%m-%Y')

# Extracting data from nselib library
try:
    option = derivatives.nse_live_option_chain(index, exp)

    # Rename columns and add time column (hh:mm format)
    o = option[['CALLS_OI', 'CALLS_Chng_in_OI', 'CALLS_LTP', 'Strike_Price', 'PUTS_LTP', 'PUTS_Chng_in_OI', 'PUTS_OI']].set_index('Strike_Price')
    o.rename(columns={
        'CALLS_OI': 'CE_OI',
        'CALLS_Chng_in_OI': 'CE_CHG_OI',
        'CALLS_LTP': 'CE_LTP',
        'PUTS_OI': 'PE_OI',
        'PUTS_Chng_in_OI': 'PE_CHG_OI',
        'PUTS_LTP': 'PE_LTP'
    }, inplace=True)

    # Add time column formatted as hh:mm
    current_time = datetime.now(indian_tz).strftime('%H:%M')
    o['Time'] = current_time

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

    # ---- Signal Generation (For Trading) ----
    # Example signal generation logic (can be customized)
    def generate_signal(row):
        # Example conditions for buy/sell signals
        if row['CE_CHG_OI'] > 0 and row['CE_LTP'] > row['CE_LTP'].shift(1):  # Buy CE signal condition
            return 'BUY CE'
        elif row['PE_CHG_OI'] > 0 and row['PE_LTP'] > row['PE_LTP'].shift(1):  # Buy PE signal condition
            return 'BUY PE'
        elif row['CE_CHG_OI'] < 0 and row['CE_LTP'] < row['CE_LTP'].shift(1):  # Sell CE signal condition
            return 'SELL CE'
        elif row['PE_CHG_OI'] < 0 and row['PE_LTP'] < row['PE_LTP'].shift(1):  # Sell PE signal condition
            return 'SELL PE'
        return 'NO SIGNAL'  # Default when no condition is met

    # Apply signal generation
    oi['Signal'] = oi.apply(generate_signal, axis=1)

    # Tab 7: Virtual Trading Terminal
    with tab7:
        st.subheader('Virtual Trading Terminal')

        # Allow user to define capital
        capital = st.sidebar.number_input('Enter Capital Amount', value=1000000)

        # Lot sizes based on index
        lot_size = 25 if index in ['NIFTY', 'FINNIFTY'] else 15

        # Define a function to execute virtual trades
        def execute_trade(signal, cmp, lot_size):
            entry_price = cmp
            target_price = entry_price + np.random.uniform(10, 30)  # Target range: 10-30 points
            stop_loss_price = entry_price - 10  # Initial stop loss set at 10 points below entry price

            trade = {
                'Signal': signal,
                'Entry_Price': entry_price,
                'Target_Price': target_price,
                'Stop_Loss_Price': stop_loss_price,
                'Lot_Size': lot_size,
                'Status': 'Open'  # Trade is active
            }

            return trade

        # Initialize trading session state
        if 'trades' not in st.session_state:
            st.session_state.trades = []

        # Execute trades based on OI signals
        for _, row in oi.iterrows():
            signal = row['Signal']
            if signal in ['BUY CE', 'BUY PE']:
                st.session_state.trades.append(execute_trade(signal, cmp, lot_size))

        # Display current open trades
        st.write("## Current Open Trades")
        open_trades_df = pd.DataFrame([trade for trade in st.session_state.trades if trade['Status'] == 'Open'])
        st.table(open_trades_df)

        # Function to simulate the price movements and check for target or stop loss
        def update_trades():
            for trade in st.session_state.trades:
                # Simulate current price movement (could use real-time data in production)
                current_price = cmp + np.random.uniform(-5, 5)  # Random price movement

                # Check if the target or stop-loss is hit
                if current_price >= trade['Target_Price']:
                    trade['Status'] = 'Target Hit'
                elif current_price <= trade['Stop_Loss_Price']:
                    trade['Status'] = 'Stop Loss Hit'
                else:
                    # Trail the stop loss to maintain 10 points distance from current price
                    trade['Stop_Loss_Price'] = max(trade['Stop_Loss_Price'], current_price - 10)

        # Button to manually refresh and update trade status
        if st.button("Update Trades"):
            update_trades()

        # Display closed trades
        st.write("## Closed Trades")
        closed_trades_df = pd.DataFrame([trade for trade in st.session_state.trades if trade['Status'] != 'Open'])
        st.table(closed_trades_df)

except Exception as e:
    st.error(f"An error occurred: {e}")

# Refresh every 3 minutes
time.sleep(180)  # Wait for 180 seconds
st.experimental_rerun()  # Re-run the script to refresh the data
