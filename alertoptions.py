from nselib import derivatives
from nselib import capital_market
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import pandas as pd
import streamlit as st

# Add title of the web-app
st.title(':red[NSE] **Option Dashboard**')
st.header('Option Analysis')

# Create some tabs for option analysis
tab1, tab2, tab3, tab4 = st.tabs(["Option Chain", "OI", "Ratio Strategy", "Alerts"])

# Create sidebar to select index instrument and expiry date
index = st.sidebar.selectbox("Select index name", ('NIFTY', "BANKNIFTY", "FINNIFTY"))
ex = st.sidebar.selectbox('Select expiry date', derivatives.expiry_dates_option_index()[index])
exp = datetime.strptime(ex, '%d-%b-%Y').strftime('%d-%m-%Y')

# Extracting data from nselib library
try:
    option = derivatives.nse_live_option_chain(index, exp)
    o = option[['CALLS_OI', 'CALLS_Chng_in_OI', 'CALLS_LTP', 'Strike_Price', 'PUTS_LTP', 'PUTS_Chng_in_OI', 'PUTS_OI']].set_index('Strike_Price')
    st.write("Option Chain Data:", o)

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
    st.write("Filtered OI Data:", oi)

    with tab1:
        st.subheader('Option Chain')
        st.table(oi.style.highlight_max(axis=0, subset=['CALLS_OI', 'PUTS_OI', 'CALLS_Chng_in_OI', 'PUTS_Chng_in_OI']))

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

    def calculate_vwap(df):
        df['VWAP'] = (df['CALLS_LTP'] * df['CALLS_OI'] + df['PUTS_LTP'] * df['PUTS_OI']) / (df['CALLS_OI'] + df['PUTS_OI'])
        return df

    def calculate_rsi(df, window=14):
        delta = df['CALLS_LTP'].diff()
        gain = (delta.where(delta > 0, 0)).fillna(0)
        loss = (-delta.where(delta < 0, 0)).fillna(0)
        avg_gain = gain.rolling(window=window, min_periods=1).mean()
        avg_loss = loss.rolling(window=window, min_periods=1).mean()
        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))
        return df

    def filter_strikes(df, cmp, avg_vol, avg_oi):
        df['Volume'] = df['CALLS_OI'] + df['PUTS_OI']
        df['Avg_Volume'] = avg_vol
        df['Avg_OI'] = avg_oi
        st.write("Data with VWAP and RSI:", df)

        conditions_met = df[(df['CALLS_LTP'] > df['VWAP']) &
                            (df['Volume'] > 1.5 * df['Avg_Volume']) &
                            (df['RSI'] > 60) &
                            (df['CALLS_OI'] < df['Avg_OI']) &
                            (abs(df['CALLS_OI'] - df['Avg_OI']) > 0.01 * df['Avg_OI'])]
        st.write("Conditions Met:", conditions_met)

        itm_calls = conditions_met[conditions_met.index > cmp].head(7)
        itm_puts = conditions_met[conditions_met.index < cmp].tail(7)
        return pd.concat([itm_calls, itm_puts])

    o = calculate_vwap(o)
    o = calculate_rsi(o)

    average_volume = o['CALLS_OI'].rolling(window=20).mean()
    average_oi = o['CALLS_OI'].rolling(window=20).mean()

    valid_strikes = filter_strikes(o, cmp, average_volume, average_oi)
    st.write("Valid Strikes:", valid_strikes)

    with tab3:
        st.subheader('Ratio Spread Strategy')
        st.table(valid_strikes)

    with tab4:
        st.subheader('Alerts Based on Conditions')
        st.table(valid_strikes)

    st.write(index)
    col1, col2 = st.columns(2)
    col1.metric('**Spot Price**', cmp)
    pcr = np.round(o.PUTS_OI.sum() / o.CALLS_OI.sum(), 2)
    col2.metric('**PCR:**', pcr)

    # Display buy price and strike price
    if not valid_strikes.empty:
        best_strike = valid_strikes.loc[valid_strikes['CALLS_LTP'].idxmax()]
        buy_price = best_strike['CALLS_LTP']
        strike_price = best_strike.name

        st.write("**Buy Price:**", buy_price)
        st.write("**Strike Price:**", strike_price)
    else:
        st.write("No valid strikes found for the alert conditions.")

except Exception as e:
    st.text(f'Please select accurate expiry date. Error: {e}')
