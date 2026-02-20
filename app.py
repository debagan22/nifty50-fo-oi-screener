import streamlit as st
import pandas as pd
import requests
import numpy as np
from io import StringIO
import json

st.title("Nifty 50 F&O OI Screener with Buy/Sell Suggestions")

@st.cache_data(ttl=600)
def get_nifty50_symbols():
    """Fetch official Nifty 50 list from NSE"""
    url = "https://archives.nseindia.com/content/indices/ind_nifty50list.csv"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    session = requests.Session()
    session.headers.update(headers)
    session.get('https://www.nseindia.com', headers=headers)  # Warmup cookies
    resp = session.get(url, headers=headers)
    df = pd.read_csv(StringIO(resp.text))
    return df['Symbol'].tolist()

@st.cache_data(ttl=300)
def fetch_option_chain(symbol):
    """NSE Option Chain API"""
    url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    session = requests.Session()
    session.headers.update(headers)
    session.get('https://www.nseindia.com')
    resp = session.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json()
    return None

nifty_symbols = get_nifty50_symbols()
fo_symbols = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'HINDUNILVR']  # Common Nifty F&O subset
selected_symbol = st.selectbox("Select Nifty F&O Stock/Index", ['NIFTY'] + fo_symbols)

if st.button("Analyze Option Chain & Get Suggestions"):
    chain = fetch_option_chain(selected_symbol)
    if chain and 'records' in chain and 'data' in chain['records']:
        df = pd.DataFrame(chain['records']['data'])
        
        # Nearest expiry
        expiry = df['expiryDate'].value_counts().idxmax()
        nearest_df = df[df['expiryDate'] == expiry].copy()
        
        # PCR & Max OI
        ce_oi_total = nearest_df['CE'].apply(lambda x: x.get('openInterest', 0) if isinstance(x, dict) else 0).sum()
        pe_oi_total = nearest_df['PE'].apply(lambda x: x.get('openInterest', 0) if isinstance(x, dict) else 0).sum()
        pcr = pe_oi_total / ce_oi_total if ce_oi_total > 0 else 0
        
        ce_oi_max_idx = nearest_df['CE'].apply(lambda x: x.get('openInterest', 0) if isinstance(x, dict) else 0).idxmax()
        pe_oi_max_idx = nearest_df['PE'].apply(lambda x: x.get('openInterest', 0) if isinstance(x, dict) else 0).idxmax()
        resistance = nearest_df.loc[ce_oi_max_idx, 'strikePrice']
        support = nearest_df.loc[pe_oi_max_idx, 'strikePrice']
        
        ce_ltp_max = nearest_df.loc[ce_oi_max_idx, 'CE']['lastPrice']
        pe_ltp_max = nearest_df.loc[pe_oi_max_idx, 'PE']['lastPrice']
        
        # Display
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("PCR (OI)", f"{pcr:.2f}")
        col2.metric("Resistance", resistance)
        col3.metric("Support", support)
        col4.metric("Underlying LTP", f"₹{chain.get('underlyingValue', 0):.2f}")
        
        # Top chain
        top_df = nearest_df.head(10)[['strikePrice']]
        top_df['CE OI'] = nearest_df['CE'].head(10).apply(lambda x: x.get('openInterest', 0))
        top_df['PE OI'] = nearest_df['PE'].head(10).apply(lambda x: x.get('openInterest', 0))
        top_df['CE LTP'] = nearest_df['CE'].head(10).apply(lambda x: x.get('lastPrice', 0))
        top_df['PE LTP'] = nearest_df['PE'].head(10).apply(lambda x: x.get('lastPrice', 0))
        st.dataframe(top_df.round(0))
        
        # Suggestions
        st.subheader("Trade Suggestions (Educational)")
        if pcr > 1.2:
            st.success(f"**Bullish (PCR {pcr:.2f})**: Expect upside to {resistance}.\n- **Sell Put** {support} strike @ ₹{pe_ltp_max:.2f} (max OI support)\n- **Buy Call** near {chain.get('underlyingValue', 0):.0f} @ avg ₹{nearest_df['CE']['lastPrice'].apply(lambda x: x.get('lastPrice', 0)).mean():.2f}")
        elif pcr < 0.8:
            st.error(f"**Bearish (PCR {pcr:.2f})**: Downside to {support}.\n- **Sell Call** {resistance} strike @ ₹{ce_ltp_max:.2f} (max OI resistance)\n- **Buy Put** near {chain.get('underlyingValue', 0):.0f} @ avg ₹{nearest_df['PE']['lastPrice'].apply(lambda x: x.get('lastPrice', 0)).mean():.2f}")
        else:
            st.info(f"**Sideways (PCR {pcr:.2f})**: Range {support}-{resistance}.\n**Iron Condor**: Sell Call {resistance} @ ₹{ce_ltp_max:.2f}, Sell Put {support} @ ₹{pe_ltp_max:.2f}")
        
        st.warning("**Risk Disclaimer**: Simulations only. Use stop-loss. Market data live 9:15-15:30 IST. Not advice.")
    else:
        st.error("Failed to fetch data. Try 'NIFTY' during market hours or check internet.")

st.caption(f"Updated {datetime.now().strftime('%Y-%m-%d')}. NSE direct API.")[web:36][web:30][web:37]
