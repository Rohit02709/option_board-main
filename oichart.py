# Import necessary libraries
from nselib import derivatives
from nselib import capital_market
import matplotlib.pyplot as plt
from datetime import datetime
import pytz  # New import for handling Indian time zone
import numpy as np
import pandas as pd
import streamlit as st
import time

# Add title of the web-app
st.title(':red[NSE] **Option Dashboard**')
st.header('Option Analysis', divider='rainbow')

# Initialize Indian timezone
indian_tz = pytz.timezone('Asia/Kolkata')  # Set Indian Time Zone

# Create some tabs for option analysis
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Option Chain", "OI Analysis", "Ratio Strategy", "OI-based Buy/Sell Signal", "Signal History"])

# Create side bar to select index instrument and for expiry day selection
index = st.sidebar.selectbox("Select index name", ('NIFTY', "BANKNIFTY", "FINNIFTY"))
ex = st.sidebar.selectbox('Select expiry date', derivatives.expiry_dates_option_index()[index])
exp = datetime.strptime(ex, '%d-%b-%Y').strftime('%d-%m-%Y')

# Extracting data from nselib library
try:
    option = derivatives.nse_live_option_chain(index, exp)

    # Rename columns and add time column (IST time zone, hh:mm format)
    o = option[['CALLS_OI', 'CALLS_Chng_in_OI', 'CALLS_LTP', 'Strike_Price', 'PUTS_LTP', 'PUTS_Chng_in_OI', 'PUTS_OI']].set_index('Strike_Price')
    o.rename(columns={
        'CALLS_OI': 'CE_OI',
        'CALLS_Chng_in_OI': 'CE_CHG_OI',
        'CALLS_LTP': 'CE_LTP',
        'PUTS_OI': 'PE_OI',
        'PUTS_Chng_in_OI': 'PE_CHG_OI',
        'PUTS_LTP': 'PE_LTP'
    }, inplace=True)

    # Get current time in Indian Standard Time
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

    # Tab 1: Option Chain
    with tab1:
        st.subheader('Option Chain')
        st.table(oi.style.highlight_max(axis=0, subset=['CE_OI', 'PE_OI', 'CE_CHG_OI', 'PE_CHG_OI']))

    # Tab 2: OI Analysis
    with tab2:
        st.subheader('Open Interest Analysis')

        # Identify ATM (At-The-Money) strike
        atm_strike = oi.index.get_loc(min(oi.index, key=lambda x: abs(x - cmp)))  # Closest strike to current market price
        strikes_above_below_atm = list(oi.index[max(0, atm_strike - 5):min(len(oi), atm_strike + 6)])  # 5 strikes above and below ATM

        # Filter the dataframe to only include these strikes
        oi_atm_filtered = oi.loc[strikes_above_below_atm]

        # Plot OI and OI change for 5 strikes above and below ATM in separate subplots
        fig, ax = plt.subplots(2, 2, figsize=(12, 8))  # 2x2 grid for Call and Put OI and changes

        # Bar plot for Call OI (Left Column)
        ax[0, 0].bar(oi_atm_filtered.index, oi_atm_filtered['CE_OI'], color='blue', width=10)
        ax[0, 0].axvline(x=cmp, color='black', linestyle='--', label='Spot Price')
        ax[0, 0].set_title('Call OI')
        ax[0, 0].set_xlabel('Strike Price')
        ax[0, 0].set_ylabel('Open Interest')
        ax[0, 0].legend()

        # Bar plot for Put OI (Right Column)
        ax[0, 1].bar(oi_atm_filtered.index, oi_atm_filtered['PE_OI'], color='red', width=10)
        ax[0, 1].axvline(x=cmp, color='black', linestyle='--', label='Spot Price')
        ax[0, 1].set_title('Put OI')
        ax[0, 1].set_xlabel('Strike Price')
        ax[0, 1].set_ylabel('Open Interest')
        ax[0, 1].legend()

        # Bar plot for Call OI Change (Bottom Left)
        ax[1, 0].bar(oi_atm_filtered.index, oi_atm_filtered['CE_CHG_OI'], 
                     color=['green' if v > 0 else 'red' for v in oi_atm_filtered['CE_CHG_OI']], width=10)
        ax[1, 0].axvline(x=cmp, color='black', linestyle='--', label='Spot Price')
        ax[1, 0].set_title('Call OI Change')
        ax[1, 0].set_xlabel('Strike Price')
        ax[1, 0].set_ylabel('OI Change')
        ax[1, 0].legend()

        # Bar plot for Put OI Change (Bottom Right)
        ax[1, 1].bar(oi_atm_filtered.index, oi_atm_filtered['PE_CHG_OI'], 
                     color=['green' if v > 0 else 'red' for v in oi_atm_filtered['PE_CHG_OI']], width=10)
        ax[1, 1].axvline(x=cmp, color='black', linestyle='--', label='Spot Price')
        ax[1, 1].set_title('Put OI Change')
        ax[1, 1].set_xlabel('Strike Price')
        ax[1, 1].set_ylabel('OI Change')
        ax[1, 1].legend()

        # Adjust the layout for better spacing
        plt.tight_layout()

        # Display the plots
        st.pyplot(fig)

        # Display OI table with color formatting for OI changes
        st.table(oi_atm_filtered[['CE_OI', 'CE_CHG_OI', 'PE_OI', 'PE_CHG_OI']].style.applymap(
            lambda val: 'color: green' if val > 0 else 'color: red' if val < 0 else 'color: black'))

    # Tab 4: OI-based Buy/Sell Signal
    with tab4:
        st.subheader('OI-based Buy/Sell Signal')

        def generate_signal(row):
            """
            Function to generate buy/sell signals based on OI change.
            Buy CE: Significant increase in PE OI or decrease in CE OI
            Buy PE: Significant increase in CE OI or decrease in PE OI
            """
            if row['PE_CHG_OI'] > row['CE_CHG_OI'] * 2:
                return "BUY CE"
            elif row['CE_CHG_OI'] > row['PE_CHG_OI'] * 2:
                return "BUY PE"
            else:
                return "HOLD"

        # Apply the signal generation function
        oi['Signal'] = oi.apply(generate_signal, axis=1)

        # Sort by the absolute value of change in OI (largest change first)
        oi_sorted = oi.reindex(oi[['CE_CHG_OI', 'PE_CHG_OI']].abs().sum(axis=1).sort_values(ascending=False).index)

        # Select only the top 5 strikes with the most significant change in OI
        oi_top_5 = oi_sorted.head(9)

        # Display the table with buy/sell signals
        st.table(oi_top_5[['CE_OI', 'CE_CHG_OI', 'CE_LTP', 'PE_OI', 'PE_CHG_OI', 'PE_LTP', 'Signal']].style.applymap(
            lambda val: 'color: green' if val == 'BUY CE' else 'color: red' if val == 'BUY PE' else 'color: black',
            subset=['Signal']
        ))

        # Storing signals in session state for history tracking
        if 'signal_history' not in st.session_state:
            st.session_state.signal_history = pd.DataFrame(columns=['Strike_Price', 'CE_OI', 'CE_CHG_OI', 'PE_OI', 'PE_CHG_OI', 'Signal', 'Time'])

        # Append the new signal data to the signal history DataFrame
        st.session_state.signal_history = pd.concat([st.session_state.signal_history, oi_top_5.reset_index()[['Strike_Price', 'CE_OI', 'CE_CHG_OI', 'PE_OI', 'PE_CHG_OI', 'Signal', 'Time']]])

    # Tab 5: Signal History
    with tab5:
        st.subheader('Signal History')
        # Display signal history
        st.dataframe(st.session_state.signal_history)

    # Adding additional metrics: Spot price and PCR (Put-Call Ratio)
    st.write(index)
    col1, col2 = st.columns(2)
    col1.metric('**Spot price**', cmp)
    pcr = np.round(o.PE_OI.sum() / o.CE_OI.sum(), 2)
    col2.metric('**PCR:**', pcr)

except Exception as e:
    st.text(f"An error occurred: {e}")

# Refresh every 3 minutes
time.sleep(180)  # Wait for 180 seconds
st.experimental_rerun()  # Re-run the script to refresh the data
