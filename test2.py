from nselib import derivatives
from nselib import capital_market
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import pandas as pd
import streamlit as st
import time
import pytz  # Handling Indian time zone

# Add title of the web-app
st.title(':red[NSE] **Option Dashboard**')
st.header('Option Analysis', divider='rainbow')

# Initialize Indian timezone
indian_tz = pytz.timezone('Asia/Kolkata')

# Tabs for different option analyses
tab1, tab2, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "Option Chain", "OI Analysis", "OI-based Buy/Sell Signal", "Signal History", "Enhanced OI-based Buy/Sell Signal", "OI Change Alert", "Market Watch"
])

# Sidebar for index instrument and expiry date selection
index = st.sidebar.selectbox("Select index name", ('NIFTY', "BANKNIFTY", "FINNIFTY"))
ex = st.sidebar.selectbox('Select expiry date', derivatives.expiry_dates_option_index()[index])
exp = datetime.strptime(ex, '%d-%b-%Y').strftime('%d-%m-%Y')

# Extracting data from nselib
try:
    option = derivatives.nse_live_option_chain(index, exp)

    # Renaming and reformatting columns for better readability
    o = option[['CALLS_OI', 'CALLS_Chng_in_OI', 'CALLS_LTP', 'Strike_Price', 'PUTS_LTP', 'PUTS_Chng_in_OI', 'PUTS_OI']].set_index('Strike_Price')
    o.rename(columns={
        'CALLS_OI': 'CE_OI',
        'CALLS_Chng_in_OI': 'CE_CHG_OI',
        'CALLS_LTP': 'CE_LTP',
        'PUTS_OI': 'PE_OI',
        'PUTS_Chng_in_OI': 'PE_CHG_OI',
        'PUTS_LTP': 'PE_LTP'
    }, inplace=True)

    # Adding time column formatted as hh:mm
    current_time = datetime.now(indian_tz).strftime('%H:%M')
    o['Time'] = current_time

    # Spot price and range setup for analysis
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

    # Tab 1: Option Chain display
    with tab1:
        st.subheader('Option Chain')
        st.table(oi.style.highlight_max(axis=0, subset=['CE_OI', 'PE_OI', 'CE_CHG_OI', 'PE_CHG_OI']))

    # Tab 2: OI Analysis with ATM strikes, additional columns (CE_LTP, PE_LTP)
    with tab2:
        st.subheader('Open Interest Analysis')

        # Finding ATM strike and filtering strikes around ATM
        atm_strike = oi.index.get_loc(min(oi.index, key=lambda x: abs(x - cmp)))
        strikes_above_below_atm = list(oi.index[max(0, atm_strike - 5):min(len(oi), atm_strike + 6)])

        oi_atm_filtered = oi.loc[strikes_above_below_atm]
        oi_atm_filtered['CE_LTP'] = oi['CE_LTP']
        oi_atm_filtered['PE_LTP'] = oi['PE_LTP']
        oi_atm_filtered['Time'] = current_time

        # Plotting OI and OI Change
        fig, ax = plt.subplots(2, 2, figsize=(12, 8))
        ax[0, 0].bar(oi_atm_filtered.index, oi_atm_filtered['CE_OI'], color='blue', width=10)
        ax[0, 1].bar(oi_atm_filtered.index, oi_atm_filtered['PE_OI'], color='red', width=10)
        ax[1, 0].bar(oi_atm_filtered.index, oi_atm_filtered['CE_CHG_OI'], 
                     color=['green' if v > 0 else 'red' for v in oi_atm_filtered['CE_CHG_OI']], width=10)
        ax[1, 1].bar(oi_atm_filtered.index, oi_atm_filtered['PE_CHG_OI'], 
                     color=['green' if v > 0 else 'red' for v in oi_atm_filtered['PE_CHG_OI']], width=10)

        st.pyplot(fig)

        # Display the filtered table with OI, OI Change, CE_LTP, PE_LTP, and Time
        def color_positive_negative(val):
            color = 'green' if val > 0 else 'red' if val < 0 else 'black'
            return f'color: {color}'

        st.table(oi_atm_filtered[['CE_OI', 'CE_CHG_OI', 'CE_LTP', 'PE_OI', 'PE_CHG_OI', 'PE_LTP', 'Time']].style.applymap(
            color_positive_negative, subset=['CE_CHG_OI', 'PE_CHG_OI']))

    # Tab 4: OI-based Buy/Sell Signal generation
    with tab4:
        st.subheader('OI-based Buy/Sell Signal')
        
        def generate_signal(row):
            if row['PE_CHG_OI'] > row['CE_CHG_OI'] * 2:
                return "BUY CE"
            elif row['CE_CHG_OI'] > row['PE_CHG_OI'] * 2:
                return "BUY PE"
            else:
                return "HOLD"

        oi['Signal'] = oi.apply(generate_signal, axis=1)
        oi_top_5 = oi.reindex(oi[['CE_CHG_OI', 'PE_CHG_OI']].abs().sum(axis=1).sort_values(ascending=False).index).head(18)

        st.table(oi_top_5[['CE_OI', 'CE_CHG_OI', 'CE_LTP', 'PE_OI', 'PE_CHG_OI', 'PE_LTP', 'Signal']].style.applymap(
            lambda val: 'color: green' if val == 'BUY CE' else 'color: red' if val == 'BUY PE' else 'color: black', subset=['Signal']))

    # Tab 5: Signal History
    with tab5:
        st.subheader('Signal History')

        if 'signal_history' not in st.session_state:
            st.session_state.signal_history = pd.DataFrame(columns=[
                'Strike_Price', 'CE_OI', 'CE_CHG_OI', 'CE_LTP', 'PE_OI', 'PE_CHG_OI', 'PE_LTP', 'Signal', 'Time'
            ])

        current_signals = oi[['CE_OI', 'CE_CHG_OI', 'CE_LTP', 'PE_OI', 'PE_CHG_OI', 'PE_LTP', 'Signal', 'Time']].copy()
        current_signals['Strike_Price'] = current_signals.index

        st.session_state.signal_history = pd.concat([st.session_state.signal_history, current_signals], ignore_index=True)

        st.dataframe(
            st.session_state.signal_history.style.applymap(
                lambda val: 'color: green' if 'BUY CE' in val else 'color: red' if 'BUY PE' in val else 'color: black', subset=['Signal']
            ), use_container_width=True
        )

        csv = st.session_state.signal_history.to_csv(index=False)
        st.download_button(label="Download Signal History", data=csv, file_name='signal_history.csv', mime='text/csv')

    # Adding metrics: Spot price and PCR (Put-Call Ratio)
    st.write(index)
    col1, col2 = st.columns(2)
    col1.metric('**Spot price**', cmp)
    pcr = np.round(o.PE_OI.sum() / o.CE_OI.sum(), 2)
    col2.metric('**PCR:**', pcr)

    # Tab 6: Enhanced OI-based Buy/Sell Signal with more data points
    with tab6:
        st.subheader('Enhanced OI-based Buy/Sell Signal')
        st.write("Future enhancement can include data points like volume, IV, and trade activity to refine signals.")

except Exception as e:
    st.error(f'Error: {str(e)}')

# Tab 7: Market Watch for all NSE Indices
with tab7:
    st.subheader('Market Watch - All Indices')

    # Fetch all indices data
    try:
        indices_data = capital_market.market_watch_all_indices()

        # Display the data
        st.dataframe(indices_data.style.highlight_max(axis=0), use_container_width=True)
    except Exception as e:
        st.error(f"Error fetching indices data: {str(e)}")
