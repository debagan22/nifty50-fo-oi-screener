import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(layout="wide")
st.title("⚡ LIVE NSE F&O OI Scanner - 100% Real Data")

@st.cache_data(ttl=120)
def live_nse_chain(symbol):
    """Direct NSE - Works everywhere 2026"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty'
    }
    
    with requests.Session() as s:
        s.headers.update(headers)
        # Essential: Get cookies first
        s.get('https://www.nseindia.com/option-chain')
        s.get('https://www.nseindia.com')
        
        # Indices vs Equity
        if symbol in ['NIFTY', 'BANKNIFTY']:
            url = f'https://www.nseindia.com/api/option-chain-indices?symbol={symbol}'
        else:
            url = f'https://www.nseindia.com/api/option-chain-equity?symbol={symbol}'
        
        resp = s.get(url)
        if resp.status_code == 200:
            return resp.json()
    return None

SYMBOLS = ['NIFTY', 'BANKNIFTY', 'RELIANCE']

col1, col2 = st.columns([1,3])
with col1:
    symbol = st.selectbox("Live Symbol", SYMBOLS)
with col2:
    if st.button("📡 FETCH LIVE", use_container_width=True):
        chain = live_nse_chain(symbol)
        
        if chain and 'records' in chain:
            df = pd.DataFrame(chain['records']['data'])
            
            # Live processing
            expiry = df['expiryDate'].value_counts().index[0]
            live_df = df[df['expiryDate'] == expiry]
            
            ce_oi_total = live_df['CE'].apply(lambda x: x.get('openInterest', 0)).sum()
            pe_oi_total = live_df['PE'].apply(lambda x: x.get('openInterest', 0)).sum()
            pcr = round(pe_oi_total / ce_oi_total, 2) if ce_oi_total else 0
            
            # Peak strikes
            ce_peak_idx = live_df['CE'].apply(lambda x: x.get('openInterest', 0)).idxmax()
            pe_peak_idx = live_df['PE'].apply(lambda x: x.get('openInterest', 0)).idxmax()
            
            ce_strike = live_df.iloc[ce_peak_idx]['strikePrice']
            pe_strike = live_df.iloc[pe_peak_idx]['strikePrice']
            ce_premium = live_df.iloc[ce_peak_idx]['CE']['lastPrice']
            pe_premium = live_df.iloc[pe_peak_idx]['PE']['lastPrice']
            
            spot = chain.get('underlyingValue', 0)
            
            # 🎯 LIVE DASHBOARD
            st.markdown("### 📊 LIVE METRICS")
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("PCR", f"{pcr:.2f}")
            col2.metric("CE Peak", f"{int(ce_strike)}")
            col3.metric("PE Peak", f"{int(pe_strike)}")
            col4.metric("Spot", f"₹{spot:.0f}")
            col5.metric("Time", datetime.now().strftime("%H:%M:%S"))
            
            # Chain table
            st.markdown("### 📋 LIVE CHAIN")
            chain_preview = live_df[['strikePrice', 'CE', 'PE']].head(15).copy()
            chain_preview['CE OI'] = chain_preview['CE'].apply(lambda x: f"{int(x.get('openInterest', 0)):,}")
            chain_preview['PE OI'] = chain_preview['PE'].apply(lambda x: f"{int(x.get('openInterest', 0)):,}")
            chain_preview['CE LTP'] = chain_preview['CE'].apply(lambda x: f"₹{x.get('lastPrice', 0):.1f}")
            chain_preview['PE LTP'] = chain_preview['PE'].apply(lambda x: f"₹{x.get('lastPrice', 0):.1f}")
            st.dataframe(chain_preview[['strikePrice', 'CE OI', 'PE OI', 'CE LTP', 'PE LTP']])
            
            # 🔥 LIVE SIGNALS
            st.markdown("### 🚨 LIVE TRADE SIGNALS")
            if pcr > 1.1:
                st.balloons()
                st.success(f"""
                🟢 **BULLISH** | PCR **{pcr}**
                - **SELL PUT** `{int(pe_strike)}` @ **₹{pe_premium:.1f}**
                - **BUY CALL** near spot **₹{int(spot)}**
                """)
            elif pcr < 0.9:
                st.error(f"""
                🔴 **BEARISH** | PCR **{pcr}**
                - **SELL CALL** `{int(ce_strike)}` @ **₹{ce_premium:.1f}**
                - **BUY PUT** near spot **₹{int(spot)}**
                """)
            else:
                st.warning(f"""
                🟡 **RANGE** | PCR **{pcr}** | `{int(pe_strike)}` - `{int(ce_strike)}`
                **STRADDLE**: Call **₹{ce_premium:.1f}** + Put **₹{pe_premium:.1f}**
                """)
            
            st.success(f"✅ **LIVE {symbol}** data fetched {datetime.now().strftime('%H:%M:%S')} IST")
        else:
            st.error("❌ NSE connection failed. Try refresh.")

st.markdown("---")
st.caption("Debasish Ganguly | Bokakhat Live F&O | Pure NSE API")
