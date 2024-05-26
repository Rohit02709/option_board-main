# import all important libraries
from nselib import derivatives
from nselib import capital_market
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import pandas as pd
import streamlit as st
def add_meta_tag():
    meta_tag = """
        <head>
            <meta name="google-site-verification" content="QBiAoAo1GAkCBe1QoWq-dQ1RjtPHeFPyzkqJqsrqW-s" />
        </head>
    """
    st.markdown(meta_tag, unsafe_allow_html=True)

# Main code
add_meta_tag()
# add title of the web-app
st.title(':green[NSE] **Option Dashboard**')
st.header('option analysis',divider='rainbow')

#create some tab for option analysis
tab1, tab2,tab3 = st.tabs(["option chain","OI",'Ratio strategy'])

# create side bar to select index instrument and for expiry day selection
index= st.sidebar.selectbox("select index name",('NIFTY',"BANKNIFTY","FINNIFTY"))
ex= st.sidebar.selectbox('select expiry date',derivatives.expiry_dates_option_index()[index])
exp=datetime.strptime(ex,'%d-%b-%Y').strftime('%d-%m-%Y')

#extracting data from nselib library 
try:
  option=derivatives.nse_live_option_chain(index,exp)
  o=option[['CALLS_OI', 'CALLS_Chng_in_OI','CALLS_LTP','Strike_Price','PUTS_LTP','PUTS_Chng_in_OI', 'PUTS_OI']].set_index('Strike_Price')

  if index =='NIFTY':
    cmp=capital_market.market_watch_all_indices().set_index('index').loc['NIFTY 50','last']
    range=(int(np.round(cmp / 50.0)) * 50)+1000,(int(np.round(cmp / 50.0)) * 50)-1000
    oi=o.loc[range[1]:range[0]]
  elif index == 'BANKNIFTY':
    cmp=capital_market.market_watch_all_indices().set_index('index').loc['NIFTY BANK','last']
    range=(int(np.round(cmp/100.0)) *100)+1500,(int(np.round(cmp / 100.0)) * 100)-1500
    oi=o.loc[range[1]:range[0]]
  else:
      cmp = capital_market.market_watch_all_indices().set_index('index').loc['NIFTY FINANCIAL SERVICES', 'last']
      range = (int(np.round(cmp / 50.0)) * 50)+900,(int(np.round(cmp / 50.0)) * 50)-900
      oi = o.loc[range[1]:range[0]]
  with tab1:
    st.subheader('Option chain')
    st.table(oi.style.highlight_max(axis=0,subset=['CALLS_OI','PUTS_OI','CALLS_Chng_in_OI','PUTS_Chng_in_OI']))
  with tab2:
    
    st.subheader('Open interest analysis')
    fig, ax = plt.subplots(2, 1)
    ax[0].bar(oi.index, oi['CALLS_OI'], color='blue', width=20)
    ax[0].bar(oi.index - 10, oi['PUTS_OI'], color='red', width=20)
    ax[0].axvline(x=cmp, color='black', linestyle='--')
    ax[0].set_title('OI position')
    ax[1].bar(oi.index, oi['CALLS_Chng_in_OI'], color='blue', width=20)
    ax[1].bar(oi.index - 10, oi['PUTS_Chng_in_OI'], color='red', width=20)
    ax[1].axvline(x=cmp, color='black', linestyle='--')
    ax[1].set_xlabel('Change in OI')
    st.pyplot(fig)
  if index =="NIFTY":
    
    call = pd.DataFrame()
    call['CALLS 50 sprade'] = o['CALLS_LTP'] - ((o['CALLS_LTP'].shift(-1)) * 2)
    call['CALLS 100 sprade'] = o['CALLS_LTP'] - ((o['CALLS_LTP'].shift(-2)) * 2)
    call['CALLS 150 sprade'] = o['CALLS_LTP'] - ((o['CALLS_LTP'].shift(-3)) * 2)
    call['CALLS 200 sprade'] = o['CALLS_LTP'] - ((o['CALLS_LTP'].shift(-4)) * 2)
    call['CALLS 250 sprade'] = o['CALLS_LTP'] - ((o['CALLS_LTP'].shift(-5)) * 2)
    call['CALLS 300 sprade'] = o['CALLS_LTP'] - ((o['CALLS_LTP'].shift(-6)) * 2)
    call = call[call.index > cmp].dropna().iloc[:12]
    put = pd.DataFrame()
    put['PUTS 50 sprade'] = o['PUTS_LTP'] - ((o['PUTS_LTP'].shift(1)) * 2)
    put['PUTS 100 sprade'] = o['PUTS_LTP'] - ((o['PUTS_LTP'].shift(2)) * 2)
    put['PUTS 150 sprade'] = o['PUTS_LTP'] - ((o['PUTS_LTP'].shift(3)) * 2)
    put['PUTS 200 sprade'] = o['PUTS_LTP'] - ((o['PUTS_LTP'].shift(4)) * 2)
    put['PUTS 250 sprade'] = o['PUTS_LTP'] - ((o['PUTS_LTP'].shift(5)) * 2)
    put['PUTS 300 sprade'] = o['PUTS_LTP'] - ((o['PUTS_LTP'].shift(6)) * 2)
    put = put[put.index < cmp].dropna().iloc[-12:]
    ratio = pd.concat([put, call])

    def color_range(val):
        color = 'red' if 0.5 <= val <= 8 else 'black'
        return f'color: {color}'

    ratio = ratio.style.applymap(color_range)
   
  elif index== 'BANKNIFTY':
    
    call = pd.DataFrame()
    call['CALLS 100 sprade'] = o['CALLS_LTP'] - ((o['CALLS_LTP'].shift(-1)) * 2)
    call['CALLS 200 sprade'] = o['CALLS_LTP'] - ((o['CALLS_LTP'].shift(-2)) * 2)
    call['CALLS 300 sprade'] = o['CALLS_LTP'] - ((o['CALLS_LTP'].shift(-3)) * 2)
    call['CALLS 400 sprade'] = o['CALLS_LTP'] - ((o['CALLS_LTP'].shift(-4)) * 2)
    call['CALLS 500 sprade'] = o['CALLS_LTP'] - ((o['CALLS_LTP'].shift(-5)) * 2)
    call['CALLS 600 sprade'] = o['CALLS_LTP'] - ((o['CALLS_LTP'].shift(-6)) * 2)
    call = call[call.index > cmp].dropna().iloc[:12]
    put = pd.DataFrame()
    put['PUTS 100 sprade'] = o['PUTS_LTP'] - ((o['PUTS_LTP'].shift(1)) * 2)
    put['PUTS 200 sprade'] = o['PUTS_LTP'] - ((o['PUTS_LTP'].shift(2)) * 2)
    put['PUTS 300 sprade'] = o['PUTS_LTP'] - ((o['PUTS_LTP'].shift(3)) * 2)
    put['PUTS 400 sprade'] = o['PUTS_LTP'] - ((o['PUTS_LTP'].shift(4)) * 2)
    put['PUTS 500 sprade'] = o['PUTS_LTP'] - ((o['PUTS_LTP'].shift(5)) * 2)
    put['PUTS 600 sprade'] = o['PUTS_LTP'] - ((o['PUTS_LTP'].shift(6)) * 2)
    put = put[put.index < cmp].dropna().iloc[-12:]
    ratio = pd.concat([put, call])

    def color_range(val):
        color = 'red' if 0.5 <= val <= 8 else 'black'
        return f'color: {color}'

    ratio = ratio.style.applymap(color_range)
      
  else:
    
    call = pd.DataFrame()
    call['CALLS 50 sprade'] = o['CALLS_LTP'] - ((o['CALLS_LTP'].shift(-1)) * 2)
    call['CALLS 100 sprade'] = o['CALLS_LTP'] - ((o['CALLS_LTP'].shift(-2)) * 2)
    call['CALLS 150 sprade'] = o['CALLS_LTP'] - ((o['CALLS_LTP'].shift(-3)) * 2)
    call['CALLS 200 sprade'] = o['CALLS_LTP'] - ((o['CALLS_LTP'].shift(-4)) * 2)
    call['CALLS 250 sprade'] = o['CALLS_LTP'] - ((o['CALLS_LTP'].shift(-5)) * 2)
    call['CALLS 300 sprade'] = o['CALLS_LTP'] - ((o['CALLS_LTP'].shift(-6)) * 2)
    call = call[call.index > cmp].dropna().iloc[:12]
    put = pd.DataFrame()
    put['PUTS 50 sprade'] = o['PUTS_LTP'] - ((o['PUTS_LTP'].shift(1)) * 2)
    put['PUTS 100 sprade'] = o['PUTS_LTP'] - ((o['PUTS_LTP'].shift(2)) * 2)
    put['PUTS 150 sprade'] = o['PUTS_LTP'] - ((o['PUTS_LTP'].shift(3)) * 2)
    put['PUTS 200 sprade'] = o['PUTS_LTP'] - ((o['PUTS_LTP'].shift(4)) * 2)
    put['PUTS 250 sprade'] = o['PUTS_LTP'] - ((o['PUTS_LTP'].shift(5)) * 2)
    put['PUTS 300 sprade'] = o['PUTS_LTP'] - ((o['PUTS_LTP'].shift(6)) * 2)
    put = put[put.index < cmp].dropna().iloc[-12:]
    ratio = pd.concat([put, call])


    def color_range(val):
        color = 'red' if 0.5 <= val <= 8 else 'black'
        return f'color: {color}'


    ratio = ratio.style.applymap(color_range)
  with tab3:
      st.subheader('Ration Sprade strategy')
      st.table(ratio)
  # creating importent futters
  st.write(index)
  col1, col2= st.columns(2)
  col1.metric('**Spot price**',cmp)
  
  pcr= np.round(o.PUTS_OI.sum()/o.CALLS_OI.sum(),2)
  col2.metric('**PCR:**',pcr)
 
except:
  st.text('Please select accurate expiry date')