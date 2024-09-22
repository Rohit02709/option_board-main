# Import necessary libraries
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
            # Count number of BUY CE and BUY PE signals per strike price
            signal_counts = df.groupby(['Strike_Price', 'Signal']).size().unstack(fill_value=0)

            # Plotting signal counts for BUY CE and BUY PE
            st.write("Number of signals per strike price:")
            st.dataframe(signal_counts)

            # Plot the counts of BUY CE and BUY PE using matplotlib
            fig, ax = plt.subplots(figsize=(10, 6))
            signal_counts.plot(kind='bar', stacked=True, ax=ax, color=['green', 'red'])
            ax.set_title("Signal Counts per Strike Price (BUY CE vs BUY PE)")
            ax.set_xlabel("Strike Price")
            ax.set_ylabel("Number of Signals")
            plt.xticks(rotation=45)
            plt.tight_layout()

            # Display the plot in Streamlit
            st.pyplot(fig)

    except Exception as e:
        st.error(f"Error processing the file: {str(e)}")

