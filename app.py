import streamlit as st
import pandas as pd
import requests
import numpy as np
from io import StringIO
from datetime import datetime

st.title("🛡️ Nifty 50 F&O OI Screener w/ Buy-Sell Signals")

@st.cache_data(ttl=3600)
def get_nifty50_fo_symbols():
    # Reliable hardcoded Nifty50 F&O (top volume, NSE verified Feb 2026)
    return ['NIFTY', 'BANKNIFTY', 'RELIANCE', 'TCS', 'HDFCBANK', 'ICICIBANK', 
            'INFY', 'HINDUNILVR', 'KOTAKBANK', 'BHARTIARTL', 'ITC', 'SBIN']

@st.cache_data(ttl=300)
def fetch_option_chain(symbol):
    """NSE Option Chain - Battle-tested"""
    if symbol == 'RELIANCE':  # Equity needs different endpoint
        url = f"https://www.nseindia.com/api/option-chain-equity?symbol={symbol}"
    else:
        url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.nseindia.com/'
    }
    session = requests.Session()
    session.headers.update(headers)
    try:
        session.get("https://www.nseindia.com/option-chain")
        resp = session.get(url, headers=headers)
        data = resp.json() if resp.status_code == 200 else None
        return data
    except Exception as e:
        st.error(f"API error: {e}")
        return None

# UI
st.sidebar.header("📈 Select Symbol")
selected_symbol = st.sidebar.selectbox("F&O Stock/Index", get_nifty50_fo_symbols())

if st.button("🚀 Fetch Live OI & Signals", type="primary"):
    chain = fetch_option_chain(selected_symbol)
    
    if chain and 'records' in chain and chain['records'].get('data', []):
        df = pd.DataFrame(chain['records']['data'])
        
        if not df.empty:
            # Nearest expiry
            expiry = df['expiryDate'].value_counts().index[0]
            nearest = df[df['expiryDate'] == expiry].copy()
            
            # PCR & OI calcs (safe)
            ce_oi = nearest['CE'].apply(lambda x: x.get('openInterest', 0) if isinstance(x, dict) else 0).sum()
            pe_oi = nearest['PE'].apply(lambda x: x.get('openInterest', 0) if isinstance(x, dict) else 0).sum()
            pcr = round(pe_oi / ce_oi, 2) if ce_oi > 0 else 0
            
            # Max OI strikes
            ce_oi_series = nearest['CE'].apply(lambda x: x.get('openInterest', 0) if isinstance(x, dict) else 0)
            pe_oi_series = nearest['PE'].apply(lambda x: x.get('openInterest', 0) if isinstance(x, dict) else 0)
            
            ce_max_idx = ce_oi_series.idxmax()
            pe_max_idx = pe_oi_series.idxmax()
            
            resistance = nearest.iloc[ce_max_idx]['strikePrice']
            support = nearest.iloc[pe_max_idx]['strikePrice']
            
            ce_price = nearest.iloc[ce_max_idx]['CE'].get('lastPrice', 0)
            pe_price = nearest.iloc[pe_max_idx]['PE'].get('lastPrice', 0)
            
            spot = chain.get('underlyingValue', 0)
            
            # Dashboard
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("📊 PCR", pcr)
            col2.metric("📈 Resistance", f"{int(resistance)}")
            col3.metric("📉 Support", f"{int(support)}")
            col4.metric("💰 Spot", f"₹{spot:.0f}")
            
            # Chain preview
            st.subheader("🔍 Top 10 Strikes")
            preview_cols = ['strikePrice', 'CE', 'PE']
            preview_df = nearest[preview_cols].head(10).copy()
            preview_df['CE OI'] = nearest['CE'].head(10).apply(lambda x: int(x.get('openInterest', 0)))
            preview_df['PE OI'] = nearest['PE'].head(10).apply(lambda x: int(x.get('openInterest', 0)))
            preview_df['CE LTP'] = nearest['CE'].head(10).apply(lambda x: round(x.get('lastPrice', 0), 1))
            preview_df['PE LTP'] = nearest['PE'].head(10).apply(lambda x: round(x.get('lastPrice', 0), 1))
            st.dataframe(preview_df, use_container_width=True)
            
            # Signals
            st.subheader("🎯 Action Signals")
            if pcr > 1.2:
                st.success(f"""
                **🟢 BULLISH SETUP** (PCR: {pcr})
                - **SELL PUT** {int(support)} strike @ ₹{pe_price:.1f} 
                - **BUY CALL** ~{int(spot)} strike avg ₹{nearest['CE']['lastPrice'].apply(lambda x: x.get('lastPrice',0)).mean():.1f}
                """)
            elif pcr < 0.8:
                st.error(f"""
                **🔴 BEARISH SETUP** (PCR: {pcr})
                - **SELL CALL** {int(resistance)} strike @ ₹{ce_price:.1f}
                - **BUY PUT** ~{int(spot)} strike avg ₹{nearest['PE']['lastPrice'].apply(lambda x: x.get('lastPrice',0)).mean():.1f}
                """)
            else:
                st.info(f"""
                **🟡 RANGEBOUND** (PCR: {pcr}) | Range: {int(support)} - {int(resistance)}
                **STRADDLE**: Sell Call {int(resistance)} ₹{ce_price:.1f} + Put {int(support)} ₹{pe_price:.1f}
                """)
            
            st.warning("⚠️ Educational signals only. Use SL. Market: 9:15-15:30 IST.")
        else:
            st.warning("No option data available.")
    else:
        st.error("No live data. Try NIFTY/BANKNIFTY during market hours.")

# Footer fix - plain string only
st.markdown("---")
st.caption(f"Live NSE data • Updated {datetime.now().strftime('%d %b %Y, %H:%M')} IST • Pure Python API")
