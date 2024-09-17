# Import all important libraries
from nselib import derivatives
from nselib import capital_market
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import pandas as pd
import streamlit as st

# Add title of the web-app
st.title(':red[NSE] **Option Dashboard**')
st.header('Option Analysis', divider='rainbow')

# Create some tabs for option analysis
tab1, tab2, tab3, tab4 = st.tabs(["Option Chain", "OI Analysis", "Ratio Strategy", "OI-based Buy/Sell Signal"])

# Create sidebar to select index instrument and for expiry day selection
index = st.sidebar.selectbox("Select index name", ('NIFTY', "BANKNIFTY", "FINNIFTY"))
ex = st.sidebar.selectbox('Select expiry date', derivatives.expiry_dates_option_index()[index])
exp = datetime.strptime(ex, '%d-%b-%Y').strftime('%d-%m-%Y')

# Extracting data from nselib library
try:
    option = derivatives.nse_live_option_chain(index, exp)
    o = option[['CALLS_OI', 'CALLS_Chng_in_OI', 'CALLS_LTP', 'Strike_Price', 'PUTS_LTP', 'PUTS_Chng_in_OI', 'PUTS_OI']].set_index('Strike_Price')

    # Calculating spot price and setting up range for option analysis
    if index == 'NIFTY':
        cmp = int(capital_market.market_watch_all_indices().set_index('index').loc['NIFTY 50', 'last'])
        range = (int(np.round(cmp / 50.0)) * 50) + 1000, (int(np.round(cmp / 50.0)) * 50) - 1000
        oi = o.loc[range[1]:range[0]]
    elif index == 'BANKNIFTY':
        cmp = int(capital_market.market_watch_all_indices().set_index('index').loc['NIFTY BANK', 'last'])
        range = (int(np.round(cmp / 100.0)) * 100) + 1500, (int(np.round(cmp / 100.0)) * 100) - 1500
        oi = o.loc[range[1]:range[0]]
    else:
        cmp = int(capital_market.market_watch_all_indices().set_index('index').loc['NIFTY FINANCIAL SERVICES', 'last'])
        range = (int(np.round(cmp / 50.0)) * 50) + 900, (int(np.round(cmp / 50.0)) * 50) - 900
        oi = o.loc[range[1]:range[0]]

    # Tab 1: Option Chain
    with tab1:
        st.subheader('Option Chain')
        st.table(oi.style.highlight_max(axis=0, subset=['CALLS_OI', 'PUTS_OI', 'CALLS_Chng_in_OI', 'PUTS_Chng_in_OI']))

    # Tab 2: OI Analysis
    with tab2:
        st.subheader('Open Interest Analysis')
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

    # Tab 4: OI-based Buy/Sell Signal (Intraday Signals with Enhanced Logic)
    with tab4:
        st.subheader('OI-based Buy/Sell Signal (Intraday)')

        # Calculate percentage change in OI for calls and puts
        oi['CALL_OI_%'] = ((oi['CALLS_Chng_in_OI'] / oi['CALLS_OI']) * 100).round(1)
        oi['PUT_OI_%'] = ((oi['PUTS_Chng_in_OI'] / oi['PUTS_OI']) * 100).round(1)

        def intraday_signal(row):
            """
            Updated intraday signal logic based on OI changes.
            - BUY CE: Significant PUT OI increase or CALL OI decrease for intraday trades.
            - BUY PE: Significant CALL OI increase or PUT OI decrease.
            This also incorporates minimum percentage change thresholds.
            """
            # Define thresholds for meaningful changes
            min_change_pct = 5  # Minimum percentage change in OI to trigger a signal
            
            # Case 1: Buy CE (Call Option) Signal - Significant PUT OI Increase or CALL OI Decrease
            if row['PUT_OI_%'] > min_change_pct and row['CALL_OI_%'] < -min_change_pct:
                return "BUY CE"
            
            # Case 2: Buy PE (Put Option) Signal - Significant CALL OI Increase or PUT OI Decrease
            elif row['CALL_OI_%'] > min_change_pct and row['PUT_OI_%'] < -min_change_pct:
                return "BUY PE"
            
            # Case 3: HOLD if no strong signal
            else:
                return "HOLD"

        # Apply updated intraday signals
        oi['Signal'] = oi.apply(intraday_signal, axis=1)

        # Sort by the absolute value of change in OI (largest change first)
        oi_sorted = oi.reindex(oi[['CALLS_Chng_in_OI', 'PUTS_Chng_in_OI']].abs().sum(axis=1).sort_values(ascending=False).index)

        # Select only the top 5 strikes with the most significant change in OI
        oi_top_5 = oi_sorted.head(5)

        # Reset index to avoid non-unique index issue
        oi_top_5_reset = oi_top_5.reset_index()

        # Display signals with shorter labels and percentages rounded to 
