# Tab 4: OI-based Buy/Sell Signal
with tab4:
    st.subheader('OI-based Buy/Sell Signal')

    # Calculate percentage change in OI for calls and puts
    oi['CALLS_OI_Percent_Change'] = (oi['CALLS_Chng_in_OI'] / oi['CALLS_OI']) * 100
    oi['PUTS_OI_Percent_Change'] = (oi['PUTS_Chng_in_OI'] / oi['PUTS_OI']) * 100

    def generate_signal(row):
        """
        Function to generate buy/sell signals based on OI change
        Buy CE: Significant increase in PUT OI or decrease in CALL OI
        Buy PE: Significant increase in CALL OI or decrease in PUT OI
        """
        if row['PUTS_Chng_in_OI'] > row['CALLS_Chng_in_OI'] * 2:
            return "BUY CE"
        elif row['CALLS_Chng_in_OI'] > row['PUTS_Chng_in_OI'] * 2:
            return "BUY PE"
        else:
            return "HOLD"

    # Generate signals for each row
    oi['Signal'] = oi.apply(generate_signal, axis=1)

    # Sort by the absolute value of change in OI (largest change first)
    oi_sorted = oi.reindex(oi[['CALLS_Chng_in_OI', 'PUTS_Chng_in_OI']].abs().sum(axis=1).sort_values(ascending=False).index)

    # Select only the top 5 strikes with the most significant change in OI
    oi_top_5 = oi_sorted.head(5)

    # Highlight the buy/sell signals and whether to buy CE or PE
    signal_table = oi_top_5[['CALLS_OI', 'CALLS_Chng_in_OI', 'CALLS_OI_Percent_Change', 'CALLS_LTP',
                             'PUTS_LTP', 'PUTS_Chng_in_OI', 'PUTS_OI_Percent_Change', 'PUTS_OI', 'Signal']].style.applymap(
        lambda val: 'color: green' if val == 'BUY CE' else 'color: red' if val == 'BUY PE' else 'color: black',
        subset=['Signal']
    )

    # Display the table with LTP and OI % change
    st.table(signal_table)
