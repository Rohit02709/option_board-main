from nselib import derivatives
from nselib import capital_market
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import pandas as pd
import streamlit as st
import time
import pytz  # New import for handling Indian time zone
# from nselib import greeks

# Add title of the web-app
st.title(':red[NSE] **Option Dashboard**')
st.header('Option Analysis', divider='rainbow')

# Initialize Indian timezone
indian_tz = pytz.timezone('Asia/Kolkata')  # Set Indian Time Zone

# Create some tabs for option analysis
tab1, tab2, tab4, tab5, tab6 = st.tabs([
    "Option Chain", "OI Analysis", "OI-based Buy/Sell Signal", "Signal History", "Enhanced OI-based Buy/Sell Signal"
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

    # Tab 1: Option Chain
    with tab1:
        st.subheader('Option Chain')
        st.table(oi.style.highlight_max(axis=0, subset=['CE_OI', 'PE_OI', 'CE_CHG_OI', 'PE_CHG_OI']))

    # Tab 2: OI Analysis with additional columns for Time, CE_LTP, and PE_LTP
    with tab2:
        st.subheader('Open Interest Analysis')

        # Identify ATM (At-The-Money) strike
        atm_strike = oi.index.get_loc(min(oi.index, key=lambda x: abs(x - cmp)))  # Closest strike to current market price
        strikes_above_below_atm = list(oi.index[max(0, atm_strike - 5):min(len(oi), atm_strike + 6)])  # 5 strikes above and below ATM

        # Filter the dataframe to only include these strikes
        oi_atm_filtered = oi.loc[strikes_above_below_atm]

        # Add columns for CE_LTP, PE_LTP, and Time
        oi_atm_filtered['CE_LTP'] = oi.loc[oi_atm_filtered.index, 'CE_LTP']
        oi_atm_filtered['PE_LTP'] = oi.loc[oi_atm_filtered.index, 'PE_LTP']
        oi_atm_filtered['Time'] = current_time

        # Plot OI and OI change for 5 strikes above and below ATM in separate subplots
        fig, ax = plt.subplots(2, 2, figsize=(12, 8))

        ax[0, 0].bar(oi_atm_filtered.index, oi_atm_filtered['CE_OI'], color='blue', width=10)
        ax[0, 0].axvline(x=cmp, color='black', linestyle='--', label='Spot Price')
        ax[0, 0].set_title('Call OI')
        ax[0, 1].bar(oi_atm_filtered.index, oi_atm_filtered['PE_OI'], color='red', width=10)
        ax[0, 1].axvline(x=cmp, color='black', linestyle='--', label='Spot Price')
        ax[0, 1].set_title('Put OI')

        ax[1, 0].bar(oi_atm_filtered.index, oi_atm_filtered['CE_CHG_OI'], 
                     color=['green' if v > 0 else 'red' for v in oi_atm_filtered['CE_CHG_OI']], width=10)
        ax[1, 1].bar(oi_atm_filtered.index, oi_atm_filtered['PE_CHG_OI'], 
                     color=['green' if v > 0 else 'red' for v in oi_atm_filtered['PE_CHG_OI']], width=10)

        # Show plots
        st.pyplot(fig)

        # Display the filtered table with OI, OI Change, CE_LTP, PE_LTP, and Time
        oi_atm_filtered_table = oi_atm_filtered[['CE_OI', 'CE_CHG_OI', 'CE_LTP', 'PE_OI', 'PE_CHG_OI', 'PE_LTP', 'Time']].copy()

        # Apply color formatting for OI changes
        def color_positive_negative(val):
            color = 'green' if val > 0 else 'red' if val < 0 else 'black'
            return f'color: {color}'

        # Display the table with conditional formatting
        st.table(oi_atm_filtered_table.style.applymap(color_positive_negative, subset=['CE_CHG_OI', 'PE_CHG_OI']))

    # Tab 4: OI-based Buy/Sell Signal (unchanged)
    with tab4:
        st.subheader('OI-based Buy/Sell Signal')

        def generate_signal(row):
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

        # Create signal_table and include CE_LTP and PE_LTP columns
        signal_table = oi_top_5[['CE_OI', 'CE_CHG_OI', 'CE_LTP', 'PE_OI', 'PE_CHG_OI', 'PE_LTP', 'Signal']].style.applymap(
            lambda val: 'color: green' if val == 'BUY CE' else 'color: red' if val == 'BUY PE' else 'color: black',
            subset=['Signal']
        )
        st.table(signal_table)

    # Tab 5: Signal History with Time, CE_LTP, PE_LTP, and Color Coding
    with tab5:
        st.subheader('Signal History')
    
        # Initialize signal history if it doesn't exist
        if 'signal_history' not in st.session_state:
            st.session_state.signal_history = pd.DataFrame(columns=[
                'Strike_Price', 'CE_OI', 'CE_CHG_OI', 'CE_LTP', 'PE_OI', 'PE_CHG_OI', 'PE_LTP', 'Signal', 'Time'
            ])
    
        # Generate current signals
        current_signals = oi[['CE_OI', 'CE_CHG_OI', 'CE_LTP', 'PE_OI', 'PE_CHG_OI', 'PE_LTP', 'Signal', 'Time']].copy()
        current_signals['Strike_Price'] = current_signals.index
    
        # Append new signals to the history
        st.session_state.signal_history = pd.concat([st.session_state.signal_history, current_signals], ignore_index=True)
    
        # Display the updated signal history DataFrame with color coding
        st.dataframe(
            st.session_state.signal_history.style.applymap(
                lambda val: 'color: green' if 'BUY CE' in val else 'color: red' if 'BUY PE' in val else 'color: black',
                subset=['Signal']
            ),
            use_container_width=True  # This adjusts the table width based on the container width
        )
    
        # Add download button for the CSV file
        csv = st.session_state.signal_history.to_csv(index=False)
        st.download_button(
            label="Download Signal History",
            data=csv,
            file_name='signal_history.csv',
            mime='text/csv'
        )


    # Adding additional metrics: Spot price and PCR (Put-Call Ratio)
    st.write(index)
    col1, col2 = st.columns(2)
    col1.metric('**Spot price**', cmp)
    pcr = np.round(o.PE_OI.sum() / o.CE_OI.sum(), 2)
    col2.metric('**PCR:**', pcr)
    
    # Tab 6: Enhanced OI-based Buy/Sell Signal (moved from Tab 4)
  # Tab 6: Enhanced OI-based Buy/Sell Signal (moved from Tab 4)
    with tab6:
        st.subheader('Enhanced OI-based Buy/Sell Signal')
    
        # Fetch option data
        oi = fetch_data()
    
        if oi is not None:
            # Additional parameters like volume, IV, etc.
            if 'CALLS_volume' in option.columns and 'PUTS_volume' in option.columns:
                option_volume = option['CALLS_volume'] + option['PUTS_volume']  # Assuming volume data is available
                oi['Volume'] = option_volume
            else:
                oi['Volume'] = 0  # Default value if volume data is missing
    
            if 'Implied_Volatility' in option.columns:
                iv = option['Implied_Volatility']  # Assuming IV data is available
                oi['Implied_Volatility'] = iv
            else:
                oi['Implied_Volatility'] = 0  # Default value if IV data is missing
    
            # Calculate Put/Call Ratio (PCR)
            oi['PCR'] = oi['PE_OI'] / oi['CE_OI']
    
            # Option Greeks (Currently commented out; you can uncomment if needed later)
            # greeks_data = greeks.get_option_greeks(index, exp)
            # oi['Delta'] = greeks_data['Delta']
            # oi['Gamma'] = greeks_data['Gamma']
            # oi['Theta'] = greeks_data['Theta']
            # oi['Vega'] = greeks_data['Vega']
    
            # Adjusted enhanced signal logic with lower thresholds for intraday trading
            def enhanced_signal(row):
                """
                Enhanced Signal Generation based on OI change, Volume, and IV.
                Thresholds adjusted for intraday trading.
                """
                if row['PE_CHG_OI'] > row['CE_CHG_OI'] * 2 and row['Volume'] > 500 and row['Implied_Volatility'] > 15:
                    return "STRONG BUY CE"
                elif row['CE_CHG_OI'] > row['PE_CHG_OI'] * 2 and row['Volume'] > 500 and row['Implied_Volatility'] > 15:
                    return "STRONG BUY PE"
                else:
                    return "HOLD"
    
            # Apply the enhanced signal generation logic
            oi['Enhanced_Signal'] = oi.apply(enhanced_signal, axis=1)
    
            # Sort based on Volume and IV for more relevant entries
            oi_sorted = oi.sort_values(by=['Volume', 'Implied_Volatility'], ascending=False).head(10)
    
            # Display the resulting table
            st.table(
                oi_sorted[['CE_OI', 'CE_CHG_OI', 'CE_LTP', 'PE_OI', 'PE_CHG_OI', 'PE_LTP', 'Volume', 'Implied_Volatility', 'Enhanced_Signal']]
                .style.applymap(lambda val: 'color: green' if 'BUY' in val else 'color: black', subset=['Enhanced_Signal'])
            )
        else:
            st.error("Error fetching option data")



except Exception as e:
    st.error(f"An error occurred: {e}")
# Refresh every 3 minutes
time.sleep(180)  # Wait for 180 seconds
st.experimental_rerun()  # Re-run the script to refresh the data
