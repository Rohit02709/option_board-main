import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# Load data from the uploaded file
uploaded_file = st.file_uploader("Upload the historical data file for backtesting", type=["csv", "xlsx"])

if uploaded_file:
    try:
        # Detect file type and load data accordingly
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        # Display the first few rows of the data for verification
        st.write("Here are the first few rows of your data:")
        st.dataframe(df.head())

        # Ensure all the required columns are present in the data
        required_columns = ['Strike_Price', 'CE_OI', 'CE_CHG_OI', 'CE_LTP', 'PE_OI', 'PE_CHG_OI', 'PE_LTP', 'Signal', 'Time']
        if not all(column in df.columns for column in required_columns):
            st.error(f"Missing one or more required columns: {required_columns}")
        else:
            # Determine wins and losses based on your signals
            # Assuming 'BUY CE' indicates a long position in CE and 'BUY PE' for PE
            df['Outcome'] = None
            
            # Example logic to define wins/losses (customize based on your strategy)
            # Adjust the logic based on your criteria for determining win/loss
            for index, row in df.iterrows():
                if row['Signal'] == 'BUY CE' and row['CE_LTP'] > row['CE_OI']:  # Example condition for win
                    df.at[index, 'Outcome'] = 'Win'
                elif row['Signal'] == 'BUY CE' and row['CE_LTP'] <= row['CE_OI']:
                    df.at[index, 'Outcome'] = 'Loss'
                elif row['Signal'] == 'BUY PE' and row['PE_LTP'] > row['PE_OI']:
                    df.at[index, 'Outcome'] = 'Win'
                elif row['Signal'] == 'BUY PE' and row['PE_LTP'] <= row['PE_OI']:
                    df.at[index, 'Outcome'] = 'Loss'

            # Count number of signals per strike price
            signal_counts = df.groupby(['Strike_Price', 'Signal']).size().unstack(fill_value=0)
            st.write("Number of signals per strike price:")
            st.dataframe(signal_counts)

            # Count wins and losses
            wins = df[df['Outcome'] == 'Win'].groupby(['Strike_Price', 'Signal']).size().unstack(fill_value=0)
            losses = df[df['Outcome'] == 'Loss'].groupby(['Strike_Price', 'Signal']).size().unstack(fill_value=0)

            # Display wins and losses
            st.write("Number of wins per strike price:")
            st.dataframe(wins)

            st.write("Number of losses per strike price:")
            st.dataframe(losses)

            # Plotting signal counts for BUY CE and BUY PE
            fig, ax = plt.subplots(figsize=(10, 6))
            signal_counts.plot(kind='bar', stacked=True, ax=ax, color=['green', 'red'])
            ax.set_title("Signal Counts per Strike Price (BUY CE vs BUY PE)")
            ax.set_xlabel("Strike Price")
            ax.set_ylabel("Number of Signals")
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)

            # Plotting wins and losses
            fig, ax = plt.subplots(figsize=(10, 6))
            wins.plot(kind='bar', stacked=True, ax=ax, color='blue', alpha=0.7, label='Wins')
            losses.plot(kind='bar', stacked=True, ax=ax, color='orange', alpha=0.7, label='Losses')
            ax.set_title("Wins and Losses per Strike Price (BUY CE vs BUY PE)")
            ax.set_xlabel("Strike Price")
            ax.set_ylabel("Number of Signals")
            plt.xticks(rotation=45)
            ax.legend()
            plt.tight_layout()
            st.pyplot(fig)

    except Exception as e:
        st.error(f"Error processing the file: {str(e)}")
