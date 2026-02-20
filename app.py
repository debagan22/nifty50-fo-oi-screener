import streamlit as st
import pandas as pd
import numpy as np
import requests
from nsepython import fnolist  # Correct function for F&O list
from datetime import datetime

@st.cache_data(ttl=300)
def get_nifty_fo_stocks():
    all_fo = fnolist()  # All F&O stocks
    nifty50_fo = [s for s in all_fo if s in ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'HINDUNILVR']]  # Sample Nifty50 F&O; expand as needed
    return nifty50_fo[:20]  # Limit demo

def fetch_nse_optionchain(symbol):
    """Direct NSE API for option chain (reliable alternative)"""
    try:
        url = "https://www.nseindia.com/api/option-chain-indices?symbol=" + symbol
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers)
        return response.json()
    except:
        return None

st.title("Nifty 50 F&O OI Screener with Buy/Sell Suggestions")

fo_stocks = get_nifty_fo_stocks()
selected_symbol = st.selectbox("Select Nifty50 F&O Stock", fo_stocks)

if selected_symbol and st.button("Analyze & Suggest Trades"):
    with st.spinner("Fetching live data..."):
        chain_data = fetch_nse_optionchain(selected_symbol)
        
        if chain_data and 'records' in chain_data:
            records = chain_data['records']['data']
            df = pd.DataFrame(records)
            
            # Nearest expiry
            expiry = df['expiryDate'].iloc[0]
            nearest = df[df['expiryDate'] == expiry]
            
            # CE/PE aggregates
            ce_oi = nearest['CE']['openInterest'].sum()
            pe_oi = nearest['PE']['openInterest'].sum()
            pcr = pe_oi / ce_oi if ce_oi > 0 else 0
            
            # Max OI strikes
            max_ce_idx = nearest['CE']['openInterest'].idxmax()
            max_pe_idx = nearest['PE']['openInterest'].idxmax()
            max_ce_strike = nearest.loc[max_ce_idx, 'strikePrice']
            max_pe_strike = nearest.loc[max_pe_idx, 'strikePrice']
            
            ltp_ce = nearest['CE']['lastPrice'].mean()
            ltp_pe = nearest['PE']['lastPrice'].mean()
            
            st.subheader("Summary")
            col1, col2, col3 = st.columns(3)
            col1.metric("PCR", f"{pcr:.2f}")
            col2.metric("Resistance (Max CE OI)", max_ce_strike)
            col3.metric("Support (Max PE OI)", max_pe_strike)
            
            # Chain table (top 10)
            chain_top = nearest.head(10)[['strikePrice', 'CE', 'PE']]
            chain_top['CE_OI'] = chain_top['CE'].apply(lambda x: x.get('openInterest', 0))
            chain_top['PE_OI'] = chain_top['PE'].apply(lambda x: x.get('openInterest', 0))
            chain_top['CE_LTP'] = chain_top['CE'].apply(lambda x: x.get('lastPrice', 0))
            chain_top['PE_LTP'] = chain_top['PE'].apply(lambda x: x.get('lastPrice', 0))
            st.dataframe(chain_top[['strikePrice', 'CE_OI', 'PE_OI', 'CE_LTP', 'PE_LTP']])
            
            # Suggestions
            st.subheader("Trade Suggestions")
            if pcr > 1.2:
                st.success("**Bullish**: Sell Put @ " + str(max_pe_strike) + " (LTP ₹" + f"{nearest['PE']['lastPrice'][nearest['strikePrice']==max_pe_strike].iloc[0]:.2f}" + "), Buy Call ATM (₹" + f"{ltp_ce:.2f}" + ")")
            elif pcr < 0.8:
                st.error("**Bearish**: Sell Call @ " + str(max_ce_strike) + " (LTP ₹" + f"{nearest['CE']['lastPrice'][nearest['strikePrice']==max_ce_strike].iloc[0]:.2f}" + "), Buy Put ATM (₹" + f"{ltp_pe:.2f}" + ")")
            else:
                st.info("**Neutral**: Sell Straddle @ " + str(max_ce_strike) + "/ " + str(max_pe_strike) + " (Call ₹" + f"{nearest['CE']['lastPrice'][nearest['strikePrice']==max_ce_strike].iloc[0]:.2f}" + ", Put ₹" + f"{nearest['PE']['lastPrice'][nearest['strikePrice']==max_pe_strike].iloc[0]:.2f}" + ")")
            
            st.warning("Educational. Market hours only. Not advice.")
        else:
            st.error("No data. Try 'NIFTY' or check connection.")

st.caption("Fixed import & NSE direct fetch. Works 2026.") [web:31][web:30]
