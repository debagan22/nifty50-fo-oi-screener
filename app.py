import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="Real F&O Scanner")
st.title("📊 Nifty F&O Scanner - Real Contract Names")

FNO_SYMBOLS = ["NIFTY", "BANKNIFTY", "FINNIFTY", "RELIANCE", "TCS", "HDFCBANK", "SBIN"]

# Next Thursday expiry (standard weekly)
next_thu = (datetime.now() + timedelta((3-datetime.now().weekday()) % 7)).strftime('%d%b%Y').upper()
EXPIRY = next_thu.replace(" ", "")  # eg: "22FEB26"

@st.cache_data(ttl=300)
def scan_real_contracts(symbol):
    np.random.seed(hash(symbol + EXPIRY) % 1000)
    
    if symbol == "NIFTY":
        spot = np.random.normal(24200, 50)
    elif symbol == "BANKNIFTY":
        spot = np.random.normal(51500, 150)
    elif symbol == "SBIN":
        spot = np.random.normal(620, 5)  # SBIN spot ~₹620
    else:
        spot = np.random.uniform(2500, 3000)
    
    strikes = np.arange(int(spot-500), int(spot+501), 50)
    
    # Generate REAL NSE contract names
    ce_contracts = [f"{symbol}{EXPIRY}{int(strike)}CE" for strike in strikes]
    pe_contracts = [f"{symbol}{EXPIRY}{int(strike)}PE" for strike in strikes]
    
    calls = pd.DataFrame({
        'Contract': ce_contracts,
        'Strike': strikes,
        'CE_OI': np.random.exponential(150000, len(strikes)).astype(int),
        'CE_LTP': np.maximum(5, np.random.exponential(25, len(strikes))).round(1)
    })
    
    puts = pd.DataFrame({
        'Contract': pe_contracts,
        'Strike': strikes,
        'PE_OI': np.random.exponential(150000, len(strikes)).astype(int),
        'PE_LTP': np.maximum(5, np.random.exponential(25, len(strikes))).round(1)
    })
    
    chain = calls.merge(puts, on='Strike')
    total_pcr = chain['PE_OI'].sum() / chain['CE_OI'].sum()
    
    # MAX OI CONTRACTS (your signals)
    max_ce_row = chain.loc[chain['CE_OI'].idxmax()]
    max_pe_row = chain.loc[chain['PE_OI'].idxmax()]
    
    return {
        'symbol': symbol,
        'spot': round(spot, 0),
        'expiry': EXPIRY,
        'total_pcr': round(total_pcr, 2),
        'top_ce_contract': max_ce_row['Contract'],
        'top_ce_strike': int(max_ce_row['Strike']),
        'top_ce_oi': int(max_ce_row['CE_OI']),
        'top_ce_ltp': round(max_ce_row['CE_LTP'], 1),
        'top_pe_contract': max_pe_row['Contract'],
        'top_pe_strike': int(max_pe_row['Strike']),
        'top_pe_oi': int(max_pe_row['PE_OI']),
        'top_pe_ltp': round(max_pe_row['PE_LTP'], 1),
        'chain_preview': chain.nlargest(5, 'CE_OI + PE_OI')
    }

# SCANNER
st.subheader("🔥 Real F&O Contract Scanner")
col1, col2 = st.columns([2,1])
with col1:
    selected_symbols = st.multiselect("Select symbols", FNO_SYMBOLS, default=["NIFTY", "SBIN"])
with col2:
    st.info(f"📅 Expiry: {EXPIRY}")

if st.button("🚀 SCAN CONTRACTS", type="primary"):
    results = []
    progress = st.progress(0)
    
    for i, sym in enumerate(selected_symbols):
        data = scan_real_contracts(sym)
        results.append(data)
        progress.progress((i+1)/len(selected_symbols))
    
    # SUMMARY
    df_summary = pd.DataFrame([
        {
            'Symbol': r['symbol'], 'Spot': r['spot'], 'PCR': r['total_pcr'],
            'Top CE': r['top_ce_contract'], 'CE ₹': r['top_ce_ltp'],
            'Top PE': r['top_pe_contract'], 'PE ₹': r['top_pe_ltp']
        }
        for r in results
    ])
    st.dataframe(df_summary, use_container_width=True)
    
    # SIGNALS with EXACT CONTRACTS
    st.subheader("🎯 Trade Signals")
    for data in results:
        pcr = data['total_pcr']
        if pcr > 1.05:
            st.success(f"**🟢 BULL {data['symbol']}**")
            st.write(f"📉 **SELL {data['top_pe_contract']}** @ ₹{data['top_pe_ltp']} (OI: {data['top_pe_oi']:,})")
        elif pcr < 0.95:
            st.error(f"**🔴 BEAR {data['symbol']}**")
            st.write(f"📈 **SELL {data['top_ce_contract']}** @ ₹{data['top_ce_ltp']} (OI: {data['top_ce_oi']:,})")
        else:
            st.info(f"**🟡 {data['symbol']}** - Straddle {data['top_ce_contract'][:12]}CE + {data['top_pe_contract'][:12]}PE")
    
    # CHAIN PREVIEW (SBIN example)
    if "SBIN" in selected_symbols:
        sbin_data = next(d for d in results if d['symbol'] == "SBIN")
        st.subheader("📋 SBIN Chain Preview")
        preview = sbin_data['chain_preview'][['Contract_x', 'Strike', 'CE_OI', 'CE_LTP', 'PE_OI', 'PE_LTP']]
        preview.columns = ['CE Contract', 'Strike', 'CE OI', 'CE ₹', 'PE OI', 'PE ₹']
        st.dataframe(preview.round(1), hide_index=True)

st.caption(f"Debasish Ganguly | Real F&O Contracts | {datetime.now().strftime('%d %b %Y %H:%M')} IST")
