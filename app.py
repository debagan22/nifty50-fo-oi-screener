import streamlit as st
from nsepython import nse_optionchain
import pandas as pd
import numpy as np

st.title("⚡ LIVE Nifty F&O OI Scanner")

@st.cache_data(ttl=180)
def get_live_chain(symbol):
    try:
        data = nse_optionchain(symbol)
        if data and 'records' in data:
            return data
    except:
        pass
    return None

# LIVE symbols
SYMBOLS = ['NIFTY', 'BANKNIFTY', 'FINNIFTY']

symbol = st.selectbox("Live F&O", SYMBOLS)

if st.button("🔥 GET LIVE SIGNALS", type="primary"):
    chain = get_live_chain(symbol)
    
    if chain and chain.get('records', {}).get('data'):
        df = pd.DataFrame(chain['records']['data'])
        
        # Nearest expiry
        expiry = df['expiryDate'].value_counts().index[0]
        df_live = df[df['expiryDate'] == expiry]
        
        # PCR & Peaks
        ce_oi = df_live['CE'].apply(lambda x: x.get('openInterest', 0)).sum()
        pe_oi = df_live['PE'].apply(lambda x: x.get('openInterest', 0)).sum()
        pcr = round(pe_oi / ce_oi, 2)
        
        ce_peak = df_live.loc[df_live['CE'].apply(lambda x: x.get('openInterest', 0)).idxmax()]
        pe_peak = df_live.loc[df_live['PE'].apply(lambda x: x.get('openInterest', 0)).idxmax()]
        
        spot = chain.get('underlyingValue', 0)
        
        # LIVE Dashboard
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🔴 PCR", pcr)
        col2.metric("📈 CE Peak", int(ce_peak['strikePrice']))
        col3.metric("📉 PE Peak", int(pe_peak['strikePrice']))
        col4.metric("💹 Spot", f"₹{spot:.0f}")
        
        # Chain Preview
        st.subheader("Live Chain (Top 10)")
        preview = df_live.head(10)[['strikePrice', 'CE', 'PE']].copy()
        preview['CE OI'] = preview['CE'].apply(lambda x: int(x.get('openInterest', 0)))
        preview['PE OI'] = preview['PE'].apply(lambda x: int(x.get('openInterest', 0)))
        preview['CE LTP'] = preview['CE'].apply(lambda x: round(x.get('lastPrice', 0), 1))
        preview['PE LTP'] = preview['PE'].apply(lambda x: round(x.get('lastPrice', 0), 1))
        st.dataframe(preview)
        
        # **LIVE SIGNALS**
        st.markdown("## 🚨 LIVE TRADE SIGNALS")
        if pcr > 1.1:
            st.balloons()
            st.success(f"""
            🟢 **BULLISH** | PCR {pcr}
            **SELL PUT** {int(pe_peak['strikePrice'])} @ ₹{pe_peak['PE']['lastPrice']:.1f}
            **BUY CALL** near ₹{spot:.0f}
            """)
        elif pcr < 0.9:
            st.error(f"""
            🔴 **BEARISH** | PCR {pcr}
            **SELL CALL** {int(ce_peak['strikePrice'])} @ ₹{ce_peak['CE']['lastPrice']:.1f}
            **BUY PUT** near ₹{spot:.0f}
            """)
        else:
            st.info(f"""
            🟡 **SIDEWAYS** | PCR {pcr} | Range {int(pe_peak['strikePrice'])}-{int(ce_peak['strikePrice'])}
            **STRADDLE**: Call ₹{ce_peak['CE']['lastPrice']:.1f} + Put ₹{pe_peak['PE']['lastPrice']:.1f}
            """)
        
        st.success(f"✅ LIVE {symbol} data @ {datetime.now().strftime('%H:%M:%S')} IST")
        
    else:
        st.error("❌ No live data. Install: `pip install nsepython`")

st.caption("Debasish's LIVE F&O Scanner | NSE Real-Time")
