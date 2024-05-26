# installing important libraries
import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

# adding title of the page
st.title(':red[Quaterly Result] for :blue[Today]')

# extracting todays result announcement data from economic-times website using requests library
url = "https://economictimes.indiatimes.com/markets/stocks/mcalendar.cms"
response = requests.get(url)

# use beautiful soup to extract table data
soup = BeautifulSoup(response.content, 'html.parser')
table = soup.find('table', class_="event_table")
if table:
    # Extract data from the table
    rows = table.find_all('tr')
    table_data = []

    for row in rows:
        columns = row.find_all(['td', 'th'])
        row_data = [column.get_text(strip=True) for column in columns]
        table_data.append(row_data)

    # Remove any empty rows from the table data
    table_data = [row for row in table_data if any(row)]

    # Convert the table data into a DataFrame
    df = pd.DataFrame(table_data[1:], columns=table_data[0])

    # Print the DataFrame
    st.table(df)
else:
    st.text(' ** NOT RESULT ANNOUNCED TODAY**')
