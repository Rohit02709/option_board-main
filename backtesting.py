import pandas as pd
import streamlit as st
from datetime import datetime
import pytz
import plotly.express as px

# Add title of the web-app
st.title(':red[NSE] **Backtesting Option Dashboard**')
st.header('Backtest OI-based Signals', divider='rainbow')

# Initialize Indian timezone
indian_tz = pytz.timezone('Asia/Kolkata')  # Set Indian Time Zone

# Function to generate Buy/Sell signal based on OI changes
def generate_signal(row):
    if row['PE_CHG_OI'] > row['CE_CHG_OI'] * 2:
        return "BUY CE"
    elif row['CE_CHG_OI'] > row['PE_CHG_OI'] * 2:
        return "BUY PE"
    else:
        return "HOLD"

# Function to calculate backtest performance (win/loss)
def calculate_backtest_performance(data):
    wins, losses = 0, 0
    for index, row in data.iterrows():
        if row['Signal'] == "BUY CE":
            if row['CE_LTP'] > row['PE_LTP']:  # Assuming profit when CE LTP rises
                wins += 1
            else:
                losses += 1
        elif row['Signal'] == "BUY PE":
            if row['PE_LTP'] > row['CE_LTP']:  # Assuming profit when PE LTP rises
                wins += 1
            else:
                losses += 1
    total_trades = wins + losses
    return wins, losses, total_trades

# Upload CSV file with historical data
uploaded_file = st.file_uploader("Upload a CSV file for backtesting", type="csv")

if uploaded_file is not None:
    # Read uploaded CSV into DataFrame
    backtest_data = pd.read_csv(uploaded_file)

    # Expected columns for backtesting:
    # ['Strike_Price', 'CE_OI', 'PE_OI', 'CE_CHG_OI', 'PE_CHG_OI', 'CE_LTP', 'PE_LTP', 'Signal', 'Time']
    expected_columns = ['Strike_Price', 'CE_OI', 'PE_OI', 'CE_CHG_OI', 'PE_CHG_OI', 'CE_LTP', 'PE_LTP', 'Time']

    if all(col in backtest_data.columns for col in expected_columns):
        st.write("File uploaded successfully.")
        backtest_data['Time'] = pd.to_datetime(backtest_data['Time'])  # Convert 'Time' column to datetime

        # Generate signals on historical data
        backtest_data['Signal'] = backtest_data.apply(generate_signal, axis=1)

        # Calculate backtest performance (win/loss ratio, profit/loss)
        wins, losses, total_trades = calculate_backtest_performance(backtest_data)
        win_ratio = (wins / total_trades) * 100 if total_trades > 0 else 0

        # Display performance results
        st.write(f"Total Trades: {total_trades}")
        st.write(f"Win Ratio: {win_ratio:.2f}%")
        st.write(f"Wins: {wins}")
        st.write(f"Losses: {losses}")

        # Group data by Strike_Price and Signal for counting
        signal_counts = backtest_data.groupby(['Strike_Price', 'Signal']).size().unstack(fill_value=0)
        
        # Show strike price-wise signal count
        st.write("Strike Price-wise Signal Count:")
        st.dataframe(signal_counts)

        # Plotting the number of signals per strike price
        fig = px.bar(signal_counts.reset_index(), x='Strike_Price', y=['BUY CE', 'BUY PE'],
                     title="Signals per Strike Price",
                     labels={'value': 'Number of Signals', 'Strike_Price': 'Strike Price'},
                     barmode='group')
        st.plotly_chart(fig)

        # Display the first few rows of data with Strike_Price, Signal, and Signal Prices
        backtest_data['Signal Price'] = backtest_data.apply(lambda row: row['CE_LTP'] if row['Signal'] == "BUY CE" else (row['PE_LTP'] if row['Signal'] == "BUY PE" else None), axis=1)
        st.dataframe(backtest_data[['Strike_Price', 'Time', 'Signal', 'Signal Price']].head(10))

        # Option to download backtest results as CSV
        csv = backtest_data.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Backtest Results",
            data=csv,
            file_name='backtest_results.csv',
            mime='text/csv',
        )
    else:
        st.error("Uploaded file does not contain the required columns for backtesting.")
