# install importent libraries
import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime,timedelta

# create titles of the page
st.title('upcomming :red[IPO] and :gray[GMP]')

# extract data from investorgain.com using requests library
url1="https://www.investorgain.com/report/live-ipo-gmp/331/?ref=chr"
d1= requests.get(url1)

# use beautifulsoup to find data table
ta=BeautifulSoup(d1.content, 'html.parser')
table = ta.find('table',class_="table table-bordered table-striped table-hover w-auto")
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
    df=df.rename(columns={'IPO':'Company'})
    df= df.filter(items=['Company', 'Price', 'GMP(₹)', 'Est Listing','Open', 'Close', 'BoA Dt', 'Listing'])
    df['GMP%'] = df['Est Listing'].str.extract(r'\((.*?)\)')
    df= df.dropna()
    current_date= datetime.now()+timedelta(hours=5, minutes=30)   # current datetime in India
    
    df['Listing']= df['Listing'].astype(str) + '-' + str(current_date.year)
    df['Listing'] = df['Listing'].apply(pd.to_datetime,format="%d-%b-%Y")
    df = df.loc[(df['Listing'] >= current_date)]
    df=df.set_index('Company')
    df['Listing'] = df['Listing'].dt.strftime('%d-%b')
    # Print the DataFrame streamlit page
    st.table(df)
    st.write(':blue[GMP]= Gray Market Premium, which representing expencted listing gain')
else:
    st.text("No upcomming available")
