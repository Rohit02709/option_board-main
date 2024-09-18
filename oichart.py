from nselib import derivatives
from nselib import capital_market
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import pandas as pd
import streamlit as st
import time

# Add title of the web-app
st.title(':red[NSE] **Option Dashboard**')
st.header('Option Analysis', divider='rainbow')

# Create some tabs for option analysis
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Option Chain", "OI Analysis", "Ratio Strategy", "OI-based Buy/Sell Signal", "Simple OI Table"])

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
    current_time = datetime.now().strftime('%H:%M')
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

    # Tab 5: Simple OI Table (New Tab for attached format with chart)
    with tab5:
        st.subheader('OI Change Analysis')

        # Create a chart for Call OI and Put OI with increase/decrease indication
        fig, ax = plt.subplots(figsize=(10, 6))

        strike_prices = oi.index
        ce_oi = oi['CE_OI']
        pe_oi = oi['PE_OI']

        # Plot Call OI and Put OI bars
        ax.bar(strike_prices, ce_oi, color=np.where(oi['CE_CHG_OI'] > 0, 'red', 'pink'), width=50, label='Call OI')
        ax.bar(strike_prices, pe_oi, color=np.where(oi['PE_CHG_OI'] > 0, 'green', 'lightgreen'), width=25, label='Put OI')

        # Customize the chart
        ax.set_xlabel('Strike Price')
        ax.set_ylabel('Call / Put OI')
        ax.set_title(f'OI Change on {datetime.now().strftime("%a, %d %b")}')
        ax.legend()

        # Adding time slider for future implementation (you can dynamically adjust OI timeframe)
        st.pyplot(fig)

        # Display additional metrics
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
