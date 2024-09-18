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
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Option Chain", "OI Analysis", "Ratio Strategy", "OI-based Buy/Sell Signal", "OI Table + Chart"])

# Create side bar to select index instrument and for expiry day selection
index = st.sidebar.selectbox("Select index name", ('NIFTY', "BANKNIFTY", "FINNIFTY"))
ex = st.sidebar.selectbox('Select expiry date', derivatives.expiry_dates_option_index()[index])
exp = datetime.strptime(ex, '%d-%b-%Y').strftime('%d-%m-%Y')

# Extracting data from nselib library
try:
    option = derivatives.nse_live_option_chain(index, exp)

    # Rename columns and add time column (hh:mm AM/PM format)
    o = option[['CALLS_OI', 'CALLS_Chng_in_OI', 'CALLS_LTP', 'Strike_Price', 'PUTS_LTP', 'PUTS_Chng_in_OI', 'PUTS_OI']].set_index('Strike_Price')
    o.rename(columns={
        'CALLS_OI': 'CE_OI',
        'CALLS_Chng_in_OI': 'CE_CHG_OI',
        'CALLS_LTP': 'CE_LTP',
        'PUTS_OI': 'PE_OI',
        'PUTS_Chng_in_OI': 'PE_CHG_OI',
        'PUTS_LTP': 'PE_LTP'
    }, inplace=True)
    
    # Add time column formatted as hh:mm AM/PM
    current_time = datetime.now().strftime('%I:%M %p')
    o['Time'] = current_time
    
    # Calculating spot price and filtering strikes 5 above and below ATM
    if index == 'NIFTY':
        cmp = capital_market.market_watch_all_indices().set_index('index').loc['NIFTY 50', 'last']
        atm_strike = int(np.round(cmp / 50.0) * 50)  # Rounding to nearest strike
    elif index == 'BANKNIFTY':
        cmp = capital_market.market_watch_all_indices().set_index('index').loc['NIFTY BANK', 'last']
        atm_strike = int(np.round(cmp / 100.0) * 100)
    else:
        cmp = capital_market.market_watch_all_indices().set_index('index').loc['NIFTY FINANCIAL SERVICES', 'last']
        atm_strike = int(np.round(cmp / 50.0) * 50)
    
    # Filter for 5 strikes above and below ATM
    filtered_strikes = o.loc[atm_strike - (5 * 50):atm_strike + (5 * 50)]

    # Tab 5: OI Table + Chart
    with tab5:
        st.subheader('OI Change Analysis Around ATM Strikes')

        # Create the table for strikes
        table_data = filtered_strikes[['CE_OI', 'CE_CHG_OI', 'PE_OI', 'PE_CHG_OI', 'Time']].copy()
        table_data['CE_Increase_Decrease'] = np.where(table_data['CE_CHG_OI'] > 0, 'Increase', 'Decrease')
        table_data['PE_Increase_Decrease'] = np.where(table_data['PE_CHG_OI'] > 0, 'Increase', 'Decrease')

        # Display table
        st.write('## OI Table')
        st.dataframe(table_data.rename(columns={
            'CE_OI': 'Call OI',
            'CE_CHG_OI': 'Call OI Change',
            'PE_OI': 'Put OI',
            'PE_CHG_OI': 'Put OI Change',
            'Time': 'Time (hh:mm AM/PM)',
            'CE_Increase_Decrease': 'Call OI Change Type',
            'PE_Increase_Decrease': 'Put OI Change Type'
        }))

        # Create a chart for Call OI and Put OI with increase/decrease indication
        st.write('## OI Change Chart')

        fig, ax = plt.subplots(figsize=(10, 6))

        strike_prices = filtered_strikes.index
        ce_oi = filtered_strikes['CE_OI']
        pe_oi = filtered_strikes['PE_OI']

        # Plot Call OI and Put OI bars
        ax.bar(strike_prices - 25, ce_oi, color=np.where(filtered_strikes['CE_CHG_OI'] > 0, 'red', 'pink'), width=50, label='Call OI')
        ax.bar(strike_prices + 25, pe_oi, color=np.where(filtered_strikes['PE_CHG_OI'] > 0, 'green', 'lightgreen'), width=50, label='Put OI')

        # Customize the chart
        ax.set_xlabel('Strike Price')
        ax.set_ylabel('Call / Put OI')
        ax.set_title(f'OI Change on {datetime.now().strftime("%a, %d %b")}')
        ax.legend()

        # Display chart
        st.pyplot(fig)

        # Display additional metrics
        col1, col2 = st.columns(2)
        col1.metric('**Spot price**', cmp)
        pcr = np.round(filtered_strikes['PE_OI'].sum() / filtered_strikes['CE_OI'].sum(), 2)
        col2.metric('**PCR:**', pcr)

except Exception as e:
    st.text(f"An error occurred: {e}")

# Refresh every 3 minutes
time.sleep(180)  # Wait for 180 seconds
st.experimental_rerun()  # Re-run the script to refresh the data
