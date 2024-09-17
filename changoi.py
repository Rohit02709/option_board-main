# import all important libraries
from nselib import derivatives
from nselib import capital_market
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import pandas as pd
import streamlit as st
import time

# Initialize global variables to store captured data
if 'data_capture' not in st.session_state:
    st.session_state.data_capture = []
if 'time_stops' not in st.session_state:
    st.session_state.time_stops = []

# Function to capture data
def capture_data(index, exp):
    try:
        option = derivatives.nse_live_option_chain(index, exp)
        o = option[['CALLS_OI', 'CALLS_Chng_in_OI', 'CALLS_LTP', 'Strike_Price', 'PUTS_LTP', 'PUTS_Chng_in_OI', 'PUTS_OI']].set_index('Strike_Price')
        
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

        # Generate signals
        def generate_signal(row):
            if row['PUTS_Chng_in_OI'] > row['CALLS_Chng_in_OI'] * 2:
                return "BUY CE"
            elif row['CALLS_Chng_in_OI'] > row['PUTS_Chng_in_OI'] * 2:
                return "BUY PE"
            else:
                return "HOLD"
        oi['Signal'] = oi.apply(generate_signal, axis=1)

        # Append data to capture list
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for _, row in oi.iterrows():
            st.session_state.data_capture.append([
                timestamp, row['CALLS_LTP'], row['CALLS_OI'], row['CALLS_Chng_in_OI'], 
                row['PUTS_LTP'], row['PUTS_OI'], row['PUTS_Chng_in_OI'], row['Signal']
            ])
        # Add current time stop
        st.session_state.time_stops.append([timestamp, "Captured"])
    except Exception as e:
        st.text(f"An error occurred: {e}")

# add title of the web-app
st.title(':red[NSE] **Option Dashboard**')
st.header('Option Analysis', divider='rainbow')
# create some tabs for option analysis
tab1, tab2, tab3, tab4 = st.tabs(["Option Chain", "OI Analysis", "Ratio Strategy", "OI-based Buy/Sell Signal"])
# create side bar to select index instrument and for expiry day selection
index = st.sidebar.selectbox("Select index name", ('NIFTY', "BANKNIFTY", "FINNIFTY"))
ex = st.sidebar.selectbox('Select expiry date', derivatives.expiry_dates_option_index()[index])
exp = datetime.strptime(ex, '%d-%b-%Y').strftime('%d-%m-%Y')

# Capture data every 3 minutes
capture_data(index, exp)

# Tab 1: Option Chain
with tab1:
    st.subheader('Option Chain')
    try:
        option = derivatives.nse_live_option_chain(index, exp)
        o = option[['CALLS_OI', 'CALLS_Chng_in_OI', 'CALLS_LTP', 'Strike_Price', 'PUTS_LTP', 'PUTS_Chng_in_OI', 'PUTS_OI']].set_index('Strike_Price')
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
        st.table(oi.style.highlight_max(axis=0, subset=['CALLS_OI', 'PUTS_OI', 'CALLS_Chng_in_OI', 'PUTS_Chng_in_OI']))
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
    df_capture = pd.DataFrame(
        st.session_state.data_capture, 
        columns=['Time', 'CALLS_LTP', 'CALLS_OI', 'CALLS_Chng_in_OI', 'PUTS_LTP', 'PUTS_OI', 'PUTS_Chng_in_OI', 'Signal']
    )
    # Display the signal table
    st.table(df_capture.style.applymap(
        lambda val: 'color: green' if val == 'BUY CE' else 'color: red' if val == 'BUY PE' else 'color: black',
        subset=['Signal']
    ))
    
    # Display the time stop table
    df_stops = pd.DataFrame(st.session_state.time_stops, columns=['Time', 'Stop Reason'])
    st.write("**Time Stops**")
    st.table(df_stops)

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
