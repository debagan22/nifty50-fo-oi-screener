import streamlit as st
import pandas as pd
import requests
import numpy as np
from io import StringIO
from datetime import datetime  # Fixed: Added this import

st.title("🛡️ Nifty 50 F&O OI Screener w/ Buy-Sell Signals")

@st.cache_data(ttl=600)
def get_nifty50_symbols():
    url = "https://archives.nseindia.com/content/indices/ind_nifty50list.csv"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        resp = requests.get(url, headers=headers)
        df = pd.read_csv(StringIO(resp.text))
        return df['Symbol'].tolist()
    except:
        return ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY']  # Fallback

@st.cache_data(ttl=300)
def fetch_option_chain(symbol):
    url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json'
    }
    session = requests.Session()
    session.headers.update(headers)
    try:
        session.get("https://www.nseindia.com")
        resp = session.get(url, headers=headers)
        return resp.json() if resp.status_code == 200 else None
    except:
        return None

# Sidebar: Symbols
nifty_symbols = get_nifty50_symbols()
st.sidebar.header("Nifty F&O Stocks")
selected_symbol = st.sidebar.selectbox("Pick Symbol", ['NIFTY', 'BANKNIFTY'] + ['RELIANCE', 'TCS', 'HDFCBANK'])

if st.button("🚀 Analyze & Get Trade Signals", type="primary"):
    with st.spinner("Fetching live NSE data..."):
        chain = fetch_option_chain(selected_symbol)
        
        if chain and 'records' in chain and chain['records'].get('data'):
            data = chain['records']['data']
            df = pd.DataFrame(data)
            
            # Nearest expiry
            expiry_counts = df['expiryDate'].value_counts()
            if not expiry_counts.empty:
                expiry = expiry_counts.index[0]
                nearest = df[df['expiryDate'] == expiry].copy()
                
                # Safe PCR calc
                ce_oi = nearest['CE'].apply(lambda x: x.get('openInterest', 0) if isinstance(x, dict) else 0).sum()
                pe_oi = nearest['PE'].apply(lambda x: x.get('openInterest', 0) if isinstance(x, dict) else 0).sum()
                pcr = pe_oi / ce_oi if ce_oi > 0 else 0
                
                # Max OI strikes
                ce_max_idx = nearest['CE'].apply(lambda x: x.get('openInterest', 0)).idxmax()
                pe_max_idx = nearest['PE'].apply(lambda x: x.get('openInterest', 0)).idxmax()
                resistance = nearest.iloc[ce_max_idx]['strikePrice']
                support = nearest.iloc[pe_max_idx]['strikePrice']
                
                ce_premium = nearest.iloc[ce_max_idx]['CE'].get('lastPrice', 0)
                pe_premium = nearest.iloc[pe_max_idx]['PE'].get('lastPrice', 0)
                
                # Metrics
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("📊 PCR", f"{pcr:.2f}")
                col2.metric("📈 Resistance", resistance)
                col3.metric("📉 Support", support)
                col4.metric("💰 Spot LTP", f"₹{chain.get('underlyingValue', 0):.0f}")
                
                # Chain table
                st.subheader("Top Strikes Chain")
                chain_df = nearest.head(10)[['strikePrice']].copy()
                chain_df['CE OI'] = nearest['CE'].head(10).apply(lambda x: x.get('openInterest', 0) if isinstance(x,dict) else 0)
                chain_df['PE OI'] = nearest['PE'].head(10).apply(lambda x: x.get('openInterest', 0) if isinstance(x,dict) else 0)
                chain_df['CE Premium'] = nearest['CE'].head(10).apply(lambda x: x.get('lastPrice', 0))
                chain_df['PE Premium'] = nearest['PE'].head(10).apply(lambda x: x.get('lastPrice', 0))
                st.dataframe(chain_df.round(0))
                
                # Signals
                st.subheader("🎯 Trade Signals")
                signal_color = "success" if pcr > 1.2 else "error" if pcr < 0.8 else "info"
                if pcr > 1.2:
                    st.markdown(f"""
                    <div style="background-color: #d4edda; padding: 15px; border-radius: 10px; border-left: 5px solid #28a745;">
                    **🟢 BULLISH** (PCR {pcr:.2f})<br>
                    • **SELL PUT** {support} @ ₹{pe_premium:.2f} (Strong support)<br>
                    • **BUY CALL** ATM (~spot) avg ₹{nearest['CE']['lastPrice'].apply(lambda x: x.get('lastPrice',0)).mean():.2f}
                    </div>
                    """, unsafe_allow_html=True)
                elif pcr < 0.8:
                    st.markdown(f"""
                    <div style="background-color: #f8d7da; padding: 15px; border-radius: 10px; border-left: 5px solid #dc3545;">
                    **🔴 BEARISH** (PCR {pcr:.2f})<br>
                    • **SELL CALL** {resistance} @ ₹{ce_premium:.2f} (Resistance cap)<br>
                    • **BUY PUT** ATM avg ₹{nearest['PE']['lastPrice'].apply(lambda x: x.get('lastPrice',0)).mean():.2f}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background-color: #d1ecf1; padding: 15px; border-radius: 10px; border-left: 5px solid #17a2b8;">
                    **🟡 NEUTRAL** (PCR {pcr:.2f}) Range {support}-{resistance}<br>
                    **STRADDLE**: Sell Call {resistance} ₹{ce_premium:.2f} + Put {support} ₹{pe_premium:.2f}
                    </div>
                    """, unsafe_allow_html=True)
                
                st.error("⚠️ **Educational tool only**. Add SL 25%. Verify manually. Market hrs: 9:15-15:30 IST.")
            else:
                st.warning("No expiry data found.")
        else:
            st.error("❌ No live data. Use 'NIFTY' during market hours.")

st.markdown("---")
st.caption(f"Updated {datetime.now().strftime('%d %b %Y')}. Pure NSE API. No external libs needed.")[web:36][web:30]
