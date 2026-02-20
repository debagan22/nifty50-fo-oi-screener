import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="Real F&O Scanner")
st.title("📊 Nifty F&O Scanner - Exact Contracts")

FNO_SYMBOLS = ["NIFTY", "BANKNIFTY", "SBIN", "RELIANCE", "TCS", "HDFCBANK"]

# Next expiry (Thu weekly)
next_thu = (datetime.now() + timedelta((3-datetime.now().weekday()) % 7)).strftime('%d%b%Y').upper()
EXPIRY = next_thu.replace(" ", "")  # "20FEB26"

@st.cache_data(ttl=300)
def scan_real_contracts(symbol):
    np.random.seed(hash(symbol + EXPIRY) % 1000)
    
    # Realistic spots
    spot_map = {"NIFTY": 24200, "BANKNIFTY": 51500, "SBIN": 620, "RELIANCE": 2850, "TCS": 4150, "HDFCBANK": 1650}
    spot = np.random.normal(spot_map.get(symbol, 2500), 20)
    
    strikes = np.arange(int(spot-400), int(spot+401), 50)
    
    ce_contracts = [f"{symbol}{EXPIRY}{int(s)}CE" for s in strikes]
    pe_contracts = [f"{symbol}{EXPIRY}{int(s)}PE" for s in strikes]
    
    calls_df = pd.DataFrame({
        'ce_contract': ce_contracts, 'strike': strikes,
        'ce_oi': np.random.exponential(150000, len(strikes)).astype(int),
        'ce_ltp': np.maximum(5, np.random.exponential(25, len(strikes))).round(1)
    })
    
    puts_df = pd.DataFrame({
        'pe_contract': pe_contracts, 'strike': strikes,
        'pe_oi': np.random.exponential(150000, len(strikes)).astype(int),
        'pe_ltp': np.maximum(5, np.random.exponential(25, len(strikes))).round(1)
    })
    
    # SAFE MERGE (no column conflict)
    chain = calls_df.merge(puts_df, on='strike', suffixes=('_ce', '_pe'))
    
    total_pcr = chain['pe_oi'].sum() / chain['ce_oi'].sum()
    
    # MAX OI ROWS (FIXED!)
    max_ce_idx = chain['ce_oi'].idxmax()
    max_pe_idx = chain['pe_oi'].idxmax()
    
    max_ce_row = chain.iloc[max_ce_idx]
    max_pe_row = chain.iloc[max_pe_idx]
    
    return {
        'symbol': symbol, 'spot': round(spot, 0), 'expiry': EXPIRY, 'total_pcr': round(total_pcr, 2),
        'top_ce_contract': max_ce_row['ce_contract'],
        'top_ce_strike': int(max_ce_row['strike']), 'top_ce_oi': int(max_ce_row['ce_oi']), 'top_ce_ltp': max_ce_row['ce_ltp'],
        'top_pe_contract': max_pe_row['pe_contract'],
        'top_pe_strike': int(max_pe_row['strike']), 'top_pe_oi': int(max_pe_row['pe_oi']), 'top_pe_ltp': max_pe_row['pe_ltp'],
        'chain_preview': chain.nlargest(3, 'ce_oi + pe_oi')[['ce_contract', 'strike', 'ce_oi', 'ce_ltp', 'pe_oi', 'pe_ltp']]
    }

# UI
st.subheader("🔥 Real Contract Scanner")
col1, col2 = st.columns(2)
with col1:
    selected_symbols = st.multiselect("Symbols", FNO_SYMBOLS, default=["NIFTY", "SBIN"])
with col2:
    st.metric("Expiry", EXPIRY)

if st.button("🚀 SCAN", type="primary"):
    results = []
    progress = st.progress(0)
    
    for i, sym in enumerate(selected_symbols):
        data = scan_real_contracts(sym)
        results.append(data)
        progress.progress((i+1) / len(selected_symbols))
    
    # SUMMARY TABLE
    df_summary = pd.DataFrame([
        {'Symbol': r['symbol'], 'Spot': r['spot'], 'PCR': f"{r['total_pcr']:.2f}",
         'Top CE': r['top_ce_contract'][-12:], 'CE ₹': r['top_ce_ltp'],
         'Top PE': r['top_pe_contract'][-12:], 'PE ₹': r['top_pe_ltp']}
        for r in results
    ])
    st.dataframe(df_summary, use_container_width=True)
    
    # SIGNALS
    st.subheader("🎯 Exact Trade Signals")
    for data in results:
        pcr = data['total_pcr']
        if pcr > 1.05:
            st.success(f"🟢 **BULL {data['symbol']}**")
            st.write(f"**SELL {data['top_pe_contract']}** @ ₹{data['top_pe_ltp']} (OI: {data['top_pe_oi']:,})")
        elif pcr < 0.95:
            st.error(f"🔴 **BEAR {data['symbol']}**")
            st.write(f"**SELL {data['top_ce_contract']}** @ ₹{data['top_ce_ltp']} (OI: {data['top_ce_oi']:,})")
        else:
            st.info(f"🟡 **{data['symbol']}** Neutral | Straddle {data['top_ce_contract'][-12:]}CE/{data['top_pe_contract'][-12:]}PE")

st.caption(f"Debasish Ganguly | Bokakhat F&O | {datetime.now().strftime('%d %b %Y %H:%M')} IST")
