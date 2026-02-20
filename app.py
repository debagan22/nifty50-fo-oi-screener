import streamlit as st
import pandas as pd
import requests
import numpy as np
from datetime import datetime

st.set_page_config(page_title="Nifty F&O OI Scanner", layout="wide")

st.title("🔥 Nifty F&O OI Screener - Live Signals")

@st.cache_data(ttl=60)
def fetch_nse_chain(symbol):
    """2026 NSE-proof option chain fetch"""
    is_equity = symbol in ['RELIANCE', 'TCS', 'HDFCBANK']
    url = f"https://www.nseindia.com/api/option-chain-{'equity' if is_equity else 'indices'}?symbol={symbol}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Referer': 'https://www.nseindia.com/option-chain',
        'authority': 'www.nseindia.com'
    }
    
    with requests.Session() as s:
        s.headers.update(headers)
        s.get('https://www.nseindia.com/option-chain')
        resp = s.get(url)
        
        if resp.status_code == 200:
            return resp.json()
    return None

# Live symbols
SYMBOLS = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'RELIANCE', 'TCS']

selected = st.selectbox("Select F&O", SYMBOLS, index=0)

if st.button("📡 LIVE SCAN", type="primary", use_container_width=True):
    with st.spinner('Scanning NSE...'):
        chain = fetch_nse_chain(selected)
        
        if chain and chain.get('records', {}).get('data'):
            df = pd.DataFrame(chain['records']['data'])
            expiry = df['expiryDate'].value_counts().index[0]
            nearest = df[df['expiryDate'] == expiry]
            
            # Calculations
            ce_oi = nearest['CE'].apply(lambda x: x.get('openInterest', 0)).sum()
            pe_oi = nearest['PE'].apply(lambda x: x.get('openInterest', 0)).sum()
            pcr = round(pe_oi/ce_oi, 2) if ce_oi else 0
            
            ce_max = nearest.loc[nearest['CE'].apply(lambda x: x.get('openInterest', 0)).idxmax()]
            pe_max = nearest.loc[nearest['PE'].apply(lambda x: x.get('openInterest', 0)).idxmax()]
            
            spot = chain.get('underlyingValue', 0)
            
            # Dashboard
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("PCR", pcr)
            col2.metric("Resistance", ce_max['strikePrice'])
            col3.metric("Support", pe_max['strikePrice'])
            col4.metric("Spot", f"₹{spot:.0f}")
            
            # Signals
            st.markdown("## 🎯 LIVE TRADE SIGNALS")
            if pcr > 1.1:
                st.success(f"🟢 **BUY CALL** | Sell Put {pe_max['strikePrice']} ₹{pe_max['PE']['lastPrice']:.1f}")
            elif pcr < 0.9:
                st.error(f"🔴 **BUY PUT** | Sell Call {ce_max['strikePrice']} ₹{ce_max['CE']['lastPrice']:.1f}")
            else:
                st.info(f"🟡 **STRADDLE** {ce_max['strikePrice']}C ₹{ce_max['CE']['lastPrice']:.1f} + {pe_max['strikePrice']}P ₹{pe_max['PE']['lastPrice']:.1f}")
            
            st.balloons()
            
        else:
            st.error("❌ NSE blocked. Try in 1 min or use VPN")

st.caption("Debasish's F&O Scanner • Live NSE • Educational")
